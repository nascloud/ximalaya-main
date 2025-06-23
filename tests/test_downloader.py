import pytest
from unittest.mock import patch, MagicMock, mock_open
import requests
import os
from downloader.downloader import M4ADownloader

# Test cases for M4ADownloader
class TestM4ADownloader:
    @patch("requests.get")
    def test_download_once_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2", b"chunk3"]
        mock_get.return_value = mock_response

        mock_log_func = MagicMock()
        downloader = M4ADownloader()
        
        with patch("builtins.open", mock_open()) as mocked_file:
            result = downloader._download_once("http://test.url/file.m4a", "test_output.m4a", log_func=mock_log_func)
            assert result is True
            mock_get.assert_called_once_with("http://test.url/file.m4a", stream=True, timeout=20)
            mocked_file.assert_called_once_with("test_output.m4a", 'wb')
            mocked_file().write.assert_any_call(b"chunk1")
            mocked_file().write.assert_any_call(b"chunk2")
            mocked_file().write.assert_any_call(b"chunk3")
            assert mock_log_func.call_count >= 2 # For progress and completion

    @patch("requests.get")
    def test_download_once_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        mock_log_func = MagicMock()
        downloader = M4ADownloader()
        
        with pytest.raises(requests.exceptions.HTTPError):
            downloader._download_once("http://test.url/file.m4a", "test_output.m4a", log_func=mock_log_func)

    @patch("downloader.downloader.M4ADownloader._download_once")
    def test_download_m4a_success_first_attempt(self, mock_download_once):
        mock_download_once.return_value = True
        mock_log_func = MagicMock()
        downloader = M4ADownloader()
        result = downloader.download_m4a("http://test.url/file.m4a", "test_output.m4a", log_func=mock_log_func)
        assert result is True
        mock_download_once.assert_called_once()
        mock_log_func.assert_not_called() # No warnings/retries

    @patch("time.sleep", return_value=None)
    @patch("downloader.downloader.M4ADownloader._download_once")
    def test_download_m4a_retries_then_success(self, mock_download_once, mock_sleep):
        mock_download_once.side_effect = [requests.exceptions.RequestException("Error"), True]
        mock_log_func = MagicMock()
        downloader = M4ADownloader(max_retries=2, retry_delay=0)
        result = downloader.download_m4a("http://test.url/file.m4a", "test_output.m4a", log_func=mock_log_func)
        assert result is True
        assert mock_download_once.call_count == 2
        assert mock_log_func.call_count >= 2 # Warning and retry message

    @patch("time.sleep", return_value=None)
    @patch("downloader.downloader.M4ADownloader._download_once")
    def test_download_m4a_all_retries_fail(self, mock_download_once, mock_sleep):
        mock_download_once.side_effect = [requests.exceptions.RequestException("Error")] * 3
        mock_log_func = MagicMock()
        downloader = M4ADownloader(max_retries=3, retry_delay=0)
        result = downloader.download_m4a("http://test.url/file.m4a", "test_output.m4a", log_func=mock_log_func)
        assert result is False
        assert mock_download_once.call_count == 3
        assert mock_log_func.call_count >= 6 # Warnings and retry messages, plus final error

    @patch("fetcher.track_fetcher.fetch_track_crypted_url")
    @patch("utils.utils.decrypt_url")
    def test_get_track_download_url_success(self, mock_decrypt_url, mock_fetch_crypted_url):
        mock_fetch_crypted_url.return_value = "crypted_url"
        mock_decrypt_url.return_value = "decrypted_url"
        downloader = M4ADownloader()
        url = downloader.get_track_download_url(123, 456)
        assert url == "decrypted_url"
        mock_fetch_crypted_url.assert_called_once_with(123, 456)
        mock_decrypt_url.assert_called_once_with("crypted_url")

    @patch("fetcher.track_fetcher.fetch_track_crypted_url")
    @patch("utils.utils.decrypt_url")
    def test_get_track_download_url_no_crypted_url(self, mock_decrypt_url, mock_fetch_crypted_url):
        mock_fetch_crypted_url.return_value = ""
        downloader = M4ADownloader()
        url = downloader.get_track_download_url(123, 456)
        assert url is None
        mock_fetch_crypted_url.assert_called_once_with(123, 456)
        mock_decrypt_url.assert_not_called()

    @patch("fetcher.track_fetcher.fetch_track_crypted_url", side_effect=TypeError)
    @patch("utils.utils.decrypt_url")
    def test_get_track_download_url_type_error_fallback(self, mock_decrypt_url, mock_fetch_crypted_url):
        mock_fetch_crypted_url.side_effect = [TypeError, "crypted_url"] # First call raises TypeError, second returns value
        mock_decrypt_url.return_value = "decrypted_url"
        downloader = M4ADownloader()
        url = downloader.get_track_download_url(123, 456)
        assert url == "decrypted_url"
        assert mock_fetch_crypted_url.call_count == 2 # Called once with album_id, then with 0

    @patch("downloader.downloader.M4ADownloader.download_m4a")
    def test_download_from_url_success(self, mock_download_m4a):
        mock_download_m4a.return_value = True
        mock_log_func = MagicMock()
        downloader = M4ADownloader()
        result = downloader.download_from_url("http://test.url/file.m4a", "test_output.m4a", log_func=mock_log_func)
        assert result is True
        mock_download_m4a.assert_called_once_with("http://test.url/file.m4a", "test_output.m4a", log_func=mock_log_func)
        assert mock_log_func.call_count == 2 # "正在下载" and "下载完成"

    @patch("downloader.downloader.M4ADownloader.get_track_download_url")
    @patch("downloader.downloader.M4ADownloader.download_from_url")
    def test_download_track_by_id_success(self, mock_download_from_url, mock_get_track_download_url):
        mock_get_track_download_url.return_value = "http://download.url/track.m4a"
        mock_log_func = MagicMock()
        downloader = M4ADownloader()
        downloader.download_track_by_id(123, 456, "output.m4a", log_func=mock_log_func)
        mock_get_track_download_url.assert_called_once_with(123, 456)
        mock_download_from_url.assert_called_once_with("http://download.url/track.m4a", "output.m4a", log_func=mock_log_func)
        mock_log_func.assert_not_called() # No error logs

    @patch("downloader.downloader.M4ADownloader.get_track_download_url")
    def test_download_track_by_id_no_url(self, mock_get_track_download_url):
        mock_get_track_download_url.return_value = None
        mock_log_func = MagicMock()
        downloader = M4ADownloader()
        with pytest.raises(Exception, match="未获取到下载URL"):
            downloader.download_track_by_id(123, 456, "output.m4a", log_func=mock_log_func)
        mock_log_func.assert_called_once_with('未获取到下载URL: track_id=123', level='error')