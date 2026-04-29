# blender_mcp_server.py
from mcp.server.fastmcp import FastMCP, Context, Image
import socket
import json
import asyncio
import logging
import tempfile
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List
import os
from pathlib import Path
import base64
from urllib.parse import urlparse

# Import telemetry
from .telemetry import record_startup, get_telemetry
from .telemetry_decorator import telemetry_tool
from ._envelope import tool_envelope, ToolError, ErrorCode, _tool_response, _check_addon_result
from ._errors import _format_error
from ._query_guide import asset_query_help_data

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlenderMCPServer")

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876


def _is_valid_http_url(value: str) -> bool:
    """Return True when value is an absolute HTTP(S) URL with a host."""
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


class BlenderCommandError(Exception):
    """Raised when the Blender addon reports an error for a command.

    Distinguished from generic Exception so callers can tell a Python
    exception inside executed code (socket healthy, addon responsive)
    from a real transport failure (socket dead, addon unreachable).
    """


@dataclass
class BlenderConnection:
    host: str
    port: int
    sock: socket.socket = None  # Changed from 'socket' to 'sock' to avoid naming conflict
    
    def connect(self) -> bool:
        """Connect to the Blender addon socket server"""
        if self.sock:
            return True
            
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Blender at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Blender: {str(e)}")
            self.sock = None
            return False
    
    def disconnect(self):
        """Disconnect from the Blender addon"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Blender: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=8192):
        """Receive the complete response, potentially in multiple chunks"""
        chunks = []
        # Use a consistent timeout value that matches the addon's timeout
        sock.settimeout(180.0)  # Match the addon's timeout
        
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        # If we get an empty chunk, the connection might be closed
                        if not chunks:  # If we haven't received anything yet, this is an error
                            raise Exception("Connection closed before receiving any data")
                        break
                    
                    chunks.append(chunk)
                    
                    # Check if we've received a complete JSON object
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        # If we get here, it parsed successfully
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue receiving
                        continue
                except socket.timeout:
                    # If we hit a timeout during receiving, break the loop and try to use what we have
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise  # Re-raise to be handled by the caller
        except socket.timeout:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise
            
        # If we get here, we either timed out or broke out of the loop
        # Try to use what we have
        if chunks:
            data = b''.join(chunks)
            logger.info(f"Returning data after receive completion ({len(data)} bytes)")
            try:
                # Try to parse what we have
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                # If we can't parse it, it's incomplete
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Blender and return the response"""
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Blender")
        
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        try:
            # Log the command being sent
            logger.info(f"Sending command: {command_type} with params: {params}")
            
            # Send the command
            self.sock.sendall(json.dumps(command).encode('utf-8'))
            logger.info(f"Command sent, waiting for response...")
            
            # Set a timeout for receiving - use the same timeout as in receive_full_response
            self.sock.settimeout(180.0)  # Match the addon's timeout
            
            # Receive the response using the improved receive_full_response method
            response_data = self.receive_full_response(self.sock)
            logger.info(f"Received {len(response_data)} bytes of data")
            
            response = json.loads(response_data.decode('utf-8'))
            logger.info(f"Response parsed, status: {response.get('status', 'unknown')}")
            
            if response.get("status") == "error":
                logger.error(f"Blender error: {response.get('message')}")
                raise BlenderCommandError(response.get("message", "Unknown error from Blender"))

            return response.get("result", {})
        except BlenderCommandError:
            # Addon responded with an error status — socket is healthy,
            # don't wrap as a communication error and don't drop the socket.
            raise
        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Blender")
            # Don't try to reconnect here - let the get_blender_connection handle reconnection
            # Just invalidate the current socket so it will be recreated next time
            self.sock = None
            raise Exception("Timeout waiting for Blender response - try simplifying your request")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.sock = None
            raise Exception(f"Connection to Blender lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Blender: {str(e)}")
            # Try to log what was received
            if 'response_data' in locals() and response_data:
                logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
            raise Exception(f"Invalid response from Blender: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with Blender: {str(e)}")
            # Don't try to reconnect here - let the get_blender_connection handle reconnection
            self.sock = None
            raise Exception(f"Communication error with Blender: {str(e)}")

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    # We don't need to create a connection here since we're using the global connection
    # for resources and tools

    try:
        # Just log that we're starting up
        logger.info("BlenderMCP server starting up")

        # Record startup event for telemetry
        try:
            record_startup()
        except Exception as e:
            logger.debug(f"Failed to record startup telemetry: {e}")

        # Try to connect to Blender on startup to verify it's available
        try:
            # This will initialize the global connection if needed
            blender = get_blender_connection()
            logger.info("Successfully connected to Blender on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Blender on startup: {str(e)}")
            logger.warning("Make sure the Blender addon is running before using Blender resources or tools")

        # Return an empty context - we're using the global connection
        yield {}
    finally:
        # Clean up the global connection on shutdown
        global _blender_connection
        if _blender_connection:
            logger.info("Disconnecting from Blender on shutdown")
            _blender_connection.disconnect()
            _blender_connection = None
        logger.info("BlenderMCP server shut down")

# Create the MCP server with lifespan support
mcp = FastMCP(
    "BlenderMCP",
    lifespan=server_lifespan
)

# Resource endpoints

# Global connection for resources (since resources can't access context)
_blender_connection = None
_polyhaven_enabled = False  # Add this global variable

def get_blender_connection():
    """Get or create a persistent Blender connection"""
    global _blender_connection, _polyhaven_enabled  # Add _polyhaven_enabled to globals
    
    # If we have an existing connection, check if it's still valid
    if _blender_connection is not None:
        try:
            # First check if PolyHaven is enabled by sending a ping command
            result = _blender_connection.send_command("get_polyhaven_status")
            # Store the PolyHaven status globally
            _polyhaven_enabled = result.get("enabled", False)
            return _blender_connection
        except Exception as e:
            # Connection is dead, close it and create a new one
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            try:
                _blender_connection.disconnect()
            except:
                pass
            _blender_connection = None
    
    # Create a new connection if needed
    if _blender_connection is None:
        host = os.getenv("BLENDER_HOST", DEFAULT_HOST)
        port = int(os.getenv("BLENDER_PORT", DEFAULT_PORT))
        _blender_connection = BlenderConnection(host=host, port=port)
        if not _blender_connection.connect():
            logger.error("Failed to connect to Blender")
            _blender_connection = None
            raise Exception("Could not connect to Blender. Make sure the Blender addon is running.")
        logger.info("Created new persistent connection to Blender")
    
    return _blender_connection


@mcp.tool()
@telemetry_tool("get_scene_info")
@tool_envelope
def get_scene_info(ctx: Context, full: bool = False) -> str:
    """Get information about the current Blender scene.

    Two modes:
    - full=False (default): first 10 objects with name + type + location.
      Designed to keep transport payload small — use when you just need
      "what's the active scene named, what version of Blender".
    - full=True: every object in the scene, each with name + type +
      poly_count. Use this for cleanup decisions ("which 167 leftover
      Test* objects can I delete?"). Larger payload but still bounded
      by object_count, not by mesh detail.

    Response includes Blender version (e.g. [5, 1, 0]) and version
    string. Inspect these before emitting code that touches version-
    sensitive surface (shader/modifier enums, operator arguments,
    renamed APIs).
    """
    blender = get_blender_connection()
    result = _check_addon_result(
        blender.send_command("get_scene_info", {"full": full}))
    return result

@mcp.tool()
@telemetry_tool("get_object_info")
@tool_envelope
def get_object_info(
    ctx: Context,
    object_name: str = None,
    names: list[str] = None,
) -> str:
    """Get info about one or many objects in the scene.

    - Pass `object_name="Cube"` to get a single object's info dict
      (vertices, polys, materials, world location, bounding box).
    - Pass `names=["Cube", "Sphere", ...]` to fetch multiple objects in
      one call. Response shape: {"objects": {name: info_or_error}}.
      Missing objects have `{"error": "..."}` in their slot — the call
      doesn't fail just because one name is wrong.

    Use the batch form whenever you'd otherwise loop multiple
    `get_object_info` calls — fewer round trips, lower token cost.
    """
    if object_name is None and not names:
        raise ToolError(
            ErrorCode.BAD_INPUT,
            hint="Provide either `object_name` (str) or `names` (list[str])",
        )
    payload = {}
    if object_name is not None:
        payload["object_name"] = object_name
    if names is not None:
        payload["names"] = names
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_object_info", payload))
    return result

@mcp.tool()
@telemetry_tool("get_viewport_screenshot")
def get_viewport_screenshot(
    ctx: Context,
    max_size: int = 800,
    target_object: str = None,
    view: str = "front",
    distance_factor: float = 2.5,
    ortho_padding: float = 1.25,
) -> Image:
    """
    Capture a screenshot of the current Blender 3D viewport OR a clean
    orthographic diagnostic render of a specific object.

    Default behavior (target_object=None): screenshots the active viewport
    as the user sees it, including overlays and the user's camera.

    If `target_object` is provided: creates a temporary orthographic camera
    framed on that object from the named `view` direction and renders a
    clean image. Use this to verify visual claims — grounding, alignment,
    material changes — without relying on position math that lies after
    asymmetric mesh edits or Displace modifiers.

    Parameters:
    - max_size: Maximum pixels for the longest dimension (default 800).
    - target_object: If set, render an orthographic view of this object instead
      of a viewport screenshot.
    - view: Axis direction for the diagnostic view. One of:
      front, back, left, right, top, bottom. Default 'front'.
    - distance_factor: Camera distance as a multiple of the object's largest
      world-bbox dimension (default 2.5).
    - ortho_padding: Ortho scale multiplier (default 1.25, >1 leaves margin).

    Returns the screenshot/render as an Image.
    """
    try:
        blender = get_blender_connection()

        # Create temp file path
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"blender_screenshot_{os.getpid()}.png")

        params = {
            "max_size": max_size,
            "filepath": temp_path,
            "format": "png",
        }
        if target_object is not None:
            params["target_object"] = target_object
            params["view"] = view
            params["distance_factor"] = distance_factor
            params["ortho_padding"] = ortho_padding

        result = blender.send_command("get_viewport_screenshot", params)

        if "error" in result:
            raise Exception(result["error"])
        
        if not os.path.exists(temp_path):
            raise Exception("Screenshot file was not created")
        
        # Read the file
        with open(temp_path, 'rb') as f:
            image_bytes = f.read()
        
        # Delete the temp file
        os.remove(temp_path)
        
        return Image(data=image_bytes, format="png")
        
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise Exception(f"Screenshot failed: {str(e)}")


@mcp.tool()
@telemetry_tool("verify_object_grounded")
@tool_envelope
def verify_object_grounded(
    ctx: Context,
    object_name: str,
    ground_name: str,
    slice_height: float = 1.0,
    max_samples: int = 500,
) -> str:
    """
    Measure the vertical gap between an object's base and a ground mesh.

    Samples vertices from the object's lower slice (world z within
    `slice_height` of the object's lowest vertex) and raycasts straight down
    onto the ground's evaluated mesh. Returns a JSON summary with min, max,
    median, and mean gap in meters. Positive = above ground, negative =
    intersecting. Uses evaluated geometry, so Displace modifiers on the
    ground and armature/shape-key deformation on the object are honored.

    Use this to verify grounding instead of relying on `object.location.z`
    or `object.dimensions`, both of which lie after asymmetric mesh edits
    (e.g., bottom-half deletion of a sphere to make a hemisphere).

    Parameters:
    - object_name: The object whose base should rest on the ground.
    - ground_name: The mesh that serves as the ground plane.
    - slice_height: Meters above the object's bottom to sample from
      (default 1.0). Keep small for trees / canopy-heavy meshes so the
      sample is actually the trunk/base, not lower branches.
    - max_samples: Cap on raycasts (default 500).
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("verify_object_grounded", {
        "object_name": object_name,
        "ground_name": ground_name,
        "slice_height": slice_height,
        "max_samples": max_samples,
    }))
    return result


# --------------------------------------------------------------------------
# Design-workflow helpers (added by fork) — high-frequency operations that
# would otherwise require execute_blender_code boilerplate.
# --------------------------------------------------------------------------

@mcp.tool()
@tool_envelope
def apply_material_color(
    ctx: Context,
    object_name: str,
    hex_color: str,
    roughness: float = 0.7,
    metallic: float = 0.0,
    emission_color: str = None,
    emission_strength: float = 0.0,
) -> str:
    """
    Apply a single solid Principled BSDF material to an object.

    Use this when you want a flat painted surface (walls, doors, panels) and
    do NOT need a textured material. Replaces any existing material on the
    object with a new BSDF tinted to hex_color.

    Parameters:
    - object_name: Mesh object to paint
    - hex_color: '#RRGGBB' or '#RGB' or 'RRGGBB'
    - roughness: 0..1 (0=mirror, 1=matte)
    - metallic: 0..1 (0=dielectric, 1=metal)
    - emission_color: Optional '#RRGGBB' for self-illuminating surfaces
    - emission_strength: Emission watts/m^2 multiplier (0..many)
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("apply_material_color", {
        "object_name": object_name,
        "hex_color": hex_color,
        "roughness": roughness,
        "metallic": metallic,
        "emission_color": emission_color,
        "emission_strength": emission_strength,
    }))
    return result


