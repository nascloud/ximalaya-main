import pytest
import requests
from unittest.mock import patch, MagicMock
from fetcher.track_fetcher import fetch_track_crypted_url, fetch_album_tracks, BlockedException, Track
from fetcher.album_fetcher import fetch_album, Album
import os

# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {"XIMALAYA_COOKIES": "test_cookie"}):
        yield

# Test cases for fetch_track_crypted_url
def test_fetch_track_crypted_url_success():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ret": 0,
            "trackInfo": {
                "playUrlList": [{"url": "http://crypted.url/test"}]
            }
        }
        mock_get.return_value = mock_response
        
        url = fetch_track_crypted_url(123, 456)
        assert url == "http://crypted.url/test"
        mock_get.assert_called_once_with(
            "https://www.ximalaya.com/mobile-playpage/track/v3/baseInfo/456",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Cookie": "test_cookie"
            },
            params={"device": "web", "trackId": 123, "trackQualityLevel": 1}
        )

def test_fetch_track_crypted_url_blocked_ret_1001():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ret": 1001, "msg": "系统繁忙"}
        mock_get.return_value = mock_response
        
        with pytest.raises(BlockedException, match="系统繁忙，风控触发"):
            fetch_track_crypted_url(123, 456)

def test_fetch_track_crypted_url_blocked_msg():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ret": 0, "msg": "系统繁忙"}
        mock_get.return_value = mock_response
        
        with pytest.raises(BlockedException, match="系统繁忙，风控触发"):
            fetch_track_crypted_url(123, 456)

def test_fetch_track_crypted_url_no_play_url():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ret": 0,
            "trackInfo": {"playUrlList": []}
        }
        mock_get.return_value = mock_response
        
        url = fetch_track_crypted_url(123, 456)
        assert url == ""

def test_fetch_track_crypted_url_http_error():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        url = fetch_track_crypted_url(123, 456)
        assert url == ""

# Test cases for fetch_album_tracks
@patch("fetcher.track_fetcher.fetch_track_crypted_url")
@patch("requests.get")
@patch("utils.utils.decrypt_url")
def test_fetch_album_tracks_success(mock_decrypt_url, mock_requests_get, mock_fetch_crypted_url):
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {
        "data": {
            "trackDetailInfos": [
                {"trackInfo": {"id": 1, "title": "Track 1", "createdTime": "t1", "updatedTime": "u1", "duration": 100, "cover": "cover1"}},
                {"trackInfo": {"id": 2, "title": "Track 2", "createdTime": "t2", "updatedTime": "u2", "duration": 200, "cover": "cover2"}}
            ],
            "totalCount": 2
        }
    }
    mock_fetch_crypted_url.side_effect = ["crypted_url_1", "crypted_url_2"]
    mock_decrypt_url.side_effect = ["decrypted_url_1", "decrypted_url_2"]

    tracks = fetch_album_tracks(789, 1, 2)
    assert len(tracks) == 2
    assert tracks[0].trackId == 1
    assert tracks[0].title == "Track 1"
    assert tracks[0].url == "decrypted_url_1"
    assert tracks[0].cover == "https://imagev2.xmcdn.com/cover1"
    assert tracks[1].trackId == 2
    assert tracks[1].title == "Track 2"
    assert tracks[1].url == "decrypted_url_2"
    assert tracks[1].cover == "https://imagev2.xmcdn.com/cover2"
    assert tracks[0].totalCount == 2
    assert tracks[0].page == 1
    assert tracks[0].pageSize == 2

@patch("fetcher.track_fetcher.fetch_track_crypted_url")
@patch("requests.get")
def test_fetch_album_tracks_crypted_url_blocked(mock_requests_get, mock_fetch_crypted_url):
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {
        "data": {
            "trackDetailInfos": [
                {"trackInfo": {"id": 1, "title": "Track 1", "createdTime": "t1", "updatedTime": "u1", "duration": 100, "cover": "cover1"}}
            ],
            "totalCount": 1
        }
    }
    mock_fetch_crypted_url.side_effect = BlockedException("风控触发")

    with pytest.raises(BlockedException):
        fetch_album_tracks(789, 1, 1)

@patch("fetcher.track_fetcher.fetch_track_crypted_url")
@patch("requests.get")
def test_fetch_album_tracks_no_crypted_url(mock_requests_get, mock_fetch_crypted_url):
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {
        "data": {
            "trackDetailInfos": [
                {"trackInfo": {"id": 1, "title": "Track 1", "createdTime": "t1", "updatedTime": "u1", "duration": 100, "cover": "cover1"}}
            ],
            "totalCount": 1
        }
    }
    mock_fetch_crypted_url.return_value = "" # Simulate no crypted URL

    tracks = fetch_album_tracks(789, 1, 1)
    assert len(tracks) == 0 # Should skip the track

@patch("requests.get")
def test_fetch_album_tracks_http_error(mock_requests_get):
    mock_requests_get.return_value.status_code = 500
    mock_requests_get.return_value.text = "Internal Server Error"

    tracks = fetch_album_tracks(789, 1, 1)
    assert len(tracks) == 0

# Test cases for fetch_album
def test_fetch_album_success():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "albumPageMainInfo": {
                    "albumTitle": "Test Album",
                    "cover": "//imagev2.xmcdn.com/group1/M0A/B1/C2/wKgADFj_z_jQ.jpg",
                    "createDate": "2023-01-01",
                    "updateDate": "2023-01-02",
                    "richIntro": "Intro"
                }
            }
        }
        mock_get.return_value = mock_response

        album = fetch_album(123)
        assert album is not None
        assert album.albumId == 123
        assert album.albumTitle == "Test Album"
        assert album.cover == "https://imagev2.xmcdn.com/group1/M0A/B1/C2/wKgADFj_z_jQ.jpg"
        assert album.createDate == "2023-01-01"
        assert album.updateDate == "2023-01-02"
        assert album.richIntro == "Intro"
        assert album.tracks == []

def test_fetch_album_http_error():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_get.return_value = mock_response

        album = fetch_album(123)
        assert album is None

def test_fetch_album_exception():
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Network Error")

        album = fetch_album(123)
        assert album is None