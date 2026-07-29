from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import pytest
import requests

from xdownload import sexstudentki


def response(text, status_code=200):
    result = SimpleNamespace(text=text, status_code=status_code)
    result.raise_for_status = Mock()
    if status_code >= 400:
        result.raise_for_status.side_effect = requests.HTTPError(str(status_code))
    return result


def test_login_configures_session_and_optional_proxy():
    proxy = {"https": "socks5://localhost:1080"}

    session = sexstudentki.login(proxy)

    assert session.verify is False
    assert session.proxies == proxy
    assert session.headers["Referer"] == sexstudentki._DOMAIN


def test_get_video_info_extracts_metadata_and_normalizes_poster_url():
    html = """
        <html>
          <head><title>Example video</title></head>
          <body>
            <div class="tags-alt"><a>First</a><a>Second</a></div>
            <video poster="/images/poster.jpg">
              <source src="/media/video.mp4">
            </video>
          </body>
        </html>
    """
    session = Mock()
    session.get.return_value = response(html)
    page_url = sexstudentki._DOMAIN + "/video/example"

    info = sexstudentki.get_video_info(session, page_url, timeout=7)

    session.get.assert_called_once_with(page_url, timeout=7)
    assert info == {
        "page": page_url,
        "title": "Example video",
        "tags": ["First", "Second"],
        "description": "",
        "mp4": "/media/video.mp4",
        "poster": sexstudentki._DOMAIN + "/images/poster.jpg",
    }


def test_get_video_info_retries_request_failures():
    html = '<title>Recovered</title><video poster=""><source src="video.mp4"></video>'
    session = Mock()
    session.get.side_effect = [
        requests.ConnectionError("temporary failure"),
        response(html),
    ]

    with patch.object(sexstudentki.time, "sleep") as sleep:
        info = sexstudentki.get_video_info(session, "https://example.test/v", timeout=4)

    assert info["title"] == "Recovered"
    assert session.get.call_count == 2
    sleep.assert_called_once_with(4)


def test_get_video_info_raises_after_all_attempts_fail():
    session = Mock()
    session.get.side_effect = requests.Timeout("offline")

    with (
        patch.object(sexstudentki.time, "sleep") as sleep,
        pytest.raises(RuntimeError, match="All retries failed"),
    ):
        sexstudentki.get_video_info(session, "https://example.test/v", tries=2, timeout=3)

    assert session.get.call_count == 2
    assert sleep.call_args_list == [call(3), call(6)]


def test_parse_url_keeps_video_links_and_resolves_relative_urls():
    html = """
        <div class="videos-page">
          <div class="video"><a href="/video/relative">Relative</a></div>
          <div class="video"><a href="https://cdn.test/video/absolute">Absolute</a></div>
          <div class="video"><a href="/category/not-a-video">Category</a></div>
        </div>
    """
    session = Mock()
    session.get.return_value = response(html)

    urls = sexstudentki.parse_url(
        session, "https://example.test/list", "https://example.test"
    )

    assert urls == [
        "https://example.test/video/relative",
        "https://cdn.test/video/absolute",
    ]


def test_get_recent_videos_uses_homepage_for_page_zero_and_skips_real_sleep():
    session = Mock()

    with (
        patch.object(
            sexstudentki,
            "parse_url",
            side_effect=[["https://video/zero"], ["https://video/two"]],
        ) as parse,
        patch.object(sexstudentki.time, "sleep") as sleep,
    ):
        urls = sexstudentki.get_recent_videos(session, pages=[0, 2])

    assert urls == ["https://video/zero", "https://video/two"]
    assert parse.call_args_list == [
        call(session, sexstudentki._DOMAIN, sexstudentki._DOMAIN),
        call(
            session,
            sexstudentki._DOMAIN + "/videos?page=2",
            sexstudentki._DOMAIN,
        ),
    ]
    assert sleep.call_args_list == [call(10), call(10)]
