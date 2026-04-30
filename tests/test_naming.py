"""After v2.0 mass-rename, no stale legacy names should remain in
server.py @mcp.tool() definitions or addon.py dispatcher entries."""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERVER = (REPO / "src" / "atelier" / "server.py").read_text()
ADDON = (REPO / "addon.py").read_text()

LEGACY_NAMES = [
    "import_generated_asset",
    "import_generated_asset_hunyuan",
    "poll_rodin_job_status",
    "generate_hyper3d_model_via_text",
    "generate_hyper3d_model_via_images",
]


def test_no_legacy_function_defs_in_server():
    for name in LEGACY_NAMES:
        # def lines (zero or one for old names — legacy deprecated, none allowed)
        assert f"def {name}(" not in SERVER, f"legacy name still defined: {name}"


def test_no_legacy_dispatcher_keys_in_addon():
    for name in LEGACY_NAMES:
        # exact dispatcher key match: "<name>": self.<name>
        assert f'"{name}"' not in ADDON, f"legacy dispatcher key remains: {name}"