@mcp.tool()
@tool_envelope
def apply_glass_material(
    ctx: Context,
    object_name: str,
    tint_hex: str = "#FFFFFF",
    emission_color: str = None,
    emission_strength: float = 0.0,
    transmission: float = 0.95,
    roughness: float = 0.05,
    ior: float = 1.45,
    material_name: str = None,
) -> str:
    """
    Apply a Principled BSDF tuned for glass on a mesh. Common in
    archviz: windows, glasses, water surfaces, screens, transparent
    plastic.

    Parameters:
    - object_name: target mesh.
    - tint_hex: '#RRGGBB' base color (#FFFFFF = clear; #ffc77a = amber).
    - emission_color: '#RRGGBB' interior glow color, or None.
    - emission_strength: 0-10 typical. 1.5 reads as 'lit interior'.
    - transmission: 0-1 (0.95+ for true glass).
    - roughness: 0-1 (0.05 clear; 0.3+ frosted).
    - ior: 1.45 glass / 1.33 water / 1.5 lead crystal.
    - material_name: optional override; default 'Glass_<object_name>'.

    Returns the assigned material name + the parameters applied.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("apply_glass_material", {
        "object_name": object_name,
        "tint_hex": tint_hex,
        "emission_color": emission_color,
        "emission_strength": emission_strength,
        "transmission": transmission,
        "roughness": roughness,
        "ior": ior,
        "material_name": material_name,
    }))
    return result


@mcp.tool()
@tool_envelope
def delete_objects(
    ctx: Context,
    names: List[str] = None,
    patterns: List[str] = None,
    keep: List[str] = None,
    purge_orphans: bool = True,
) -> str:
    """
    Bulk-remove scene objects by name list and/or fnmatch glob
    patterns, with an allowlist that's never touched.

    Common pattern -- clean up after import / scatter test:

        delete_objects(
            patterns=["Test*", "Cone.*", "Cube.*", "Cylinder.*"],
            keep=["HouseBody", "Roof", "Camera", "Ground"],
        )

    Avoids 20+ lines of execute_blender_code: walking bpy.data.objects,
    matching, removing, then purging orphans. The `keep` allowlist wins
    over both `names` and `patterns` -- listing a name in both `names`
    and `keep` will preserve it, not remove it.

    Parameters:
    - names: explicit exact-match names to remove.
    - patterns: fnmatch globs ("Test*"). Matched against object names.
    - keep: names that must NOT be removed (overrides names + patterns).
    - purge_orphans: when True (default), runs orphans_purge after
      removal to free unused meshes/materials/images.

    Returns: count + sample of removed names + protected count.
    """
    if not names and not patterns:
        raise ToolError(
            ErrorCode.BAD_INPUT,
            hint="Provide at least one of `names` or `patterns`",
        )
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("delete_objects", {
        "names": names or [],
        "patterns": patterns or [],
        "keep": keep or [],
        "purge_orphans": purge_orphans,
    }))
    return result


@mcp.tool()
@tool_envelope
def place_on_ground(
    ctx: Context,
    object_name: str,
    ground_z: float = 0.0,
    center_xy: bool = False,
    target_xy: List[float] = None,
) -> str:
    """
    Translate an object so the bottom of its world bounding box sits on ground_z.

    Useful immediately after importing a Sketchfab/Polyhaven model whose origin
    is offset from its visible base. Walks descendant meshes so FBX/GLB
    hierarchies (multi-mesh imports with empty parents) work without flattening.

    Parameters:
    - object_name: Object (or hierarchy root) to ground
    - ground_z: Target world z for the bbox bottom (default 0)
    - center_xy: If True, also recenter the bbox to (0, 0) on the XY plane
    - target_xy: If provided ([x, y]), center the bbox there (overrides center_xy)
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("place_on_ground", {
        "object_name": object_name,
        "ground_z": ground_z,
        "center_xy": center_xy,
        "target_xy": target_xy,
    }))
    return result


@mcp.tool()
@tool_envelope
def render_image(
    ctx: Context,
    filepath: str,
    resolution: List[int] = None,
    samples: int = 64,
    engine: str = "CYCLES",
    use_gpu: bool = True,
    view_transform: str = "Filmic",
    look: str = "Medium High Contrast",
    return_preview: bool = False,
    preview_max_dim: int = 256,
) -> str:
    """
    Render the active camera to a PNG file with one call.

    Skips the boilerplate of setting scene.render.engine, samples, resolution,
    tone-mapping, and triggering bpy.ops.render. Returns the absolute filepath
    on success.

    Parameters:
    - filepath: Output PNG path (.png appended if missing)
    - resolution: [width, height] (default 1920x1080 if scene unset)
    - samples: Cycles samples (ignored for EEVEE)
    - engine: 'CYCLES' or 'EEVEE'
    - use_gpu: Try GPU device for Cycles
    - view_transform: 'Filmic' (default), 'Standard', 'AgX', etc.
    - look: 'Medium High Contrast' (default), 'None', 'High Contrast', etc.
    - return_preview: When True, the response includes a `preview_b64` key
      holding a base64-encoded JPEG thumbnail of the render so the LLM can
      see it inline without a separate file Read step. Default False.
    - preview_max_dim: Longest-side pixel cap for the preview thumbnail
      (default 256). Only used when return_preview=True.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("render_image", {
        "filepath": filepath,
        "resolution": resolution,
        "samples": samples,
        "engine": engine,
        "use_gpu": use_gpu,
        "view_transform": view_transform,
        "look": look,
        "return_preview": return_preview,
        "preview_max_dim": preview_max_dim,
    }))
    return result


@mcp.tool()
@tool_envelope
def set_camera_view(
    ctx: Context,
    target_object: str = None,
    target_xyz: List[float] = None,
    angle: str = "3q",
    distance: float = 10.0,
    lens: float = 35.0,
    height_offset: float = 0.0,
) -> str:
    """
    WHEN TO USE THIS vs frame_camera_to_objects:
    - set_camera_view: pick a preset angle (front/back/left/right/top/3q/iso)
      for a quick one-call camera positioning. No DOF, no composition rules.
    - frame_camera_to_objects: fit camera to a list of target objects with
      composition (thirds/center) + optional DOF. Preferred for hero shots.

    Position the active camera to look at a target using a preset angle.

    Skips quaternion math. Either target_object (name) or target_xyz must be
    provided. If no camera exists in the scene, one is created.

    Parameters:
    - target_object: Look at this object's bounding-box center
    - target_xyz: Or look at this explicit world-space point
    - angle: One of 'front', 'back', 'left', 'right', 'top',
             '3q' (3/4 hero — default), 'iso' (isometric)
    - distance: Camera distance from target (meters)
    - lens: Focal length in mm (35=wide-ish, 50=natural, 85=portrait)
    - height_offset: Raise the look-at point this much above bbox center
                     (useful to compose toward an upper feature like a roof)
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("set_camera_view", {
        "target_object": target_object,
        "target_xyz": target_xyz,
        "angle": angle,
        "distance": distance,
        "lens": lens,
        "height_offset": height_offset,
    }))
    return result


# --------------------------------------------------------------------------
# Sprint 2 helpers — generic geometry/lighting/composition wrappers
# --------------------------------------------------------------------------

@mcp.tool()
@tool_envelope
def mesh_cleanup(
    ctx: Context,
    object_name: str,
    merge_distance: float = 0.0001,
    decimate_ratio: float = 1.0,
    recalc_normals: bool = True,
    remove_loose: bool = True,
    fix_non_manifold: bool = False,
    triangulate: bool = False,
) -> str:
    """
    Clean up a mesh in one call: merge duplicate vertices, recalc normals,
    optional decimate, remove loose verts/edges, optional non-manifold fix
    and triangulate.

    Essential preprocessing for any imported scan (LiDAR, photogrammetry) —
    those typically have duplicate vertices, flipped normals, and 100k+
    triangles. Idempotent on already-clean meshes.

    Parameters:
    - object_name: Mesh to clean
    - merge_distance: Merge verts within this radius (meters). 0 to skip.
    - decimate_ratio: 1.0 = no decimate; 0.5 = halve face count; 0.1 = 10% kept
    - recalc_normals: Recompute consistent outward normals
    - remove_loose: Delete loose verts and edges
    - fix_non_manifold: Try to fill non-manifold edges (best-effort)
    - triangulate: Convert all quads/ngons to triangles

    Returns before/after vertex/edge/face counts.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("mesh_cleanup", {
        "object_name": object_name,
        "merge_distance": merge_distance,
        "decimate_ratio": decimate_ratio,
        "recalc_normals": recalc_normals,
        "remove_loose": remove_loose,
        "fix_non_manifold": fix_non_manifold,
        "triangulate": triangulate,
    }))
    return result


@mcp.tool()
@tool_envelope
def boolean_cutout(
    ctx: Context,
    target_object: str,
    cutter_shape: str = "box",
    location: List[float] = (0, 0, 0),
    size: List[float] = (1, 1, 1),
    rotation: List[float] = (0, 0, 0),
    cutter_object_name: str = None,
    operation: str = "DIFFERENCE",
    solver: str = "EXACT",
    apply: bool = True,
) -> str:
    """
    Cut a hole / merge / intersect with a primitive (or named mesh).

    Common interior-design ops: window apertures in walls, door cutouts,
    vent holes, decorative mortises. The native bpy flow is ~25 lines and
    LLMs frequently pick the wrong solver or forget to clean up the cutter.

    Parameters:
    - target_object: Mesh that will be cut/merged
    - cutter_shape: 'box' | 'cylinder' | 'sphere' | 'mesh'
    - location: World-space center of the primitive cutter [x, y, z]
    - size: XYZ extents of the primitive cutter (meters)
    - rotation: Euler radians [rx, ry, rz] for primitive cutters
    - cutter_object_name: Required when cutter_shape='mesh' — name of an
      existing object to use (will not be deleted)
    - operation: 'DIFFERENCE' (default — hole), 'UNION', 'INTERSECT'
    - solver: 'EXACT' (slower, robust on overlapping geometry — recommended
      for clean architectural cuts), 'FAST' (legacy, faster, fragile)
    - apply: True applies the modifier and removes the primitive cutter;
      False keeps the modifier live (useful for non-destructive workflows)

    Example: cut an 80x150cm doorway in 'WallA':
      boolean_cutout('WallA', 'box', location=[0, 0, 1.0], size=[0.8, 0.5, 2.0])
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("boolean_cutout", {
        "target_object": target_object,
        "cutter_shape": cutter_shape,
        "location": list(location),
        "size": list(size),
        "rotation": list(rotation),
        "cutter_object_name": cutter_object_name,
        "operation": operation,
        "solver": solver,
        "apply": apply,
    }))
    return result


@mcp.tool()
@tool_envelope
def frame_camera_to_objects(
    ctx: Context,
    targets: List[str],
    orbit_deg: float = 35.0,
    elevation_deg: float = 15.0,
    focal_mm: float = 35.0,
    padding: float = 1.1,
    composition: str = "thirds_left",
    dof_target: str = None,
    f_stop: float = 2.8,
    camera_xyz: List[float] = None,
) -> str:
    """
    WHEN TO USE THIS vs set_camera_view:
    - frame_camera_to_objects: needed when you want the camera to actually
      contain specific objects in its frame, with composition + DOF.
    - set_camera_view: when you just need a preset angle, no specific subject.

    Position the active camera so all targets fit in frame, with composed
    orbit + elevation + thirds offset.

    LLMs frequently put cameras inside walls or aimed at the world origin;
    this wraps Blender's camera_to_view_selected logic with sensible
    composition defaults. Uses lens shift (not tilt) for thirds offset so
    verticals stay straight — the single biggest "looks pro vs amateur"
    tell in archviz.

    Two positioning modes:

    1. **Implicit (orbit + elevation)** — default. The camera is placed
       on a sphere around the targets' bbox at `orbit_deg` around Z and
       `elevation_deg` above horizontal. Good for quick 3/4 hero shots
       when you don't care about exact vantage.

    2. **Explicit (`camera_xyz=[x, y, z]`)** — the camera is placed at
       exactly those world coordinates and aimed at the targets' bbox
       center. `orbit_deg` and `elevation_deg` are ignored. Use this
       when you know the vantage you want — orbit math conventions
       (`0=front`) aren't obvious for arbitrary scenes. Composition
       presets are skipped in explicit mode.

    Parameters:
    - targets: Single object name or list — frames their combined bbox
    - orbit_deg: Rotation around Z (0=front, 90=right side, 180=back)
    - elevation_deg: Tilt above horizontal (0=level, 45=down-angled, 90=top)
    - focal_mm: Lens focal length (24=wide, 35=natural, 50=portrait, 85=tight)
    - padding: 1.0 = bbox kisses frame edges; 1.2 = 20% breathing room
    - composition: 'center' | 'thirds_left' | 'thirds_right' |
                   'thirds_top' | 'thirds_bottom'
    - dof_target: Optional object name to focus on (enables DOF)
    - f_stop: Aperture (lower = more blur). Only used when dof_target is set.
    - camera_xyz: [x, y, z] world coords for explicit mode (overrides
      orbit/elevation). When None (default), uses orbit/elevation.

    Returns final camera location, distance, FOV, etc.
    """
    if isinstance(targets, str):
        targets = [targets]
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("frame_camera_to_objects", {
        "targets": targets,
        "orbit_deg": orbit_deg,
        "elevation_deg": elevation_deg,
        "focal_mm": focal_mm,
        "padding": padding,
        "composition": composition,
        "dof_target": dof_target,
        "f_stop": f_stop,
        "camera_xyz": camera_xyz,
    }))
    return result


