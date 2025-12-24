# tests/test_whoami.py
from src.cloudflare_updater.check_ip import get_ip


def test_get_current_ip_success(mocker):
    """Test ip_get logic"""
    mock_resp = mocker.Mock()
    mock_resp.text = "RemoteAddr: 123.123.123.123:12345"
    mock_resp.raise_for_status = lambda: None

    mocker.patch("requests.get", return_value=mock_resp)

    ip = get_ip(["http://fake-url"])
    assert ip == "123.123.123.123"
