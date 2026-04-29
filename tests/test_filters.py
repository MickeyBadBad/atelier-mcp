"""Sprint 6 — response slimming filter tests."""
from blender_mcp._filters import slim_sketchfab, slim_polyhaven


def test_slim_sketchfab_keeps_essential_fields():
    raw = {
        "results": [
            {
                "uid": "abc123",
                "name": "Wooden Bench",
                "viewCount": 24000,
                "likeCount": 200,
                "isDownloadable": True,
                "faceCount": 1348,
                "vertexCount": 800,
                "license": {"label": "CC Attribution"},
                "categories": [{"name": "furniture-home"}],
                "thumbnails": {
                    "images": [
                        {"width": 1024, "height": 576,
                         "url": "https://media/thumb/1024.jpg"},
                        {"width": 256, "height": 144,
                         "url": "https://media/thumb/256.jpg"},
                    ]
                },
                "user": {
                    "username": "3dmish",
                    "displayName": "3DMish",
                    "avatar": {"images": [
                        {"size": 32, "url": "..."}, {"size": 90, "url": "..."}]},
                    "uri": "https://api.sketchfab.com/v3/users/...",
                },
                "archives": {
                    "glb": {"size": 381692, "type": "glb"},
                    "gltf": {"size": 136954, "type": "gltf"},
                    "source": {"size": 286926, "type": "source"},
                    "usdz": {"size": 206253, "type": "usdz"},
                },
                "tags": [{"name": "bench", "slug": "bench", "uri": "..."}],
                "description": "Free 3d-model of wooden bench.",
                "createdAt": "2017-10-03T10:18:57",
                "publishedAt": "2017-10-03T10:40:38",
                "embedUrl": "https://sketchfab.com/...",
                "viewerUrl": "https://sketchfab.com/...",
                "uri": "https://api.sketchfab.com/v3/models/...",
                "files_hash": "abc123def456",
            }
        ],
        "cursors": {"next": "10", "previous": None},
    }
    out = slim_sketchfab(raw)
    assert "results" in out
    assert len(out["results"]) == 1
    item = out["results"][0]
    # Kept
    assert item["uid"] == "abc123"
    assert item["name"] == "Wooden Bench"
    assert item["face_count"] == 1348
    assert item["license"] == "CC Attribution"
    assert item["downloadable"] is True
    assert item["view_count"] == 24000
    assert item["like_count"] == 200
    assert item["category"] == "furniture-home"
    assert item["thumb_url"] == "https://media/thumb/1024.jpg"  # only one
    assert item["author"] == "3DMish"
    # Dropped (token bloat)
    assert "thumbnails" not in item
    assert "archives" not in item
    assert "tags" not in item
    assert "user" not in item
    assert "files_hash" not in item
    assert "embedUrl" not in item


def test_slim_sketchfab_handles_no_thumbnail_or_no_user():
    raw = {"results": [{"uid": "x", "name": "y", "isDownloadable": False,
                        "faceCount": 0, "thumbnails": {"images": []}}]}
    out = slim_sketchfab(raw)
    item = out["results"][0]
    assert item["thumb_url"] is None
    assert item["author"] is None


def test_slim_polyhaven_keeps_essentials_drops_metadata():
    raw = {
        "assets": {
            "alps_field": {
                "name": "Alps Field",
                "categories": ["natural light", "outdoor", "nature"],
                "tags": ["sun", "grass", "field", "mountain"],
                "type": 0,
                "max_resolution": [20634, 10317],
                "download_count": 265859,
                "thumbnail_url": "https://cdn.polyhaven.com/.../alps_field.png",
                "evs_cap": 22,
                "whitebalance": 5500,
                "files_hash": "abcdef",
                "sponsors": ["12345"],
                "coords": [46.6, 9.4],
                "authors": {"Andreas Mischok": "All"},
                "date_taken": 1649928720,
                "date_published": 1656547200,
                "description": "Free 20K HDRI of an Alps field.",
                "backplates": False,
            }
        },
        "total_count": 682,
        "returned_count": 20,
    }
    out = slim_polyhaven(raw)
    assert out["total_count"] == 682
    assert out["returned_count"] == 20
    assert "alps_field" in out["assets"]
    asset = out["assets"]["alps_field"]
    # Kept
    assert asset["name"] == "Alps Field"
    assert asset["categories"] == ["natural light", "outdoor", "nature"]
    assert asset["max_resolution"] == "20634x10317"
    assert asset["download_count"] == 265859
    assert asset["thumb_url"] == "https://cdn.polyhaven.com/.../alps_field.png"
    # Dropped
    assert "evs_cap" not in asset
    assert "whitebalance" not in asset
    assert "files_hash" not in asset
    assert "sponsors" not in asset
    assert "coords" not in asset
    assert "date_taken" not in asset


def test_slim_passthrough_on_error_response():
    """If the addon returned an error envelope, don't try to slim — pass
    through unchanged so the upper layer can classify it normally."""
    err = {"error": "API key missing"}
    assert slim_sketchfab(err) == err
    assert slim_polyhaven(err) == err