@mcp.tool()
@tool_envelope
def setup_lighting(
    ctx: Context,
    mood: str = "warm_intimate",
    target_object: str = None,
    target_xyz: List[float] = None,
    area_m2: float = 20.0,
    ceiling_height_m: float = 3.0,
    remove_existing_lights: bool = True,
) -> str:
    """
    Build a 3-layer lighting rig (ambient + accent + key) tuned to a named
    design-intent mood. Generic across cafe / retail / residential / office /
    studio — the mood describes intent, not space type.

    Available moods:
    - warm_intimate     — Low Kelvin, low ambient, strong table-level key.
                          Bars, lounges, evening dining, bedrooms.
    - daylight_neutral  — Balanced 4000-4500K, medium lux, soft sky fill.
                          Daylit interior shoots, residential common areas.
    - bright_workspace  — High lux, neutral 4000K, even coverage.
                          Offices, kitchens, classrooms, retail back-of-house.
    - dramatic_accent   — Low ambient + tight accent spotlights.
                          Galleries, retail focal displays, hero plates.
    - golden_hour       — Warm sun-side key + cool sky ambient.
                          Exterior renders, interior at sunset.
    - cool_modern       — 5500-6500K, clean even lighting.
                          Modernist showrooms, modern offices.
    - studio_neutral    — 5500K even product photography setup.
                          Product viz, e-commerce, neutral catalog.
    - moody_lowkey      — Deep shadows, small key, no fill.
                          Cinematic, noir, mystery, horror.

    Parameters:
    - mood: One of the keys above
    - target_object: Focal point object (uses bbox center)
    - target_xyz: Or explicit [x, y, z] focal point
    - area_m2: Room floor area in square meters (used to scale wattage)
    - ceiling_height_m: Where to place ambient lights
    - remove_existing_lights: Clear MCP_*-prefixed lights before building

    Returns the created light names + key parameters.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("setup_lighting", {
        "mood": mood,
        "target_object": target_object,
        "target_xyz": target_xyz,
        "area_m2": area_m2,
        "ceiling_height_m": ceiling_height_m,
        "remove_existing_lights": remove_existing_lights,
    }))
    return result


@mcp.tool()
@tool_envelope
def apply_archviz_material(
    ctx: Context,
    object_name: str,
    genre: str,
    color_hint: str = None,
    finish: str = None,
    resolution: str = "2k",
    custom_hex: str = None,
    roughness: float = 0.7,
    library: str = "auto",
    uv_scale: float = None,
) -> str:
    """
    Apply a textured PBR material chosen by generic genre keyword.

    Routes through PolyHaven by default, picking from a curated list of
    candidate asset IDs per genre. For flat painted surfaces, pass
    genre='painted_wall' along with custom_hex='#RRGGBB' to short-circuit
    to apply_material_color (no texture download needed).

    Available genres (call list_archviz_genres for the up-to-date list):
    - painted_wall (special — requires custom_hex)
    - hardwood_floor, softwood_planks, exposed_wood
    - brick_wall, brick_floor
    - concrete_smooth, concrete_rough, plaster_wall
    - natural_stone, tile_ceramic
    - metal_industrial
    - grass_ground, roof_clay_tiles, roof_slate

    Parameters:
    - object_name: Mesh to apply the material to
    - genre: One of the genre keys above
    - color_hint, finish: Reserved for future filtering (currently ignored)
    - resolution: '1k' / '2k' (default) / '4k' / '8k' for PolyHaven download
    - custom_hex: Required when genre='painted_wall' ('#RRGGBB')
    - roughness: Roughness for painted_wall (0..1)
    - library: 'auto' (default) | 'polyhaven'
    - uv_scale: optional UV repeat multiplier (1.0-8.0 typical). When None,
      uses the genre's default. Set to e.g. 4.0 when the default reads too
      coarse on a small mesh ('roof_clay_tiles' on a 5m roof). Ignored for
      painted_wall (no Mapping node).
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("apply_archviz_material", {
        "object_name": object_name,
        "genre": genre,
        "color_hint": color_hint,
        "finish": finish,
        "resolution": resolution,
        "custom_hex": custom_hex,
        "roughness": roughness,
        "library": library,
        "uv_scale": uv_scale,
    }))
    return result


@mcp.tool()
@tool_envelope
def list_archviz_genres(ctx: Context) -> str:
    """
    Return the full list of generic genre keys for apply_archviz_material,
    each with a description, default UV scale, and candidate PolyHaven
    asset IDs. Use this for discovery before calling apply_archviz_material.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("list_archviz_genres", {}))
    return result


@mcp.tool()
@tool_envelope
def get_ambientcg_status(ctx: Context) -> str:
    """Check if ambientCG (CC0 PBR texture library, ~2000+ materials) is
    reachable. No API key required — public CC0 service."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_ambientcg_status", {}))
    return result


@mcp.tool()
@tool_envelope
def search_ambientcg_assets(
    ctx: Context,
    query: str = None,
    asset_type: str = "Material",
    category: str = None,
    limit: int = 20,
) -> str:
    """
    Search the ambientCG asset library (CC0 PBR textures + HDRIs).

    Complements PolyHaven for materials it doesn't cover well — fabrics,
    leather, more concrete variants, plant decals.

    **Query tips:** single material noun beats sentences. Skip color
    adjectives (apply tint via shader after download). 'velvet' returns
    many; 'green velvet sofa upholstery' returns zero. Categories help
    when free text is too broad: pair `query='brick'` with
    `category='Bricks'` for cleaner results. For the full per-service
    query cheat sheet, call `asset_query_help`.

    Parameters:
    - query: Free-text search, single noun preferred (e.g. 'brick',
             'velvet', 'corduroy', 'rusted metal')
    - asset_type: 'Material' (default) | 'HDRI' | '3DModel' | 'Decal' | 'PlantModel'
    - category: Bricks | Wood | Fabric | Concrete | Metal | Plaster |
                Plastic | Stone | Tiles | Ceramic | Leather | Carpet |
                Asphalt | Roof | Ground | Plants
    - limit: Max results (1-100)

    Returns asset_ids + categories + tags + available resolutions.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("search_ambientcg_assets", {
        "query": query,
        "asset_type": asset_type,
        "category": category,
        "limit": limit,
    }))
    from ._filters import attach_zero_result_hint
    result = attach_zero_result_hint(result, service="ambientcg")
    return result


@mcp.tool()
@tool_envelope
def download_ambientcg_asset(
    ctx: Context,
    asset_id: str,
    resolution: str = "2k",
    file_format: str = "jpg",
) -> str:
    """
    Download a CC0 ambientCG material, extract maps, and create a Blender
    material wired up like a PolyHaven texture import (Color/Roughness/
    Normal/Metallic/Displacement/AO).

    Use search_ambientcg_assets first to find the asset_id.

    Parameters:
    - asset_id: e.g. 'Bricks001', 'WoodFloor035', 'Fabric001'
    - resolution: '1k' | '2k' (default) | '4k' | '8k'
    - file_format: 'jpg' (default — smaller) | 'png'

    Returns the created material name + which maps were loaded.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("download_ambientcg_asset", {
        "asset_id": asset_id,
        "resolution": resolution,
        "file_format": file_format,
    }))
    return result


# --------------------------------------------------------------------------
# Sprint 3 — scatter / array / curve / export / hdri
# --------------------------------------------------------------------------

@mcp.tool()
@tool_envelope
def scatter_on_surface(
    ctx: Context,
    surface_object: str,
    instance_objects: List[str],
    density: float = 10.0,
    max_count: int = 1000,
    seed: int = 0,
    scale_min: float = 0.8,
    scale_max: float = 1.2,
    rotate_random: bool = True,
    align_to_normal: bool = True,
    parent_to_surface: bool = False,
    collection_name: str = None,
) -> str:
    """
    Distribute copies of one or more objects across a surface mesh,
    area-weighted with random rotation/scale and optional normal alignment.

    Use cases: books on a shelf, bottles on a bar, gravel on a path,
    scattered foliage on terrain, plates on a table.

    Parameters:
    - surface_object: mesh whose faces define the placement region
    - instance_objects: name or list of names — randomly picked per placement
    - density: target placements per square meter
    - max_count: hard cap on placements (safety)
    - seed: RNG seed for reproducibility
    - scale_min, scale_max: random uniform scale multiplier per instance
    - rotate_random: random rotation around the surface normal
    - align_to_normal: rotate instance so +Z aligns with face normal
                      (good for surfaces; disable for vertical decor)
    - parent_to_surface: parent each instance to surface_object
    - collection_name: link instances into a (newly created) collection

    Linked-data copies are created so memory stays low.
    """
    if isinstance(instance_objects, str):
        instance_objects = [instance_objects]
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("scatter_on_surface", {
        "surface_object": surface_object,
        "instance_objects": instance_objects,
        "density": density,
        "max_count": max_count,
        "seed": seed,
        "scale_min": scale_min,
        "scale_max": scale_max,
        "rotate_random": rotate_random,
        "align_to_normal": align_to_normal,
        "parent_to_surface": parent_to_surface,
        "collection_name": collection_name,
    }))
    return result


@mcp.tool()
@tool_envelope
def array_duplicate(
    ctx: Context,
    source_object: str,
    mode: str = "linear",
    count: int = 5,
    offset: List[float] = None,
    angle_deg: float = 360.0,
    axis: str = "Z",
    center: List[float] = None,
    apply: bool = False,
) -> str:
    """
    Duplicate an object linearly or radially using a Blender Array modifier
    (live or applied).

    Linear example (5 pendant lights spaced 1m on X):
      array_duplicate('Pendant', 'linear', 5, offset=[1.0, 0, 0])
    Radial example (8 chairs around a table center, full circle on Z):
      array_duplicate('Chair', 'radial', 8, angle_deg=360, axis='Z',
                      center=[0, 0, 0])

    Parameters:
    - source_object: object to duplicate
    - mode: 'linear' | 'radial'
    - count: total copies including the original (>= 2)
    - offset: linear mode [dx, dy, dz] world-space step. None = default
              dimensions.x × 1.05 along X.
    - angle_deg: radial mode total spread (default 360 = full ring)
    - axis: radial mode rotation axis 'X' | 'Y' | 'Z'
    - center: radial mode pivot [x, y, z]; None = source object location
    - apply: True applies modifier (and removes radial helper Empty);
             False keeps it live for tweaking
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("array_duplicate", {
        "source_object": source_object,
        "mode": mode,
        "count": count,
        "offset": list(offset) if offset is not None else None,
        "angle_deg": angle_deg,
        "axis": axis,
        "center": list(center) if center is not None else None,
        "apply": apply,
    }))
    return result


@mcp.tool()
@tool_envelope
def curve_extrude_profile(
    ctx: Context,
    name: str,
    path_points: List[List[float]],
    profile: str = "round",
    thickness: float = 0.02,
    resolution: int = 12,
    closed: bool = False,
    smooth: bool = True,
    convert_to_mesh: bool = False,
    location: List[float] = (0, 0, 0),
) -> str:
    """
    Build a curve from path_points and apply a bevel profile — for neon
    signs, brass pipes, electrical cables, decorative trim, railings,
    handrails, hose runs.

    Parameters:
    - name: name for the new curve object
    - path_points: list of [x, y, z] — at least 2 points
    - profile: 'round' (cylindrical) | 'square' | 'flat' (extruded ribbon)
               | name of an existing 2D curve object for custom profile
    - thickness: bevel depth (radius for round, half-width for square,
                 extrusion for flat)
    - resolution: bevel smoothness (round/square only)
    - closed: True closes the curve into a loop
    - smooth: shade smooth (round profile only)
    - convert_to_mesh: convert curve to mesh after creation
    - location: object origin offset
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("curve_extrude_profile", {
        "name": name,
        "path_points": [list(p) for p in path_points],
        "profile": profile,
        "thickness": thickness,
        "resolution": resolution,
        "closed": closed,
        "smooth": smooth,
        "convert_to_mesh": convert_to_mesh,
        "location": list(location),
    }))
    return result


