from app.utilities.env_loaders import (
    get_cloudflare_api_token,
    get_whoami_urls,
)

# ---------------------------------------------------------
# Tests for get_cloudflare_api_token()
# ---------------------------------------------------------


def test_get_cloudflare_api_token_valid(mocker, monkeypatch):
    """Valid token → returns (True, token)"""

    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "valid-token")

    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {"success": True}

    mocker.patch("app.utilities.env_loaders.requests.get", return_value=mock_resp)

    ok, token = get_cloudflare_api_token()
    assert ok is True
    assert token == "valid-token"


def test_get_cloudflare_api_token_invalid(mocker, monkeypatch, caplog):
    """Cloudflare returns success=False → returns (False, None)"""

    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "bad-token")

    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {"success": False, "errors": ["bad token"]}

    mocker.patch("app.utilities.env_loaders.requests.get", return_value=mock_resp)

    ok, token = get_cloudflare_api_token()
    assert ok is False
    assert token is None

    # Optional: verify logging
    assert "invalid" in caplog.text.lower()


def test_get_cloudflare_api_token_missing(monkeypatch, caplog):
    """No env var → returns (False, None)"""

    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)

    ok, token = get_cloudflare_api_token()
    assert ok is False
    assert token is None
    assert "not set" in caplog.text.lower()


# ---------------------------------------------------------
# Tests for get_whoami_urls()
# ---------------------------------------------------------


def test_get_whoami_urls_default(monkeypatch):
    """No WHOAMI_URLS → fallback URL is added"""

    monkeypatch.delenv("WHOAMI_URLS", raising=False)
    monkeypatch.setenv("OVERRIDE_OBSOLETE_WHOAMI", "false")

    ok, urls = get_whoami_urls()
    assert ok is True
    assert "http://whoami.obsoletelabs.org:12345/" in urls


def test_get_whoami_urls_override(monkeypatch):
    """Override disables fallback URL"""

    monkeypatch.setenv("WHOAMI_URLS", "http://example.com")
    monkeypatch.setenv("OVERRIDE_OBSOLETE_WHOAMI", "true")

    ok, urls = get_whoami_urls()
    assert ok is True
    assert "http://whoami.obsoletelabs.org:12345/" not in urls
    assert urls == ["http://example.com"]


def test_get_whoami_urls_invalid_removed(monkeypatch, caplog):
    """Invalid URLs should be removed"""

    monkeypatch.setenv("WHOAMI_URLS", "http://good.com,not-a-url,https://ok.com")
    monkeypatch.setenv("OVERRIDE_OBSOLETE_WHOAMI", "true")

    ok, urls = get_whoami_urls()
    assert ok is True
    assert "http://good.com" in urls
    assert "https://ok.com" in urls
    assert "not-a-url" not in urls

    assert "invalid" in caplog.text.lower()


def test_get_whoami_urls_empty_and_no_fallback(monkeypatch, caplog):
    """Empty WHOAMI_URLS + fallback disabled → error"""

    monkeypatch.setenv("WHOAMI_URLS", "")
    monkeypatch.setenv("OVERRIDE_OBSOLETE_WHOAMI", "true")

    ok, urls = get_whoami_urls()
    assert ok is False
    assert urls is None
    assert "empty" in caplog.text.lower()
