"""HTTP 래퍼 retry/cache 동작 검증."""

from unittest.mock import MagicMock, patch

import requests

from src.marketed_drugs._http import fetch_json, get_session


def test_fetch_json_returns_parsed_response():
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"hello": "world"}
    mock_resp.raise_for_status = MagicMock()

    with patch("src.marketed_drugs._http.get_session") as mock_session:
        session = MagicMock()
        session.get.return_value = mock_resp
        mock_session.return_value = session

        result = fetch_json("http://example.com/api")

    assert result == {"hello": "world"}


def test_fetch_json_retries_on_5xx():
    mock_500 = MagicMock(spec=requests.Response)
    mock_500.status_code = 500
    mock_500.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

    mock_200 = MagicMock(spec=requests.Response)
    mock_200.status_code = 200
    mock_200.json.return_value = {"ok": True}
    mock_200.raise_for_status = MagicMock()

    with patch("src.marketed_drugs._http.get_session") as mock_session:
        session = MagicMock()
        session.get.side_effect = [mock_500, mock_200]
        mock_session.return_value = session

        result = fetch_json("http://example.com/api")

    assert result == {"ok": True}
    assert session.get.call_count == 2


def test_get_session_returns_cached_session():
    s1 = get_session()
    s2 = get_session()
    assert s1 is s2
