"""Tests that generate_image_openai routes to the configured base_url.

Task 12 (Sprint 5): the addon-side image-generation method must POST to
whatever OpenAI-compatible endpoint the user has configured (Comfly,
OpenRouter, vLLM, OpenAI-direct, ...), not a hardcoded api.openai.com URL.

These tests mock requests.post so no real HTTP is made.
"""
from unittest.mock import patch, MagicMock


def _make_server(base_url):
    """Build a bare BlenderMCPServer instance with just the bits
    generate_image_openai needs — bypassing __init__ avoids touching
    the socket layer / Blender state."""
    from addon import BlenderMCPServer
    s = BlenderMCPServer.__new__(BlenderMCPServer)
    s._get_openai_api_key = lambda: "sk-test"
    s._get_openai_base_url = lambda: base_url
    return s


def _fake_post_capturing(captured):
    def fake_post(url, headers=None, json=None, timeout=None, **kwargs):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = {"data": [{"url": "https://x/y.png",
                                         "revised_prompt": "rev"}]}
        return m
    return fake_post


def test_image_gen_uses_configured_base_url(tmp_path):
    """Mock requests.post to capture the URL it's called with —
    must start with the configured base_url, not api.openai.com."""
    from addon import BlenderMCPServer
    s = _make_server("https://ai.comfly.chat/v1")

    captured = {}
    target_path = str(tmp_path / "out.png")

    with patch("addon.requests.post", side_effect=_fake_post_capturing(captured)), \
         patch("addon._resilient_download_to_file",
               lambda u, p, **kw: open(p, "wb").close()):
        out = BlenderMCPServer.generate_image_openai(
            s, prompt="test", model="dall-e-3", size="1024x1024",
            quality="standard", save_to=target_path,
        )

    assert captured["url"].startswith("https://ai.comfly.chat/v1/"), \
        f"expected Comfly URL, got {captured['url']!r}"
    assert captured["url"].endswith("/images/generations"), \
        f"expected /images/generations suffix, got {captured['url']!r}"
    # Auth header still goes through.
    assert captured["headers"]["Authorization"] == "Bearer sk-test"
    # Returned dict carries the requested save target.
    assert isinstance(out, dict), f"expected dict, got {type(out).__name__}: {out!r}"
    assert "saved_paths" in out, f"missing saved_paths in {out!r}"
    assert any("out.png" in p for p in out["saved_paths"])


def test_image_gen_default_base_url_is_openai(tmp_path):
    """When no override is set, the default endpoint stays api.openai.com
    so the OpenAI-direct path doesn't break."""
    from addon import BlenderMCPServer
    s = _make_server("https://api.openai.com/v1")

    captured = {}
    target_path = str(tmp_path / "out.png")

    with patch("addon.requests.post", side_effect=_fake_post_capturing(captured)), \
         patch("addon._resilient_download_to_file",
               lambda u, p, **kw: open(p, "wb").close()):
        BlenderMCPServer.generate_image_openai(
            s, prompt="test", model="dall-e-3", size="1024x1024",
            quality="standard", save_to=target_path,
        )

    assert captured["url"] == "https://api.openai.com/v1/images/generations"


def test_image_gen_strips_trailing_slash_in_base_url(tmp_path):
    """Users will sometimes paste a base URL with a trailing slash.
    The constructed POST URL must not end up double-slashed."""
    from addon import BlenderMCPServer
    s = _make_server("https://ai.comfly.chat/v1/")

    captured = {}
    target_path = str(tmp_path / "out.png")

    with patch("addon.requests.post", side_effect=_fake_post_capturing(captured)), \
         patch("addon._resilient_download_to_file",
               lambda u, p, **kw: open(p, "wb").close()):
        BlenderMCPServer.generate_image_openai(
            s, prompt="test", model="dall-e-3", size="1024x1024",
            quality="standard", save_to=target_path,
        )

    assert "//images/generations" not in captured["url"], \
        f"double-slash in {captured['url']!r}"
    assert captured["url"] == "https://ai.comfly.chat/v1/images/generations"
