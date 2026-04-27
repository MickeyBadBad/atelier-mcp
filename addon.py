# Code created by Siddharth Ahuja: www.github.com/ahujasid © 2025

import re
import bpy
import mathutils
import json
import threading
import socket
import time
import requests
import tempfile
import traceback
import os
import shutil
import zipfile
from bpy.props import IntProperty, BoolProperty
import io
from datetime import datetime
import hashlib, hmac, base64
import os.path as osp
from contextlib import redirect_stdout, suppress

bl_info = {
    "name": "Blender MCP",
    "author": "BlenderMCP",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to Claude via MCP",
    "category": "Interface",
}

RODIN_FREE_TRIAL_KEY = "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"

# Add User-Agent as required by Poly Haven API
REQ_HEADERS = requests.utils.default_headers()
REQ_HEADERS.update({"User-Agent": "blender-mcp"})


# --------------------------------------------------------------------------
# Resilient download helpers — wrap requests.get with exponential backoff +
# transparent resume for partial downloads. Sketchfab / PolyHaven CDNs
# regularly drop large transfers mid-stream (urllib3.IncompleteRead), so any
# call site that downloads more than ~100KB should go through these.
# --------------------------------------------------------------------------

def _resilient_retryable_excs():
    """Build the tuple of exception classes worth retrying on lazily so missing
    optional packages don't break import."""
    excs = []
    try:
        from requests.exceptions import (
            ChunkedEncodingError, ConnectionError as ReqConnErr, Timeout,
        )
        excs += [ChunkedEncodingError, ReqConnErr, Timeout]
    except Exception:
        pass
    try:
        from urllib3.exceptions import IncompleteRead, ProtocolError
        excs += [IncompleteRead, ProtocolError]
    except Exception:
        pass
    return tuple(excs) or (Exception,)


def _resilient_get(url, max_retries=3, backoff_base=1.7, timeout=30, **kwargs):
    """Wrap requests.get() with retry + exponential backoff for transient
    network errors. Returns the final Response, or raises after max_retries.

    Suitable for *small* responses (JSON, HTML, metadata) where loading
    .content into memory in one shot is fine. For large file downloads use
    _resilient_download_to_file() instead — it streams + resumes.
    """
    retryable = _resilient_retryable_excs()
    last_err = None
    kwargs.setdefault("timeout", timeout)
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, **kwargs)
            # Treat 5xx as retryable; 4xx is a client error, fail fast
            if response.status_code >= 500:
                raise requests.exceptions.HTTPError(
                    f"{response.status_code} {response.reason}", response=response
                )
            # Reading .content can also IncompleteRead — sniff once
            try:
                _ = response.content
            except retryable as e:
                raise e
            return response
        except retryable as e:
            last_err = e
            if attempt < max_retries:
                wait = backoff_base ** attempt
                print(f"[blender-mcp] _resilient_get retry {attempt}/{max_retries} "
                      f"for {url[:80]}{'...' if len(url) > 80 else ''}: "
                      f"{type(e).__name__}: {e}. Waiting {wait:.1f}s")
                time.sleep(wait)
                continue
        except requests.exceptions.HTTPError as e:
            # 5xx wrapped above ends up here; 4xx falls through to raise
            if 500 <= getattr(e.response, "status_code", 0) < 600 and attempt < max_retries:
                last_err = e
                wait = backoff_base ** attempt
                print(f"[blender-mcp] _resilient_get retry {attempt}/{max_retries} "
                      f"for {url[:80]} (HTTP {e.response.status_code}). "
                      f"Waiting {wait:.1f}s")
                time.sleep(wait)
                continue
            raise
    raise last_err