@mcp.tool()
@tool_envelope
def quick_export(
    ctx: Context,
    filepath: str,
    objects: List[str] = None,
    format: str = "auto",
    pack_textures: bool = True,
    apply_modifiers: bool = True,
    selected_only: bool = False,
    axis_forward: str = "-Z",
    axis_up: str = "Y",
    draco: bool = True,
) -> str:
    """
    Export objects to GLB / FBX / OBJ / USD with sensible defaults for
    contractor / 3D viewer / game engine handoff.

    Format auto-detected from extension. Always packs textures for GLB by
    default (otherwise clients open empty files — the #1 r/blender gotcha).

    Parameters:
    - filepath: output path; extension drives format if format='auto'
    - objects: list of object names; None = whole scene
    - format: 'auto' | 'glb' | 'gltf' | 'fbx' | 'obj' | 'usd' | 'usdz'
    - pack_textures: GLB/USDZ embed textures into file; FBX copy alongside
    - apply_modifiers: bake modifier stack at export
    - selected_only: export only currently selected (overrides `objects`)
    - axis_forward, axis_up: coordinate convention for FBX/OBJ
    - draco: GLB Draco mesh compression
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("quick_export", {
        "filepath": filepath,
        "objects": objects,
        "format": format,
        "pack_textures": pack_textures,
        "apply_modifiers": apply_modifiers,
        "selected_only": selected_only,
        "axis_forward": axis_forward,
        "axis_up": axis_up,
        "draco": draco,
    }))
    return result


@mcp.tool()
@tool_envelope
def set_world_hdri_rotation(
    ctx: Context,
    z_rotation_deg: float = 0.0,
    strength: float = None,
) -> str:
    """
    Rotate the world environment HDRI around Z and/or set its strength.

    Convenient for time-of-day adjustments without re-downloading: spin
    the existing HDRI to put the sun behind/in-front-of the camera.

    Parameters:
    - z_rotation_deg: rotation around Z (0 = original orientation)
    - strength: if provided, set Background node strength (typical 0.3-2.0)

    Requires an HDRI to be already loaded (e.g. via download_polyhaven_asset).
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("set_world_hdri_rotation", {
        "z_rotation_deg": z_rotation_deg,
        "strength": strength,
    }))
    return result


# --------------------------------------------------------------------------
# Sprint 4 — AI 3D generation: Tripo3D + Meshy.ai
# Sync wrappers (kick-off + poll + download + import in one MCP call) so
# the LLM gets a single round-trip per generation request.
# --------------------------------------------------------------------------

@mcp.tool()
@tool_envelope
def get_tripo3d_status(ctx: Context) -> str:
    """Check if Tripo3D is configured and reachable. Tripo3D is a top-tier
    text-to-3D / image-to-3D service with full PBR output."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_tripo3d_status", {}))
    return result


@mcp.tool()
@tool_envelope
def generate_tripo3d_text_to_3d(
    ctx: Context,
    prompt: str,
    model_version: str = None,
    texture: bool = True,
    pbr: bool = True,
    face_limit: int = 30000,
    target_size: float = 2.0,
    max_wait_seconds: int = 240,
) -> str:
    """
    Generate a 3D model from text via Tripo3D — synchronous: the call
    creates the task, polls until done, downloads the GLB, and imports
    into the scene. Returns task_id, imported object names, and download URL.

    **Prompt tips:** ONE object, not a scene. 'a chair' beats 'a chair
    in a lounge'. Bake material + style into the prompt: 'hand-thrown
    ceramic vase, raku glaze, photorealistic'. Color-and-material
    specifics win: 'walnut wood' beats 'brown wood'. For the full prompt
    cheat sheet, call `asset_query_help(service='tripo3d')`.

    Parameters:
    - prompt: SINGLE-object English description with material + style
              (e.g. "hand-thrown ceramic vase with raku glaze, ornate")
    - model_version: 'v3.1-20260211' (default, newest), 'v3.0-20250812',
                     'v2.5-20250123', 'P1-20260311' (low-poly tuned)
    - texture: include textures
    - pbr: use PBR shading (recommended for archviz)
    - face_limit: max polygon count (1000 - 100000). Drop to ~10000 for
                  blockouts; raise to 50000+ for hero objects.
    - target_size: rescale imported model so largest dim = this many meters
    - max_wait_seconds: polling timeout (typical 30-90s; up to 4 min)

    Cost estimate: 3-10 credits per generation (~$0.03-$0.10).
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("generate_tripo3d_text_to_3d", {
        "prompt": prompt,
        "model_version": model_version,
        "texture": texture,
        "pbr": pbr,
        "face_limit": face_limit,
        "target_size": target_size,
        "max_wait_seconds": max_wait_seconds,
    }))
    return result


@mcp.tool()
@tool_envelope
def generate_tripo3d_image_to_3d(
    ctx: Context,
    image_url: str,
    model_version: str = None,
    texture: bool = True,
    pbr: bool = True,
    target_size: float = 2.0,
    max_wait_seconds: int = 240,
) -> str:
    """
    Generate a 3D model from a single reference image via Tripo3D.

    Parameters:
    - image_url: PUBLIC URL to a JPG/PNG/WebP. For local files, host them
      first (imgur, S3, etc.) or use the Hyper3D image-upload path.
    - model_version: see generate_tripo3d_text_to_3d
    - texture, pbr: enable texturing / PBR
    - target_size: rescale imported model so largest dim = this many meters
    - max_wait_seconds: polling timeout
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("generate_tripo3d_image_to_3d", {
        "image_url": image_url,
        "model_version": model_version,
        "texture": texture,
        "pbr": pbr,
        "target_size": target_size,
        "max_wait_seconds": max_wait_seconds,
    }))
    return result


@mcp.tool()
@tool_envelope
def get_meshy_status(ctx: Context) -> str:
    """Check if Meshy.ai is configured and reachable. Meshy.ai is a top-tier
    text-to-3D / image-to-3D service with strong all-around quality."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_meshy_status", {}))
    return result


@mcp.tool()
@tool_envelope
def generate_meshy_text_to_3d(
    ctx: Context,
    prompt: str,
    ai_model: str = "meshy-6",
    topology: str = "quad",
    target_polycount: int = 30000,
    enable_pbr: bool = True,
    refine: bool = True,
    target_size: float = 2.0,
    max_wait_seconds: int = 480,
) -> str:
    """
    Generate a 3D model from text via Meshy.ai — synchronous full pipeline.

    Runs the preview pass, then optionally chains a refine pass with PBR
    textures (more credits, much better result). Imports the final GLB into
    the scene at target_size.

    **Prompt tips:** Meshy responds well to texture descriptors and can
    take longer prompts than Tripo3D. Topology hints ('quad-based',
    'low-poly') affect output. ONE object only — scene prompts produce
    hybrids. For cheap iteration: do 3 `refine=False` previews and
    only refine the chosen one. For the full prompt cheat sheet, call
    `asset_query_help(service='meshy')`.

    Parameters:
    - prompt: SINGLE-object English description, up to 600 chars,
              with texture + topology hints
              (e.g. "intricate Persian rug, deep red and gold woven
              pattern, rectangular")
    - ai_model: 'meshy-6' (default), 'meshy-5', or 'latest'.
                Meshy-4 was retired 2026-03-20.
    - topology: 'quad' (default — clean retopology) or 'triangle'
    - target_polycount: 100-300000, default 30000
    - enable_pbr: turn on PBR textures during refine pass (defaults
                  off-looking flat in Cycles when False)
    - refine: True (default) does preview + refine; False is preview only
              (cheaper, no textures, blobby)
    - target_size: rescale so largest dim = this many meters
    - max_wait_seconds: total polling timeout for both passes

    Cost (Meshy-6): preview = 20 credits + refine 20 credits = 40 credits.
    Use refine=False for cheap iteration (20 credits).
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("generate_meshy_text_to_3d", {
        "prompt": prompt,
        "ai_model": ai_model,
        "topology": topology,
        "target_polycount": target_polycount,
        "enable_pbr": enable_pbr,
        "refine": refine,
        "target_size": target_size,
        "max_wait_seconds": max_wait_seconds,
    }))
    return result


@mcp.tool()
@tool_envelope
def generate_meshy_image_to_3d(
    ctx: Context,
    image_url: str,
    enable_pbr: bool = True,
    topology: str = "quad",
    target_polycount: int = 30000,
    target_size: float = 2.0,
    max_wait_seconds: int = 300,
) -> str:
    """
    Generate a 3D model from an image via Meshy.ai.

    Parameters:
    - image_url: PUBLIC URL to a JPG/PNG, OR a base64 data URI
                 ('data:image/jpeg;base64,...'). No multipart upload required.
    - enable_pbr: turn on PBR textures
    - topology: 'quad' (default) or 'triangle'
    - target_polycount: 100-300000, default 30000
    - target_size: rescale so largest dim = this many meters
    - max_wait_seconds: polling timeout

    Cost (Meshy-6): 30 credits for image-to-3D with texturing.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("generate_meshy_image_to_3d", {
        "image_url": image_url,
        "enable_pbr": enable_pbr,
        "topology": topology,
        "target_polycount": target_polycount,
        "target_size": target_size,
        "max_wait_seconds": max_wait_seconds,
    }))
    return result


# --------------------------------------------------------------------------
# v1.10.0 — usage tracking, smart routing, OpenAI image gen
# --------------------------------------------------------------------------

@mcp.tool()
@tool_envelope
def get_usage_report(ctx: Context) -> str:
    """
    Show current session usage + per-service caps + live API balance where
    supported. Returns counters for Tripo3D credits, Meshy.ai credits, and
    OpenAI dollars spent. Helpful before kicking off expensive batch
    generations.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_usage_report", {}))
    return result


@mcp.tool()
@tool_envelope
def set_usage_budget(ctx: Context, service: str, max_value: float) -> str:
    """
    Adjust the per-session cap for a metered service.

    Parameters:
    - service: 'tripo3d' | 'meshy' | 'openai'
    - max_value: tripo3d/meshy = credits (int); openai = dollars (float)

    Defaults: tripo3d=500 credits (~$5), meshy=200 credits, openai=$5.00.
    Counters reset when the addon is re-registered (Disable → Enable).
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("set_usage_budget", {
        "service": service, "max_value": max_value,
    }))
    return result


@mcp.tool()
@tool_envelope
def reset_usage_counters(ctx: Context) -> str:
    """Reset all session usage counters back to zero. Useful at the start
    of a new design sprint. Doesn't change configured budget caps."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("reset_usage_counters", {}))
    return result


@mcp.tool()
@tool_envelope
def generate_3d_smart(
    ctx: Context,
    prompt: str,
    quality: str = "standard",
    max_credits: int = None,
    prefer_provider: str = None,
    target_size: float = 2.0,
    max_wait_seconds: int = 240,
    reference_image_url: str = None,
) -> str:
    """
    Auto-route a 3D-generation request to the best AI provider available
    based on quality target, configured services, and remaining budget.

    Quality tiers:
    - 'fast'     — minimum credits, OK for blockouts. Tries Hyper3D
                   (free trial) → Tripo3D Turbo → Meshy preview.
                   Estimated cost: 0-3 credits.
    - 'standard' — balanced quality + cost. Tripo3D v2.5 → Hyper3D →
                   Meshy preview. Estimated cost: 5-20 credits.
    - 'best'     — highest quality with PBR. Tripo3D v3.1 + pbr → Meshy
                   refine → Hyper3D. Estimated cost: 10-40 credits.

    Provider selection respects the per-session budget cap. If the
    estimated cost would push you over your `set_usage_budget()` ceiling,
    that provider is skipped and the next-best one is tried.

    Parameters:
    - prompt: text description
    - quality: 'fast' / 'standard' (default) / 'best'
    - max_credits: per-call cap; skip providers whose estimate exceeds this
    - prefer_provider: 'tripo3d' | 'meshy' | 'hyper3d' to override auto-select
    - target_size: rescale imported model so largest dim = this many meters
    - max_wait_seconds: polling timeout
    - reference_image_url: optional public image URL. When provided AND the
                   chosen provider is Tripo3D or Meshy, the image-to-3D
                   variant is used instead of text-to-3D. Hyper3D and
                   Hunyuan3D fall back to the text path in this release
                   (image-input wrappers for those providers are deferred
                   to a future sprint). Public URLs only — file uploads
                   are out of scope.

    Returns the chosen provider + the underlying generation result.
    Use this when you don't care which AI service runs the call — you
    care about the result + cost discipline.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("generate_3d_smart", {
        "prompt": prompt, "quality": quality,
        "max_credits": max_credits,
        "prefer_provider": prefer_provider,
        "target_size": target_size,
        "max_wait_seconds": max_wait_seconds,
        "reference_image_url": reference_image_url,
    }))
    return result


