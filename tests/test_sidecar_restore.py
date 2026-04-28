"""Sidecar credential restore tests (v2.0.1 polish).

Regression coverage for the bug where ``openai_base_url`` had a
non-empty schema default (``https://api.openai.com/v1``), so the
"only restore if live is empty" guard in ``_load_credentials_from_sidecar``
silently skipped it after every addon reload — the user's saved Comfly
URL was being overwritten by the schema default on every Blender restart.

These tests don't mock all of bpy — they import addon.py (which
conftest.py already lets us load with a mock bpy), then test the
behavior of ``_load_credentials_from_sidecar`` against a synthetic
prefs object using monkeypatch.
"""
import json
import os
import sys
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def fake_prefs():
    """Stand-in for AddonPreferences. Plain object that getattr/setattr
    against — no Blender machinery."""
    class FakePrefs:
        # Match the schema defaults from BLENDERMCP_AddonPreferences:
        # passwords default to ""; openai_base_url defaults to OpenAI.
        sketchfab_api_key = ""
        hyper3d_api_key = ""
        tripo3d_api_key = ""
        meshy_api_key = ""
        openai_api_key = ""
        openai_base_url = "https://api.openai.com/v1"
        hunyuan3d_secret_id = ""
        hunyuan3d_secret_key = ""
        hunyuan3d_api_url = ""
    return FakePrefs()


@pytest.fixture
def addon_module(monkeypatch, tmp_path, fake_prefs):
    """Import addon.py and route its sidecar path to a temp file +
    its prefs lookup to fake_prefs."""
    # addon.py is at the repo root; ensure that's on sys.path
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    # Force a clean import each test so monkeypatch settings don't leak
    if "addon" in sys.modules:
        del sys.modules["addon"]
    import addon

    # Redirect sidecar to a temp path
    sidecar = tmp_path / "creds.json"
    monkeypatch.setattr(addon, "_BLENDERMCP_CRED_SIDECAR", str(sidecar))

    # Make bpy.context.preferences.addons.get(__name__) return a thing
    # that has .preferences = fake_prefs.
    fake_addon_entry = MagicMock()
    fake_addon_entry.preferences = fake_prefs
    addons_collection = MagicMock()
    addons_collection.get.return_value = fake_addon_entry
    addon.bpy.context.preferences.addons = addons_collection

    return addon, fake_prefs, sidecar


# ----- Bug repro + fix coverage -----

def test_openai_base_url_in_always_restore_set(addon_module):
    """Sanity: the field is in the unconditional-restore allowlist."""
    addon, _, _ = addon_module
    assert "openai_base_url" in addon._SIDECAR_ALWAYS_RESTORE


def test_sidecar_restores_comfly_base_url_over_default(addon_module):
    """The whole point: sidecar has Comfly URL, prefs has default OpenAI
    URL; restore must replace default with Comfly."""
    addon, prefs, sidecar = addon_module
    sidecar.write_text(json.dumps({
        "openai_api_key": "sk-test-not-real-just-shape",
        "openai_base_url": "https://ai.comfly.chat/v1",
    }))
    assert prefs.openai_base_url == "https://api.openai.com/v1"  # initial default

    addon._load_credentials_from_sidecar()

    assert prefs.openai_base_url == "https://ai.comfly.chat/v1"
    assert prefs.openai_api_key == "sk-test-not-real-just-shape"


def test_sidecar_does_not_overwrite_user_set_password_field(addon_module):
    """For password fields (default = ''), if the user has already typed
    a key in this session and the sidecar holds an older one, keep the
    user's typed value — sidecar only fills in when live is empty."""
    addon, prefs, sidecar = addon_module
    prefs.tripo3d_api_key = "user-just-typed-this"

    sidecar.write_text(json.dumps({
        "tripo3d_api_key": "stale-key-from-yesterday",
    }))

    addon._load_credentials_from_sidecar()

    assert prefs.tripo3d_api_key == "user-just-typed-this"


def test_sidecar_fills_empty_password_field(addon_module):
    """If the password field is empty (e.g. userpref.blend lost it),
    sidecar fills it back in — that's the original sidecar contract."""
    addon, prefs, sidecar = addon_module
    sidecar.write_text(json.dumps({
        "tripo3d_api_key": "tk_test",
    }))

    addon._load_credentials_from_sidecar()

    assert prefs.tripo3d_api_key == "tk_test"


def test_sidecar_skips_empty_values(addon_module):
    """Sidecar with empty strings shouldn't clobber prefs."""
    addon, prefs, sidecar = addon_module
    prefs.tripo3d_api_key = "preserved"
    sidecar.write_text(json.dumps({
        "tripo3d_api_key": "",
        "openai_base_url": "",
    }))

    addon._load_credentials_from_sidecar()

    assert prefs.tripo3d_api_key == "preserved"
    # openai_base_url default stays put
    assert prefs.openai_base_url == "https://api.openai.com/v1"


def test_sidecar_missing_file_is_no_op(addon_module):
    """No sidecar file = no restore, no exception."""
    addon, prefs, sidecar = addon_module
    # sidecar fixture creates the path but we haven't written anything;
    # remove it explicitly to simulate first run.
    if sidecar.exists():
        sidecar.unlink()

    addon._load_credentials_from_sidecar()  # must not raise

    assert prefs.openai_base_url == "https://api.openai.com/v1"


def test_sidecar_restores_base_url_even_if_user_set_a_different_one(addon_module):
    """Edge: user already changed base_url to something else this session
    and there's a sidecar value too. Sidecar wins for ALWAYS_RESTORE
    fields — that's the documented semantics; the assumption is sidecar
    is the source of truth across reloads. If users want a different
    URL, they edit the N-panel, which updates the sidecar via
    _persist_credentials before the next reload."""
    addon, prefs, sidecar = addon_module
    prefs.openai_base_url = "https://different.example.com/v1"

    sidecar.write_text(json.dumps({
        "openai_base_url": "https://ai.comfly.chat/v1",
    }))

    addon._load_credentials_from_sidecar()

    # Sidecar wins for openai_base_url because it's in ALWAYS_RESTORE
    assert prefs.openai_base_url == "https://ai.comfly.chat/v1"