def _resilient_download_to_file(url, dest_path, max_retries=4, backoff_base=1.7,
                                timeout=120, chunk_size=1024 * 1024,
                                headers=None):
    """Stream-download a URL to dest_path with retry + Range-based resume.

    On retry, sends `Range: bytes=N-` so the server only resends the missing
    tail. Falls back to a fresh download if the server doesn't honor Range
    (200 instead of 206 means full reset). Returns the bytes written, or
    raises after max_retries.
    """
    retryable = _resilient_retryable_excs()
    request_headers = dict(headers) if headers else dict(REQ_HEADERS)
    last_err = None
    bytes_written = 0
    # Ensure parent dir exists
    parent = os.path.dirname(dest_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    for attempt in range(1, max_retries + 1):
        attempt_headers = dict(request_headers)
        if bytes_written > 0:
            attempt_headers["Range"] = f"bytes={bytes_written}-"
            mode = "ab"
        else:
            mode = "wb"
        try:
            response = requests.get(url, stream=True, timeout=timeout,
                                    headers=attempt_headers)
            # If we asked for a Range and server returned 200 (not 206), it
            # ignored Range — start over to keep the file consistent.
            if mode == "ab" and response.status_code == 200:
                bytes_written = 0
                with open(dest_path, "wb") as _:
                    pass
                mode = "wb"
            elif response.status_code not in (200, 206):
                raise requests.exceptions.HTTPError(
                    f"{response.status_code} {response.reason}", response=response
                )

            with open(dest_path, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        bytes_written += len(chunk)
            # If we got here without exception, transfer is complete
            return bytes_written
        except retryable as e:
            last_err = e
            if attempt < max_retries:
                wait = backoff_base ** attempt
                print(f"[blender-mcp] download retry {attempt}/{max_retries} "
                      f"for {url[:80]} ({bytes_written} bytes so far): "
                      f"{type(e).__name__}: {e}. Waiting {wait:.1f}s")
                time.sleep(wait)
                continue
        except requests.exceptions.HTTPError as e:
            sc = getattr(e.response, "status_code", 0)
            if 500 <= sc < 600 and attempt < max_retries:
                last_err = e
                wait = backoff_base ** attempt
                print(f"[blender-mcp] download retry {attempt}/{max_retries} "
                      f"for {url[:80]} (HTTP {sc}). Waiting {wait:.1f}s")
                time.sleep(wait)
                continue
            raise
    raise last_err


def get_blendermcp_addon_preferences(context=None):
    """Get add-on preferences object if available."""
    if context is None:
        context = bpy.context
    addon = context.preferences.addons.get(__name__)
    return addon.preferences if addon else None

class BlenderMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None

    def _get_config_value(self, scene_attr, pref_attr=None, env_var=None):
        """Read config in order: addon preferences -> scene -> env var."""
        prefs = get_blendermcp_addon_preferences()
        if prefs and pref_attr:
            pref_value = getattr(prefs, pref_attr, "")
            if pref_value:
                return pref_value

        scene_value = getattr(bpy.context.scene, scene_attr, "")
        if scene_value:
            return scene_value

        if env_var:
            env_value = os.getenv(env_var, "")
            if env_value:
                return env_value
        return ""

    def _get_tripo3d_api_key(self):
        return self._get_config_value(
            "blendermcp_tripo3d_api_key",
            "tripo3d_api_key",
            "BLENDERMCP_TRIPO3D_API_KEY",
        )

    def _get_meshy_api_key(self):
        return self._get_config_value(
            "blendermcp_meshy_api_key",
            "meshy_api_key",
            "BLENDERMCP_MESHY_API_KEY",
        )

    def _get_hyper3d_api_key(self):
        # Let the free-trial button temporarily override persistent keys
        # without overwriting user-saved private keys.
        scene_value = getattr(bpy.context.scene, "blendermcp_hyper3d_api_key", "")
        if scene_value == RODIN_FREE_TRIAL_KEY:
            return scene_value
        return self._get_config_value(
            "blendermcp_hyper3d_api_key",
            "hyper3d_api_key",
            "BLENDERMCP_HYPER3D_API_KEY",
        )

    def _get_sketchfab_api_key(self):
        return self._get_config_value(
            "blendermcp_sketchfab_api_key",
            "sketchfab_api_key",
            "BLENDERMCP_SKETCHFAB_API_KEY",
        )

    def _get_hunyuan3d_secret_id(self):
        return self._get_config_value(
            "blendermcp_hunyuan3d_secret_id",
            "hunyuan3d_secret_id",
            "BLENDERMCP_HUNYUAN3D_SECRET_ID",
        )

    def _get_hunyuan3d_secret_key(self):
        return self._get_config_value(
            "blendermcp_hunyuan3d_secret_key",
            "hunyuan3d_secret_key",
            "BLENDERMCP_HUNYUAN3D_SECRET_KEY",
        )

    def _get_hunyuan3d_api_url(self):
        return self._get_config_value(
            "blendermcp_hunyuan3d_api_url",
            "hunyuan3d_api_url",
            "BLENDERMCP_HUNYUAN3D_API_URL",
        ) or "http://localhost:8081"

    def start(self):
        if self.running:
            print("Server is already running")
            return

        self.running = True

        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)

            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()

            print(f"BlenderMCP server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False

        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        # Wait for thread to finish
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
            self.server_thread = None

        print("BlenderMCP server stopped")

    def _server_loop(self):
        """Main server loop in a separate thread"""
        print("Server thread started")
        self.socket.settimeout(1.0)  # Timeout to allow for stopping

        while self.running:
            try:
                # Accept new connection
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to client: {address}")

                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    # Just check running condition
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {str(e)}")
                    time.sleep(0.5)
            except Exception as e:
                print(f"Error in server loop: {str(e)}")
                if not self.running:
                    break
                time.sleep(0.5)

        print("Server thread stopped")

    def _handle_client(self, client):
        """Handle connected client"""
        print("Client handler started")
        client.settimeout(None)  # No timeout
        buffer = b''

        try:
            while self.running:
                # Receive data
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break

                    buffer += data
                    try:
                        # Try to parse command
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''

                        # Execute command in Blender's main thread
                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode('utf-8'))
                                except:
                                    print("Failed to send response - client disconnected")
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {
                                        "status": "error",
                                        "message": str(e)
                                    }
                                    client.sendall(json.dumps(error_response).encode('utf-8'))
                                except:
                                    pass
                            return None

                        # Schedule execution in main thread
                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError:
                        # Incomplete data, wait for more
                        pass
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
        except Exception as e:
            print(f"Error in client handler: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            print("Client handler stopped")

    def execute_command(self, command):
        """Execute a command in the main Blender thread"""
        try:
            return self._execute_command_internal(command)

        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        """Internal command execution with proper context"""
        cmd_type = command.get("type")
        params = command.get("params", {})

        # Add a handler for checking PolyHaven status
        if cmd_type == "get_polyhaven_status":
            return {"status": "success", "result": self.get_polyhaven_status()}

        # Base handlers that are always available
        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "get_viewport_screenshot": self.get_viewport_screenshot,
            "verify_object_grounded": self.verify_object_grounded,
            "execute_code": self.execute_code,
            "get_telemetry_consent": self.get_telemetry_consent,
            "get_polyhaven_status": self.get_polyhaven_status,
            "get_hyper3d_status": self.get_hyper3d_status,
            "get_sketchfab_status": self.get_sketchfab_status,
            "get_hunyuan3d_status": self.get_hunyuan3d_status,
            # Design-workflow helpers (added by fork)
            "apply_material_color": self.apply_material_color,
            "place_on_ground": self.place_on_ground,
            "render_image": self.render_image,
            "set_camera_view": self.set_camera_view,
            # Sprint 2 generic helpers (added by fork)
            "mesh_cleanup": self.mesh_cleanup,
            "boolean_cutout": self.boolean_cutout,
            "frame_camera_to_objects": self.frame_camera_to_objects,
            "setup_lighting": self.setup_lighting,
            "apply_archviz_material": self.apply_archviz_material,
            "list_archviz_genres": self.list_archviz_genres,
            "get_ambientcg_status": self.get_ambientcg_status,
            "search_ambientcg_assets": self.search_ambientcg_assets,
            "download_ambientcg_asset": self.download_ambientcg_asset,
            # Sprint 3: scatter / array / curve / export / hdri rotation
            "scatter_on_surface": self.scatter_on_surface,
            "array_duplicate": self.array_duplicate,
            "curve_extrude_profile": self.curve_extrude_profile,
            "quick_export": self.quick_export,
            "set_world_hdri_rotation": self.set_world_hdri_rotation,
            # Sprint 4: Tripo3D + Meshy.ai AI 3D generation
            "get_tripo3d_status": self.get_tripo3d_status,
            "generate_tripo3d_text_to_3d": self.generate_tripo3d_text_to_3d,
            "generate_tripo3d_image_to_3d": self.generate_tripo3d_image_to_3d,
            "get_meshy_status": self.get_meshy_status,
            "generate_meshy_text_to_3d": self.generate_meshy_text_to_3d,
            "generate_meshy_image_to_3d": self.generate_meshy_image_to_3d,
        }

        # Add Polyhaven handlers only if enabled
        if bpy.context.scene.blendermcp_use_polyhaven:
            polyhaven_handlers = {
                "get_polyhaven_categories": self.get_polyhaven_categories,
                "search_polyhaven_assets": self.search_polyhaven_assets,
                "download_polyhaven_asset": self.download_polyhaven_asset,
                "set_texture": self.set_texture,
            }
            handlers.update(polyhaven_handlers)

        # Add Hyper3d handlers only if enabled
        if bpy.context.scene.blendermcp_use_hyper3d:
            polyhaven_handlers = {
                "create_rodin_job": self.create_rodin_job,
                "poll_rodin_job_status": self.poll_rodin_job_status,
                "import_generated_asset": self.import_generated_asset,
            }
            handlers.update(polyhaven_handlers)

        # Add Sketchfab handlers only if enabled
        if bpy.context.scene.blendermcp_use_sketchfab:
            sketchfab_handlers = {
                "search_sketchfab_models": self.search_sketchfab_models,
                "get_sketchfab_model_preview": self.get_sketchfab_model_preview,
                "download_sketchfab_model": self.download_sketchfab_model,
            }
            handlers.update(sketchfab_handlers)
        
        # Add Hunyuan3d handlers only if enabled
        if bpy.context.scene.blendermcp_use_hunyuan3d:
            hunyuan_handlers = {
                "create_hunyuan_job": self.create_hunyuan_job,
                "poll_hunyuan_job_status": self.poll_hunyuan_job_status,
                "import_generated_asset_hunyuan": self.import_generated_asset_hunyuan
            }
            handlers.update(hunyuan_handlers)

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = handler(**params)
                print(f"Handler execution complete")
                return {"status": "success", "result": result}
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}



    def get_scene_info(self):
        """Get information about the current Blender scene"""
        try:
            print("Getting scene info...")
            # Simplify the scene info to reduce data size
            scene_info = {
                "name": bpy.context.scene.name,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "materials_count": len(bpy.data.materials),
                # Blender version is exposed so callers can branch on
                # version-sensitive API surface (enum values, operator args,
                # removed/renamed nodes) rather than guessing.
                "blender_version": list(bpy.app.version),
                "blender_version_string": bpy.app.version_string,
            }

            # Collect minimal object information (limit to first 10 objects)
            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= 10:  # Reduced from 20 to 10
                    break

                obj_info = {
                    "name": obj.name,
                    "type": obj.type,
                    # Only include basic location data
                    "location": [round(float(obj.location.x), 2),
                                round(float(obj.location.y), 2),
                                round(float(obj.location.z), 2)],
                }
                scene_info["objects"].append(obj_info)

            print(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            print(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

    @staticmethod
    def _get_aabb(obj):
        """ Returns the world-space axis-aligned bounding box (AABB) of an object. """
        if obj.type != 'MESH':
            raise TypeError("Object must be a mesh")

        # Get the bounding box corners in local space
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]

        # Convert to world coordinates
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]

        # Compute axis-aligned min/max coordinates
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))

        return [
            [*min_corner], [*max_corner]
        ]



    def get_object_info(self, name):
        """Get detailed information about a specific object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        # Basic object info
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
            "materials": [],
        }

        if obj.type == "MESH":
            bounding_box = self._get_aabb(obj)
            obj_info["world_bounding_box"] = bounding_box

        # Add material slots
        for slot in obj.material_slots:
            if slot.material:
                obj_info["materials"].append(slot.material.name)

        # Add mesh data if applicable
        if obj.type == 'MESH' and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }

        return obj_info

    def get_viewport_screenshot(self, max_size=800, filepath=None, format="png",
                                target_object=None, view="front",
                                distance_factor=2.5, ortho_padding=1.25):
        """
        Capture a screenshot of the current 3D viewport OR a clean orthographic
        diagnostic render of a specific object.

        Default path (target_object=None) screenshots the active 3D viewport,
        preserving overlays and the user's view. If target_object is provided,
        creates a temporary orthographic camera framed on that object from
        the named view and renders a clean image — useful for verifying
        grounding, alignment, and material claims that position math alone
        cannot confirm (asymmetric mesh edits, Displace modifiers, etc.).

        Parameters:
        - max_size: Maximum size in pixels for the largest dimension of the image
        - filepath: Path where to save the screenshot file
        - format: Image format (png, jpg, etc.)
        - target_object: If set, render an orthographic view of this object
        - view: Camera direction (front, back, left, right, top, bottom)
        - distance_factor: Camera distance as multiple of object's largest dimension
        - ortho_padding: Ortho scale multiplier (>1 leaves margin around the object)

        Returns success/error status
        """
        try:
            if not filepath:
                return {"error": "No filepath provided"}

            if target_object is not None:
                return self._render_ortho_diag(
                    target_object, filepath, max_size, format,
                    view, distance_factor, ortho_padding,
                )

            # Find the active 3D viewport
            area = None
            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    area = a
                    break

            if not area:
                return {"error": "No 3D viewport found"}

            # Take screenshot with proper context override
            with bpy.context.temp_override(area=area):
                bpy.ops.screen.screenshot_area(filepath=filepath)

            # Load and resize if needed
            img = bpy.data.images.load(filepath)
            width, height = img.size

            if max(width, height) > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img.scale(new_width, new_height)

                # Set format and save
                img.file_format = format.upper()
                img.save()
                width, height = new_width, new_height

            # Cleanup Blender image data
            bpy.data.images.remove(img)

            return {
                "success": True,
                "width": width,
                "height": height,
                "filepath": filepath
            }

        except Exception as e:
            return {"error": str(e)}

    def _render_ortho_diag(self, target_name, filepath, max_size, format,
                           view, distance_factor, ortho_padding):
        """Render a clean orthographic view of target_name from `view`."""
        import math

        scene = bpy.context.scene
        obj = scene.objects.get(target_name)
        if obj is None:
            return {"error": f"Object '{target_name}' not found in scene"}

        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mw = eval_obj.matrix_world
        corners = [mw @ mathutils.Vector(c) for c in eval_obj.bound_box]
        xs = [c.x for c in corners]
        ys = [c.y for c in corners]
        zs = [c.z for c in corners]
        center = mathutils.Vector((
            (min(xs) + max(xs)) / 2,
            (min(ys) + max(ys)) / 2,
            (min(zs) + max(zs)) / 2,
        ))
        size_x = max(xs) - min(xs)
        size_y = max(ys) - min(ys)
        size_z = max(zs) - min(zs)
        max_dim = max(size_x, size_y, size_z, 0.01)

        # (offset_direction_from_center, camera_euler_rotation)
        view_configs = {
            "front":  (mathutils.Vector((0, -1, 0)), (math.pi / 2, 0, 0)),
            "back":   (mathutils.Vector((0, 1, 0)),  (math.pi / 2, 0, math.pi)),
            "right":  (mathutils.Vector((1, 0, 0)),  (math.pi / 2, 0, math.pi / 2)),
            "left":   (mathutils.Vector((-1, 0, 0)), (math.pi / 2, 0, -math.pi / 2)),
            "top":    (mathutils.Vector((0, 0, 1)),  (0, 0, 0)),
            "bottom": (mathutils.Vector((0, 0, -1)), (math.pi, 0, 0)),
        }
        if view not in view_configs:
            return {"error": f"Unknown view '{view}'. Choose from: {sorted(view_configs)}"}

        offset_dir, rotation_euler = view_configs[view]
        cam_distance = max_dim * distance_factor
        cam_pos = center + offset_dir * cam_distance

        cam_data = bpy.data.cameras.new("_MCPDiagCam")
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = max_dim * ortho_padding
        cam_data.clip_start = 0.01
        cam_data.clip_end = cam_distance * 4 + max_dim * 4
        cam_obj = bpy.data.objects.new("_MCPDiagCam", cam_data)
        cam_obj.location = cam_pos
        cam_obj.rotation_euler = rotation_euler
        scene.collection.objects.link(cam_obj)

        # Save render state, render, restore
        prev_camera = scene.camera
        prev_res_x = scene.render.resolution_x
        prev_res_y = scene.render.resolution_y
        prev_filepath = scene.render.filepath
        prev_file_format = scene.render.image_settings.file_format
        width = height = 0
        render_error = None
        try:
            scene.camera = cam_obj
            scene.render.resolution_x = max_size
            scene.render.resolution_y = max_size
            scene.render.filepath = filepath
            scene.render.image_settings.file_format = format.upper()
            bpy.ops.render.render(write_still=True)

            if os.path.exists(filepath):
                img = bpy.data.images.load(filepath)
                width, height = img.size
                bpy.data.images.remove(img)
            else:
                render_error = "Render file was not created"
        except Exception as e:
            render_error = str(e)
        finally:
            scene.camera = prev_camera
            scene.render.resolution_x = prev_res_x
            scene.render.resolution_y = prev_res_y
            scene.render.filepath = prev_filepath
            scene.render.image_settings.file_format = prev_file_format
            bpy.data.objects.remove(cam_obj, do_unlink=True)
            bpy.data.cameras.remove(cam_data, do_unlink=True)

        if render_error:
            return {"error": render_error}

        return {
            "success": True,
            "width": width,
            "height": height,
            "filepath": filepath,
            "target": target_name,
            "view": view,
        }

    def verify_object_grounded(self, object_name, ground_name,
                               slice_height=1.0, max_samples=500):
        """Measure the vertical gap between an object's base and a ground mesh.

        Samples vertices from the object's lower slice (z <= zmin + slice_height)
        in world space and raycasts straight down onto the ground's evaluated
        mesh. Returns min/max/median/mean gaps (positive = floating above,
        negative = intersecting). Uses evaluated geometry so Displace modifiers
        on the ground and shape keys / armatures on the object are honored.

        If `object_name` resolves to an EMPTY (typical Sketchfab/GLB import
        hierarchy with multi-mesh children), all descendant meshes are sampled
        together — answers the question "is the imported model grounded?" in
        one call instead of forcing the caller to find the right child.
        """
        from mathutils.bvhtree import BVHTree

        scene = bpy.context.scene
        obj = scene.objects.get(object_name)
        ground = scene.objects.get(ground_name)
        if obj is None:
            return {"error": f"Object '{object_name}' not found"}
        if ground is None:
            return {"error": f"Ground object '{ground_name}' not found"}
        if ground.type != 'MESH':
            return {"error": f"Ground '{ground_name}' is not a mesh (type={ground.type})"}

        # Collect every mesh descendant (or just the object itself if it's a mesh)
        def collect_meshes(o, acc):
            if o.type == 'MESH' and o.data is not None:
                acc.append(o)
            for c in o.children:
                collect_meshes(c, acc)
        meshes = []
        collect_meshes(obj, meshes)
        if not meshes:
            return {"error": f"Object '{object_name}' has no mesh geometry to test (type={obj.type}, no mesh descendants)"}

        depsgraph = bpy.context.evaluated_depsgraph_get()
        ground_eval = ground.evaluated_get(depsgraph)
        bvh = BVHTree.FromObject(ground_eval, depsgraph)

        # Aggregate world-space verts from all descendant meshes
        world_verts = []
        sampled_meshes = []
        for m in meshes:
            m_eval = m.evaluated_get(depsgraph)
            mw = m_eval.matrix_world
            verts = [mw @ v.co for v in m_eval.data.vertices]
            world_verts.extend(verts)
            sampled_meshes.append(m.name)
        if not world_verts:
            return {"error": f"Object '{object_name}' (and its mesh descendants) have no vertices"}

        zmin = min(v.z for v in world_verts)
        slice_verts = [v for v in world_verts if v.z <= zmin + slice_height]
        if len(slice_verts) > max_samples:
            step = max(1, len(slice_verts) // max_samples)
            slice_verts = slice_verts[::step]

        gaps = []
        missed = 0
        for v in slice_verts:
            origin = mathutils.Vector((v.x, v.y, v.z + 1000.0))
            direction = mathutils.Vector((0, 0, -1))
            hit_loc, hit_normal, hit_idx, hit_dist = bvh.ray_cast(origin, direction)
            if hit_loc is None:
                missed += 1
                continue
            gaps.append(v.z - hit_loc.z)

        if not gaps:
            return {
                "error": "No ground samples hit — object may be outside ground bounds or ground mesh is empty",
                "samples_tested": len(slice_verts),
                "samples_missed": missed,
            }

        gaps_sorted = sorted(gaps)
        median_gap = gaps_sorted[len(gaps_sorted) // 2]
        min_gap = min(gaps)
        max_gap = max(gaps)

        if min_gap < -0.01 and max_gap > 0.01:
            hint = "mixed: tilted or uneven ground; base partly above and partly below"
        elif max_gap < 0.01:
            hint = "grounded or intersecting (no samples above ground)"
        elif min_gap > 0.05:
            hint = f"floating: closest sample is {min_gap:.3f}m above ground"
        else:
            hint = "close to ground"

        return {
            "object_name": object_name,
            "ground_name": ground_name,
            "sampled_meshes": sampled_meshes,
            "samples_tested": len(slice_verts),
            "samples_hit": len(gaps),
            "samples_missed": missed,
            "min_gap": round(min_gap, 4),
            "max_gap": round(max_gap, 4),
            "median_gap": round(median_gap, 4),
            "mean_gap": round(sum(gaps) / len(gaps), 4),
            "slice_height": slice_height,
            "hint": hint,
        }

    # ------------------------------------------------------------------
    # Design-workflow helpers (added by fork)
    # ------------------------------------------------------------------

    @staticmethod
    def _hex_to_rgba(hex_color: str):
        """Parse '#RRGGBB' / '#RGB' / 'RRGGBB' into a Blender (r,g,b,a) tuple."""
        h = hex_color.lstrip("#").strip()
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) != 6:
            raise ValueError(f"Invalid hex color: {hex_color!r}")
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        return (r, g, b, 1.0)

    @staticmethod
    def _world_bbox(obj):
        """World-space (min, max) of obj plus all descendant meshes, or (None, None)."""
        mins = [float("inf")] * 3
        maxs = [-float("inf")] * 3
        found = False

        def walk(o):
            nonlocal found
            if o.type == "MESH" and o.data:
                for v in o.bound_box:
                    w = o.matrix_world @ mathutils.Vector(v)
                    for i in range(3):
                        mins[i] = min(mins[i], w[i])
                        maxs[i] = max(maxs[i], w[i])
                    found = True
            for c in o.children:
                walk(c)

        walk(obj)
        if not found:
            return None, None
        return mathutils.Vector(mins), mathutils.Vector(maxs)

    def apply_material_color(self, object_name, hex_color,
                             roughness=0.7, metallic=0.0,
                             emission_color=None, emission_strength=0.0,
                             material_name=None):
        """Replace the object's material with a single Principled BSDF tinted to hex_color.

        Common case for design mock-ups: 'paint this wall #1a3a2e'. Avoids the
        boilerplate of building a shader graph via execute_code.
        """
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            return {"error": f"Object '{object_name}' not found"}
        if obj.type != "MESH":
            return {"error": f"Object '{object_name}' is not a mesh (type={obj.type})"}

        rgba = self._hex_to_rgba(hex_color)
        emission_rgba = self._hex_to_rgba(emission_color) if emission_color else None

        mat_name = material_name or f"Color_{hex_color.lstrip('#')}_{object_name}"
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        out.location = (300, 0)
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = float(roughness)
        bsdf.inputs["Metallic"].default_value = float(metallic)
        if emission_rgba is not None:
            # Principled BSDF in Blender 4.x has Emission Color + Emission Strength
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission_rgba
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = emission_rgba
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = float(emission_strength)
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

        obj.data.materials.clear()
        obj.data.materials.append(mat)

        return {
            "object_name": object_name,
            "material_name": mat.name,
            "base_color": list(rgba),
            "roughness": float(roughness),
            "metallic": float(metallic),
            "emission_strength": float(emission_strength),
        }

    def place_on_ground(self, object_name, ground_z=0.0,
                        center_xy=False, target_xy=None):
        """Translate an object so its bounding-box bottom sits on ground_z.

        Optional center_xy=True moves the bbox center to (0,0). Or pass an
        explicit target_xy=[x,y] to set the center elsewhere. Walks descendant
        meshes so imported FBX/GLB hierarchies (Sketchfab models) work
        without flattening the parent hierarchy.
        """
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            return {"error": f"Object '{object_name}' not found"}
        bmin, bmax = self._world_bbox(obj)
        if bmin is None:
            return {"error": f"Object '{object_name}' has no mesh geometry to bound"}

        delta_z = float(ground_z) - bmin.z
        delta_x = 0.0
        delta_y = 0.0
        if target_xy is not None:
            cx = (bmin.x + bmax.x) / 2
            cy = (bmin.y + bmax.y) / 2
            delta_x = float(target_xy[0]) - cx
            delta_y = float(target_xy[1]) - cy
        elif center_xy:
            cx = (bmin.x + bmax.x) / 2
            cy = (bmin.y + bmax.y) / 2
            delta_x = -cx
            delta_y = -cy

        obj.location.x += delta_x
        obj.location.y += delta_y
        obj.location.z += delta_z

        # Re-evaluate bbox for the response
        new_min, new_max = self._world_bbox(obj)
        return {
            "object_name": object_name,
            "delta": [round(delta_x, 4), round(delta_y, 4), round(delta_z, 4)],
            "new_bbox_min": [round(new_min.x, 4), round(new_min.y, 4), round(new_min.z, 4)],
            "new_bbox_max": [round(new_max.x, 4), round(new_max.y, 4), round(new_max.z, 4)],
        }

    def render_image(self, filepath, resolution=None, samples=64,
                     engine="CYCLES", use_gpu=True,
                     view_transform="Filmic", look="Medium High Contrast"):
        """Render the active camera to filepath (PNG by extension).

        Sets engine, samples, resolution, and tone-mapping in one call instead
        of asking the LLM to wire scene properties through execute_code.
        Returns the absolute filepath of the rendered image.
        """
        scene = bpy.context.scene
        if not scene.camera:
            return {"error": "Scene has no active camera. Use set_camera_view first."}

        # Engine
        if engine.upper() == "CYCLES":
            scene.render.engine = "CYCLES"
            scene.cycles.samples = int(samples)
            scene.cycles.use_denoising = True
            if use_gpu:
                try:
                    scene.cycles.device = "GPU"
                except Exception:
                    scene.cycles.device = "CPU"
        elif engine.upper() in ("EEVEE", "BLENDER_EEVEE", "EEVEE_NEXT", "BLENDER_EEVEE_NEXT"):
            for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
                try:
                    scene.render.engine = candidate
                    break
                except Exception:
                    continue
        else:
            return {"error": f"Unsupported engine '{engine}'. Use CYCLES or EEVEE."}

        if resolution is not None:
            scene.render.resolution_x = int(resolution[0])
            scene.render.resolution_y = int(resolution[1])
            scene.render.resolution_percentage = 100

        scene.view_settings.view_transform = view_transform
        scene.view_settings.look = look
        scene.render.film_transparent = False

        scene.render.filepath = filepath
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)

        return {
            "filepath": bpy.path.abspath(filepath),
            "engine": scene.render.engine,
            "samples": int(samples) if engine.upper() == "CYCLES" else None,
            "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        }

    def set_camera_view(self, target_object=None, target_xyz=None,
                        angle="3q", distance=10.0, lens=35.0,
                        height_offset=0.0):
        """Position the active camera to look at a target from a preset angle.

        Presets: front / back / left / right / top / 3q (3/4 hero shot) / iso.
        Either target_object (name) or target_xyz ([x,y,z]) is required.
        """
        import math
        if target_object is not None:
            obj = bpy.data.objects.get(target_object)
            if obj is None:
                return {"error": f"Object '{target_object}' not found"}
            bmin, bmax = self._world_bbox(obj)
            if bmin is None:
                target = obj.location.copy()
            else:
                target = mathutils.Vector((
                    (bmin.x + bmax.x) / 2,
                    (bmin.y + bmax.y) / 2,
                    (bmin.z + bmax.z) / 2,
                ))
        elif target_xyz is not None:
            target = mathutils.Vector(target_xyz)
        else:
            return {"error": "Either target_object or target_xyz is required"}

        target.z += float(height_offset)

        d = float(distance)
        offsets = {
            "front":  mathutils.Vector(( d,  0,  0)),
            "back":   mathutils.Vector((-d,  0,  0)),
            "left":   mathutils.Vector(( 0, -d,  0)),
            "right":  mathutils.Vector(( 0,  d,  0)),
            "top":    mathutils.Vector(( 0,  0,  d)),
            "3q":     mathutils.Vector(( d, -d, d * 0.5)),
            "iso":    mathutils.Vector(( d / math.sqrt(3),
                                        -d / math.sqrt(3),
                                         d / math.sqrt(3))),
        }
        if angle not in offsets:
            return {"error": f"Unknown angle '{angle}'. Choose from: {sorted(offsets)}"}

        cam = bpy.context.scene.camera
        if cam is None:
            # Find any camera, or create one
            cam = next((o for o in bpy.context.scene.objects if o.type == "CAMERA"), None)
            if cam is None:
                cam_data = bpy.data.cameras.new("Camera")
                cam = bpy.data.objects.new("Camera", cam_data)
                bpy.context.collection.objects.link(cam)
            bpy.context.scene.camera = cam

        cam.location = target + offsets[angle]
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = float(lens)

        return {
            "camera_name": cam.name,
            "location": [round(v, 4) for v in cam.location],
            "rotation_euler_deg": [round(math.degrees(v), 2) for v in cam.rotation_euler],
            "target": [round(v, 4) for v in target],
            "lens_mm": float(lens),
            "angle": angle,
        }

    # ------------------------------------------------------------------
    # Geometry / scene helpers — generic ops with high LLM error rate
    # ------------------------------------------------------------------

    def mesh_cleanup(self, object_name, merge_distance=0.0001,
                     decimate_ratio=1.0, recalc_normals=True,
                     remove_loose=True, fix_non_manifold=False,
                     triangulate=False):
        """Clean up a mesh: merge duplicate vertices, recalc normals, optional
        decimate, remove loose geometry, optional non-manifold fix and
        triangulate. Idempotent and safe on already-clean meshes.

        For LiDAR / photogrammetry imports this is the gate before any
        downstream work — those scans typically have duplicate verts,
        flipped normals, and excessive triangle counts.
        """
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            return {"error": f"Object '{object_name}' not found"}
        if obj.type != 'MESH':
            return {"error": f"Object '{object_name}' is not a mesh (type={obj.type})"}

        before_verts = len(obj.data.vertices)
        before_faces = len(obj.data.polygons)
        before_edges = len(obj.data.edges)

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Edit-mode operations
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        if merge_distance and merge_distance > 0:
            bpy.ops.mesh.remove_doubles(threshold=float(merge_distance))
        if recalc_normals:
            bpy.ops.mesh.normals_make_consistent(inside=False)
        if remove_loose:
            bpy.ops.mesh.delete_loose()
        if fix_non_manifold:
            try:
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.mesh.select_non_manifold()
                bpy.ops.mesh.fill()
            except Exception:
                pass
        if triangulate:
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.object.mode_set(mode='OBJECT')

        # Decimate via modifier (more reliable than the operator)
        decimate_applied = False
        if decimate_ratio < 1.0:
            mod = obj.modifiers.new(name="MCPDecimate", type='DECIMATE')
            mod.ratio = float(decimate_ratio)
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                decimate_applied = True
            except Exception as e:
                obj.modifiers.remove(mod)
                return {"error": f"Decimate failed: {e}"}

        after_verts = len(obj.data.vertices)
        after_faces = len(obj.data.polygons)
        after_edges = len(obj.data.edges)

        return {
            "object_name": object_name,
            "before": {"verts": before_verts, "edges": before_edges, "faces": before_faces},
            "after":  {"verts": after_verts,  "edges": after_edges,  "faces": after_faces},
            "removed": {
                "verts": before_verts - after_verts,
                "edges": before_edges - after_edges,
                "faces": before_faces - after_faces,
            },
            "decimate_applied": decimate_applied,
            "decimate_ratio": float(decimate_ratio) if decimate_applied else None,
        }

    def boolean_cutout(self, target_object, cutter_shape="box",
                       location=(0, 0, 0), size=(1, 1, 1),
                       rotation=(0, 0, 0),
                       cutter_object_name=None, operation="DIFFERENCE",
                       solver="EXACT", apply=True):
        """Cut a hole / merge / intersect with a primitive (or named mesh).

        Common interior-design ops: window apertures in walls, door frames,
        ventilation cutouts, decorative mortises. The native bpy flow is
        ~25 lines and easy to get wrong (Exact vs Fast solver, modifier
        ordering, post-cleanup).

        Parameters:
        - target_object: object to be cut
        - cutter_shape: 'box' | 'cylinder' | 'sphere' | 'mesh'
        - location, size (XYZ extents), rotation (radians) for primitive cutters
        - cutter_object_name: required when cutter_shape='mesh' — name of
          existing object to use as the cutter (won't be deleted)
        - operation: 'DIFFERENCE' (default — hole) | 'UNION' | 'INTERSECT'
        - solver: 'EXACT' (slower, robust on overlapping geo) | 'FAST'
        - apply: True to apply the modifier and delete the cutter primitive;
                 False to keep the modifier live
        """
        target = bpy.data.objects.get(target_object)
        if target is None:
            return {"error": f"Target '{target_object}' not found"}
        if target.type != 'MESH':
            return {"error": f"Target '{target_object}' is not a mesh (type={target.type})"}

        op_upper = operation.upper()
        if op_upper not in ('DIFFERENCE', 'UNION', 'INTERSECT'):
            return {"error": f"Unknown operation '{operation}'. Choose DIFFERENCE / UNION / INTERSECT."}
        solver_upper = solver.upper()
        if solver_upper not in ('EXACT', 'FAST'):
            return {"error": f"Unknown solver '{solver}'. Choose EXACT or FAST."}

        primitive_created = False
        if cutter_shape == 'mesh':
            if not cutter_object_name:
                return {"error": "cutter_shape='mesh' requires cutter_object_name"}
            cutter = bpy.data.objects.get(cutter_object_name)
            if cutter is None:
                return {"error": f"Cutter object '{cutter_object_name}' not found"}
        elif cutter_shape == 'box':
            bpy.ops.mesh.primitive_cube_add(size=2, location=tuple(location), rotation=tuple(rotation))
            cutter = bpy.context.active_object
            cutter.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
            bpy.ops.object.transform_apply(scale=True)
            cutter.name = f"_cutter_{target_object}"
            primitive_created = True
        elif cutter_shape == 'cylinder':
            bpy.ops.mesh.primitive_cylinder_add(radius=size[0] / 2, depth=size[2],
                                                location=tuple(location), rotation=tuple(rotation))
            cutter = bpy.context.active_object
            if size[1] != size[0]:
                cutter.scale = (1.0, size[1] / size[0], 1.0)
                bpy.ops.object.transform_apply(scale=True)
            cutter.name = f"_cutter_{target_object}"
            primitive_created = True
        elif cutter_shape == 'sphere':
            bpy.ops.mesh.primitive_uv_sphere_add(radius=size[0] / 2,
                                                 location=tuple(location), rotation=tuple(rotation))
            cutter = bpy.context.active_object
            if size[1] != size[0] or size[2] != size[0]:
                cutter.scale = (1.0, size[1] / size[0], size[2] / size[0])
                bpy.ops.object.transform_apply(scale=True)
            cutter.name = f"_cutter_{target_object}"
            primitive_created = True
        else:
            return {"error": f"Unknown cutter_shape '{cutter_shape}'. Use box/cylinder/sphere/mesh."}

        # Apply the boolean modifier
        bpy.ops.object.select_all(action='DESELECT')
        target.select_set(True)
        bpy.context.view_layer.objects.active = target

        mod = target.modifiers.new(name=f"BoolCut_{cutter.name}", type='BOOLEAN')
        mod.operation = op_upper
        mod.solver = solver_upper
        mod.object = cutter

        applied = False
        if apply:
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                applied = True
            except Exception as e:
                target.modifiers.remove(mod)
                if primitive_created:
                    bpy.data.objects.remove(cutter, do_unlink=True)
                return {"error": f"Boolean apply failed: {e}"}

            # Delete cutter primitive after successful apply
            if primitive_created:
                bpy.data.objects.remove(cutter, do_unlink=True)

        return {
            "target_object": target_object,
            "cutter_shape": cutter_shape,
            "cutter_object": None if (apply and primitive_created) else cutter.name,
            "operation": op_upper,
            "solver": solver_upper,
            "applied": applied,
            "modifier_name": None if applied else mod.name,
        }

    def frame_camera_to_objects(self, targets, orbit_deg=35, elevation_deg=15,
                                focal_mm=35.0, padding=1.1,
                                composition="thirds_left",
                                dof_target=None, f_stop=2.8):
        """Position the active camera so all `targets` fit in frame, with
        composed orbit + elevation + thirds offset. LLMs frequently put
        cameras inside walls or aimed at the world origin; this wraps
        Blender's camera_to_view_selected logic with sensible composition
        defaults.

        Parameters:
        - targets: object name OR list of object names (will frame their
                   combined bbox)
        - orbit_deg: rotation around Z (0 = front, 90 = right side, etc.)
        - elevation_deg: tilt above horizontal (0 = level, 90 = top-down)
        - focal_mm: lens focal length
        - padding: 1.0 = bbox kisses edges; 1.2 = 20% breathing room
        - composition: 'center' | 'thirds_left' | 'thirds_right' | 'thirds_top' | 'thirds_bottom'
        - dof_target: object name to focus on (creates focus distance);
                      None = no DOF
        - f_stop: aperture (lower = more blur)
        """
        import math as _math

        if isinstance(targets, str):
            targets = [targets]
        if not targets:
            return {"error": "targets is empty"}

        # Aggregate world bbox of all targets (and their mesh descendants)
        mins = [float('inf')] * 3
        maxs = [-float('inf')] * 3
        found = False
        def _walk(o):
            nonlocal found
            if o.type == 'MESH' and o.data:
                for v in o.bound_box:
                    w = o.matrix_world @ mathutils.Vector(v)
                    for i in range(3):
                        mins[i] = min(mins[i], w[i])
                        maxs[i] = max(maxs[i], w[i])
                    found = True
            for c in o.children:
                _walk(c)

        missing = []
        for name in targets:
            obj = bpy.data.objects.get(name)
            if obj is None:
                missing.append(name)
                continue
            _walk(obj)
        if missing:
            return {"error": f"Targets not found: {missing}"}
        if not found:
            return {"error": "No mesh geometry found in target hierarchy"}

        bbox_min = mathutils.Vector(mins)
        bbox_max = mathutils.Vector(maxs)
        center = (bbox_min + bbox_max) * 0.5
        size = bbox_max - bbox_min
        radius = max(size) / 2

        # Camera distance: ensure bbox fits FOV with padding
        fov_h = 2 * _math.atan(18.0 / float(focal_mm))   # Blender default sensor width = 36mm
        distance = (radius * float(padding)) / _math.tan(fov_h / 2)
        distance = max(distance, radius * 1.5)            # never inside the bbox

        orbit_rad = _math.radians(orbit_deg)
        elev_rad = _math.radians(elevation_deg)
        offset = mathutils.Vector((
            _math.cos(elev_rad) * _math.sin(orbit_rad) * distance,
            -_math.cos(elev_rad) * _math.cos(orbit_rad) * distance,
            _math.sin(elev_rad) * distance,
        ))

        cam = bpy.context.scene.camera
        if cam is None:
            cam = next((o for o in bpy.context.scene.objects if o.type == 'CAMERA'), None)
            if cam is None:
                cam_data = bpy.data.cameras.new("Camera")
                cam = bpy.data.objects.new("Camera", cam_data)
                bpy.context.collection.objects.link(cam)
            bpy.context.scene.camera = cam

        cam.location = center + offset
        direction = center - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = float(focal_mm)

        # Composition: thirds offset via lens shift (keeps perspective straight)
        cam.data.shift_x = 0.0
        cam.data.shift_y = 0.0
        if composition == "thirds_left":
            cam.data.shift_x = +0.166
        elif composition == "thirds_right":
            cam.data.shift_x = -0.166
        elif composition == "thirds_top":
            cam.data.shift_y = -0.166
        elif composition == "thirds_bottom":
            cam.data.shift_y = +0.166
        # "center" is the default (no shift)

        # Optional DOF
        if dof_target:
            dof_obj = bpy.data.objects.get(dof_target)
            if dof_obj is None:
                return {"error": f"DOF target '{dof_target}' not found"}
            cam.data.dof.use_dof = True
            cam.data.dof.focus_object = dof_obj
            cam.data.dof.aperture_fstop = float(f_stop)
        else:
            cam.data.dof.use_dof = False

        return {
            "camera_name": cam.name,
            "location": [round(v, 4) for v in cam.location],
            "target_center": [round(v, 4) for v in center],
            "bbox_size": [round(v, 4) for v in size],
            "distance": round(distance, 4),
            "lens_mm": float(focal_mm),
            "composition": composition,
            "shift_xy": [round(cam.data.shift_x, 4), round(cam.data.shift_y, 4)],
            "dof_enabled": cam.data.dof.use_dof,
            "framed_targets": targets,
        }

    # ------------------------------------------------------------------
    # Lighting moods — generic design intent, not space-specific
    # ------------------------------------------------------------------

    LIGHTING_MOODS = {
        "warm_intimate": {
            "description": "Low Kelvin, low ambient lux, strong table-level key lamps. "
                           "Dim cozy spaces — bars, lounges, evening dining, bedrooms.",
            "ambient_kelvin": 2200, "ambient_lux": 60,
            "accent_kelvin": 2400, "accent_lux": 200,
            "key_kelvin":    2200, "key_lux":    40,
            "world_strength": 0.3,
        },
        "daylight_neutral": {
            "description": "Balanced 4000-4500K, medium lux, soft sky fill. "
                           "Daylit interior shoots, residential common areas.",
            "ambient_kelvin": 4500, "ambient_lux": 250,
            "accent_kelvin": 5000, "accent_lux": 400,
            "key_kelvin":    5000, "key_lux":    600,
            "world_strength": 1.5,
        },
        "bright_workspace": {
            "description": "High lux, neutral 4000K, even coverage. "
                           "Offices, kitchens, classrooms, retail back-of-house.",
            "ambient_kelvin": 4000, "ambient_lux": 500,
            "accent_kelvin": 4000, "accent_lux": 700,
            "key_kelvin":    4000, "key_lux":    800,
            "world_strength": 2.0,
        },
        "dramatic_accent": {
            "description": "Low ambient + tight accent spotlights. "
                           "Galleries, retail focal displays, restaurants with hero plates.",
            "ambient_kelvin": 2700, "ambient_lux": 80,
            "accent_kelvin": 3000, "accent_lux": 600,
            "key_kelvin":    3000, "key_lux":    400,
            "world_strength": 0.4,
        },
        "golden_hour": {
            "description": "Warm sun-side key + cool sky ambient. "
                           "Exterior renders, interior at sunset, hero shots.",
            "ambient_kelvin": 6500, "ambient_lux": 200,
            "accent_kelvin": 2400, "accent_lux": 300,
            "key_kelvin":    2400, "key_lux":   1200,
            "world_strength": 1.8,
        },
        "cool_modern": {
            "description": "5500-6500K, clean even lighting. "
                           "Modernist showrooms, clinical/laboratory spaces, modern offices.",
            "ambient_kelvin": 5500, "ambient_lux": 300,
            "accent_kelvin": 6000, "accent_lux": 500,
            "key_kelvin":    5500, "key_lux":    700,
            "world_strength": 1.5,
        },
        "studio_neutral": {
            "description": "5500K even product photography setup. "
                           "Product viz, e-commerce, neutral catalog shoots.",
            "ambient_kelvin": 5500, "ambient_lux": 400,
            "accent_kelvin": 5500, "accent_lux": 600,
            "key_kelvin":    5500, "key_lux":   1000,
            "world_strength": 1.0,
        },
        "moody_lowkey": {
            "description": "Deep shadows, small key, no fill. "
                           "Cinematic / noir / mystery / horror.",
            "ambient_kelvin": 3000, "ambient_lux": 30,
            "accent_kelvin": 3000, "accent_lux": 100,
            "key_kelvin":    3500, "key_lux":    300,
            "world_strength": 0.2,
        },
    }

    def setup_lighting(self, mood="warm_intimate", target_object=None,
                       target_xyz=None, area_m2=20.0, ceiling_height_m=3.0,
                       remove_existing_lights=True):
        """Build a 3-layer lighting rig (ambient / accent / key) tuned to a
        named design-intent mood. Generic across cafe / retail / residential /
        office / studio. Returns the created light names + parameters.

        Parameters:
        - mood: one of LIGHTING_MOODS keys (warm_intimate / daylight_neutral /
                bright_workspace / dramatic_accent / golden_hour / cool_modern /
                studio_neutral / moody_lowkey)
        - target_object: focal point (uses bbox center) — accent and key
                         aim here. Mutually exclusive with target_xyz.
        - target_xyz: explicit focal point [x, y, z]
        - area_m2: room area, used to scale wattage
        - ceiling_height_m: where to place ambient lights
        - remove_existing_lights: clear lights named 'MCP_*' before building
        """
        import math as _math

        if mood not in self.LIGHTING_MOODS:
            return {"error": f"Unknown mood '{mood}'. Choose from: "
                             f"{sorted(self.LIGHTING_MOODS)}"}
        spec = self.LIGHTING_MOODS[mood]

        # Resolve focal point
        if target_object is not None:
            obj = bpy.data.objects.get(target_object)
            if obj is None:
                return {"error": f"target_object '{target_object}' not found"}
            bmin, bmax = self._world_bbox(obj)
            if bmin is None:
                target = obj.location.copy()
            else:
                target = mathutils.Vector(((bmin.x+bmax.x)/2, (bmin.y+bmax.y)/2, (bmin.z+bmax.z)/2))
        elif target_xyz is not None:
            target = mathutils.Vector(target_xyz)
        else:
            target = mathutils.Vector((0, 0, 1.0))

        # Optionally clean previous MCP lights
        if remove_existing_lights:
            for o in list(bpy.data.objects):
                if o.type == 'LIGHT' and o.name.startswith("MCP_"):
                    bpy.data.objects.remove(o, do_unlink=True)

        def _add_light(name, ltype, location, kelvin, lux_eqv,
                       size_m=1.0, rotation=(0, 0, 0)):
            light_data = bpy.data.lights.new(name=name, type=ltype)
            light_data.color = self._kelvin_to_rgb(kelvin)
            # Convert lux-ish target to Blender Watts:
            # Blender point/area lights: 1 W ~= ~683 lm at scotopic peak,
            # but for a 1m^2 area light the visible illuminance ratio is
            # roughly Watts*100 ~ lux at ~1m. Empirical, good enough for
            # design previews.
            light_data.energy = float(lux_eqv) * (size_m if ltype == 'AREA' else 1.0) * 1.0
            if ltype == 'AREA':
                light_data.size = size_m
            elif ltype == 'SPOT':
                light_data.spot_size = _math.radians(40)
                light_data.spot_blend = 0.3
            obj = bpy.data.objects.new(name, light_data)
            obj.location = location
            obj.rotation_euler = rotation
            bpy.context.collection.objects.link(obj)
            return obj

        # Ambient ring: 2-4 area lights below ceiling, evenly placed
        ambient_count = 3
        ambient_radius = max(2.0, _math.sqrt(area_m2) * 0.45)
        ambient_h = ceiling_height_m - 0.2
        ambients = []
        for i in range(ambient_count):
            angle = (i / ambient_count) * 2 * _math.pi
            loc = (target.x + ambient_radius * _math.cos(angle),
                   target.y + ambient_radius * _math.sin(angle),
                   ambient_h)
            # Point downward
            ambients.append(_add_light(
                f"MCP_Ambient_{i+1}", 'AREA', loc,
                spec["ambient_kelvin"], spec["ambient_lux"],
                size_m=1.5, rotation=(0, 0, 0),
            ))

        # Accent: spot light from above-left (45° elevation, 30° orbit)
        elev = _math.radians(45)
        orbit = _math.radians(30)
        d = max(2.5, _math.sqrt(area_m2) * 0.6)
        accent_loc = (target.x + d * _math.cos(elev) * _math.sin(orbit),
                      target.y - d * _math.cos(elev) * _math.cos(orbit),
                      target.z + d * _math.sin(elev))
        direction = target - mathutils.Vector(accent_loc)
        accent_rot = direction.to_track_quat('-Z', 'Y').to_euler()
        accent = _add_light(
            "MCP_Accent_Key", 'SPOT', accent_loc,
            spec["accent_kelvin"], spec["accent_lux"],
            rotation=accent_rot,
        )

        # Key/fill: small area light at table/object level
        key_loc = (target.x - 0.5, target.y - 0.5, target.z + 1.0)
        key = _add_light(
            "MCP_Key_Table", 'AREA', key_loc,
            spec["key_kelvin"], spec["key_lux"],
            size_m=0.4,
        )

        # World strength
        world = bpy.context.scene.world
        if world is None:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs["Strength"].default_value = float(spec["world_strength"])

        return {
            "mood": mood,
            "description": spec["description"],
            "ambient_lights": [a.name for a in ambients],
            "accent_light": accent.name,
            "key_light": key.name,
            "ambient_kelvin": spec["ambient_kelvin"],
            "accent_kelvin": spec["accent_kelvin"],
            "key_kelvin": spec["key_kelvin"],
            "world_strength": spec["world_strength"],
            "target": [round(v, 4) for v in target],
        }

    # ------------------------------------------------------------------
    # Archviz material genres — generic, library-agnostic
    # ------------------------------------------------------------------

    ARCHVIZ_GENRES = {
        # Each genre maps to: PolyHaven candidate IDs (priority order),
        # PolyHaven search filters (category + keywords) used as fallback,
        # default UV scale, description.
        "hardwood_floor": {
            "polyhaven_ids": ["dark_wooden_planks", "wood_floor_worn"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "wood,floor"},
            "uv_scale": 2.0,
            "description": "Hardwood floor (walnut, oak, dark)",
        },
        "softwood_planks": {
            "polyhaven_ids": ["brown_planks_05", "brown_planks_03", "brown_planks_09"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "wood"},
            "uv_scale": 3.0,
            "description": "Pine/cedar plank wall or panel",
        },
        "exposed_wood": {
            "polyhaven_ids": ["weathered_brown_planks", "green_rough_planks", "beam_wall_01"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "wood,raw wood"},
            "uv_scale": 2.0,
            "description": "Weathered/raw exposed wood",
        },
        "brick_wall": {
            "polyhaven_ids": ["brick_wall_003", "brick_wall_001", "brick_wall_006"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "brick"},
            "uv_scale": 3.0,
            "description": "Brick wall (clean to weathered)",
        },
        "brick_floor": {
            "polyhaven_ids": ["brick_floor", "brick_floor_003", "brick_pavement_02"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "brick,floor"},
            "uv_scale": 4.0,
            "description": "Brick or paved floor",
        },
        "concrete_smooth": {
            "polyhaven_ids": ["concrete_wall_007", "concrete_floor_painted"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "concrete"},
            "uv_scale": 2.0,
            "description": "Polished smooth concrete",
        },
        "concrete_rough": {
            "polyhaven_ids": ["concrete_layers_02", "rough_concrete_wall"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "concrete"},
            "uv_scale": 2.0,
            "description": "Rough or exposed concrete",
        },
        "plaster_wall": {
            "polyhaven_ids": ["beige_wall_001", "plaster_brick_01"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "plaster-concrete,plaster"},
            "uv_scale": 2.0,
            "description": "Painted plaster / drywall surface",
        },
        "natural_stone": {
            "polyhaven_ids": ["rock_face_03", "cliff_side"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "rock"},
            "uv_scale": 1.5,
            "description": "Natural stone (granite, slate, limestone)",
        },
        "tile_ceramic": {
            "polyhaven_ids": ["square_floor_tiles_01", "blue_floor_tiles_01"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "tiles"},
            "uv_scale": 4.0,
            "description": "Ceramic / porcelain tile",
        },
        "metal_industrial": {
            "polyhaven_ids": ["factory_wall", "corrugated_iron"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "metal"},
            "uv_scale": 2.0,
            "description": "Industrial metal panel (brushed steel, corrugated)",
        },
        "grass_ground": {
            "polyhaven_ids": ["aerial_grass_rock", "brown_mud_leaves_01"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "terrain,natural"},
            "uv_scale": 6.0,
            "description": "Grass / outdoor terrain",
        },
        "roof_clay_tiles": {
            "polyhaven_ids": ["clay_roof_tiles_03", "ceramic_roof_01", "red_slate_roof_tiles_01"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "roofing"},
            "uv_scale": 4.0,
            "description": "Terracotta or red clay roof tiles",
        },
        "roof_slate": {
            "polyhaven_ids": ["roof_slates_03", "roof_slates_02"],
            "polyhaven_filter": {"asset_type": "textures", "categories": "roofing"},
            "uv_scale": 4.0,
            "description": "Grey slate roofing",
        },
        # painted_wall is a special case — routes to apply_material_color
        # (no texture download required for flat paint).
    }

    def apply_archviz_material(self, object_name, genre,
                               color_hint=None, finish=None,
                               resolution="2k", custom_hex=None,
                               roughness=0.7, library="auto"):
        """High-level: pick a textured PBR material by generic genre keyword,
        download from PolyHaven, apply to the object via set_texture.

        For flat painted surfaces, pass genre='painted_wall' along with
        custom_hex='#RRGGBB' — this short-circuits to apply_material_color
        (no texture download).

        Parameters:
        - object_name: target mesh
        - genre: one of ARCHVIZ_GENRES keys, or 'painted_wall'
        - color_hint, finish: reserved for future genre filtering (currently
          ignored — picks first PolyHaven candidate that downloads)
        - resolution: PolyHaven resolution preference ('1k' / '2k' / '4k')
        - custom_hex: required when genre='painted_wall', ignored otherwise
        - roughness: only used for painted_wall
        - library: 'auto' (default — try polyhaven, then any registered
          alternative) | 'polyhaven' (force PolyHaven only)

        Returns the chosen asset_id and library, or an error if all
        candidates failed.
        """
        # painted_wall short-circuit
        if genre == "painted_wall":
            if not custom_hex:
                return {"error": "genre='painted_wall' requires custom_hex='#RRGGBB'"}
            return self.apply_material_color(
                object_name, custom_hex,
                roughness=roughness, metallic=0.0,
            )

        if genre not in self.ARCHVIZ_GENRES:
            available = sorted(self.ARCHVIZ_GENRES) + ["painted_wall"]
            return {"error": f"Unknown genre '{genre}'. Available: {available}"}

        spec = self.ARCHVIZ_GENRES[genre]
        candidates = list(spec.get("polyhaven_ids", []))
        last_err = None
        for asset_id in candidates:
            try:
                dl = self.download_polyhaven_asset(
                    asset_id=asset_id,
                    asset_type="textures",
                    resolution=resolution,
                )
                if isinstance(dl, dict) and dl.get("error"):
                    last_err = dl["error"]
                    continue
                # Successfully downloaded — apply
                applied = self.set_texture(object_name, asset_id)
                if isinstance(applied, dict) and applied.get("error"):
                    last_err = applied["error"]
                    continue
                return {
                    "object_name": object_name,
                    "genre": genre,
                    "library": "polyhaven",
                    "asset_id": asset_id,
                    "resolution": resolution,
                    "description": spec.get("description"),
                    "uv_scale_hint": spec.get("uv_scale", 1.0),
                }
            except Exception as e:
                last_err = str(e)
                continue

        return {
            "error": f"All PolyHaven candidates failed for genre '{genre}'. "
                     f"Tried: {candidates}. Last error: {last_err}",
            "genre": genre,
            "candidates_tried": candidates,
        }

    def list_archviz_genres(self):
        """Return all available archviz genre keys with descriptions and
        candidate asset IDs. Useful for the LLM to discover what's possible
        without trial-and-error."""
        return {
            genre: {
                "description": spec.get("description"),
                "uv_scale": spec.get("uv_scale", 1.0),
                "polyhaven_candidates": spec.get("polyhaven_ids", []),
            }
            for genre, spec in self.ARCHVIZ_GENRES.items()
        } | {
            "painted_wall": {
                "description": "Solid color paint (use custom_hex param)",
                "special": True,
                "requires": "custom_hex='#RRGGBB'",
            },
        }

    # ------------------------------------------------------------------
    # ambientCG integration — CC0 PBR textures (~2000+ materials)
    # https://docs.ambientcg.com/api/  No auth required.
    # ------------------------------------------------------------------

    def get_ambientcg_status(self):
        """Check ambientCG connectivity (no key needed; just verify network)."""
        try:
            r = _resilient_get(
                "https://ambientcg.com/api/v2/full_json",
                params={"type": "Material", "limit": 1},
                max_retries=2, timeout=10,
            )
            data = r.json()
            total = data.get("numberOfResults", 0)
            return {
                "enabled": True,
                "message": f"ambientCG reachable — {total} materials available",
                "total_materials": total,
            }
        except Exception as e:
            return {"enabled": False, "message": f"ambientCG unreachable: {e}"}

    def search_ambientcg_assets(self, query=None, asset_type="Material",
                                category=None, limit=20):
        """Search ambientCG asset library.

        Parameters:
        - query: free-text search term (e.g. 'brick', 'wood floor')
        - asset_type: 'Material' (default) | 'HDRI' | '3DModel' | 'Decal' | 'PlantModel'
        - category: optional category filter (e.g. 'Bricks', 'Wood')
        - limit: max results (1-100)

        Returns a list of {asset_id, name, category, available_resolutions}.
        """
        params = {
            "type": asset_type,
            "limit": min(int(limit), 100),
            "include": "downloadData,tagsArray",
        }
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        try:
            r = _resilient_get(
                "https://ambientcg.com/api/v2/full_json",
                params=params, max_retries=3, timeout=20,
            )
            data = r.json()
        except Exception as e:
            return {"error": f"ambientCG search failed: {e}"}

        assets = data.get("foundAssets", [])
        out = []
        for a in assets:
            asset_id = a.get("assetId")
            # Walk the actual structure:
            # downloadFolders (dict) -> 'default' -> downloadFiletypeCategories ->
            # 'zip' -> downloads (list of {attribute, fileName, size, downloadLink})
            res_set = set()
            df = a.get("downloadFolders") or {}
            for folder_key, folder_val in df.items():
                if not isinstance(folder_val, dict):
                    continue
                for cat_val in folder_val.get("downloadFiletypeCategories", {}).values():
                    for dl in cat_val.get("downloads", []):
                        attr = dl.get("attribute") or ""
                        for tok in ("1K", "2K", "4K", "8K"):
                            if tok in attr:
                                res_set.add(tok.lower())
            out.append({
                "asset_id": asset_id,
                "display_name": a.get("displayName") or a.get("customDisplayName"),
                "category": a.get("category") or a.get("displayCategory"),
                "tags": (a.get("tags") or "").split(",")[:6] if isinstance(a.get("tags"), str) else (a.get("tagsArray") or [])[:6],
                "resolutions": sorted(res_set) or ["unknown"],
                "downloads_total": a.get("downloadCount", 0),
            })
        return {
            "query": query, "asset_type": asset_type, "category": category,
            "total_results": data.get("numberOfResults", len(out)),
            "returned": len(out),
            "assets": out,
        }

    def download_ambientcg_asset(self, asset_id, resolution="2k", file_format="jpg"):
        """Download an ambientCG material zip, extract maps into bpy.data.images,
        and create a Blender material wired up like a Polyhaven texture import.

        Parameters:
        - asset_id: e.g. 'Bricks001', 'WoodFloor035'
        - resolution: '1k' | '2k' | '4k' | '8k'
        - file_format: 'jpg' (default, smaller) | 'png'

        Returns the created material name + downloaded map list.
        """
        # Look up download URL
        try:
            params = {
                "type": "Material",
                "id": asset_id,
                "include": "downloadData",
            }
            r = _resilient_get(
                "https://ambientcg.com/api/v2/full_json",
                params=params, max_retries=3, timeout=15,
            )
            data = r.json()
            assets = data.get("foundAssets", [])
            if not assets:
                return {"error": f"ambientCG asset '{asset_id}' not found"}
            target_asset = assets[0]

            # Find the matching zip download URL.
            # downloadFolders is a dict of folder_name -> {downloadFiletypeCategories ->
            # {zip -> {downloads: [{attribute: '2K-JPG', downloadLink: '...'}, ...]}}}
            target_attr = f"{resolution.upper()}-{file_format.upper()}"
            zip_url = None
            df = target_asset.get("downloadFolders") or {}
            for folder_key, folder_val in df.items():
                if not isinstance(folder_val, dict):
                    continue
                for cat_val in folder_val.get("downloadFiletypeCategories", {}).values():
                    for dl in cat_val.get("downloads", []):
                        if (dl.get("attribute") or "").upper() == target_attr:
                            zip_url = dl.get("downloadLink") or dl.get("fullDownloadPath")
                            if zip_url:
                                break
                    if zip_url: break
                if zip_url: break
            if not zip_url:
                return {"error": f"No {target_attr} bundle for '{asset_id}'"}
            if not zip_url.startswith("http"):
                zip_url = "https://ambientcg.com" + zip_url

            # Download the zip
            tmp_dir = tempfile.mkdtemp(prefix="ambientcg_")
            zip_path = os.path.join(tmp_dir, f"{asset_id}.zip")
            try:
                _resilient_download_to_file(zip_url, zip_path, max_retries=3)
            except Exception as e:
                with suppress(Exception):
                    shutil.rmtree(tmp_dir)
                return {"error": f"ambientCG download failed: {e}"}

            # Extract
            import zipfile
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_dir)

            # Load images into bpy.data.images
            loaded_maps = {}
            for fn in os.listdir(tmp_dir):
                low = fn.lower()
                if not (low.endswith(".jpg") or low.endswith(".png") or low.endswith(".jpeg")):
                    continue
                # Detect map type from filename
                kind = None
                if "color" in low: kind = "color"
                elif "normaldx" in low or "_dx" in low: kind = "nor_dx"
                elif "normalgl" in low or "_gl" in low: kind = "nor_gl"
                elif "roughness" in low or "rough" in low: kind = "rough"
                elif "displacement" in low or "disp" in low: kind = "displacement"
                elif "ao" in low or "occlusion" in low: kind = "ao"
                elif "metalness" in low or "metallic" in low: kind = "metallic"
                if not kind: continue
                full = os.path.join(tmp_dir, fn)
                img = bpy.data.images.load(full)
                img.name = f"{asset_id}_{kind}"
                img.pack()
                if kind != "color":
                    with suppress(Exception):
                        img.colorspace_settings.name = "Non-Color"
                loaded_maps[kind] = img

            # Build a material similar to PolyHaven set_texture
            mat = bpy.data.materials.new(f"ambientcg_{asset_id}")
            mat.use_nodes = True
            nt = mat.node_tree
            nt.nodes.clear()
            out_n = nt.nodes.new("ShaderNodeOutputMaterial"); out_n.location = (700, 0)
            bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (400, 0)
            tex_coord = nt.nodes.new("ShaderNodeTexCoord"); tex_coord.location = (-700, 0)
            mapping = nt.nodes.new("ShaderNodeMapping"); mapping.location = (-500, 0)
            nt.links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

            if "color" in loaded_maps:
                n = nt.nodes.new("ShaderNodeTexImage"); n.location = (-200, 200)
                n.image = loaded_maps["color"]
                nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])
                nt.links.new(n.outputs["Color"], bsdf.inputs["Base Color"])
            if "rough" in loaded_maps:
                n = nt.nodes.new("ShaderNodeTexImage"); n.location = (-200, 0)
                n.image = loaded_maps["rough"]
                nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])
                nt.links.new(n.outputs["Color"], bsdf.inputs["Roughness"])
            if "metallic" in loaded_maps:
                n = nt.nodes.new("ShaderNodeTexImage"); n.location = (-200, -150)
                n.image = loaded_maps["metallic"]
                nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])
                nt.links.new(n.outputs["Color"], bsdf.inputs["Metallic"])
            if "nor_gl" in loaded_maps or "nor_dx" in loaded_maps:
                norm_img = loaded_maps.get("nor_gl") or loaded_maps["nor_dx"]
                n_tex = nt.nodes.new("ShaderNodeTexImage"); n_tex.location = (-200, -350)
                n_tex.image = norm_img
                norm_node = nt.nodes.new("ShaderNodeNormalMap"); norm_node.location = (100, -350)
                nt.links.new(mapping.outputs["Vector"], n_tex.inputs["Vector"])
                nt.links.new(n_tex.outputs["Color"], norm_node.inputs["Color"])
                nt.links.new(norm_node.outputs["Normal"], bsdf.inputs["Normal"])
            nt.links.new(bsdf.outputs["BSDF"], out_n.inputs["Surface"])

            with suppress(Exception):
                shutil.rmtree(tmp_dir)

            return {
                "asset_id": asset_id,
                "resolution": resolution,
                "file_format": file_format,
                "material_name": mat.name,
                "maps_loaded": sorted(loaded_maps.keys()),
                "library": "ambientcg",
            }
        except Exception as e:
            return {"error": f"ambientCG download error: {e}"}

    @staticmethod
    def _kelvin_to_rgb(kelvin):
        """Convert color temperature to RGB (linear) — Tanner Helland's
        approximation, clamped. Good enough for preview lighting."""
        t = max(1000, min(40000, float(kelvin))) / 100.0
        if t <= 66:
            r = 1.0
            g = (99.4708025861 * (t ** 0.0) - 161.1195681661 + 0) / 255.0
            # Simpler: piecewise polynomial
            g = (99.4708025861 * (t / t)) / 255.0  # placeholder
        # Use a known-good polynomial via mathutils internal? Simpler: linear
        # approximation between 2000K (1, 0.45, 0.15) and 6500K (1, 1, 1).
        if kelvin <= 2000:
            return (1.0, 0.30, 0.10)
        if kelvin >= 6500:
            return (1.0, 1.0, 1.0)
        ratio = (kelvin - 2000) / (6500 - 2000)
        r = 1.0
        g = 0.30 + (1.0 - 0.30) * ratio
        b = 0.10 + (1.0 - 0.10) * (ratio ** 1.3)
        return (r, g, b)

    # ------------------------------------------------------------------
    # Sprint 3: scatter / array / curve / export / hdri rotation
    # ------------------------------------------------------------------

    def scatter_on_surface(self, surface_object, instance_objects,
                           density=10.0, max_count=1000, seed=0,
                           scale_min=0.8, scale_max=1.2,
                           rotate_random=True, align_to_normal=True,
                           parent_to_surface=False,
                           collection_name=None):
        """Distribute copies of one or more objects across the faces of a
        surface mesh, area-weighted with random rotation/scale and optional
        normal alignment.

        Use cases: books on a shelf, bottles on a bar, gravel on a path,
        scattered foliage on terrain, plates on a table.

        Parameters:
        - surface_object: mesh whose faces define the placement region
        - instance_objects: object name OR list of names (one is picked at
          random per placement). Originals are not moved; linked-data copies
          are created so memory stays low.
        - density: target placements per square meter of surface area
        - max_count: hard cap on placements (safety)
        - seed: RNG seed for reproducibility
        - scale_min/max: random uniform scale multiplier per instance
        - rotate_random: apply a random Z rotation to each instance
        - align_to_normal: rotate instance so +Z aligns with face normal
                           (good for surfaces, bad for vertical objects)
        - parent_to_surface: parent each instance to the surface object
        - collection_name: if set, link instances into a (newly created)
                           collection by this name; otherwise active collection
        """
        import random as _random

        surface = bpy.data.objects.get(surface_object)
        if surface is None:
            return {"error": f"Surface object '{surface_object}' not found"}
        if surface.type != 'MESH':
            return {"error": f"Surface '{surface_object}' is not a mesh (type={surface.type})"}

        if isinstance(instance_objects, str):
            instance_objects = [instance_objects]
        instances = []
        missing = []
        for name in instance_objects:
            o = bpy.data.objects.get(name)
            if o is None:
                missing.append(name)
            else:
                instances.append(o)
        if missing:
            return {"error": f"Instance objects not found: {missing}"}
        if not instances:
            return {"error": "instance_objects is empty"}

        # Evaluate the surface to honor modifiers / shape keys
        depsgraph = bpy.context.evaluated_depsgraph_get()
        surface_eval = surface.evaluated_get(depsgraph)
        mw = surface_eval.matrix_world
        polys = surface_eval.data.polygons
        verts = surface_eval.data.vertices
        if not len(polys):
            return {"error": "Surface mesh has no polygons"}

        # Compute per-polygon world area + cumulative distribution
        face_areas = []
        face_world_centers = []
        face_world_normals = []
        face_world_verts = []
        total_area = 0.0
        for p in polys:
            # Sample area in world space (account for non-uniform scale)
            w_pts = [mw @ verts[vi].co for vi in p.vertices]
            if len(w_pts) < 3:
                face_areas.append(0.0); face_world_centers.append(mw @ p.center)
                face_world_normals.append((mw.to_3x3() @ p.normal).normalized())
                face_world_verts.append(w_pts)
                continue
            # Triangulate area: sum of triangle fan from v0
            area = 0.0
            for i in range(1, len(w_pts) - 1):
                e1 = w_pts[i] - w_pts[0]
                e2 = w_pts[i + 1] - w_pts[0]
                area += 0.5 * (e1.cross(e2)).length
            face_areas.append(area)
            face_world_centers.append(mw @ p.center)
            face_world_normals.append((mw.to_3x3() @ p.normal).normalized())
            face_world_verts.append(w_pts)
            total_area += area

        if total_area <= 0:
            return {"error": "Surface area is zero (degenerate mesh?)"}

        target = min(int(total_area * float(density)), int(max_count))
        if target <= 0:
            return {"error": f"Density {density} on area {total_area:.3f}m² yields zero placements"}

        # Build cumulative weights for area-weighted face sampling
        cum = []
        running = 0.0
        for a in face_areas:
            running += a
            cum.append(running)

        # Set up collection
        if collection_name:
            coll = bpy.data.collections.get(collection_name)
            if coll is None:
                coll = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(coll)
        else:
            coll = bpy.context.collection

        rng = _random.Random(seed)
        placed_names = []
        # Up vector for normal alignment (Z axis of instance)
        up = mathutils.Vector((0, 0, 1))

        def sample_point_in_polygon(verts_list):
            """Random point uniformly in a triangulated polygon (fan)."""
            n = len(verts_list)
            if n < 3:
                return verts_list[0] if verts_list else mathutils.Vector((0, 0, 0))
            # Triangle area-weighted picking among fan triangles
            tris = []
            sum_a = 0.0
            for i in range(1, n - 1):
                a = verts_list[0]; b = verts_list[i]; c = verts_list[i + 1]
                ar = 0.5 * ((b - a).cross(c - a)).length
                sum_a += ar
                tris.append((a, b, c, sum_a))
            if sum_a <= 0:
                return verts_list[0]
            r = rng.uniform(0, sum_a)
            for (a, b, c, csum) in tris:
                if r <= csum:
                    # Barycentric random point in triangle
                    r1 = rng.random()
                    r2 = rng.random()
                    if r1 + r2 > 1.0:
                        r1 = 1.0 - r1
                        r2 = 1.0 - r2
                    return a + r1 * (b - a) + r2 * (c - a)
            return tris[-1][0]

        for i in range(target):
            # Sample a face by cumulative area
            r = rng.uniform(0, total_area)
            # Linear search is fine for typical face counts; binary search would
            # be marginally faster but adds bisect import for ~no win.
            fi = 0
            while fi < len(cum) and cum[fi] < r:
                fi += 1
            if fi >= len(face_areas):
                fi = len(face_areas) - 1

            point = sample_point_in_polygon(face_world_verts[fi])
            normal = face_world_normals[fi]

            # Pick a random instance source
            src = rng.choice(instances)
            inst = src.copy()
            if src.data is not None:
                inst.data = src.data   # share mesh data
            inst.name = f"{src.name}_scatter_{i+1}"
            coll.objects.link(inst)

            # Position
            inst.location = point

            # Rotation: align local Z to normal then optional random spin
            if align_to_normal and normal.length > 0:
                quat = up.rotation_difference(normal)
                inst.rotation_mode = 'QUATERNION'
                inst.rotation_quaternion = quat
                if rotate_random:
                    # Add random twist around the new Z axis
                    twist_q = mathutils.Quaternion(normal, rng.uniform(0, 6.283185))
                    inst.rotation_quaternion = twist_q @ inst.rotation_quaternion
            elif rotate_random:
                inst.rotation_euler = (0, 0, rng.uniform(0, 6.283185))

            # Scale
            s = rng.uniform(scale_min, scale_max)
            inst.scale = (s, s, s)

            # Optional parenting
            if parent_to_surface:
                inst.parent = surface

            placed_names.append(inst.name)

        return {
            "surface_object": surface_object,
            "instance_sources": [o.name for o in instances],
            "total_area_m2": round(total_area, 3),
            "density_per_m2": float(density),
            "placed_count": len(placed_names),
            "first_5_placed": placed_names[:5],
            "collection": coll.name,
        }

    def array_duplicate(self, source_object, mode="linear", count=5,
                        offset=None, angle_deg=360.0, axis="Z",
                        center=None, apply=False):
        """Duplicate an object linearly or radially using a real Array
        modifier (live or applied).

        Parameters:
        - source_object: mesh to duplicate
        - mode: 'linear' | 'radial'
        - count: total copies (including the original)
        - offset: linear mode: [dx, dy, dz] world-space step between copies.
                  None = use object dimensions × X axis (handy default).
        - angle_deg: radial mode: total spread (default 360 = full ring)
        - axis: radial mode: rotation axis 'X' | 'Y' | 'Z'
        - center: radial mode: world-space pivot [x, y, z];
                  None = use source_object location
        - apply: True = apply the modifier (and remove the helper Empty for
                 radial); False = keep live for further tweaking
        """
        obj = bpy.data.objects.get(source_object)
        if obj is None:
            return {"error": f"Source '{source_object}' not found"}
        if int(count) < 2:
            return {"error": "count must be >= 2"}

        import math as _math
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        if mode == "linear":
            mod = obj.modifiers.new(name="MCPArrayLinear", type='ARRAY')
            mod.count = int(count)
            mod.use_relative_offset = False
            mod.use_constant_offset = True
            if offset is None:
                # Default: one unit along X based on dimension
                offset = [obj.dimensions.x * 1.05, 0.0, 0.0]
            mod.constant_offset_displace = offset
            helper_empty = None
        elif mode == "radial":
            # Radial uses an Empty with rotation
            pivot = list(center) if center is not None else list(obj.location)
            empty = bpy.data.objects.new(f"_array_pivot_{obj.name}", None)
            empty.location = pivot
            bpy.context.collection.objects.link(empty)
            ax = axis.upper()
            ax_idx = {"X": 0, "Y": 1, "Z": 2}.get(ax)
            if ax_idx is None:
                return {"error": f"Unknown axis '{axis}'. Use X/Y/Z."}
            step = _math.radians(float(angle_deg) / int(count))
            empty.rotation_euler = (0, 0, 0)
            empty.rotation_euler[ax_idx] = step
            mod = obj.modifiers.new(name="MCPArrayRadial", type='ARRAY')
            mod.count = int(count)
            mod.use_relative_offset = False
            mod.use_constant_offset = False
            mod.use_object_offset = True
            mod.offset_object = empty
            helper_empty = empty
        else:
            return {"error": f"Unknown mode '{mode}'. Use 'linear' or 'radial'."}

        applied = False
        if apply:
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                applied = True
                if helper_empty is not None:
                    bpy.data.objects.remove(helper_empty, do_unlink=True)
            except Exception as e:
                return {"error": f"Array apply failed: {e}"}

        return {
            "source_object": source_object,
            "mode": mode,
            "count": int(count),
            "offset": offset if mode == "linear" else None,
            "angle_deg": float(angle_deg) if mode == "radial" else None,
            "axis": axis if mode == "radial" else None,
            "applied": applied,
            "modifier_name": None if applied else mod.name,
            "helper_empty": None if (apply or mode == "linear") else helper_empty.name,
        }

    def curve_extrude_profile(self, name, path_points,
                              profile="round", thickness=0.02,
                              resolution=12, closed=False, smooth=True,
                              convert_to_mesh=False,
                              location=(0, 0, 0)):
        """Build a Blender curve from path_points and apply a bevel profile
        for neon signs, brass pipes, cables, decorative trim, railings.

        Parameters:
        - name: name for the new object
        - path_points: list of [x, y, z] (world space). >=2 points.
        - profile: 'round' (cylindrical) | 'square' | 'flat' | name of an
          existing 2D curve object to use as a custom profile
        - thickness: bevel depth (radius for round, half-width for square)
        - resolution: bevel resolution (round/square only)
        - closed: True closes the curve into a loop
        - smooth: True sets shade smooth (round profile only)
        - convert_to_mesh: True converts curve to mesh after creation
        - location: object origin (path_points are interpreted relative
          to this if given non-zero; default places points in world space)
        """
        if not path_points or len(path_points) < 2:
            return {"error": "path_points must contain >= 2 points"}

        curve_data = bpy.data.curves.new(name=f"{name}_curve_data", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = max(2, int(resolution))

        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(count=len(path_points) - 1)
        for i, pt in enumerate(path_points):
            bp = spline.bezier_points[i]
            bp.co = tuple(pt)
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'
        spline.use_cyclic_u = bool(closed)

        # Bevel profile
        if profile == "round":
            curve_data.bevel_mode = 'ROUND'
            curve_data.bevel_depth = float(thickness)
            curve_data.bevel_resolution = max(0, int(resolution // 2))
            custom_profile_name = None
        elif profile == "square":
            curve_data.bevel_mode = 'PROFILE'
            curve_data.bevel_depth = float(thickness)
            try:
                curve_data.bevel_profile.preset = 'STEPS'
            except Exception:
                pass
            custom_profile_name = None
        elif profile == "flat":
            curve_data.bevel_mode = 'ROUND'
            curve_data.bevel_depth = 0.0
            curve_data.extrude = float(thickness)
            custom_profile_name = None
        else:
            # Treat as custom curve object name
            custom = bpy.data.objects.get(profile)
            if custom is None or custom.type != 'CURVE':
                return {"error": f"profile '{profile}' must be 'round'/'square'/'flat' or a curve object name"}
            curve_data.bevel_mode = 'OBJECT'
            curve_data.bevel_object = custom
            custom_profile_name = profile

        obj = bpy.data.objects.new(name, curve_data)
        obj.location = tuple(location)
        bpy.context.collection.objects.link(obj)

        if smooth and profile == "round":
            curve_data.use_fill_caps = True

        converted = False
        if convert_to_mesh:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            try:
                bpy.ops.object.convert(target='MESH')
                converted = True
            except Exception as e:
                return {"error": f"Curve-to-mesh conversion failed: {e}"}

        return {
            "name": obj.name,
            "type": obj.type,  # CURVE or MESH after conversion
            "profile": profile,
            "custom_profile_object": custom_profile_name,
            "thickness": float(thickness),
            "closed": bool(closed),
            "point_count": len(path_points),
            "converted_to_mesh": converted,
        }

    def quick_export(self, filepath, objects=None, format="auto",
                     pack_textures=True, apply_modifiers=True,
                     selected_only=False, axis_forward="-Z", axis_up="Y",
                     draco=True):
        """Export objects to GLB/FBX/OBJ/USD with sensible defaults for
        contractor / 3D viewer / game engine handoff.

        Format is auto-detected from the file extension; pass format='glb'
        to override. Always packs textures for GLB by default (otherwise
        clients open empty files — the #1 gotcha on r/blender).

        Parameters:
        - filepath: output path. Extension drives format if format='auto'.
        - objects: list of object names to export. None = whole scene.
        - format: 'auto' | 'glb' | 'gltf' | 'fbx' | 'obj' | 'usd' | 'usdz'
        - pack_textures: GLB/USDZ embed textures into file
        - apply_modifiers: bake modifier stack at export time
        - selected_only: export only selected (overrides `objects`)
        - axis_forward, axis_up: coordinate convention for FBX/OBJ
        - draco: GLB Draco compression
        """
        # Determine format
        ext = os.path.splitext(filepath)[1].lower().lstrip('.')
        fmt = format.lower()
        if fmt == "auto":
            fmt = ext if ext in ("glb", "gltf", "fbx", "obj", "usd", "usdz") else "glb"

        # Selection management
        if not selected_only:
            bpy.ops.object.select_all(action='DESELECT')
            if objects:
                missing = []
                for name in objects:
                    o = bpy.data.objects.get(name)
                    if o is None:
                        missing.append(name); continue
                    o.select_set(True)
                if missing:
                    return {"error": f"Objects not found: {missing}"}
                use_selection = True
            else:
                # Select everything
                for o in bpy.context.scene.objects:
                    if o.type in ('MESH', 'EMPTY', 'CURVE', 'ARMATURE', 'LIGHT', 'CAMERA'):
                        o.select_set(True)
                use_selection = False
        else:
            use_selection = True

        # Ensure parent dir exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)) or ".", exist_ok=True)

        try:
            if fmt in ("glb", "gltf"):
                kwargs = dict(
                    filepath=filepath,
                    export_format='GLB' if fmt == "glb" else 'GLTF_SEPARATE',
                    use_selection=use_selection if (selected_only or objects) else False,
                    export_apply=apply_modifiers,
                )
                # Embed textures and Draco compression where supported
                try: kwargs["export_image_format"] = 'AUTO'
                except Exception: pass
                if draco:
                    try: kwargs["export_draco_mesh_compression_enable"] = True
                    except Exception: pass
                bpy.ops.export_scene.gltf(**kwargs)
            elif fmt == "fbx":
                bpy.ops.export_scene.fbx(
                    filepath=filepath,
                    use_selection=use_selection if (selected_only or objects) else False,
                    bake_space_transform=True,
                    apply_unit_scale=True,
                    apply_scale_options='FBX_SCALE_NONE',
                    use_mesh_modifiers=apply_modifiers,
                    path_mode='COPY' if pack_textures else 'AUTO',
                    embed_textures=bool(pack_textures),
                    axis_forward=axis_forward,
                    axis_up=axis_up,
                )
            elif fmt == "obj":
                # Blender 4.x uses wm.obj_export; legacy export_scene.obj is gone
                try:
                    bpy.ops.wm.obj_export(
                        filepath=filepath,
                        export_selected_objects=use_selection if (selected_only or objects) else False,
                        apply_modifiers=apply_modifiers,
                        forward_axis={'-Z': 'NEGATIVE_Z', 'Z': 'Z',
                                      '-Y': 'NEGATIVE_Y', 'Y': 'Y',
                                      '-X': 'NEGATIVE_X', 'X': 'X'}.get(axis_forward, 'NEGATIVE_Z'),
                        up_axis={'X': 'X', 'Y': 'Y', 'Z': 'Z'}.get(axis_up, 'Y'),
                    )
                except AttributeError:
                    bpy.ops.export_scene.obj(
                        filepath=filepath,
                        use_selection=use_selection if (selected_only or objects) else False,
                        use_mesh_modifiers=apply_modifiers,
                        axis_forward=axis_forward,
                        axis_up=axis_up,
                    )
            elif fmt in ("usd", "usdz"):
                try:
                    bpy.ops.wm.usd_export(
                        filepath=filepath,
                        selected_objects_only=use_selection if (selected_only or objects) else False,
                        export_textures=pack_textures,
                        evaluation_mode='RENDER' if apply_modifiers else 'VIEWPORT',
                    )
                except Exception as e:
                    return {"error": f"USD export not available: {e}"}
            else:
                return {"error": f"Unsupported format '{fmt}'. Use glb/gltf/fbx/obj/usd/usdz."}
        except Exception as e:
            return {"error": f"Export failed: {e}"}

        size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        return {
            "filepath": os.path.abspath(filepath),
            "format": fmt,
            "bytes_written": size,
            "selected_only": selected_only,
            "exported_objects": objects if objects else "all_scene",
            "pack_textures": pack_textures,
            "apply_modifiers": apply_modifiers,
        }

    def set_world_hdri_rotation(self, z_rotation_deg=0.0, strength=None):
        """Rotate the world environment HDRI around Z and/or set its strength.

        Convenient for time-of-day adjustments without re-downloading a new
        HDRI: spin the existing one to put the sun behind/in-front-of the
        camera.

        Parameters:
        - z_rotation_deg: rotation around Z (0 = original orientation)
        - strength: if not None, set Background node strength
        """
        world = bpy.context.scene.world
        if world is None:
            return {"error": "Scene has no world environment. Download an HDRI first."}
        if not world.use_nodes:
            world.use_nodes = True
        nt = world.node_tree

        # Find existing TexEnvironment + Mapping or create them
        env = next((n for n in nt.nodes if n.type == 'TEX_ENVIRONMENT'), None)
        if env is None:
            return {"error": "No TexEnvironment node — set an HDRI first via download_polyhaven_asset"}

        bg = next((n for n in nt.nodes if n.type == 'BACKGROUND'), None)
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_WORLD'), None)

        # Find or create Mapping + TexCoord between TexCoord and Env
        mapping = next((n for n in nt.nodes if n.type == 'MAPPING'), None)
        if mapping is None:
            mapping = nt.nodes.new("ShaderNodeMapping")
            mapping.location = (env.location.x - 200, env.location.y)
        tex_coord = next((n for n in nt.nodes if n.type == 'TEX_COORD'), None)
        if tex_coord is None:
            tex_coord = nt.nodes.new("ShaderNodeTexCoord")
            tex_coord.location = (mapping.location.x - 200, mapping.location.y)

        # Wire if not already wired
        # TexCoord.Generated -> Mapping.Vector -> Env.Vector
        def _has_link(from_node, from_socket, to_node, to_socket):
            for l in nt.links:
                if (l.from_node == from_node and l.from_socket.name == from_socket
                    and l.to_node == to_node and l.to_socket.name == to_socket):
                    return True
            return False
        if not _has_link(tex_coord, "Generated", mapping, "Vector"):
            nt.links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
        if not _has_link(mapping, "Vector", env, "Vector"):
            nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])

        # Apply rotation
        import math as _math
        rot = list(mapping.inputs["Rotation"].default_value)
        rot[2] = _math.radians(float(z_rotation_deg))
        mapping.inputs["Rotation"].default_value = rot

        result = {
            "z_rotation_deg": float(z_rotation_deg),
            "rotation_radians": [round(v, 4) for v in rot],
        }
        if strength is not None and bg is not None:
            bg.inputs["Strength"].default_value = float(strength)
            result["strength"] = float(strength)
        return result

    # ------------------------------------------------------------------
    # Sprint 4: AI 3D generation services (Tripo3D + Meshy.ai)
    # Both sync wrappers — kick off + poll + download + import in one call
    # so the LLM gets a single round-trip per generation request.
    # ------------------------------------------------------------------

    # ---- Tripo3D ----------------------------------------------------

    TRIPO3D_BASE = "https://api.tripo3d.ai/v2/openapi"
    TRIPO3D_DEFAULT_MODEL_VERSION = "v3.1-20260211"

    def get_tripo3d_status(self):
        """Verify Tripo3D API connectivity and balance."""
        key = self._get_tripo3d_api_key()
        if not key:
            return {"enabled": False, "message": "No Tripo3D API key configured. "
                    "Get one at https://platform.tripo3d.ai/ and add to "
                    "Blender prefs or set BLENDERMCP_TRIPO3D_API_KEY."}
        try:
            r = _resilient_get(
                f"{self.TRIPO3D_BASE}/user/balance",
                headers={"Authorization": f"Bearer {key}"},
                timeout=15, max_retries=2,
            )
            data = r.json()
            if data.get("code") != 0:
                return {"enabled": False, "message": f"Tripo3D auth failed: {data}"}
            balance = data.get("data", {}).get("balance", "unknown")
            return {"enabled": True, "balance_credits": balance,
                    "message": f"Tripo3D ready. Balance: {balance} credits."}
        except Exception as e:
            return {"enabled": False, "message": f"Tripo3D unreachable: {e}"}

    def _tripo3d_create_task(self, body):
        """POST /task; return task_id."""
        key = self._get_tripo3d_api_key()
        if not key:
            return None, "No Tripo3D API key"
        try:
            r = requests.post(
                f"{self.TRIPO3D_BASE}/task",
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"},
                json=body, timeout=30,
            )
            data = r.json()
            if data.get("code") != 0:
                return None, f"Tripo3D create_task failed: {data}"
            return data["data"]["task_id"], None
        except Exception as e:
            return None, str(e)

    def _tripo3d_poll(self, task_id, max_wait_seconds=240, interval=2.5):
        """Poll GET /task/{id} until success/failed/timeout. Return final data."""
        key = self._get_tripo3d_api_key()
        url = f"{self.TRIPO3D_BASE}/task/{task_id}"
        deadline = time.time() + max_wait_seconds
        while time.time() < deadline:
            try:
                r = _resilient_get(url,
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=15, max_retries=2)
                data = r.json().get("data", {})
                status = data.get("status")
                if status in ("success", "failed", "cancelled", "banned", "expired"):
                    return data, None
            except Exception as e:
                # transient — keep polling
                pass
            time.sleep(interval)
        return None, f"Polling timed out after {max_wait_seconds}s"

    def generate_tripo3d_text_to_3d(self, prompt, model_version=None,
                                    texture=True, pbr=True,
                                    face_limit=30000, target_size=2.0,
                                    max_wait_seconds=240):
        """Synchronous text-to-3D via Tripo3D: kicks off task, polls until
        success, downloads the PBR GLB, imports into the scene at target_size.

        Returns the task_id, imported object names, and download URL.
        """
        body = {
            "type": "text_to_model",
            "prompt": prompt,
            "model_version": model_version or self.TRIPO3D_DEFAULT_MODEL_VERSION,
            "texture": bool(texture),
            "pbr": bool(pbr),
            "face_limit": int(face_limit),
        }
        task_id, err = self._tripo3d_create_task(body)
        if err:
            return {"error": err}
        data, err = self._tripo3d_poll(task_id, max_wait_seconds)
        if err:
            return {"error": err, "task_id": task_id}
        if data.get("status") != "success":
            return {"error": f"Generation {data.get('status')}: {data.get('error_msg')}",
                    "task_id": task_id, "task_data": data}

        output = data.get("output", {})
        glb_url = output.get("pbr_model") or output.get("model")
        if not glb_url:
            return {"error": "No GLB URL in Tripo3D response", "task_id": task_id}

        return self._import_glb_from_url(glb_url, target_size,
                                         service="tripo3d", task_id=task_id)

    def generate_tripo3d_image_to_3d(self, image_url, model_version=None,
                                     texture=True, pbr=True,
                                     target_size=2.0, max_wait_seconds=240):
        """Image-to-3D via public image URL (no upload required for this path).

        For local files, host them at a public URL first or use Hyper3D's
        image-upload path.
        """
        # Detect format from URL
        suffix = ".jpg"
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            if image_url.lower().endswith(ext):
                suffix = ext.lstrip(".") if ext != ".jpeg" else "jpg"
                break
        body = {
            "type": "image_to_model",
            "file": {"type": suffix.lstrip("."), "url": image_url},
            "model_version": model_version or self.TRIPO3D_DEFAULT_MODEL_VERSION,
            "texture": bool(texture),
            "pbr": bool(pbr),
        }
        task_id, err = self._tripo3d_create_task(body)
        if err:
            return {"error": err}
        data, err = self._tripo3d_poll(task_id, max_wait_seconds)
        if err:
            return {"error": err, "task_id": task_id}
        if data.get("status") != "success":
            return {"error": f"Generation {data.get('status')}: {data.get('error_msg')}",
                    "task_id": task_id, "task_data": data}
        output = data.get("output", {})
        glb_url = output.get("pbr_model") or output.get("model")
        if not glb_url:
            return {"error": "No GLB URL", "task_id": task_id}
        return self._import_glb_from_url(glb_url, target_size,
                                         service="tripo3d", task_id=task_id)

    # ---- Meshy.ai ---------------------------------------------------

    MESHY_BASE = "https://api.meshy.ai/openapi"

    def get_meshy_status(self):
        """Verify Meshy.ai API connectivity. Use the public test key
        msy_dummy_api_key_for_test_mode_12345678 to verify auth without
        spending credits."""
        key = self._get_meshy_api_key()
        if not key:
            return {"enabled": False, "message": "No Meshy.ai API key configured. "
                    "Get one at https://www.meshy.ai/settings/api and add to "
                    "Blender prefs or set BLENDERMCP_MESHY_API_KEY."}
        # Quick check: kick off a "list tasks" or use the dummy preview path
        # by hitting /v2/text-to-3d list endpoint
        try:
            r = requests.get(
                f"{self.MESHY_BASE}/v2/text-to-3d",
                headers={"Authorization": f"Bearer {key}"},
                params={"page_size": 1, "page_num": 1}, timeout=15,
            )
            if r.status_code == 401:
                return {"enabled": False, "message": "Meshy.ai auth failed (401)"}
            if r.status_code >= 500:
                return {"enabled": False, "message": f"Meshy.ai HTTP {r.status_code}"}
            return {"enabled": True, "message": "Meshy.ai reachable",
                    "test_mode": key.startswith("msy_dummy_")}
        except Exception as e:
            return {"enabled": False, "message": f"Meshy.ai unreachable: {e}"}

    def _meshy_create_text_task(self, body, mode="preview"):
        key = self._get_meshy_api_key()
        if not key:
            return None, "No Meshy.ai API key"
        try:
            r = requests.post(
                f"{self.MESHY_BASE}/v2/text-to-3d",
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"},
                json=body, timeout=30,
            )
            data = r.json()
            if r.status_code >= 400:
                return None, f"Meshy.ai HTTP {r.status_code}: {data}"
            return data.get("result"), None
        except Exception as e:
            return None, str(e)

    def _meshy_create_image_task(self, body):
        key = self._get_meshy_api_key()
        if not key:
            return None, "No Meshy.ai API key"
        try:
            r = requests.post(
                f"{self.MESHY_BASE}/v1/image-to-3d",
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"},
                json=body, timeout=30,
            )
            data = r.json()
            if r.status_code >= 400:
                return None, f"Meshy.ai HTTP {r.status_code}: {data}"
            return data.get("result"), None
        except Exception as e:
            return None, str(e)

    def _meshy_poll(self, task_id, mode, max_wait_seconds=300, interval=3.0):
        """mode: 'text-to-3d' or 'image-to-3d'."""
        key = self._get_meshy_api_key()
        url = f"{self.MESHY_BASE}/v2/text-to-3d/{task_id}" if mode == "text-to-3d" \
              else f"{self.MESHY_BASE}/v1/image-to-3d/{task_id}"
        deadline = time.time() + max_wait_seconds
        last_status = None
        while time.time() < deadline:
            try:
                r = _resilient_get(url,
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=15, max_retries=2)
                data = r.json()
                last_status = data.get("status")
                if last_status in ("SUCCEEDED", "FAILED", "CANCELED"):
                    return data, None
            except Exception:
                pass
            time.sleep(interval)
        return None, f"Polling timed out after {max_wait_seconds}s (last status: {last_status})"

    def generate_meshy_text_to_3d(self, prompt, ai_model="meshy-6",
                                  topology="quad", target_polycount=30000,
                                  enable_pbr=True, refine=True,
                                  target_size=2.0, max_wait_seconds=480):
        """Sync text-to-3D via Meshy.ai. Runs preview pass; if refine=True,
        chains a refine pass with PBR textures (more credits, better result).
        Imports the final GLB into the scene at target_size.
        """
        # Preview pass
        preview_body = {
            "mode": "preview",
            "prompt": prompt,
            "ai_model": ai_model,
            "topology": topology,
            "target_polycount": int(target_polycount),
            "target_formats": ["glb"],
        }
        preview_id, err = self._meshy_create_text_task(preview_body)
        if err:
            return {"error": err, "stage": "preview-create"}
        preview_data, err = self._meshy_poll(preview_id, "text-to-3d", max_wait_seconds // 2)
        if err:
            return {"error": err, "stage": "preview-poll", "task_id": preview_id}
        if preview_data.get("status") != "SUCCEEDED":
            return {"error": f"Preview {preview_data.get('status')}",
                    "stage": "preview-fail", "task_id": preview_id,
                    "task_data": preview_data}

        final_data = preview_data
        final_id = preview_id

        if refine:
            refine_body = {
                "mode": "refine",
                "preview_task_id": preview_id,
                "enable_pbr": bool(enable_pbr),
                "target_formats": ["glb"],
            }
            refine_id, err = self._meshy_create_text_task(refine_body)
            if err:
                return {"error": err, "stage": "refine-create",
                        "preview_task_id": preview_id}
            refine_data, err = self._meshy_poll(refine_id, "text-to-3d", max_wait_seconds // 2)
            if err:
                return {"error": err, "stage": "refine-poll", "task_id": refine_id}
            if refine_data.get("status") != "SUCCEEDED":
                return {"error": f"Refine {refine_data.get('status')}",
                        "stage": "refine-fail", "task_id": refine_id,
                        "task_data": refine_data}
            final_data = refine_data
            final_id = refine_id

        glb_url = (final_data.get("model_urls") or {}).get("glb")
        if not glb_url:
            return {"error": "No GLB URL in Meshy response",
                    "task_id": final_id, "task_data": final_data}

        result = self._import_glb_from_url(glb_url, target_size,
                                           service="meshy",
                                           task_id=final_id)
        result["preview_task_id"] = preview_id
        result["refined"] = bool(refine)
        return result

    def generate_meshy_image_to_3d(self, image_url, enable_pbr=True,
                                   topology="quad", target_polycount=30000,
                                   target_size=2.0, max_wait_seconds=300):
        """Sync image-to-3D via Meshy.ai. image_url must be a public URL OR
        a base64 data URI ('data:image/jpeg;base64,...').
        """
        body = {
            "image_url": image_url,
            "should_texture": True,
            "enable_pbr": bool(enable_pbr),
            "topology": topology,
            "target_polycount": int(target_polycount),
            "target_formats": ["glb"],
        }
        task_id, err = self._meshy_create_image_task(body)
        if err:
            return {"error": err, "stage": "create"}
        data, err = self._meshy_poll(task_id, "image-to-3d", max_wait_seconds)
        if err:
            return {"error": err, "stage": "poll", "task_id": task_id}
        if data.get("status") != "SUCCEEDED":
            return {"error": f"Image-to-3D {data.get('status')}",
                    "task_id": task_id, "task_data": data}
        glb_url = (data.get("model_urls") or {}).get("glb")
        if not glb_url:
            return {"error": "No GLB URL", "task_id": task_id}
        return self._import_glb_from_url(glb_url, target_size,
                                         service="meshy", task_id=task_id)

    # ---- Shared GLB import helper -----------------------------------

    def _import_glb_from_url(self, glb_url, target_size, service, task_id):
        """Download a GLB to a temp file (resilient), import, optionally
        rescale so largest dim equals target_size. Returns import metadata.
        """
        suffix = ".glb"
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix=f"{service}_{task_id[:8]}_")
        os.close(tmp_fd)
        try:
            _resilient_download_to_file(glb_url, tmp_path, max_retries=4)
        except Exception as e:
            with suppress(Exception):
                os.unlink(tmp_path)
            return {"error": f"Download failed: {e}", "task_id": task_id,
                    "service": service, "glb_url": glb_url}

        # Snapshot existing object names so we can identify newly imported
        before = set(o.name for o in bpy.data.objects)
        try:
            bpy.ops.import_scene.gltf(filepath=tmp_path)
        except Exception as e:
            return {"error": f"GLB import failed: {e}", "task_id": task_id,
                    "service": service, "downloaded_to": tmp_path}
        new_names = [o.name for o in bpy.data.objects if o.name not in before]

        # Find the imported root — first new object that has no parent OR is named Sketchfab_model-style
        new_objs = [bpy.data.objects[n] for n in new_names]
        roots = [o for o in new_objs if o.parent is None or o.parent.name not in new_names]
        # Resize to target_size if requested
        scale_factor = None
        if target_size and roots:
            # Compute bbox of all newly imported meshes
            mins = [float("inf")] * 3
            maxs = [-float("inf")] * 3
            for o in new_objs:
                if o.type != 'MESH' or o.data is None:
                    continue
                for v in o.bound_box:
                    w = o.matrix_world @ mathutils.Vector(v)
                    for i in range(3):
                        mins[i] = min(mins[i], w[i])
                        maxs[i] = max(maxs[i], w[i])
            size = [maxs[i] - mins[i] for i in range(3)]
            largest = max(size) if size and max(size) > 0 else 0
            if largest > 0:
                scale_factor = float(target_size) / largest
                for r in roots:
                    r.scale = (r.scale[0] * scale_factor,
                               r.scale[1] * scale_factor,
                               r.scale[2] * scale_factor)

        return {
            "service": service,
            "task_id": task_id,
            "glb_url": glb_url,
            "imported_objects": new_names,
            "imported_roots": [r.name for r in roots],
            "scale_factor_applied": scale_factor,
            "target_size": float(target_size) if target_size else None,
            "downloaded_to": tmp_path,
        }

    def execute_code(self, code):
        """Execute arbitrary Blender Python code"""
        # This is powerful but potentially dangerous - use with caution
        try:
            # Create a local namespace for execution
            namespace = {"bpy": bpy}

            # Capture stdout during execution, and return it as result
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)

            captured_output = capture_buffer.getvalue()
            return {"executed": True, "result": captured_output}
        except Exception as e:
            raise Exception(f"Code execution error: {str(e)}")



    def get_polyhaven_categories(self, asset_type):
        """Get categories for a specific asset type from Polyhaven"""
        try:
            if asset_type not in ["hdris", "textures", "models", "all"]:
                return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}

            response = requests.get(f"https://api.polyhaven.com/categories/{asset_type}", headers=REQ_HEADERS)
            if response.status_code == 200:
                return {"categories": response.json()}
            else:
                return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def search_polyhaven_assets(self, asset_type=None, categories=None):
        """Search for assets from Polyhaven with optional filtering"""
        try:
            url = "https://api.polyhaven.com/assets"
            params = {}

            if asset_type and asset_type != "all":
                if asset_type not in ["hdris", "textures", "models"]:
                    return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}
                params["type"] = asset_type

            if categories:
                params["categories"] = categories

            response = requests.get(url, params=params, headers=REQ_HEADERS)
            if response.status_code == 200:
                # Limit the response size to avoid overwhelming Blender
                assets = response.json()
                # Return only the first 20 assets to keep response size manageable
                limited_assets = {}
                for i, (key, value) in enumerate(assets.items()):
                    if i >= 20:  # Limit to 20 assets
                        break
                    limited_assets[key] = value

                return {"assets": limited_assets, "total_count": len(assets), "returned_count": len(limited_assets)}
            else:
                return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def download_polyhaven_asset(self, asset_id, asset_type, resolution="1k", file_format=None):
        try:
            # First get the files information
            files_response = requests.get(f"https://api.polyhaven.com/files/{asset_id}", headers=REQ_HEADERS)
            if files_response.status_code != 200:
                return {"error": f"Failed to get asset files: {files_response.status_code}"}

            files_data = files_response.json()

            # Handle different asset types
            if asset_type == "hdris":
                # For HDRIs, download the .hdr or .exr file
                if not file_format:
                    file_format = "hdr"  # Default format for HDRIs

                if "hdri" in files_data and resolution in files_data["hdri"] and file_format in files_data["hdri"][resolution]:
                    file_info = files_data["hdri"][resolution][file_format]
                    file_url = file_info["url"]

                    # For HDRIs, we need to save to a temporary file first
                    # since Blender can't properly load HDR data directly from memory
                    tmp_fd, tmp_path = tempfile.mkstemp(suffix=f".{file_format}")
                    os.close(tmp_fd)
                    try:
                        _resilient_download_to_file(file_url, tmp_path)
                    except Exception as e:
                        return {"error": f"Failed to download HDRI after retries: {e}"}

                    try:
                        # Create a new world if none exists
                        if not bpy.data.worlds:
                            bpy.data.worlds.new("World")

                        world = bpy.data.worlds[0]
                        world.use_nodes = True
                        node_tree = world.node_tree

                        # Clear existing nodes
                        for node in node_tree.nodes:
                            node_tree.nodes.remove(node)

                        # Create nodes
                        tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
                        tex_coord.location = (-800, 0)

                        mapping = node_tree.nodes.new(type='ShaderNodeMapping')
                        mapping.location = (-600, 0)

                        # Load the image from the temporary file
                        env_tex = node_tree.nodes.new(type='ShaderNodeTexEnvironment')
                        env_tex.location = (-400, 0)
                        env_tex.image = bpy.data.images.load(tmp_path)

                        # Use a color space that exists in all Blender versions
                        if file_format.lower() == 'exr':
                            # Try to use Linear color space for EXR files
                            try:
                                env_tex.image.colorspace_settings.name = 'Linear'
                            except:
                                # Fallback to Non-Color if Linear isn't available
                                env_tex.image.colorspace_settings.name = 'Non-Color'
                        else:  # hdr
                            # For HDR files, try these options in order
                            for color_space in ['Linear', 'Linear Rec.709', 'Non-Color']:
                                try:
                                    env_tex.image.colorspace_settings.name = color_space
                                    break  # Stop if we successfully set a color space
                                except:
                                    continue

                        background = node_tree.nodes.new(type='ShaderNodeBackground')
                        background.location = (-200, 0)

                        output = node_tree.nodes.new(type='ShaderNodeOutputWorld')
                        output.location = (0, 0)

                        # Connect nodes
                        node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
                        node_tree.links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
                        node_tree.links.new(env_tex.outputs['Color'], background.inputs['Color'])
                        node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])

                        # Set as active world
                        bpy.context.scene.world = world

                        # Clean up temporary file
                        try:
                            tempfile._cleanup()  # This will clean up all temporary files
                        except:
                            pass

                        return {
                            "success": True,
                            "message": f"HDRI {asset_id} imported successfully",
                            "image_name": env_tex.image.name
                        }
                    except Exception as e:
                        return {"error": f"Failed to set up HDRI in Blender: {str(e)}"}
                else:
                    return {"error": f"Requested resolution or format not available for this HDRI"}

            elif asset_type == "textures":
                if not file_format:
                    file_format = "jpg"  # Default format for textures

                downloaded_maps = {}

                try:
                    for map_type in files_data:
                        if map_type not in ["blend", "gltf"]:  # Skip non-texture files
                            if resolution in files_data[map_type] and file_format in files_data[map_type][resolution]:
                                file_info = files_data[map_type][resolution][file_format]
                                file_url = file_info["url"]

                                # Use NamedTemporaryFile like we do for HDRIs
                                tmp_fd, tmp_path = tempfile.mkstemp(suffix=f".{file_format}")
                                os.close(tmp_fd)
                                try:
                                    _resilient_download_to_file(file_url, tmp_path)
                                    download_ok = True
                                except Exception as e:
                                    print(f"[blender-mcp] Texture {map_type} download failed: {e}")
                                    download_ok = False
                                if download_ok:
                                    if True:

                                        # Load image from temporary file
                                        image = bpy.data.images.load(tmp_path)
                                        image.name = f"{asset_id}_{map_type}.{file_format}"

                                        # Pack the image into .blend file
                                        image.pack()

                                        # Set color space based on map type
                                        if map_type in ['color', 'diffuse', 'albedo']:
                                            try:
                                                image.colorspace_settings.name = 'sRGB'
                                            except:
                                                pass
                                        else:
                                            try:
                                                image.colorspace_settings.name = 'Non-Color'
                                            except:
                                                pass

                                        downloaded_maps[map_type] = image

                                        # Clean up temporary file
                                        try:
                                            os.unlink(tmp_path)
                                        except:
                                            pass

                    if not downloaded_maps:
                        return {"error": f"No texture maps found for the requested resolution and format"}

                    # Create a new material with the downloaded textures
                    mat = bpy.data.materials.new(name=asset_id)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links

                    # Clear default nodes
                    for node in nodes:
                        nodes.remove(node)

                    # Create output node
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    output.location = (300, 0)

                    # Create principled BSDF node
                    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
                    principled.location = (0, 0)
                    links.new(principled.outputs[0], output.inputs[0])

                    # Add texture nodes based on available maps
                    tex_coord = nodes.new(type='ShaderNodeTexCoord')
                    tex_coord.location = (-800, 0)

                    mapping = nodes.new(type='ShaderNodeMapping')
                    mapping.location = (-600, 0)
                    mapping.vector_type = 'TEXTURE'  # Changed from default 'POINT' to 'TEXTURE'
                    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

                    # Position offset for texture nodes
                    x_pos = -400
                    y_pos = 300

                    # Connect different texture maps
                    for map_type, image in downloaded_maps.items():
                        tex_node = nodes.new(type='ShaderNodeTexImage')
                        tex_node.location = (x_pos, y_pos)
                        tex_node.image = image

                        # Set color space based on map type
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            try:
                                tex_node.image.colorspace_settings.name = 'sRGB'
                            except:
                                pass  # Use default if sRGB not available
                        else:
                            try:
                                tex_node.image.colorspace_settings.name = 'Non-Color'
                            except:
                                pass  # Use default if Non-Color not available

                        links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])

                        # Connect to appropriate input on Principled BSDF
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                        elif map_type.lower() in ['roughness', 'rough']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                        elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                        elif map_type.lower() in ['normal', 'nor']:
                            # Add normal map node
                            normal_map = nodes.new(type='ShaderNodeNormalMap')
                            normal_map.location = (x_pos + 200, y_pos)
                            links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                            links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                        elif map_type in ['displacement', 'disp', 'height']:
                            # Add displacement node
                            disp_node = nodes.new(type='ShaderNodeDisplacement')
                            disp_node.location = (x_pos + 200, y_pos - 200)
                            links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                            links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])

                        y_pos -= 250

                    return {
                        "success": True,
                        "message": f"Texture {asset_id} imported as material",
                        "material": mat.name,
                        "maps": list(downloaded_maps.keys())
                    }

                except Exception as e:
                    return {"error": f"Failed to process textures: {str(e)}"}

            elif asset_type == "models":
                # For models, prefer glTF format if available
                if not file_format:
                    file_format = "gltf"  # Default format for models

                if file_format in files_data and resolution in files_data[file_format]:
                    file_info = files_data[file_format][resolution][file_format]
                    file_url = file_info["url"]

                    # Create a temporary directory to store the model and its dependencies
                    temp_dir = tempfile.mkdtemp()
                    main_file_path = ""

                    try:
                        # Download the main model file
                        main_file_name = file_url.split("/")[-1]
                        main_file_path = os.path.join(temp_dir, main_file_name)

                        try:
                            _resilient_download_to_file(file_url, main_file_path)
                        except Exception as e:
                            return {"error": f"Failed to download model after retries: {e}"}

                        # Check for included files and download them
                        if "include" in file_info and file_info["include"]:
                            for include_path, include_info in file_info["include"].items():
                                # Get the URL for the included file - this is the fix
                                include_url = include_info["url"]

                                # Create the directory structure for the included file
                                include_file_path = os.path.join(temp_dir, include_path)
                                os.makedirs(os.path.dirname(include_file_path), exist_ok=True)

                                # Download the included file (best-effort with retry)
                                try:
                                    _resilient_download_to_file(include_url, include_file_path)
                                except Exception as e:
                                    print(f"Failed to download included file {include_path}: {e}")

                        # Import the model into Blender
                        if file_format == "gltf" or file_format == "glb":
                            bpy.ops.import_scene.gltf(filepath=main_file_path)
                        elif file_format == "fbx":
                            bpy.ops.import_scene.fbx(filepath=main_file_path)
                        elif file_format == "obj":
                            bpy.ops.import_scene.obj(filepath=main_file_path)
                        elif file_format == "blend":
                            # For blend files, we need to append or link
                            with bpy.data.libraries.load(main_file_path, link=False) as (data_from, data_to):
                                data_to.objects = data_from.objects

                            # Link the objects to the scene
                            for obj in data_to.objects:
                                if obj is not None:
                                    bpy.context.collection.objects.link(obj)
                        else:
                            return {"error": f"Unsupported model format: {file_format}"}

                        # Get the names of imported objects
                        imported_objects = [obj.name for obj in bpy.context.selected_objects]

                        return {
                            "success": True,
                            "message": f"Model {asset_id} imported successfully",
                            "imported_objects": imported_objects
                        }
                    except Exception as e:
                        return {"error": f"Failed to import model: {str(e)}"}
                    finally:
                        # Clean up temporary directory
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                else:
                    return {"error": f"Requested format or resolution not available for this model"}

            else:
                return {"error": f"Unsupported asset type: {asset_type}"}

        except Exception as e:
            return {"error": f"Failed to download asset: {str(e)}"}

    def set_texture(self, object_name, texture_id):
        """Apply a previously downloaded Polyhaven texture to an object by creating a new material"""
        try:
            # Get the object
            obj = bpy.data.objects.get(object_name)
            if not obj:
                return {"error": f"Object not found: {object_name}"}

            # Make sure object can accept materials
            if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
                return {"error": f"Object {object_name} cannot accept materials"}

            # Find all images related to this texture and ensure they're properly loaded
            texture_images = {}
            for img in bpy.data.images:
                if img.name.startswith(texture_id + "_"):
                    # Extract the map type from the image name
                    map_type = img.name.split('_')[-1].split('.')[0]

                    # Force a reload of the image
                    img.reload()

                    # Ensure proper color space
                    if map_type.lower() in ['color', 'diffuse', 'albedo']:
                        try:
                            img.colorspace_settings.name = 'sRGB'
                        except:
                            pass
                    else:
                        try:
                            img.colorspace_settings.name = 'Non-Color'
                        except:
                            pass

                    # Ensure the image is packed
                    if not img.packed_file:
                        img.pack()

                    texture_images[map_type] = img
                    print(f"Loaded texture map: {map_type} - {img.name}")

                    # Debug info
                    print(f"Image size: {img.size[0]}x{img.size[1]}")
                    print(f"Color space: {img.colorspace_settings.name}")
                    print(f"File format: {img.file_format}")
                    print(f"Is packed: {bool(img.packed_file)}")

            if not texture_images:
                return {"error": f"No texture images found for: {texture_id}. Please download the texture first."}

            # Create a new material
            new_mat_name = f"{texture_id}_material_{object_name}"

            # Remove any existing material with this name to avoid conflicts
            existing_mat = bpy.data.materials.get(new_mat_name)
            if existing_mat:
                bpy.data.materials.remove(existing_mat)

            new_mat = bpy.data.materials.new(name=new_mat_name)
            new_mat.use_nodes = True

            # Set up the material nodes
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links

            # Clear default nodes
            nodes.clear()

            # Create output node
            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (600, 0)

            # Create principled BSDF node
            principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            principled.location = (300, 0)
            links.new(principled.outputs[0], output.inputs[0])

            # Add texture nodes based on available maps
            tex_coord = nodes.new(type='ShaderNodeTexCoord')
            tex_coord.location = (-800, 0)

            mapping = nodes.new(type='ShaderNodeMapping')
            mapping.location = (-600, 0)
            mapping.vector_type = 'TEXTURE'  # Changed from default 'POINT' to 'TEXTURE'
            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

            # Position offset for texture nodes
            x_pos = -400
            y_pos = 300

            # Connect different texture maps
            for map_type, image in texture_images.items():
                tex_node = nodes.new(type='ShaderNodeTexImage')
                tex_node.location = (x_pos, y_pos)
                tex_node.image = image

                # Set color space based on map type
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    try:
                        tex_node.image.colorspace_settings.name = 'sRGB'
                    except:
                        pass  # Use default if sRGB not available
                else:
                    try:
                        tex_node.image.colorspace_settings.name = 'Non-Color'
                    except:
                        pass  # Use default if Non-Color not available

                links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])

                # Connect to appropriate input on Principled BSDF
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                elif map_type.lower() in ['roughness', 'rough']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                elif map_type.lower() in ['normal', 'nor', 'dx', 'gl']:
                    # Add normal map node
                    normal_map = nodes.new(type='ShaderNodeNormalMap')
                    normal_map.location = (x_pos + 200, y_pos)
                    links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                elif map_type.lower() in ['displacement', 'disp', 'height']:
                    # Add displacement node
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (x_pos + 200, y_pos - 200)
                    disp_node.inputs['Scale'].default_value = 0.1  # Reduce displacement strength
                    links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])

                y_pos -= 250

            # Second pass: Connect nodes with proper handling for special cases
            texture_nodes = {}

            # First find all texture nodes and store them by map type
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    for map_type, image in texture_images.items():
                        if node.image == image:
                            texture_nodes[map_type] = node
                            break

            # Now connect everything using the nodes instead of images
            # Handle base color (diffuse)
            for map_name in ['color', 'diffuse', 'albedo']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Base Color'])
                    print(f"Connected {map_name} to Base Color")
                    break

            # Handle roughness
            for map_name in ['roughness', 'rough']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Roughness'])
                    print(f"Connected {map_name} to Roughness")
                    break

            # Handle metallic
            for map_name in ['metallic', 'metalness', 'metal']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Metallic'])
                    print(f"Connected {map_name} to Metallic")
                    break

            # Handle normal maps
            for map_name in ['gl', 'dx', 'nor']:
                if map_name in texture_nodes:
                    normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                    normal_map_node.location = (100, 100)
                    links.new(texture_nodes[map_name].outputs['Color'], normal_map_node.inputs['Color'])
                    links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                    print(f"Connected {map_name} to Normal")
                    break

            # Handle displacement
            for map_name in ['displacement', 'disp', 'height']:
                if map_name in texture_nodes:
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (300, -200)
                    disp_node.inputs['Scale'].default_value = 0.1  # Reduce displacement strength
                    links.new(texture_nodes[map_name].outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                    print(f"Connected {map_name} to Displacement")
                    break

            # Handle ARM texture (Ambient Occlusion, Roughness, Metallic)
            if 'arm' in texture_nodes:
                # Blender 4.0+ removed ShaderNodeSeparateRGB. Use ShaderNodeSeparateColor
                # (mode='RGB'); outputs are now Red/Green/Blue, input is Color.
                separate_rgb = nodes.new(type='ShaderNodeSeparateColor')
                separate_rgb.mode = 'RGB'
                separate_rgb.location = (-200, -100)
                links.new(texture_nodes['arm'].outputs['Color'], separate_rgb.inputs['Color'])

                # Connect Roughness (G) if no dedicated roughness map
                if not any(map_name in texture_nodes for map_name in ['roughness', 'rough']):
                    links.new(separate_rgb.outputs['Green'], principled.inputs['Roughness'])
                    print("Connected ARM.G to Roughness")

                # Connect Metallic (B) if no dedicated metallic map
                if not any(map_name in texture_nodes for map_name in ['metallic', 'metalness', 'metal']):
                    links.new(separate_rgb.outputs['Blue'], principled.inputs['Metallic'])
                    print("Connected ARM.B to Metallic")

                # For AO (R channel), multiply with base color if we have one
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(separate_rgb.outputs['Red'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    print("Connected ARM.R to AO mix with Base Color")

            # Handle AO (Ambient Occlusion) if separate
            if 'ao' in texture_nodes:
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(texture_nodes['ao'].outputs['Color'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    print("Connected AO to mix with Base Color")

            # CRITICAL: Make sure to clear all existing materials from the object
            while len(obj.data.materials) > 0:
                obj.data.materials.pop(index=0)

            # Assign the new material to the object
            obj.data.materials.append(new_mat)

            # CRITICAL: Make the object active and select it
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            # CRITICAL: Force Blender to update the material
            bpy.context.view_layer.update()

            # Get the list of texture maps
            texture_maps = list(texture_images.keys())

            # Get info about texture nodes for debugging
            material_info = {
                "name": new_mat.name,
                "has_nodes": new_mat.use_nodes,
                "node_count": len(new_mat.node_tree.nodes),
                "texture_nodes": []
            }

            for node in new_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    connections = []
                    for output in node.outputs:
                        for link in output.links:
                            connections.append(f"{output.name} → {link.to_node.name}.{link.to_socket.name}")

                    material_info["texture_nodes"].append({
                        "name": node.name,
                        "image": node.image.name,
                        "colorspace": node.image.colorspace_settings.name,
                        "connections": connections
                    })

            return {
                "success": True,
                "message": f"Created new material and applied texture {texture_id} to {object_name}",
                "material": new_mat.name,
                "maps": texture_maps,
                "material_info": material_info
            }

        except Exception as e:
            print(f"Error in set_texture: {str(e)}")
            traceback.print_exc()
            return {"error": f"Failed to apply texture: {str(e)}"}

    def get_telemetry_consent(self):
        """Get the current telemetry consent status"""
        try:
            # Get addon preferences - use the module name
            addon_prefs = bpy.context.preferences.addons.get(__name__)
            if addon_prefs:
                consent = addon_prefs.preferences.telemetry_consent
            else:
                # Fallback to default if preferences not available
                consent = True
        except (AttributeError, KeyError):
            # Fallback to default if preferences not available
            consent = True
        return {"consent": consent}

    def get_polyhaven_status(self):
        """Get the current status of PolyHaven integration"""
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        if enabled:
            return {"enabled": True, "message": "PolyHaven integration is enabled and ready to use."}
        else:
            return {
                "enabled": False,
                "message": """PolyHaven integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Poly Haven' checkbox
                            3. Restart the connection to Claude"""
        }

    #region Hyper3D
    def get_hyper3d_status(self):
        """Get the current status of Hyper3D Rodin integration"""
        enabled = bpy.context.scene.blendermcp_use_hyper3d
        hyper3d_api_key = self._get_hyper3d_api_key()
        if enabled:
            if not hyper3d_api_key:
                return {
                    "enabled": False,
                    "message": """Hyper3D Rodin integration is currently enabled, but API key is not given. To enable it:
                                1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                                2. Keep the 'Use Hyper3D Rodin 3D model generation' checkbox checked
                                3. Choose the right plaform and fill in the API Key
                                4. Restart the connection to Claude"""
                }
            mode = bpy.context.scene.blendermcp_hyper3d_mode
            message = f"Hyper3D Rodin integration is enabled and ready to use. Mode: {mode}. " + \
                f"Key type: {'private' if hyper3d_api_key != RODIN_FREE_TRIAL_KEY else 'free_trial'}"
            return {
                "enabled": True,
                "message": message
            }
        else:
            return {
                "enabled": False,
                "message": """Hyper3D Rodin integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use Hyper3D Rodin 3D model generation' checkbox
                            3. Restart the connection to Claude"""
            }

    def create_rodin_job(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.create_rodin_job_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.create_rodin_job_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def create_rodin_job_main_site(
            self,
            text_prompt: str=None,
            images: list[tuple[str, str]]=None,
            bbox_condition=None
        ):
        try:
            api_key = self._get_hyper3d_api_key()
            if not api_key:
                return {"error": "Hyper3D API key is not given"}
            if images is None:
                images = []
            """Call Rodin API, get the job uuid and subscription key"""
            files = [
                *[("images", (f"{i:04d}{img_suffix}", base64.b64decode(img))) for i, (img_suffix, img) in enumerate(images)],
                ("tier", (None, "Sketch")),
                ("mesh_mode", (None, "Raw")),
            ]
            if text_prompt:
                files.append(("prompt", (None, text_prompt)))
            if bbox_condition:
                files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
            response = requests.post(
                "https://hyperhuman.deemos.com/api/v2/rodin",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                files=files
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def create_rodin_job_fal_ai(
            self,
            text_prompt: str=None,
            images: list[tuple[str, str]]=None,
            bbox_condition=None
        ):
        try:
            api_key = self._get_hyper3d_api_key()
            if not api_key:
                return {"error": "Hyper3D API key is not given"}
            req_data = {
                "tier": "Sketch",
            }
            if images:
                req_data["input_image_urls"] = images
            if text_prompt:
                req_data["prompt"] = text_prompt
            if bbox_condition:
                req_data["bbox_condition"] = bbox_condition
            response = requests.post(
                "https://queue.fal.run/fal-ai/hyper3d/rodin",
                headers={
                    "Authorization": f"Key {api_key}",
                    "Content-Type": "application/json",
                },
                json=req_data
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def poll_rodin_job_status(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.poll_rodin_job_status_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.poll_rodin_job_status_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def poll_rodin_job_status_main_site(self, subscription_key: str):
        """Call the job status API to get the job status"""
        api_key = self._get_hyper3d_api_key()
        if not api_key:
            return {"error": "Hyper3D API key is not given"}
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/status",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "subscription_key": subscription_key,
            },
        )
        data = response.json()
        return {
            "status_list": [i["status"] for i in data["jobs"]]
        }

    def poll_rodin_job_status_fal_ai(self, request_id: str):
        """Call the job status API to get the job status"""
        api_key = self._get_hyper3d_api_key()
        if not api_key:
            return {"error": "Hyper3D API key is not given"}
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}/status",
            headers={
                "Authorization": f"KEY {api_key}",
            },
        )
        data = response.json()
        return data

    @staticmethod
    def _clean_imported_glb(filepath, mesh_name=None):
        # Get the set of existing objects before import
        existing_objects = set(bpy.data.objects)

        # Import the GLB file
        bpy.ops.import_scene.gltf(filepath=filepath)

        # Ensure the context is updated
        bpy.context.view_layer.update()

        # Get all imported objects
        imported_objects = list(set(bpy.data.objects) - existing_objects)
        # imported_objects = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]

        if not imported_objects:
            print("Error: No objects were imported.")
            return

        # Identify the mesh object
        mesh_obj = None

        if len(imported_objects) == 1 and imported_objects[0].type == 'MESH':
            mesh_obj = imported_objects[0]
            print("Single mesh imported, no cleanup needed.")
        else:
            if len(imported_objects) == 2:
                empty_objs = [i for i in imported_objects if i.type == "EMPTY"]
                if len(empty_objs) != 1:
                    print("Error: Expected an empty node with one mesh child or a single mesh object.")
                    return
                parent_obj = empty_objs.pop()
                if len(parent_obj.children) == 1:
                    potential_mesh = parent_obj.children[0]
                    if potential_mesh.type == 'MESH':
                        print("GLB structure confirmed: Empty node with one mesh child.")

                        # Unparent the mesh from the empty node
                        potential_mesh.parent = None

                        # Remove the empty node
                        bpy.data.objects.remove(parent_obj)
                        print("Removed empty node, keeping only the mesh.")

                        mesh_obj = potential_mesh
                    else:
                        print("Error: Child is not a mesh object.")
                        return
                else:
                    print("Error: Expected an empty node with one mesh child or a single mesh object.")
                    return
            else:
                print("Error: Expected an empty node with one mesh child or a single mesh object.")
                return

        # Rename the mesh if needed
        try:
            if mesh_obj and mesh_obj.name is not None and mesh_name:
                mesh_obj.name = mesh_name
                if mesh_obj.data.name is not None:
                    mesh_obj.data.name = mesh_name
                print(f"Mesh renamed to: {mesh_name}")
        except Exception as e:
            print("Having issue with renaming, give up renaming.")

        return mesh_obj

    def import_generated_asset(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.import_generated_asset_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.import_generated_asset_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def import_generated_asset_main_site(self, task_uuid: str, name: str):
        """Fetch the generated asset, import into blender"""
        api_key = self._get_hyper3d_api_key()
        if not api_key:
            return {"succeed": False, "error": "Hyper3D API key is not given"}
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/download",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            json={
                'task_uuid': task_uuid
            }
        )
        data_ = response.json()
        temp_file = None
        for i in data_["list"]:
            if i["name"].endswith(".glb"):
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    prefix=task_uuid,
                    suffix=".glb",
                )

                temp_file.close()
                try:
                    _resilient_download_to_file(i["url"], temp_file.name)
                except Exception as e:
                    with suppress(Exception):
                        os.unlink(temp_file.name)
                    return {"succeed": False, "error": str(e)}

                break
        else:
            return {"succeed": False, "error": "Generation failed. Please first make sure that all jobs of the task are done and then try again later."}

        try:
            obj = self._clean_imported_glb(
                filepath=temp_file.name,
                mesh_name=name
            )
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {
                "succeed": True, **result
            }
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    def import_generated_asset_fal_ai(self, request_id: str, name: str):
        """Fetch the generated asset, import into blender"""
        api_key = self._get_hyper3d_api_key()
        if not api_key:
            return {"succeed": False, "error": "Hyper3D API key is not given"}
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
            headers={
                "Authorization": f"Key {api_key}",
            }
        )
        data_ = response.json()
        temp_file = None

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            prefix=request_id,
            suffix=".glb",
        )

        try:
            # Download the content
            response = requests.get(data_["model_mesh"]["url"], stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Write the content to the temporary file
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)

            # Close the file
            temp_file.close()

        except Exception as e:
            # Clean up the file if there's an error
            temp_file.close()
            os.unlink(temp_file.name)
            return {"succeed": False, "error": str(e)}

        try:
            obj = self._clean_imported_glb(
                filepath=temp_file.name,
                mesh_name=name
            )
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {
                "succeed": True, **result
            }
        except Exception as e:
            return {"succeed": False, "error": str(e)}
    #endregion
 
    #region Sketchfab API
    def get_sketchfab_status(self):
        """Get the current status of Sketchfab integration"""
        enabled = bpy.context.scene.blendermcp_use_sketchfab
        api_key = self._get_sketchfab_api_key()

        # Test the API key if present
        if api_key:
            try:
                headers = {
                    "Authorization": f"Token {api_key}"
                }

                response = requests.get(
                    "https://api.sketchfab.com/v3/me",
                    headers=headers,
                    timeout=30  # Add timeout of 30 seconds
                )

                if response.status_code == 200:
                    user_data = response.json()
                    username = user_data.get("username", "Unknown user")
                    return {
                        "enabled": True,
                        "message": f"Sketchfab integration is enabled and ready to use. Logged in as: {username}"
                    }
                else:
                    return {
                        "enabled": False,
                        "message": f"Sketchfab API key seems invalid. Status code: {response.status_code}"
                    }
            except requests.exceptions.Timeout:
                return {
                    "enabled": False,
                    "message": "Timeout connecting to Sketchfab API. Check your internet connection."
                }
            except Exception as e:
                return {
                    "enabled": False,
                    "message": f"Error testing Sketchfab API key: {str(e)}"
                }

        if enabled and api_key:
            return {"enabled": True, "message": "Sketchfab integration is enabled and ready to use."}
        elif enabled and not api_key:
            return {
                "enabled": False,
                "message": """Sketchfab integration is currently enabled, but API key is not given. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Keep the 'Use Sketchfab' checkbox checked
                            3. Enter your Sketchfab API Key
                            4. Restart the connection to Claude"""
            }
        else:
            return {
                "enabled": False,
                "message": """Sketchfab integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Sketchfab' checkbox
                            3. Enter your Sketchfab API Key
                            4. Restart the connection to Claude"""
            }

    def search_sketchfab_models(self, query, categories=None, count=20, downloadable=True):
        """Search for models on Sketchfab based on query and optional filters"""
        try:
            api_key = self._get_sketchfab_api_key()
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}

            # Build search parameters with exact fields from Sketchfab API docs
            params = {
                "type": "models",
                "q": query,
                "count": count,
                "downloadable": downloadable,
                "archives_flavours": False
            }

            if categories:
                params["categories"] = categories

            # Make API request to Sketchfab search endpoint
            # The proper format according to Sketchfab API docs for API key auth
            headers = {
                "Authorization": f"Token {api_key}"
            }


            # Use the search endpoint as specified in the API documentation
            response = requests.get(
                "https://api.sketchfab.com/v3/search",
                headers=headers,
                params=params,
                timeout=30  # Add timeout of 30 seconds
            )

            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}

            if response.status_code != 200:
                return {"error": f"API request failed with status code {response.status_code}"}

            response_data = response.json()

            # Safety check on the response structure
            if response_data is None:
                return {"error": "Received empty response from Sketchfab API"}

            # Handle 'results' potentially missing from response
            results = response_data.get("results", [])
            if not isinstance(results, list):
                return {"error": f"Unexpected response format from Sketchfab API: {response_data}"}

            return response_data

        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection."}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def get_sketchfab_model_preview(self, uid):
        """Get thumbnail preview image of a Sketchfab model by its UID"""
        try:
            import base64
            
            api_key = self._get_sketchfab_api_key()
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}

            headers = {"Authorization": f"Token {api_key}"}
            
            # Get model info which includes thumbnails
            response = requests.get(
                f"https://api.sketchfab.com/v3/models/{uid}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}
            
            if response.status_code == 404:
                return {"error": f"Model not found: {uid}"}
            
            if response.status_code != 200:
                return {"error": f"Failed to get model info: {response.status_code}"}
            
            data = response.json()
            thumbnails = data.get("thumbnails", {}).get("images", [])
            
            if not thumbnails:
                return {"error": "No thumbnail available for this model"}
            
            # Find a suitable thumbnail (prefer medium size ~640px)
            selected_thumbnail = None
            for thumb in thumbnails:
                width = thumb.get("width", 0)
                if 400 <= width <= 800:
                    selected_thumbnail = thumb
                    break
            
            # Fallback to the first available thumbnail
            if not selected_thumbnail:
                selected_thumbnail = thumbnails[0]
            
            thumbnail_url = selected_thumbnail.get("url")
            if not thumbnail_url:
                return {"error": "Thumbnail URL not found"}
            
            # Download the thumbnail image
            img_response = requests.get(thumbnail_url, timeout=30)
            if img_response.status_code != 200:
                return {"error": f"Failed to download thumbnail: {img_response.status_code}"}
            
            # Encode image as base64
            image_data = base64.b64encode(img_response.content).decode('ascii')
            
            # Determine format from content type or URL
            content_type = img_response.headers.get("Content-Type", "")
            if "png" in content_type or thumbnail_url.endswith(".png"):
                img_format = "png"
            else:
                img_format = "jpeg"
            
            # Get additional model info for context
            model_name = data.get("name", "Unknown")
            author = data.get("user", {}).get("username", "Unknown")
            
            return {
                "success": True,
                "image_data": image_data,
                "format": img_format,
                "model_name": model_name,
                "author": author,
                "uid": uid,
                "thumbnail_width": selected_thumbnail.get("width"),
                "thumbnail_height": selected_thumbnail.get("height")
            }
            
        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection."}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Failed to get model preview: {str(e)}"}

    def download_sketchfab_model(self, uid, normalize_size=False, target_size=1.0):
        """Download a model from Sketchfab by its UID
        
        Parameters:
        - uid: The unique identifier of the Sketchfab model
        - normalize_size: If True, scale the model so its largest dimension equals target_size
        - target_size: The target size in Blender units (meters) for the largest dimension
        """
        try:
            api_key = self._get_sketchfab_api_key()
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}

            # Use proper authorization header for API key auth
            headers = {
                "Authorization": f"Token {api_key}"
            }

            # Request download URL using the exact endpoint from the documentation
            download_endpoint = f"https://api.sketchfab.com/v3/models/{uid}/download"

            response = requests.get(
                download_endpoint,
                headers=headers,
                timeout=30  # Add timeout of 30 seconds
            )

            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}

            if response.status_code != 200:
                return {"error": f"Download request failed with status code {response.status_code}"}

            data = response.json()

            # Safety check for None data
            if data is None:
                return {"error": "Received empty response from Sketchfab API for download request"}

            # Extract download URL with safety checks
            gltf_data = data.get("gltf")
            if not gltf_data:
                return {"error": "No gltf download URL available for this model. Response: " + str(data)}

            download_url = gltf_data.get("url")
            if not download_url:
                return {"error": "No download URL available for this model. Make sure the model is downloadable and you have access."}

            # Save to temporary file (streamed + retried; Sketchfab CDN
            # commonly drops large transfers mid-stream).
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, f"{uid}.zip")
            try:
                bytes_written = _resilient_download_to_file(
                    download_url, zip_file_path,
                    max_retries=4, timeout=180,
                )
                print(f"[blender-mcp] Sketchfab model {uid}: downloaded {bytes_written} bytes")
            except Exception as e:
                with suppress(Exception):
                    shutil.rmtree(temp_dir)
                return {"error": f"Model download failed after retries: {e}"}

            # Extract the zip file with enhanced security
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                # More secure zip slip prevention
                for file_info in zip_ref.infolist():
                    # Get the path of the file
                    file_path = file_info.filename

                    # Convert directory separators to the current OS style
                    # This handles both / and \ in zip entries
                    target_path = os.path.join(temp_dir, os.path.normpath(file_path))

                    # Get absolute paths for comparison
                    abs_temp_dir = os.path.abspath(temp_dir)
                    abs_target_path = os.path.abspath(target_path)

                    # Ensure the normalized path doesn't escape the target directory
                    if not abs_target_path.startswith(abs_temp_dir):
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                        return {"error": "Security issue: Zip contains files with path traversal attempt"}

                    # Additional explicit check for directory traversal
                    if ".." in file_path:
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                        return {"error": "Security issue: Zip contains files with directory traversal sequence"}

                # If all files passed security checks, extract them
                zip_ref.extractall(temp_dir)

            # Find the main glTF file
            gltf_files = [f for f in os.listdir(temp_dir) if f.endswith('.gltf') or f.endswith('.glb')]

            if not gltf_files:
                with suppress(Exception):
                    shutil.rmtree(temp_dir)
                return {"error": "No glTF file found in the downloaded model"}

            main_file = os.path.join(temp_dir, gltf_files[0])

            # Import the model
            bpy.ops.import_scene.gltf(filepath=main_file)

            # Get the imported objects
            imported_objects = list(bpy.context.selected_objects)
            imported_object_names = [obj.name for obj in imported_objects]

            # Clean up temporary files
            with suppress(Exception):
                shutil.rmtree(temp_dir)

            # Find root objects (objects without parents in the imported set)
            root_objects = [obj for obj in imported_objects if obj.parent is None]

            # Helper function to recursively get all mesh children
            def get_all_mesh_children(obj):
                """Recursively collect all mesh objects in the hierarchy"""
                meshes = []
                if obj.type == 'MESH':
                    meshes.append(obj)
                for child in obj.children:
                    meshes.extend(get_all_mesh_children(child))
                return meshes

            # Collect ALL meshes from the entire hierarchy (starting from roots)
            all_meshes = []
            for obj in root_objects:
                all_meshes.extend(get_all_mesh_children(obj))
            
            if all_meshes:
                # Calculate combined world bounding box for all meshes
                all_min = mathutils.Vector((float('inf'), float('inf'), float('inf')))
                all_max = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
                
                for mesh_obj in all_meshes:
                    # Get world-space bounding box corners
                    for corner in mesh_obj.bound_box:
                        world_corner = mesh_obj.matrix_world @ mathutils.Vector(corner)
                        all_min.x = min(all_min.x, world_corner.x)
                        all_min.y = min(all_min.y, world_corner.y)
                        all_min.z = min(all_min.z, world_corner.z)
                        all_max.x = max(all_max.x, world_corner.x)
                        all_max.y = max(all_max.y, world_corner.y)
                        all_max.z = max(all_max.z, world_corner.z)
                
                # Calculate dimensions
                dimensions = [
                    all_max.x - all_min.x,
                    all_max.y - all_min.y,
                    all_max.z - all_min.z
                ]
                max_dimension = max(dimensions)
                
                # Apply normalization if requested
                scale_applied = 1.0
                if normalize_size and max_dimension > 0:
                    scale_factor = target_size / max_dimension
                    scale_applied = scale_factor
                    
                    # ✅ Only apply scale to ROOT objects (not children!)
                    # Child objects inherit parent's scale through matrix_world
                    for root in root_objects:
                        root.scale = (
                            root.scale.x * scale_factor,
                            root.scale.y * scale_factor,
                            root.scale.z * scale_factor
                        )
                    
                    # Update the scene to recalculate matrix_world for all objects
                    bpy.context.view_layer.update()
                    
                    # Recalculate bounding box after scaling
                    all_min = mathutils.Vector((float('inf'), float('inf'), float('inf')))
                    all_max = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
                    
                    for mesh_obj in all_meshes:
                        for corner in mesh_obj.bound_box:
                            world_corner = mesh_obj.matrix_world @ mathutils.Vector(corner)
                            all_min.x = min(all_min.x, world_corner.x)
                            all_min.y = min(all_min.y, world_corner.y)
                            all_min.z = min(all_min.z, world_corner.z)
                            all_max.x = max(all_max.x, world_corner.x)
                            all_max.y = max(all_max.y, world_corner.y)
                            all_max.z = max(all_max.z, world_corner.z)
                    
                    dimensions = [
                        all_max.x - all_min.x,
                        all_max.y - all_min.y,
                        all_max.z - all_min.z
                    ]
                
                world_bounding_box = [[all_min.x, all_min.y, all_min.z], [all_max.x, all_max.y, all_max.z]]
            else:
                world_bounding_box = None
                dimensions = None
                scale_applied = 1.0

            result = {
                "success": True,
                "message": "Model imported successfully",
                "imported_objects": imported_object_names
            }
            
            if world_bounding_box:
                result["world_bounding_box"] = world_bounding_box
            if dimensions:
                result["dimensions"] = [round(d, 4) for d in dimensions]
            if normalize_size:
                result["scale_applied"] = round(scale_applied, 6)
                result["normalized"] = True
            
            return result

        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection and try again with a simpler model."}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Failed to download model: {str(e)}"}
    #endregion

    #region Hunyuan3D
    def get_hunyuan3d_status(self):
        """Get the current status of Hunyuan3D integration"""
        enabled = bpy.context.scene.blendermcp_use_hunyuan3d
        hunyuan3d_mode = bpy.context.scene.blendermcp_hunyuan3d_mode
        secret_id = self._get_hunyuan3d_secret_id()
        secret_key = self._get_hunyuan3d_secret_key()
        api_url = self._get_hunyuan3d_api_url()
        if enabled:
            match hunyuan3d_mode:
                case "OFFICIAL_API":
                    if not secret_id or not secret_key:
                        return {
                            "enabled": False, 
                            "mode": hunyuan3d_mode, 
                            "message": """Hunyuan3D integration is currently enabled, but SecretId or SecretKey is not given. To enable it:
                                1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                                2. Keep the 'Use Tencent Hunyuan 3D model generation' checkbox checked
                                3. Choose the right platform and fill in the SecretId and SecretKey
                                4. Restart the connection to Claude"""
                        }
                case "LOCAL_API":
                    if not api_url:
                        return {
                            "enabled": False, 
                            "mode": hunyuan3d_mode, 
                            "message": """Hunyuan3D integration is currently enabled, but API URL  is not given. To enable it:
                                1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                                2. Keep the 'Use Tencent Hunyuan 3D model generation' checkbox checked
                                3. Choose the right platform and fill in the API URL
                                4. Restart the connection to Claude"""
                        }
                case _:
                    return {
                        "enabled": False, 
                        "message": "Hunyuan3D integration is enabled and mode is not supported."
                    }
            return {
                "enabled": True, 
                "mode": hunyuan3d_mode,
                "message": "Hunyuan3D integration is enabled and ready to use."
            }
        return {
            "enabled": False, 
            "message": """Hunyuan3D integration is currently disabled. To enable it:
                        1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                        2. Check the 'Use Tencent Hunyuan 3D model generation' checkbox
                        3. Restart the connection to Claude"""
        }
    
    @staticmethod
    def get_tencent_cloud_sign_headers(
        method: str,
        path: str,
        headParams: dict,
        data: dict,
        service: str,
        region: str,
        secret_id: str,
        secret_key: str,
        host: str = None
    ):
        """Generate the signature header required for Tencent Cloud API requests headers"""
        # Generate timestamp
        timestamp = int(time.time())
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        
        # If host is not provided, it is generated based on service and region.
        if not host:
            host = f"{service}.tencentcloudapi.com"
        
        endpoint = f"https://{host}"
        
        # Constructing the request body
        payload_str = json.dumps(data)
        
        # ************* Step 1: Concatenate the canonical request string *************
        canonical_uri = path
        canonical_querystring = ""
        ct = "application/json; charset=utf-8"
        canonical_headers = f"content-type:{ct}\nhost:{host}\nx-tc-action:{headParams.get('Action', '').lower()}\n"
        signed_headers = "content-type;host;x-tc-action"
        hashed_request_payload = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        
        canonical_request = (method + "\n" +
                            canonical_uri + "\n" +
                            canonical_querystring + "\n" +
                            canonical_headers + "\n" +
                            signed_headers + "\n" +
                            hashed_request_payload)

        # ************* Step 2: Construct the reception signature string *************
        credential_scope = f"{date}/{service}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = ("TC3-HMAC-SHA256" + "\n" +
                        str(timestamp) + "\n" +
                        credential_scope + "\n" +
                        hashed_canonical_request)

        # ************* Step 3: Calculate the signature *************
        def sign(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
        secret_service = sign(secret_date, service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(
            secret_signing, 
            string_to_sign.encode("utf-8"), 
            hashlib.sha256
        ).hexdigest()

        # ************* Step 4: Connect Authorization *************
        authorization = ("TC3-HMAC-SHA256" + " " +
                        "Credential=" + secret_id + "/" + credential_scope + ", " +
                        "SignedHeaders=" + signed_headers + ", " +
                        "Signature=" + signature)

        # Constructing request headers
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": host,
            "X-TC-Action": headParams.get("Action", ""),
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": headParams.get("Version", ""),
            "X-TC-Region": region
        }

        return headers, endpoint

    def create_hunyuan_job(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hunyuan3d_mode:
            case "OFFICIAL_API":
                return self.create_hunyuan_job_main_site(*args, **kwargs)
            case "LOCAL_API":
                return self.create_hunyuan_job_local_site(*args, **kwargs)
            case _:
                return f"Error: Unknown Hunyuan3D mode!"

    def create_hunyuan_job_main_site(
        self,
        text_prompt: str = None,
        image: str = None
    ):
        try:
            secret_id = self._get_hunyuan3d_secret_id()
            secret_key = self._get_hunyuan3d_secret_key()

            if not secret_id or not secret_key:
                return {"error": "SecretId or SecretKey is not given"}

            # Parameter verification
            if not text_prompt and not image:
                return {"error": "Prompt or Image is required"}
            if text_prompt and image:
                return {"error": "Prompt and Image cannot be provided simultaneously"}
            # Fixed parameter configuration
            service = "hunyuan"
            action = "SubmitHunyuanTo3DJob"
            version = "2023-09-01"
            region = "ap-guangzhou"

            headParams={
                "Action": action,
                "Version": version,
                "Region": region,
            }

            # Constructing request parameters
            data = {
                "Num": 1  # The current API limit is only 1
            }

            # Handling text prompts
            if text_prompt:
                if len(text_prompt) > 200:
                    return {"error": "Prompt exceeds 200 characters limit"}
                data["Prompt"] = text_prompt

            # Handling image
            if image:
                if re.match(r'^https?://', image, re.IGNORECASE) is not None:
                    data["ImageUrl"] = image
                else:
                    try:
                        # Convert to Base64 format
                        with open(image, "rb") as f:
                            image_base64 = base64.b64encode(f.read()).decode("ascii")
                        data["ImageBase64"] = image_base64
                    except Exception as e:
                        return {"error": f"Image encoding failed: {str(e)}"}
            
            # Get signed headers
            headers, endpoint = self.get_tencent_cloud_sign_headers("POST", "/", headParams, data, service, region, secret_id, secret_key)

            response = requests.post(
                endpoint,
                headers = headers,
                data = json.dumps(data)
            )

            if response.status_code == 200:
                return response.json()
            return {
                "error": f"API request failed with status {response.status_code}: {response}"
            }
        except Exception as e:
            return {"error": str(e)}

    def create_hunyuan_job_local_site(
        self,
        text_prompt: str = None,
        image: str = None):
        try:
            base_url = self._get_hunyuan3d_api_url().rstrip('/')
            octree_resolution = bpy.context.scene.blendermcp_hunyuan3d_octree_resolution
            num_inference_steps = bpy.context.scene.blendermcp_hunyuan3d_num_inference_steps
            guidance_scale = bpy.context.scene.blendermcp_hunyuan3d_guidance_scale
            texture = bpy.context.scene.blendermcp_hunyuan3d_texture

            if not base_url:
                return {"error": "API URL is not given"}
            # Parameter verification
            if not text_prompt and not image:
                return {"error": "Prompt or Image is required"}

            # Constructing request parameters
            data = {
                "octree_resolution": octree_resolution,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "texture": texture,
            }

            # Handling text prompts
            if text_prompt:
                data["text"] = text_prompt

            # Handling image
            if image:
                if re.match(r'^https?://', image, re.IGNORECASE) is not None:
                    try:
                        resImg = requests.get(image)
                        resImg.raise_for_status()
                        image_base64 = base64.b64encode(resImg.content).decode("ascii")
                        data["image"] = image_base64
                    except Exception as e:
                        return {"error": f"Failed to download or encode image: {str(e)}"} 
                else:
                    try:
                        # Convert to Base64 format
                        with open(image, "rb") as f:
                            image_base64 = base64.b64encode(f.read()).decode("ascii")
                        data["image"] = image_base64
                    except Exception as e:
                        return {"error": f"Image encoding failed: {str(e)}"}

            response = requests.post(
                f"{base_url}/generate",
                json = data,
            )

            if response.status_code != 200:
                return {
                    "error": f"Generation failed: {response.text}"
                }
        
            # Decode base64 and save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".glb") as temp_file:
                temp_file.write(response.content)
                temp_file_name = temp_file.name

            # Import the GLB file in the main thread
            def import_handler():
                bpy.ops.import_scene.gltf(filepath=temp_file_name)
                os.unlink(temp_file.name)
                return None
            
            bpy.app.timers.register(import_handler)

            return {
                "status": "DONE",
                "message": "Generation and Import glb succeeded"
            }
        except Exception as e:
            print(f"An error occurred: {e}")
            return {"error": str(e)}
        
    
    def poll_hunyuan_job_status(self, *args, **kwargs):
        return self.poll_hunyuan_job_status_ai(*args, **kwargs)
    
    def poll_hunyuan_job_status_ai(self, job_id: str):
        """Call the job status API to get the job status"""
        print(job_id)
        try:
            secret_id = self._get_hunyuan3d_secret_id()
            secret_key = self._get_hunyuan3d_secret_key()

            if not secret_id or not secret_key:
                return {"error": "SecretId or SecretKey is not given"}
            if not job_id:
                return {"error": "JobId is required"}
            
            service = "hunyuan"
            action = "QueryHunyuanTo3DJob"
            version = "2023-09-01"
            region = "ap-guangzhou"

            headParams={
                "Action": action,
                "Version": version,
                "Region": region,
            }

            clean_job_id = job_id.removeprefix("job_")
            data = {
                "JobId": clean_job_id
            }

            headers, endpoint = self.get_tencent_cloud_sign_headers("POST", "/", headParams, data, service, region, secret_id, secret_key)

            response = requests.post(
                endpoint,
                headers=headers,
                data=json.dumps(data)
            )

            if response.status_code == 200:
                return response.json()
            return {
                "error": f"API request failed with status {response.status_code}: {response}"
            }
        except Exception as e:
            return {"error": str(e)}

    def import_generated_asset_hunyuan(self, *args, **kwargs):
        return self.import_generated_asset_hunyuan_ai(*args, **kwargs)
            
    def import_generated_asset_hunyuan_ai(self, name: str , zip_file_url: str):
        if not zip_file_url:
            return {"error": "Zip file not found"}
        
        # Validate URL
        if not re.match(r'^https?://', zip_file_url, re.IGNORECASE):
            return {"error": "Invalid URL format. Must start with http:// or https://"}
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="tencent_obj_")
        zip_file_path = osp.join(temp_dir, "model.zip")
        obj_file_path = osp.join(temp_dir, "model.obj")
        mtl_file_path = osp.join(temp_dir, "model.mtl")

        try:
            # Download ZIP file (streamed + retried)
            _resilient_download_to_file(zip_file_url, zip_file_path)

            # Unzip the ZIP
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find the .obj file (there may be multiple, assuming the main file is model.obj)
            for file in os.listdir(temp_dir):
                if file.endswith(".obj"):
                    obj_file_path = osp.join(temp_dir, file)

            if not osp.exists(obj_file_path):
                return {"succeed": False, "error": "OBJ file not found after extraction"}

            # Import obj file
            if bpy.app.version>=(4, 0, 0):
                bpy.ops.wm.obj_import(filepath=obj_file_path)
            else:
                bpy.ops.import_scene.obj(filepath=obj_file_path)

            imported_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
            if not imported_objs:
                return {"succeed": False, "error": "No mesh objects imported"}

            obj = imported_objs[0]
            if name:
                obj.name = name

            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {"succeed": True, **result}
        except Exception as e:
            return {"succeed": False, "error": str(e)}
        finally:
            #  Clean up temporary zip and obj, save texture and mtl
            try:
                if os.path.exists(zip_file_path):
                    os.remove(zip_file_path) 
                if os.path.exists(obj_file_path):
                    os.remove(obj_file_path)
            except Exception as e:
                print(f"Failed to clean up temporary directory {temp_dir}: {e}")
    #endregion

# Blender Addon Preferences
class BLENDERMCP_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    telemetry_consent: BoolProperty(
        name="Allow Telemetry",
        description="Allow collection of prompts, code snippets, and screenshots to help improve Blender MCP",
        default=True
    )
    hyper3d_api_key: bpy.props.StringProperty(
        name="Hyper3D API Key",
        subtype="PASSWORD",
        description="Persistent Hyper3D API Key",
        default=""
    )
    sketchfab_api_key: bpy.props.StringProperty(
        name="Sketchfab API Key",
        subtype="PASSWORD",
        description="Persistent Sketchfab API Key",
        default=""
    )
    hunyuan3d_secret_id: bpy.props.StringProperty(
        name="Hunyuan3D SecretId",
        description="Persistent Hunyuan3D SecretId",
        default=""
    )
    hunyuan3d_secret_key: bpy.props.StringProperty(
        name="Hunyuan3D SecretKey",
        subtype="PASSWORD",
        description="Persistent Hunyuan3D SecretKey",
        default=""
    )
    hunyuan3d_api_url: bpy.props.StringProperty(
        name="Hunyuan3D API URL",
        description="Persistent Hunyuan3D API URL",
        default=""
    )
    tripo3d_api_key: bpy.props.StringProperty(
        name="Tripo3D API Key",
        subtype="PASSWORD",
        description="Persistent Tripo3D API Key (https://platform.tripo3d.ai/)",
        default=""
    )
    meshy_api_key: bpy.props.StringProperty(
        name="Meshy.ai API Key",
        subtype="PASSWORD",
        description="Persistent Meshy.ai API Key (https://www.meshy.ai/settings/api)",
        default=""
    )

    def draw(self, context):
        layout = self.layout
        
        # Telemetry section
        layout.label(text="Telemetry & Privacy:", icon='PREFERENCES')
        
        box = layout.box()
        row = box.row()
        row.prop(self, "telemetry_consent", text="Allow Telemetry")
        
        # Info text
        box.separator()
        if self.telemetry_consent:
            box.label(text="With consent: We collect anonymized prompts, code, and screenshots.", icon='INFO')
        else:
            box.label(text="Without consent: We only collect minimal anonymous usage data", icon='INFO')
            box.label(text="(tool names, success/failure, duration - no prompts or code).", icon='BLANK1')
        box.separator()
        box.label(text="All data is fully anonymized. You can change this anytime.", icon='CHECKMARK')
        
        # Terms and Conditions link
        box.separator()
        row = box.row()
        row.operator("blendermcp.open_terms", text="View Terms and Conditions", icon='TEXT')

        layout.separator()
        layout.label(text="Persistent API Credentials:", icon='LOCKED')
        cred_box = layout.box()
        cred_box.prop(self, "sketchfab_api_key", text="Sketchfab API Key")
        cred_box.prop(self, "hyper3d_api_key", text="Hyper3D API Key")
        cred_box.prop(self, "hunyuan3d_secret_id", text="Hunyuan3D SecretId")
        cred_box.prop(self, "hunyuan3d_secret_key", text="Hunyuan3D SecretKey")
        cred_box.prop(self, "hunyuan3d_api_url", text="Hunyuan3D API URL")
        cred_box.prop(self, "tripo3d_api_key", text="Tripo3D API Key")
        cred_box.prop(self, "meshy_api_key", text="Meshy.ai API Key")

# Blender UI Panel
class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BlenderMCP'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        prefs = get_blendermcp_addon_preferences(context)

        layout.prop(scene, "blendermcp_port")
        layout.prop(scene, "blendermcp_use_polyhaven", text="Use assets from Poly Haven")

        layout.prop(scene, "blendermcp_use_hyper3d", text="Use Hyper3D Rodin 3D model generation")
        if scene.blendermcp_use_hyper3d:
            layout.prop(scene, "blendermcp_hyper3d_mode", text="Rodin Mode")
            if prefs:
                layout.prop(prefs, "hyper3d_api_key", text="API Key")
            else:
                layout.prop(scene, "blendermcp_hyper3d_api_key", text="API Key")
            layout.operator("blendermcp.set_hyper3d_free_trial_api_key", text="Set Free Trial API Key")

        layout.prop(scene, "blendermcp_use_sketchfab", text="Use assets from Sketchfab")
        if scene.blendermcp_use_sketchfab:
            if prefs:
                layout.prop(prefs, "sketchfab_api_key", text="API Key")
            else:
                layout.prop(scene, "blendermcp_sketchfab_api_key", text="API Key")

        layout.prop(scene, "blendermcp_use_hunyuan3d", text="Use Tencent Hunyuan 3D model generation")
        if scene.blendermcp_use_hunyuan3d:
            layout.prop(scene, "blendermcp_hunyuan3d_mode", text="Hunyuan3D Mode")
            if scene.blendermcp_hunyuan3d_mode == 'OFFICIAL_API':
                if prefs:
                    layout.prop(prefs, "hunyuan3d_secret_id", text="SecretId")
                    layout.prop(prefs, "hunyuan3d_secret_key", text="SecretKey")
                else:
                    layout.prop(scene, "blendermcp_hunyuan3d_secret_id", text="SecretId")
                    layout.prop(scene, "blendermcp_hunyuan3d_secret_key", text="SecretKey")
            if scene.blendermcp_hunyuan3d_mode == 'LOCAL_API':
                if prefs:
                    layout.prop(prefs, "hunyuan3d_api_url", text="API URL")
                else:
                    layout.prop(scene, "blendermcp_hunyuan3d_api_url", text="API URL")
                layout.prop(scene, "blendermcp_hunyuan3d_octree_resolution", text="Octree Resolution")
                layout.prop(scene, "blendermcp_hunyuan3d_num_inference_steps", text="Number of Inference Steps")
                layout.prop(scene, "blendermcp_hunyuan3d_guidance_scale", text="Guidance Scale")
                layout.prop(scene, "blendermcp_hunyuan3d_texture", text="Generate Texture")

        # Tripo3D — added by fork
        layout.prop(scene, "blendermcp_use_tripo3d", text="Use Tripo3D AI 3D generation")
        if scene.blendermcp_use_tripo3d:
            if prefs:
                layout.prop(prefs, "tripo3d_api_key", text="Tripo3D API Key")
            else:
                layout.prop(scene, "blendermcp_tripo3d_api_key", text="Tripo3D API Key")

        # Meshy.ai — added by fork
        layout.prop(scene, "blendermcp_use_meshy", text="Use Meshy.ai AI 3D generation")
        if scene.blendermcp_use_meshy:
            if prefs:
                layout.prop(prefs, "meshy_api_key", text="Meshy.ai API Key")
            else:
                layout.prop(scene, "blendermcp_meshy_api_key", text="Meshy.ai API Key")

        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Connect to MCP server")
        else:
            layout.operator("blendermcp.stop_server", text="Disconnect from MCP server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")

# Operator to set Hyper3D API Key
class BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey(bpy.types.Operator):
    bl_idname = "blendermcp.set_hyper3d_free_trial_api_key"
    bl_label = "Set Free Trial API Key"

    def execute(self, context):
        prefs = get_blendermcp_addon_preferences(context)
        if prefs:
            if not prefs.hyper3d_api_key or prefs.hyper3d_api_key == RODIN_FREE_TRIAL_KEY:
                prefs.hyper3d_api_key = RODIN_FREE_TRIAL_KEY
            else:
                self.report(
                    {'INFO'},
                    "Using free trial for this session only; saved private key was kept."
                )
        context.scene.blendermcp_hyper3d_api_key = RODIN_FREE_TRIAL_KEY
        context.scene.blendermcp_hyper3d_mode = 'MAIN_SITE'
        self.report({'INFO'}, "API Key set successfully!")
        return {'FINISHED'}

# Operator to start the server
class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Connect to Claude"
    bl_description = "Start the BlenderMCP server to connect with Claude"

    def execute(self, context):
        scene = context.scene

        # Create a new server instance
        if not hasattr(bpy.types, "blendermcp_server") or not bpy.types.blendermcp_server:
            bpy.types.blendermcp_server = BlenderMCPServer(port=scene.blendermcp_port)

        # Start the server
        bpy.types.blendermcp_server.start()
        scene.blendermcp_server_running = True

        return {'FINISHED'}

# Operator to stop the server
class BLENDERMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop the connection to Claude"
    bl_description = "Stop the connection to Claude"

    def execute(self, context):
        scene = context.scene

        # Stop the server if it exists
        if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
            bpy.types.blendermcp_server.stop()
            del bpy.types.blendermcp_server

        scene.blendermcp_server_running = False

        return {'FINISHED'}

# Operator to open Terms and Conditions
class BLENDERMCP_OT_OpenTerms(bpy.types.Operator):
    bl_idname = "blendermcp.open_terms"
    bl_label = "View Terms and Conditions"
    bl_description = "Open the Terms and Conditions document"

    def execute(self, context):
        # Open the Terms and Conditions on GitHub
        terms_url = "https://github.com/ahujasid/blender-mcp/blob/main/TERMS_AND_CONDITIONS.md"
        try:
            import webbrowser
            webbrowser.open(terms_url)
            self.report({'INFO'}, "Terms and Conditions opened in browser")
        except Exception as e:
            self.report({'ERROR'}, f"Could not open Terms and Conditions: {str(e)}")
        
        return {'FINISHED'}

# Registration functions
def register():
    bpy.types.Scene.blendermcp_port = IntProperty(
        name="Port",
        description="Port for the BlenderMCP server",
        default=9876,
        min=1024,
        max=65535
    )

    bpy.types.Scene.blendermcp_server_running = bpy.props.BoolProperty(
        name="Server Running",
        default=False
    )

    bpy.types.Scene.blendermcp_use_polyhaven = bpy.props.BoolProperty(
        name="Use Poly Haven",
        description="Enable Poly Haven asset integration",
        default=False
    )

    bpy.types.Scene.blendermcp_use_hyper3d = bpy.props.BoolProperty(
        name="Use Hyper3D Rodin",
        description="Enable Hyper3D Rodin generatino integration",
        default=False
    )

    bpy.types.Scene.blendermcp_hyper3d_mode = bpy.props.EnumProperty(
        name="Rodin Mode",
        description="Choose the platform used to call Rodin APIs",
        items=[
            ("MAIN_SITE", "hyper3d.ai", "hyper3d.ai"),
            ("FAL_AI", "fal.ai", "fal.ai"),
        ],
        default="MAIN_SITE"
    )

    bpy.types.Scene.blendermcp_hyper3d_api_key = bpy.props.StringProperty(
        name="Hyper3D API Key",
        subtype="PASSWORD",
        description="API Key provided by Hyper3D",
        default=""
    )

    # Tripo3D + Meshy.ai (added by fork)
    bpy.types.Scene.blendermcp_use_tripo3d = bpy.props.BoolProperty(
        name="Use Tripo3D",
        description="Enable Tripo3D AI 3D generation (text-to-3D, image-to-3D)",
        default=False
    )
    bpy.types.Scene.blendermcp_tripo3d_api_key = bpy.props.StringProperty(
        name="Tripo3D API Key",
        subtype="PASSWORD",
        description="API Key from https://platform.tripo3d.ai/",
        default=""
    )
    bpy.types.Scene.blendermcp_use_meshy = bpy.props.BoolProperty(
        name="Use Meshy.ai",
        description="Enable Meshy.ai AI 3D generation (text-to-3D, image-to-3D)",
        default=False
    )
    bpy.types.Scene.blendermcp_meshy_api_key = bpy.props.StringProperty(
        name="Meshy.ai API Key",
        subtype="PASSWORD",
        description="API Key from https://www.meshy.ai/settings/api",
        default=""
    )

    bpy.types.Scene.blendermcp_use_hunyuan3d = bpy.props.BoolProperty(
        name="Use Hunyuan 3D",
        description="Enable Hunyuan asset integration",
        default=False
    )

    bpy.types.Scene.blendermcp_hunyuan3d_mode = bpy.props.EnumProperty(
        name="Hunyuan3D Mode",
        description="Choose a local or official APIs",
        items=[
            ("LOCAL_API", "local api", "local api"),
            ("OFFICIAL_API", "official api", "official api"),
        ],
        default="LOCAL_API"
    )

    bpy.types.Scene.blendermcp_hunyuan3d_secret_id = bpy.props.StringProperty(
        name="Hunyuan 3D SecretId",
        description="SecretId provided by Hunyuan 3D",
        default=""
    )

    bpy.types.Scene.blendermcp_hunyuan3d_secret_key = bpy.props.StringProperty(
        name="Hunyuan 3D SecretKey",
        subtype="PASSWORD",
        description="SecretKey provided by Hunyuan 3D",
        default=""
    )

    bpy.types.Scene.blendermcp_hunyuan3d_api_url = bpy.props.StringProperty(
        name="API URL",
        description="URL of the Hunyuan 3D API service",
        default="http://localhost:8081"
    )

    bpy.types.Scene.blendermcp_hunyuan3d_octree_resolution = bpy.props.IntProperty(
        name="Octree Resolution",
        description="Octree resolution for the 3D generation",
        default=256,
        min=128,
        max=512,
    )

    bpy.types.Scene.blendermcp_hunyuan3d_num_inference_steps = bpy.props.IntProperty(
        name="Number of Inference Steps",
        description="Number of inference steps for the 3D generation",
        default=20,
        min=20,
        max=50,
    )

    bpy.types.Scene.blendermcp_hunyuan3d_guidance_scale = bpy.props.FloatProperty(
        name="Guidance Scale",
        description="Guidance scale for the 3D generation",
        default=5.5,
        min=1.0,
        max=10.0,
    )

    bpy.types.Scene.blendermcp_hunyuan3d_texture = bpy.props.BoolProperty(
        name="Generate Texture",
        description="Whether to generate texture for the 3D model",
        default=False,
    )
    
    bpy.types.Scene.blendermcp_use_sketchfab = bpy.props.BoolProperty(
        name="Use Sketchfab",
        description="Enable Sketchfab asset integration",
        default=False
    )

    bpy.types.Scene.blendermcp_sketchfab_api_key = bpy.props.StringProperty(
        name="Sketchfab API Key",
        subtype="PASSWORD",
        description="API Key provided by Sketchfab",
        default=""
    )

    # Register preferences class
    bpy.utils.register_class(BLENDERMCP_AddonPreferences)

    bpy.utils.register_class(BLENDERMCP_PT_Panel)
    bpy.utils.register_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.register_class(BLENDERMCP_OT_StartServer)
    bpy.utils.register_class(BLENDERMCP_OT_StopServer)
    bpy.utils.register_class(BLENDERMCP_OT_OpenTerms)

    print("BlenderMCP addon registered")

def unregister():
    # Stop the server if it's running
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        bpy.types.blendermcp_server.stop()
        del bpy.types.blendermcp_server

    bpy.utils.unregister_class(BLENDERMCP_PT_Panel)
    bpy.utils.unregister_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.unregister_class(BLENDERMCP_OT_StartServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_StopServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_OpenTerms)
    bpy.utils.unregister_class(BLENDERMCP_AddonPreferences)

    del bpy.types.Scene.blendermcp_port
    del bpy.types.Scene.blendermcp_server_running
    del bpy.types.Scene.blendermcp_use_polyhaven
    del bpy.types.Scene.blendermcp_use_hyper3d
    del bpy.types.Scene.blendermcp_hyper3d_mode
    del bpy.types.Scene.blendermcp_hyper3d_api_key
    del bpy.types.Scene.blendermcp_use_sketchfab
    del bpy.types.Scene.blendermcp_sketchfab_api_key
    # Sprint 4 cleanup
    with suppress(Exception):
        del bpy.types.Scene.blendermcp_use_tripo3d
    with suppress(Exception):
        del bpy.types.Scene.blendermcp_tripo3d_api_key
    with suppress(Exception):
        del bpy.types.Scene.blendermcp_use_meshy
    with suppress(Exception):
        del bpy.types.Scene.blendermcp_meshy_api_key
    del bpy.types.Scene.blendermcp_use_hunyuan3d
    del bpy.types.Scene.blendermcp_hunyuan3d_mode
    del bpy.types.Scene.blendermcp_hunyuan3d_secret_id
    del bpy.types.Scene.blendermcp_hunyuan3d_secret_key
    del bpy.types.Scene.blendermcp_hunyuan3d_api_url
    del bpy.types.Scene.blendermcp_hunyuan3d_octree_resolution
    del bpy.types.Scene.blendermcp_hunyuan3d_num_inference_steps
    del bpy.types.Scene.blendermcp_hunyuan3d_guidance_scale
    del bpy.types.Scene.blendermcp_hunyuan3d_texture

    print("BlenderMCP addon unregistered")

if __name__ == "__main__":
    register()