@mcp.tool()
@tool_envelope
def get_openai_status(ctx: Context) -> str:
    """Verify OpenAI API key + connectivity for image generation
    (DALL-E 3 / gpt-image-1)."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_openai_status", {}))
    return result


@mcp.tool()
@tool_envelope
def generate_image_openai(
    ctx: Context,
    prompt: str,
    model: str = "dall-e-3",
    size: str = "1024x1024",
    quality: str = "standard",
    save_to: str = None,
    n: int = 1,
    style: str = None,
) -> str:
    """
    Generate an image via an OpenAI-compatible image-generation API
    and save to disk.

    Endpoint is configured per-server via the `openai_base_url`
    preference (defaults to https://api.openai.com/v1). Set it to
    https://ai.comfly.chat/v1 for Comfly, https://openrouter.ai/api/v1
    for OpenRouter, or any self-hosted vLLM endpoint that exposes the
    /images/generations route. The model name is passed through verbatim,
    so provider-specific aliases like 'gpt-image-2' or
    'gemini-3.1-flash-image-preview-2k' work on Comfly.

    Use cases for design workflows:
    - Mood boards / concept art for client presentations
    - Reference images that feed Tripo3D/Meshy image-to-3D
    - Custom textures, signage mockups, banner art

    Cost (OpenAI-direct DALL-E 3 standard 1024x1024 = $0.040). gpt-image-1
    ranges $0.011 - $0.167 per image depending on quality. Each call
    increments the session $ counter and respects the openai dollar
    budget cap. Comfly/OpenRouter pricing follows that provider.

    Parameters:
    - prompt: text description (DALL-E 3 max ~4000 chars)
    - model: 'dall-e-3' (older, $0.04+) or 'gpt-image-1' (newer, varies).
             Provider-specific aliases pass through unchanged.
    - size: dall-e-3: '1024x1024' | '1024x1792' | '1792x1024'
            gpt-image-1: '1024x1024' | '1024x1536' | '1536x1024'
    - quality: dall-e-3: 'standard' | 'hd'
               gpt-image-1: 'low' | 'medium' | 'high'
    - save_to: absolute PNG path. None = auto into
               <blend-dir>/references/ai_generated/<timestamp>_<slug>.png
    - n: number of images (DALL-E 3 limited to 1)
    - style: dall-e-3 only: 'vivid' (default) or 'natural'

    Returns saved path + revised prompt (DALL-E 3 always rewrites
    your prompt internally) + dollars spent.

    NOTE: For OpenAI-direct, ChatGPT Plus does NOT cover api.openai.com —
    API credits are billed separately at platform.openai.com.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("generate_image_openai", {
        "prompt": prompt, "model": model, "size": size,
        "quality": quality, "save_to": save_to,
        "n": n, "style": style,
    }))
    return result


@mcp.tool()
@tool_envelope
def get_codex_status(ctx: Context) -> str:
    """Verify Codex CLI is installed and logged in via ChatGPT."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_codex_status", {}))
    return result


@mcp.tool()
@tool_envelope
def generate_image_codex(
    ctx: Context,
    prompt: str,
    save_to: str = None,
    size: str = "1024x1024",
    reference_images: List[str] = None,
    style: str = None,
    transparent: bool = False,
    timeout_seconds: int = 300,
) -> str:
    """
    Generate an image via Codex CLI's $imagegen skill (gpt-image-2).

    **PREFERRED FREE PATH for users with a ChatGPT Plus/Pro subscription
    + Codex CLI access.** Counts against ChatGPT subscription quota,
    NOT against OpenAI API billing. About 3-5x faster quota burn than
    text turns, but no extra dollars.

    Slow (~1-2 min per image) but high quality. For high-volume batches
    where speed matters more than ChatGPT quota, use the OpenAI API
    path (`generate_image_openai`) instead.

    Use cases for design workflows:
    - Mood boards / concept art for client presentations
    - Reference images that feed Tripo3D / Meshy image-to-3D
    - Custom textures, signage mockups, hero shots

    Parameters:
    - prompt: text description (gpt-image-2 handles long detailed prompts)
    - save_to: absolute PNG path. None = auto into
               <blend-dir>/references/ai_generated/<timestamp>_<slug>.png
    - size: '1024x1024' (default) | '1024x1536' | '1536x1024' |
            '1024x1792' | '1792x1024'
    - reference_images: list of paths Codex can edit / transform / extend
                        (gpt-image-2 supports image-to-image)
    - style: optional style hint ('photographic', 'illustration', 'minimal', etc.)
    - transparent: True for transparent background (alpha channel)
    - timeout_seconds: hard cap (default 300s = 5 min)

    Returns saved path + bytes + elapsed + billing path note.

    Requirements (one-time):
    1. Install Codex CLI (https://github.com/openai/codex)
    2. Run `codex login` and sign in via ChatGPT
    3. Verify with `get_codex_status`
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("generate_image_codex", {
        "prompt": prompt, "save_to": save_to, "size": size,
        "reference_images": reference_images,
        "style": style, "transparent": transparent,
        "timeout_seconds": timeout_seconds,
    }))
    return result


@mcp.tool()
@tool_envelope
def check_services(ctx: Context) -> str:
    """
    One-call health report for every integration: PolyHaven, Sketchfab,
    Hyper3D, Hunyuan3D, Tripo3D, Meshy.ai, ambientCG. Returns:

    - Per-service status (enabled / message / balance / etc.)
    - Roll-up summary: which are ready, which need API keys, which are
      unreachable
    - Blender + addon versions

    Run this first when you don't know what's configured. It's the
    fastest way to figure out which AI 3D providers and asset libraries
    you can actually use right now.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("check_services", {}))
    return result


@mcp.tool()
@telemetry_tool("execute_blender_code")
@tool_envelope
def execute_blender_code(ctx: Context, code: str) -> str:
    """
    Run arbitrary Python in Blender — the escape hatch.

    USE ONLY WHEN no purpose-built tool fits. First check whether one of
    these covers your need:

      Materials: apply_material_color, apply_archviz_material, set_texture
      Geometry:  boolean_cutout, mesh_cleanup, scatter_on_surface,
                 array_duplicate, curve_extrude_profile, place_on_ground
      Camera:    set_camera_view, frame_camera_to_objects
      Lighting:  setup_lighting, set_world_hdri_rotation
      Render:    render_image
      Export:    quick_export
      AI gen:    generate_3d_smart, generate_image_codex, generate_image_openai
      Verify:    verify_object_grounded, get_viewport_screenshot

    Direct execute_blender_code is appropriate for one-offs that don't fit
    the above (custom modifier stacks, drivers, geometry-nodes graph
    editing, undocumented operators). Always save your .blend before
    running it — generated code can corrupt the scene.

    Parameters:
    - code: Python code to execute. `bpy` is in scope.

    Returns: any stdout from the executed code, plus a list of newly
    created/modified object names.
    """
    # Get the global connection
    blender = get_blender_connection()
    try:
        result = blender.send_command("execute_code", {"code": code})
    except BlenderCommandError as e:
        # A Python exception inside the executed code round-tripped cleanly.
        # The addon prefixes these with "Code execution error: "; strip it so
        # the user sees the underlying exception without two layers of framing.
        msg = str(e)
        prefix = "Code execution error: "
        if msg.startswith(prefix):
            msg = msg[len(prefix):]
        logger.info(f"Blender Python error: {msg}")
        return f"Blender Python error: {msg}"
    return f"Code executed successfully: {result.get('result', '')}"

@mcp.tool()
@tool_envelope
def asset_query_help(ctx: Context, service: str = "all") -> str:
    """
    Cheat sheet for how each asset service actually wants to be queried.

    Different services accept very different query formats:

    - PolyHaven: NOT a search engine — only takes canonical category
      tags (`wood`, `brick`). Free text returns nothing.
    - ambientCG: free-text + category. Single material noun beats
      sentences. Avoid color adjectives.
    - Sketchfab: full-text + ML rank. Short noun phrase (2-4 words).
      Long sentences return zero. `downloadable=True` drops ~70%.
    - Tripo3D / Meshy / Hyper3D: prompt-style English noun phrase. ONE
      object, not a scene. Material + style modifiers help.

    Call this BEFORE any search/gen call when you're unsure how to
    phrase the query. The output includes per-service query format
    rules, category taxonomies, common pitfalls, and worked examples.

    Parameters:
    - service: 'polyhaven' | 'ambientcg' | 'sketchfab' | 'tripo3d' |
               'meshy' | 'hyper3d' | 'all' (default).

    Returns the cheat sheet as JSON-serializable data.
    """
    return asset_query_help_data(service)


@mcp.tool()
@tool_envelope
def read_design_handbook(
    ctx: Context,
    chapter: str = "",
    query: str = "",
) -> str:
    """
    Read the Interior Design Handbook — the source-of-truth for design
    rules, standards, codes, and style guidance used by the Interior
    Design Workflow.

    The handbook lives as markdown in docs/handbook/. Every numeric
    value inside is sourced and cited (per the Sources & Citation
    Policy in docs/superpowers/specs/2026-04-29-interior-design-
    workflow-design.md).

    Three call modes:

    1. List all chapters: `read_design_handbook()`
    2. Read a specific chapter: `read_design_handbook(chapter="lighting")`
    3. Search across chapters: `read_design_handbook(query="Kelvin")`

    Parameters:
    - chapter: chapter slug ("lighting", "styles/scandinavian", etc.).
               Empty string means list mode.
    - query: free-text query, searched case-insensitive across all
             chapters. If both `chapter` and `query` are given,
             `chapter` wins.

    Returns the chapter content (markdown) or a list of available
    chapters or search results, all wrapped in the canonical envelope.
    """
    from ._handbook import (
        HandbookError, list_chapters, read_chapter, search_chapters,
    )

    if chapter:
        try:
            content = read_chapter(chapter)
        except HandbookError as e:
            raise ToolError(
                code=ErrorCode.NOT_FOUND,
                hint="Use read_design_handbook() with no args to list chapters.",
                detail=str(e),
            ) from e
        return _tool_response({
            "chapter": chapter,
            "content": content,
        })

    if query:
        try:
            results = search_chapters(query)
        except HandbookError as e:
            raise ToolError(
                code=ErrorCode.INTERNAL,
                hint="Handbook may be missing or corrupted.",
                detail=str(e),
            ) from e
        return _tool_response({
            "query": query,
            "results": results,
        })

    # No args → list mode
    try:
        chapters = list_chapters()
    except HandbookError as e:
        raise ToolError(
            code=ErrorCode.STATE_REQUIRED,
            hint="Run from a repo with docs/handbook/ present.",
            detail=str(e),
        ) from e
    return _tool_response({
        "available_chapters": chapters,
        "tip": (
            "Pass chapter='<slug>' to read one, or query='<keyword>' to "
            "search across all chapters."
        ),
    })


@mcp.tool()
@telemetry_tool("run_discovery_questionnaire")
@tool_envelope
def run_discovery_questionnaire(
    ctx: Context,
    depth: str = "deep",
    batch_size: int = 4,
) -> str:
    """
    Start a Discovery questionnaire session per docs/handbook/discovery.md.

    The Discovery flow extracts user taste preferences via 5 question
    types (direct / projective / metaphor / sensory / paired-A/B). Use
    this at the start of any new project, or whenever the user wants
    to refresh their taste profile.

    Parameters:
    - depth: 'quick' (5-7 q) | 'standard' (12-15 q) | 'deep' (25-30 q)
             | 'adaptive' (default 'deep')
    - batch_size: number of questions per call (default 4). Use a small
                  batch to avoid overwhelming the user; call repeatedly
                  with submit_questionnaire_answers in between.

    Returns: {session_id, depth, total_questions, batch, next_index}
    """
    from ._discovery import Depth, DiscoveryError, new_session

    try:
        d = Depth(depth.lower())
    except ValueError as e:
        raise ToolError(
            code=ErrorCode.BAD_INPUT,
            hint="depth must be one of: quick / standard / deep / adaptive",
            detail=str(e),
        ) from e
    try:
        session = new_session(depth=d, batch_size=batch_size)
    except DiscoveryError as e:
        raise ToolError(
            code=ErrorCode.INTERNAL,
            hint="discovery_bank.yaml may be missing or malformed",
            detail=str(e),
        ) from e
    return _tool_response(session)


@mcp.tool()
@telemetry_tool("submit_questionnaire_answers")
@tool_envelope
def submit_questionnaire_answers(
    ctx: Context,
    answers: dict,
    return_inferred: bool = True,
) -> str:
    """
    Validate + score discovery answers. Returns a partial / full taste
    profile. Per discovery.md, the AI should call this at the midpoint
    (around question 12) with `return_inferred=True` to surface a
    style hypothesis to the user before continuing.

    Parameters:
    - answers: dict mapping question_id → choice_value (str), list, or
               free-text string. Use validate-friendly shapes from
               run_discovery_questionnaire's batch.
    - return_inferred: if True (default), include the mid-questionnaire
                       top-style hypothesis in the response.

    Returns:
      {profile: {feeling_anchors, style_axes, material_pull,
                 style_match, recommended_style, free_text_notes},
       inferred?: {top_styles, needs_more_questions, current_axes}}
    """
    from ._discovery import (
        DiscoveryError,
        midpoint_inferred_style,
        score_answers,
        validate_answer_payload,
    )

    try:
        normalized = validate_answer_payload(answers)
    except DiscoveryError as e:
        raise ToolError(
            code=ErrorCode.BAD_INPUT,
            hint="check question id and choice value spelling",
            detail=str(e),
        ) from e
    profile = score_answers(normalized)
    out: dict = {"profile": profile}
    if return_inferred:
        out["inferred"] = midpoint_inferred_style(normalized)
    return _tool_response(out)


@mcp.tool()
@telemetry_tool("read_taste_profile_tool")
@tool_envelope
def read_taste_profile_tool(
    ctx: Context,
    project_root: str,
) -> str:
    """Return the project's current taste-profile.json content.

    Parameters:
    - project_root: absolute path to the project directory containing
                    taste-profile.json.

    Returns: {profile: {...full taste profile fields...}}
    """
    from pathlib import Path

    from ._project import ProjectError, read_taste_profile

    try:
        profile = read_taste_profile(
            Path(project_root) / "taste-profile.json"
        )
    except ProjectError as e:
        raise ToolError(
            code=ErrorCode.NOT_FOUND,
            hint="run_discovery_questionnaire first to generate a profile",
            detail=str(e),
        ) from e
    return _tool_response({"profile": profile})


@mcp.tool()
@telemetry_tool("update_taste_profile_tool")
@tool_envelope
def update_taste_profile_tool(
    ctx: Context,
    project_root: str,
    updates: dict,
) -> str:
    """Merge updates into the project's taste-profile.json.

    Used by `interior-style-locking` skill to write `locked_style`,
    `locked_palette`, `locked_material_vocab`, `locked_anchor_images`
    after the user picks a moodboard.

    Parameters:
    - project_root: absolute path to the project directory.
    - updates: dict of fields to merge (replaces existing keys).

    Returns: {profile: {...merged profile...}}
    """
    from pathlib import Path

    from ._project import ProjectError, update_taste_profile

    try:
        merged = update_taste_profile(
            Path(project_root) / "taste-profile.json",
            updates,
        )
    except ProjectError as e:
        raise ToolError(
            code=ErrorCode.INTERNAL,
            hint="check filesystem permissions on project_root",
            detail=str(e),
        ) from e
    return _tool_response({"profile": merged})


@mcp.tool()
@telemetry_tool("create_interior_project")
@tool_envelope
def create_interior_project(
    ctx: Context,
    project_name: str,
    project_type: str,
    spaces: list,
    project_root: str,
    units: str = "metric",
) -> str:
    """
    Create the project scaffold — directory layout, project.json,
    taste-profile.json (empty), and standard Blender collection names.

    Parameters:
    - project_name: display name.
    - project_type: per docs/handbook/project-types.md
                    (residential_apartment / residential_house /
                    cafe_lounge / restaurant_full_service /
                    retail_boutique / office_small).
    - spaces: list[str] of space names (e.g. ['living', 'bedroom']).
    - project_root: absolute path; will be created if missing.
    - units: 'metric' (default).

    Note: Blender collection creation itself is delegated to the addon
    via execute_blender_code in this slice. This tool writes project
    metadata + scaffold dirs and returns the canonical collection list
    for the AI to apply Blender-side.
    """
    import json as _json
    from pathlib import Path

    from ._project import (
        ProjectError, new_project_record, write_taste_profile,
    )

    try:
        rec = new_project_record(
            project_name=project_name,
            project_type=project_type,
            spaces=spaces,
            units=units,
        )
    except ProjectError as e:
        raise ToolError(
            code=ErrorCode.BAD_INPUT,
            hint=("valid project types: residential_apartment, "
                  "residential_house, cafe_lounge, "
                  "restaurant_full_service, retail_boutique, office_small"),
            detail=str(e),
        ) from e

    root = Path(project_root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "project.json").write_text(
        _json.dumps(rec, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    profile_path = root / "taste-profile.json"
    if not profile_path.exists():
        write_taste_profile(
            profile_path,
            {"version": 1, "project": project_name},
        )

    for sub in (
        "snapshots",
        "exports/renders",
        "exports/construction",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)

    return _tool_response({
        "project": rec,
        "project_root": str(root.resolve()),
        "files_created": ["project.json", "taste-profile.json"],
        "directories_created": [
            "snapshots/", "exports/renders/", "exports/construction/",
        ],
    })


@mcp.tool()
@telemetry_tool("version_snapshot")
@tool_envelope
def version_snapshot(
    ctx: Context,
    project_root: str,
    label: str,
    extra_files: list = None,
) -> str:
    """
    Snapshot the project state. Always copies project.json,
    taste-profile.json, version-log.json (if they exist), plus any
    additional files in `extra_files`.

    The medium snapshot frequency rule (per workflow spec § Interaction
    Model) calls for snapshots at phase completion + when the user
    says "looks good". The AI should also snapshot before any L3 / L4
    loop transition.

    Parameters:
    - project_root: absolute path.
    - label: short human label (e.g. 'phase-3-shell-complete' or
             'pre-L4-style-pivot').
    - extra_files: list[str] of additional absolute paths to include
                   (typically the .blend file path).

    Returns: {path, label, files}
    """
    from pathlib import Path

    from ._snapshots import SnapshotError, snapshot_create

    root = Path(project_root)
    files_to_snapshot = []
    for name in ("project.json", "taste-profile.json", "version-log.json"):
        p = root / name
        if p.is_file():
            files_to_snapshot.append(p)
    for extra in extra_files or []:
        files_to_snapshot.append(Path(extra))

    if not files_to_snapshot:
        raise ToolError(
            code=ErrorCode.STATE_REQUIRED,
            hint=(
                "No project files found to snapshot — run "
                "create_interior_project first"
            ),
            detail=f"checked under {root}",
        )
    try:
        snap = snapshot_create(
            project_root=root, label=label, files=files_to_snapshot,
        )
    except SnapshotError as e:
        raise ToolError(
            code=ErrorCode.INTERNAL,
            hint=(
                "check filesystem permissions and that all extra_files "
                "exist"
            ),
            detail=str(e),
        ) from e
    snap["path"] = str(snap["path"])
    return _tool_response(snap)


@mcp.tool()
@telemetry_tool("version_log_entry")
@tool_envelope
def version_log_entry(
    ctx: Context,
    project_root: str,
    level: str,
    why: str,
    snapshot_label: str = "",
) -> str:
    """
    Append a loop-transition entry to version-log.json.

    Per the workflow spec § Loop Architecture:
    - L1 (tweak within Stage 5): silent, no log needed
    - L2 (material/light swap): silent execute, log optional
    - L3 (layout / Stage 3-4 change): MUST log + snapshot prior state
    - L4 (style redo / Stage 2.5 pivot): MUST log + branch snapshot
                                         + user confirmation

    Parameters:
    - project_root: absolute path.
    - level: 'L1' | 'L2' | 'L3' | 'L4'.
    - why: one-line reason ("user changed sofa layout from L-shape...").
    - snapshot_label: label of the snapshot taken just before this
                      transition (recommended for L3 / L4).
    """
    from pathlib import Path

    from ._snapshots import LoopLevel, SnapshotError, version_log_append

    try:
        lvl = LoopLevel(level.upper())
    except ValueError as e:
        raise ToolError(
            code=ErrorCode.BAD_INPUT,
            hint="level must be one of L1 / L2 / L3 / L4",
            detail=str(e),
        ) from e
    try:
        version_log_append(
            project_root=Path(project_root),
            level=lvl,
            why=why,
            snapshot_label=snapshot_label,
        )
    except SnapshotError as e:
        raise ToolError(
            code=ErrorCode.INTERNAL,
            hint="check filesystem permissions",
            detail=str(e),
        ) from e
    return _tool_response({"appended": {"level": level, "why": why}})


@mcp.tool()
@telemetry_tool("audit_interior_quality")
@tool_envelope
def audit_interior_quality(
    ctx: Context,
    scene_info: dict,
    mode: str = "hero",
    project_root: str = "",
) -> str:
    """
    Run the 9-dimension Interior Quality audit on a captured scene_info.

    The AI client should first fetch scene state via
    `get_scene_info(full=True)`, then pass the result here. Each gate
    references its handbook chapter so the AI can explain failures to
    the user with citations.

    Strictness modes (per workflow spec § Quality Gates):
    - 'exploration' (Stages 0-4, L1 loops): only HARD findings reported
    - 'hero'        (Stage 5 final, Stage 6): all severities
    - 'construction' (Stage 6.5 deliverables): all severities + texture
                     packing upgraded to HARD

    Parameters:
    - scene_info: dict from get_scene_info(full=True). Required shape:
        {objects: [{name, type, has_albedo_map, has_roughness_map,
                    is_prop, category, height_m}],
         lights: [{name, layer, kelvin}],
         cameras: [{name, focal_mm, height_m, near_clip, inside_wall}],
         view_transform: 'AgX' | 'Filmic' | 'Standard',
         render_settings: {engine, cycles_samples, eevee_samples},
         scene_meta: {floor_area_m2, pack_resources}}
    - mode: 'exploration' | 'hero' | 'construction' (default 'hero')
    - project_root: optional absolute path; if given, taste-profile.json
                    is loaded so kelvin gate can apply project-type range

    Returns:
        {mode, status: 'pass' | 'warn' | 'fail',
         findings: [{gate, severity, message, citation, suggested_fix}]}
    """
    from pathlib import Path

    from ._gates import StrictnessMode, run_audit
    from ._project import ProjectError, read_taste_profile

    try:
        m = StrictnessMode(mode.lower())
    except ValueError as e:
        raise ToolError(
            code=ErrorCode.BAD_INPUT,
            hint="mode must be one of: exploration / hero / construction",
            detail=str(e),
        ) from e

    project_meta = None
    if project_root:
        try:
            profile = read_taste_profile(
                Path(project_root) / "taste-profile.json"
            )
            # Project type may live in project.json or be embedded in profile
            project_json = Path(project_root) / "project.json"
            if project_json.is_file():
                import json as _json
                project_meta = _json.loads(
                    project_json.read_text(encoding="utf-8")
                )
            else:
                project_meta = profile
        except ProjectError:
            # No profile — kelvin gate becomes a no-op, others still run
            project_meta = None

    report = run_audit(scene_info, mode=m, project=project_meta)

    # Convert Finding namedtuples to plain dicts for JSON serialization
    findings_out = [
        {
            "gate": f.gate,
            "severity": f.severity.value,
            "message": f.message,
            "citation": f.citation,
            "suggested_fix": f.suggested_fix,
        }
        for f in report["findings"]
    ]
    return _tool_response({
        "mode": report["mode"],
        "status": report["status"],
        "findings": findings_out,
        "summary": (
            f"{len(findings_out)} finding(s); "
            f"hard={sum(1 for f in findings_out if f['severity']=='hard')}, "
            f"soft={sum(1 for f in findings_out if f['severity']=='soft')}, "
            f"info={sum(1 for f in findings_out if f['severity']=='info')}"
        ),
    })


@mcp.tool()
@tool_envelope
def list_tools_by_phase(ctx: Context) -> str:
    """Return the per-phase taxonomy of fork tools.

    Use this for orientation when starting a new workflow. The phases
    map to typical LLM workflow stages:

    - discovery / diagnostics -> "what's in the scene + what works?"
    - asset_search / asset_download / asset_generation -> "get content"
    - material / geometry -> "build / tweak"
    - camera / lighting -> "compose"
    - render / export -> "ship"
    - scene_management -> "cleanup, escape hatch"
    - config -> "budget knobs"

    Returns: {"phases": {phase_name: [tool_names]}, "total_tools": N}.
    """
    from ._phases import PHASES
    return {
        "phases": {p: list(t) for p, t in PHASES.items()},
        "total_tools": sum(len(t) for t in PHASES.values()),
    }


@mcp.tool()
@telemetry_tool("get_polyhaven_categories")
@tool_envelope
def get_polyhaven_categories(ctx: Context, asset_type: str = "hdris") -> str:
    """
    Get a list of categories for a specific asset type on Polyhaven.

    Parameters:
    - asset_type: The type of asset to get categories for (hdris, textures, models, all)
    """
    blender = get_blender_connection()
    if not _polyhaven_enabled:
        raise ToolError(
            ErrorCode.STATE_REQUIRED,
            hint="PolyHaven integration is disabled. Enable it in the BlenderMCP sidebar, then retry.",
            detail="_polyhaven_enabled is False",
        )
    result = _check_addon_result(blender.send_command("get_polyhaven_categories", {"asset_type": asset_type}))
    return result

@mcp.tool()
@telemetry_tool("search_polyhaven_assets")
@tool_envelope
def search_polyhaven_assets(
    ctx: Context,
    asset_type: str = "all",
    categories: str = None,
    concise: bool = True,
) -> str:
    """
    Search for assets on Polyhaven by category filter.

    **PolyHaven is NOT a free-text search.** `categories` is the only
    real filter; passing free text like 'dark walnut floor' returns
    nothing. Use canonical tags from
    `get_polyhaven_categories(asset_type=...)`. Multiple tags
    comma-separated AND-filter (e.g. `wood,floor`).

    Common tags: textures `wood`, `brick`, `concrete`, `metal`,
    `fabric`, `tiles`, `wall`, `floor`. HDRIs `outdoor`, `indoor`,
    `studio`, `sunrise-sunset`, `night`. Models `furniture`,
    `decorative`, `architectural`.

    For free-text material search use `search_ambientcg_assets`. For a
    full per-service query cheat sheet, call `asset_query_help`.

    Parameters:
    - asset_type: hdris | textures | models | all
    - categories: comma-separated canonical tags (NOT free text)
    - concise: when True (default), drops evs_cap / whitebalance /
      sponsors / files_hash / coords / date metadata. Pass False for
      the raw API response.

    Returns a list of matching assets with basic information.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("search_polyhaven_assets", {
        "asset_type": asset_type,
        "categories": categories
    }))
    from ._filters import attach_zero_result_hint
    if concise:
        from ._filters import slim_polyhaven
        result = slim_polyhaven(result)
    result = attach_zero_result_hint(result, service="polyhaven")
    return result

@mcp.tool()
@telemetry_tool("download_polyhaven_asset")
@tool_envelope
def download_polyhaven_asset(
    ctx: Context,
    asset_id: str,
    asset_type: str,
    resolution: str = "1k",
    file_format: str = None,
    target_size: float = None,
) -> str:
    """
    Download and import a Polyhaven asset into Blender.

    Parameters:
    - asset_id: The ID of the asset to download
    - asset_type: The type of asset (hdris, textures, models)
    - resolution: The resolution to download (e.g., 1k, 2k, 4k)
    - file_format: Optional file format (e.g., hdr, exr for HDRIs; jpg, png for textures; gltf, fbx for models)
    - target_size: optional float meters. If provided AND asset_type='models',
      the imported model is rescaled so its largest dimension equals this
      value. Default None = native scale (which can be wildly off — buildings
      at 200m, props at 5cm — for archviz pass an explicit size).

    Returns a message indicating success or failure.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("download_polyhaven_asset", {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "resolution": resolution,
        "file_format": file_format,
        "target_size": target_size,
    }))
    return result

@mcp.tool()
@telemetry_tool("set_texture")
@tool_envelope
def set_texture(
    ctx: Context,
    object_name: str,
    texture_id: str
) -> str:
    """
    Apply a previously downloaded Polyhaven texture to an object.

    Parameters:
    - object_name: Name of the object to apply the texture to
    - texture_id: ID of the Polyhaven texture to apply (must be downloaded first)

    Returns a message indicating success or failure.
    """
    # Get the global connection
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("set_texture", {
        "object_name": object_name,
        "texture_id": texture_id
    }))
    return result

@mcp.tool()
@telemetry_tool("get_polyhaven_status")
@tool_envelope
def get_polyhaven_status(ctx: Context) -> str:
    """Check if PolyHaven integration is enabled. PolyHaven hosts CC0 PBR
    textures, HDRIs, and 3D models — no API key required."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_polyhaven_status"))
    return result

@mcp.tool()
@telemetry_tool("get_hyper3d_status")
@tool_envelope
def get_hyper3d_status(ctx: Context) -> str:
    """Check if Hyper3D Rodin integration is enabled in Blender."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_hyper3d_status"))
    return result

@mcp.tool()
@telemetry_tool("get_sketchfab_status")
@tool_envelope
def get_sketchfab_status(ctx: Context) -> str:
    """Check if Sketchfab integration is enabled in Blender."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_sketchfab_status"))
    return result

@mcp.tool()
@telemetry_tool("search_sketchfab_models")
@tool_envelope
def search_sketchfab_models(
    ctx: Context,
    query: str,
    categories: str = None,
    count: int = 20,
    downloadable: bool = True,
    concise: bool = True,
) -> str:
    """
    Search for models on Sketchfab.

    **Query tips:** short noun phrase, 2-4 words, English. Object-first:
    'linen sectional sofa' beats 'a sofa made of fabric for living room'.
    Long sentences return zero results. Skip brand names (they're
    copyright-cleansed).
    `downloadable=True` is the default and drops ~70% of results — set
    False to widen the pool when zero hits, then check the `license`
    field manually before commercial use. For the full per-service
    query cheat sheet, call `asset_query_help`.

    Parameters:
    - query: Short noun phrase (2-4 words). Long sentences fail.
    - categories: comma-separated. Examples: 'furniture-home',
      'architecture', 'art-abstract', 'cultural-heritage-history',
      'food-drink', 'nature-plants', 'places-travel'.
    - count: Maximum number of results to return (default 20)
    - downloadable: Whether to include only downloadable models (default True)
    - concise: when True (default), drops 4-thumbnail-size variants,
      archives metadata, user avatar URLs, tags array, etc. — keeps
      only the fields needed to pick a model. Pass `concise=False` to
      get the raw Sketchfab API response if you need a missing field.

    Returns a formatted list of matching models.
    """
    blender = get_blender_connection()
    logger.info(
        f"Searching Sketchfab models with query: {query}, categories: "
        f"{categories}, count: {count}, downloadable: {downloadable}, "
        f"concise: {concise}")
    result = _check_addon_result(blender.send_command("search_sketchfab_models", {
        "query": query,
        "categories": categories,
        "count": count,
        "downloadable": downloadable,
    }))
    from ._filters import attach_zero_result_hint
    if concise:
        from ._filters import slim_sketchfab
        result = slim_sketchfab(result)
    result = attach_zero_result_hint(result, service="sketchfab")
    return result

@mcp.tool()
@telemetry_tool("download_sketchfab_model")
def get_sketchfab_model_preview(
    ctx: Context,
    uid: str
) -> Image:
    """
    Get a preview thumbnail of a Sketchfab model by its UID.
    Use this to visually confirm a model before downloading.
    
    Parameters:
    - uid: The unique identifier of the Sketchfab model (obtained from search_sketchfab_models)
    
    Returns the model's thumbnail as an Image for visual confirmation.
    """
    try:
        blender = get_blender_connection()
        logger.info(f"Getting Sketchfab model preview for UID: {uid}")
        
        result = blender.send_command("get_sketchfab_model_preview", {"uid": uid})
        
        if result is None:
            raise Exception("Received no response from Blender")
        
        if "error" in result:
            raise Exception(result["error"])
        
        # Decode base64 image data
        image_data = base64.b64decode(result["image_data"])
        img_format = result.get("format", "jpeg")
        
        # Log model info
        model_name = result.get("model_name", "Unknown")
        author = result.get("author", "Unknown")
        logger.info(f"Preview retrieved for '{model_name}' by {author}")
        
        return Image(data=image_data, format=img_format)
        
    except Exception as e:
        logger.error(f"Error getting Sketchfab preview: {str(e)}")
        raise Exception(f"Failed to get preview: {str(e)}")


@mcp.tool()
@tool_envelope
def download_sketchfab_model(
    ctx: Context,
    uid: str,
    target_size: float
) -> str:
    """
    Download and import a Sketchfab model by its UID.
    The model will be scaled so its largest dimension equals target_size.

    Parameters:
    - uid: The unique identifier of the Sketchfab model
    - target_size: REQUIRED. The target size in Blender units/meters for the largest dimension.
                  You must specify the desired size for the model.
                  Examples:
                  - Chair: target_size=1.0 (1 meter tall)
                  - Table: target_size=0.75 (75cm tall)
                  - Car: target_size=4.5 (4.5 meters long)
                  - Person: target_size=1.7 (1.7 meters tall)
                  - Small object (cup, phone): target_size=0.1 to 0.3

    Returns a message with import details including object names, dimensions, and bounding box.
    The model must be downloadable and you must have proper access rights.
    """
    blender = get_blender_connection()
    logger.info(f"Downloading Sketchfab model: {uid}, target_size={target_size}")
    result = _check_addon_result(blender.send_command("download_sketchfab_model", {
        "uid": uid,
        "normalize_size": True,  # Always normalize
        "target_size": target_size
    }))
    return result

def _process_bbox(original_bbox: list[float] | list[int] | None) -> list[int] | None:
    if original_bbox is None:
        return None
    if all(isinstance(i, int) for i in original_bbox):
        return original_bbox
    if any(i<=0 for i in original_bbox):
        raise ValueError("Incorrect number range: bbox must be bigger than zero!")
    return [int(float(i) / max(original_bbox) * 100) for i in original_bbox] if original_bbox else None

@mcp.tool()
@telemetry_tool("generate_hyper3d_text_to_3d")
@tool_envelope
def generate_hyper3d_text_to_3d(
    ctx: Context,
    text_prompt: str,
    bbox_condition: list[float] = None,
    auto_import: bool = True,
    import_name: str = "Hyper3DGenerated",
    max_wait_seconds: int = 240,
    poll_interval_seconds: float = 5.0,
) -> str:
    """
    Generate a 3D asset via Hyper3D Rodin from a text prompt.

    Two flows:

    1. **auto_import=True (default)** — sync: creates the task, polls
       status until all entries are 'Done' (or timeout), then calls
       import_hyper3d_asset transparently. Returns the import result.
    2. **auto_import=False** — async: returns task_uuid +
       subscription_key immediately. Caller drives
       poll_hyper3d_job_status + import_hyper3d_asset manually. Use
       when you want to fire-and-forget multiple jobs in parallel and
       import them later.

    Free-trial key works for blockouts/prototyping; rate-limits during
    peak hours surface as RATE_LIMITED ErrorCode.

    **Prompt tips:** SHORT prompt-style English, ONE simple object.
    Multi-object prompts produce mesh hybrids. Hyper3D's output is
    often dense — run `mesh_cleanup` after import. For higher fidelity
    prefer Tripo3D or Meshy. For the full prompt cheat sheet, call
    `asset_query_help(service='hyper3d')`.

    Parameters:
    - text_prompt: SHORT single-object English description
                   (e.g. "small brass cube, simple geometry").
    - bbox_condition: Optional [Length, Width, Height] ratio floats.
    - auto_import: True (default) for sync poll+import. False for raw
                   async return of task_uuid + subscription_key.
    - import_name: Object name to assign on import (auto_import only).
    - max_wait_seconds: Polling timeout (auto_import only).
    - poll_interval_seconds: Wait between polls (auto_import only).

    Returns the import result with object name + bbox + status (when
    auto_import=True), or {task_uuid, subscription_key, auto_import:False}
    (when auto_import=False).
    """
    import time as _time

    blender = get_blender_connection()
    create = _check_addon_result(blender.send_command("create_rodin_job", {
        "text_prompt": text_prompt,
        "images": None,
        "bbox_condition": _process_bbox(bbox_condition),
    }))
    if not create.get("submit_time"):
        return create

    task_uuid = create["uuid"]
    sub_key = create["jobs"]["subscription_key"]

    if not auto_import:
        return {
            "task_uuid": task_uuid,
            "subscription_key": sub_key,
            "auto_import": False,
        }

    # Sync: poll until done, then import
    deadline = _time.monotonic() + max_wait_seconds
    last_status = None
    while _time.monotonic() < deadline:
        poll_result = blender.send_command("poll_hyper3d_job_status",
                                           {"subscription_key": sub_key})
        last_status = poll_result.get("status_list", [])
        if last_status and all(s == "Done" for s in last_status):
            break
        if any(s == "Failed" for s in last_status):
            raise ToolError(
                ErrorCode.INTERNAL,
                hint="Hyper3D job reported Failed status",
                detail=f"status_list={last_status}",
            )
        _time.sleep(poll_interval_seconds)
    else:
        raise ToolError(
            ErrorCode.NETWORK,
            hint=f"Hyper3D polling timed out after {max_wait_seconds}s",
            detail=f"last_status={last_status}",
        )

    return _check_addon_result(blender.send_command("import_hyper3d_asset", {
        "name": import_name,
        "task_uuid": task_uuid,
    }))

@mcp.tool()
@telemetry_tool("generate_hyper3d_image_to_3d")
@tool_envelope
def generate_hyper3d_image_to_3d(
    ctx: Context,
    input_image_paths: list[str]=None,
    input_image_urls: list[str]=None,
    bbox_condition: list[float]=None
) -> str:
    """
    Generate 3D asset using Hyper3D by giving images of the wanted asset, and import the generated asset into Blender.
    The 3D asset has built-in materials.
    The generated model has a normalized size, so re-scaling after generation can be useful.

    Parameters:
    - input_image_paths: The **absolute** paths of input images. Even if only one image is provided, wrap it into a list. Required if Hyper3D Rodin in MAIN_SITE mode.
    - input_image_urls: The URLs of input images. Even if only one image is provided, wrap it into a list. Required if Hyper3D Rodin in FAL_AI mode.
    - bbox_condition: Optional. If given, it has to be a list of ints of length 3. Controls the ratio between [Length, Width, Height] of the model.

    Only one of {input_image_paths, input_image_urls} should be given at a time, depending on the Hyper3D Rodin's current mode.
    Returns a message indicating success or failure.
    """
    if input_image_paths is not None and input_image_urls is not None:
        raise ToolError(
            ErrorCode.BAD_INPUT,
            hint="Pass exactly one of input_image_paths or input_image_urls, not both.",
            detail="Conflict parameters given.",
        )
    if input_image_paths is None and input_image_urls is None:
        raise ToolError(
            ErrorCode.BAD_INPUT,
            hint="Pass either input_image_paths (MAIN_SITE mode) or input_image_urls (FAL_AI mode).",
            detail="No image given.",
        )
    if input_image_paths is not None:
        if not all(os.path.exists(i) for i in input_image_paths):
            raise ToolError(
                ErrorCode.NOT_FOUND,
                hint="One or more input_image_paths do not exist on disk.",
                detail=f"Paths checked: {input_image_paths}",
            )
        images = []
        for path in input_image_paths:
            with open(path, "rb") as f:
                images.append(
                    (Path(path).suffix, base64.b64encode(f.read()).decode("ascii"))
                )
    elif input_image_urls is not None:
        if not all(_is_valid_http_url(i) for i in input_image_urls):
            raise ToolError(
                ErrorCode.BAD_INPUT,
                hint="All input_image_urls must be absolute HTTP(S) URLs.",
                detail=f"URLs checked: {input_image_urls}",
            )
        images = input_image_urls.copy()
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("create_rodin_job", {
        "text_prompt": None,
        "images": images,
        "bbox_condition": _process_bbox(bbox_condition),
    }))
    succeed = result.get("submit_time", False)
    if succeed:
        return {
            "task_uuid": result["uuid"],
            "subscription_key": result["jobs"]["subscription_key"],
        }
    return result

@mcp.tool()
@telemetry_tool("poll_hyper3d_job_status")
@tool_envelope
def poll_hyper3d_job_status(
    ctx: Context,
    subscription_key: str=None,
    request_id: str=None,
):
    """
    Check if the Hyper3D Rodin generation task is completed.

    For Hyper3D Rodin mode MAIN_SITE:
        Parameters:
        - subscription_key: The subscription_key given in the generate model step.

        Returns a list of status. The task is done if all status are "Done".
        If "Failed" showed up, the generating process failed.
        This is a polling API, so only proceed if the status are finally determined ("Done" or "Canceled").

    For Hyper3D Rodin mode FAL_AI:
        Parameters:
        - request_id: The request_id given in the generate model step.

        Returns the generation task status. The task is done if status is "COMPLETED".
        The task is in progress if status is "IN_PROGRESS".
        If status other than "COMPLETED", "IN_PROGRESS", "IN_QUEUE" showed up, the generating process might be failed.
        This is a polling API, so only proceed if the status are finally determined ("COMPLETED" or some failed state).
    """
    blender = get_blender_connection()
    kwargs = {}
    if subscription_key:
        kwargs = {
            "subscription_key": subscription_key,
        }
    elif request_id:
        kwargs = {
            "request_id": request_id,
        }
    result = _check_addon_result(blender.send_command("poll_hyper3d_job_status", kwargs))
    return result

@mcp.tool()
@telemetry_tool("import_hyper3d_asset")
@tool_envelope
def import_hyper3d_asset(
    ctx: Context,
    name: str,
    task_uuid: str=None,
    request_id: str=None,
):
    """
    Import the asset generated by Hyper3D Rodin after the generation task is completed.

    Parameters:
    - name: The name of the object in scene
    - task_uuid: For Hyper3D Rodin mode MAIN_SITE: The task_uuid given in the generate model step.
    - request_id: For Hyper3D Rodin mode FAL_AI: The request_id given in the generate model step.

    Only give one of {task_uuid, request_id} based on the Hyper3D Rodin Mode!
    Return if the asset has been imported successfully.
    """
    blender = get_blender_connection()
    kwargs = {
        "name": name
    }
    if task_uuid:
        kwargs["task_uuid"] = task_uuid
    elif request_id:
        kwargs["request_id"] = request_id
    result = _check_addon_result(blender.send_command("import_hyper3d_asset", kwargs))
    return result

@mcp.tool()
@tool_envelope
def get_hunyuan3d_status(ctx: Context) -> str:
    """Check if Hunyuan3D integration is enabled in Blender."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("get_hunyuan3d_status"))
    return result
    
@mcp.tool()
@tool_envelope
def generate_hunyuan3d_model(
    ctx: Context,
    text_prompt: str = None,
    input_image_url: str = None
) -> str:
    """
    Generate 3D asset using Hunyuan3D by providing either text description, image reference,
    or both for the desired asset, and import the asset into Blender.
    The 3D asset has built-in materials.

    Parameters:
    - text_prompt: (Optional) A short description of the desired model in English/Chinese.
    - input_image_url: (Optional) The local or remote url of the input image. Accepts None if only using text prompt.

    Returns:
    - When successful, returns a JSON with job_id (format: "job_xxx") indicating the task is in progress
    - When the job completes, the status will change to "DONE" indicating the model has been imported
    - Returns error message if the operation fails
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("create_hunyuan_job", {
        "text_prompt": text_prompt,
        "image": input_image_url,
    }))
    if "JobId" in result.get("Response", {}):
        job_id = result["Response"]["JobId"]
        formatted_job_id = f"job_{job_id}"
        return {"job_id": formatted_job_id}
    return result

@mcp.tool()
@tool_envelope
def poll_hunyuan_job_status(
    ctx: Context,
    job_id: str=None,
):
    """
    Check if the Hunyuan3D generation task is completed.

    For Hunyuan3D:
        Parameters:
        - job_id: The job_id given in the generate model step.

        Returns the generation task status. The task is done if status is "DONE".
        The task is in progress if status is "RUN".
        If status is "DONE", returns ResultFile3Ds, which is the generated ZIP model path
        When the status is "DONE", the response includes a field named ResultFile3Ds that contains the generated ZIP file path of the 3D model in OBJ format.
        This is a polling API, so only proceed if the status are finally determined ("DONE" or some failed state).
    """
    blender = get_blender_connection()
    kwargs = {
        "job_id": job_id,
    }
    result = _check_addon_result(blender.send_command("poll_hunyuan_job_status", kwargs))
    return result

@mcp.tool()
@tool_envelope
def import_hunyuan3d_asset(
    ctx: Context,
    name: str,
    zip_file_url: str,
):
    """
    Import the asset generated by Hunyuan3D after the generation task is completed.

    Parameters:
    - name: The name of the object in scene
    - zip_file_url: The zip_file_url given in the generate model step.

    Return if the asset has been imported successfully.
    """
    blender = get_blender_connection()
    kwargs = {
        "name": name
    }
    if zip_file_url:
        kwargs["zip_file_url"] = zip_file_url
    result = _check_addon_result(blender.send_command("import_hunyuan3d_asset", kwargs))
    return result


@mcp.prompt()
def asset_creation_strategy() -> str:
    """Defines the preferred strategy for creating assets in Blender"""
    return """When creating 3D content in Blender, always start by checking if integrations are available:

    0. Before anything, always check the scene from get_scene_info()
    1. First use the following tools to verify if the following integrations are enabled:
        1. PolyHaven
            Use get_polyhaven_status() to verify its status
            If PolyHaven is enabled:
            - For objects/models: Use download_polyhaven_asset() with asset_type="models"
            - For materials/textures: Use download_polyhaven_asset() with asset_type="textures"
            - For environment lighting: Use download_polyhaven_asset() with asset_type="hdris"
        2. Sketchfab
            Sketchfab is good at Realistic models, and has a wider variety of models than PolyHaven.
            Use get_sketchfab_status() to verify its status
            If Sketchfab is enabled:
            - For objects/models: First search using search_sketchfab_models() with your query
            - Then download specific models using download_sketchfab_model() with the UID
            - Note that only downloadable models can be accessed, and API key must be properly configured
            - Sketchfab has a wider variety of models than PolyHaven, especially for specific subjects
        3. Hyper3D(Rodin)
            Hyper3D Rodin is good at generating 3D models for single item.
            So don't try to:
            1. Generate the whole scene with one shot
            2. Generate ground using Hyper3D
            3. Generate parts of the items separately and put them together afterwards

            Use get_hyper3d_status() to verify its status
            If Hyper3D is enabled:
            - For objects/models, do the following steps:
                1. Create the model generation task
                    - Use generate_hyper3d_image_to_3d() if image(s) is/are given
                    - Use generate_hyper3d_text_to_3d() if generating 3D asset using text prompt
                    If key type is free_trial and insufficient balance error returned, tell the user that the free trial key can only generated limited models everyday, they can choose to:
                    - Wait for another day and try again
                    - Go to hyper3d.ai to find out how to get their own API key
                    - Go to fal.ai to get their own private API key
                2. Poll the status
                    - Use poll_hyper3d_job_status() to check if the generation task has completed or failed
                3. Import the asset
                    - Use import_hyper3d_asset() to import the generated GLB model the asset
                4. After importing the asset, ALWAYS check the world_bounding_box of the imported mesh, and adjust the mesh's location and size
                    Adjust the imported mesh's location, scale, rotation, so that the mesh is on the right spot.

                You can reuse assets previous generated by running python code to duplicate the object, without creating another generation task.
        4. Hunyuan3D
            Hunyuan3D is good at generating 3D models for single item.
            So don't try to:
            1. Generate the whole scene with one shot
            2. Generate ground using Hunyuan3D
            3. Generate parts of the items separately and put them together afterwards

            Use get_hunyuan3d_status() to verify its status
            If Hunyuan3D is enabled:
                if Hunyuan3D mode is "OFFICIAL_API":
                    - For objects/models, do the following steps:
                        1. Create the model generation task
                            - Use generate_hunyuan3d_model by providing either a **text description** OR an **image(local or urls) reference**.
                            - Go to cloud.tencent.com out how to get their own SecretId and SecretKey
                        2. Poll the status
                            - Use poll_hunyuan_job_status() to check if the generation task has completed or failed
                        3. Import the asset
                            - Use import_hunyuan3d_asset() to import the generated OBJ model the asset
                    if Hunyuan3D mode is "LOCAL_API":
                        - For objects/models, do the following steps:
                        1. Create the model generation task
                            - Use generate_hunyuan3d_model if image (local or urls)  or text prompt is given and import the asset

                You can reuse assets previous generated by running python code to duplicate the object, without creating another generation task.

    3. Always check the world_bounding_box for each item so that:
        - Ensure that all objects that should not be clipping are not clipping.
        - Items have right spatial relationship.
    
    4. Recommended asset source priority:
        - For specific existing objects: First try Sketchfab, then PolyHaven
        - For generic objects/furniture: First try PolyHaven, then Sketchfab
        - For custom or unique items not available in libraries: Use Hyper3D Rodin or Hunyuan3D
        - For environment lighting: Use PolyHaven HDRIs
        - For materials/textures: Use PolyHaven textures

    Only fall back to scripting when:
    - PolyHaven, Sketchfab, Hyper3D, and Hunyuan3D are all disabled
    - A simple primitive is explicitly requested
    - No suitable asset exists in any of the libraries
    - Hyper3D Rodin or Hunyuan3D failed to generate the desired asset
    - The task specifically requires a basic material/color
    """

# Main execution

def main():
    """Run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()
