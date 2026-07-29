from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import requests

from xdownload import pornhub


def response(text="", status_code=200):
    return SimpleNamespace(text=text, status_code=status_code)


def test_login_configures_headers_and_age_cookies():
    session = pornhub.login()

    assert session.headers["Referer"] == "https://www.pornhub.com/"
    assert session.cookies["age_verified"] == "1"
    assert session.cookies["accessAgeDisclaimerPH"] == "1"


def test_load_ph_page_retries_connection_errors_without_real_sleep():
    session = Mock()
    session.get.side_effect = [
        requests.ConnectionError("temporary failure"),
        response("<html>ok</html>"),
    ]

    with patch.object(pornhub.time, "sleep") as sleep:
        result = pornhub.load_ph_page(
            "https://example.test/video", session, max_tries=3, timeout=2
        )

    assert result == "<html>ok</html>"
    assert session.get.call_count == 2
    assert session.get.call_args_list == [
        call("https://example.test/video", timeout=2),
        call("https://example.test/video", timeout=2),
    ]
    sleep.assert_called_once_with(2)


def test_get_video_info_extracts_metadata_and_adds_tracking_query():
    html = """
        <h1 class="title">Sample title</h1>
        <div class="categoriesWrapper"><a>Category A</a><a>Category B</a></div>
        <div class="tagsWrapper"><a>Tag A</a></div>
        <div class="pornstarsWrapper"><a class="pstar-list-btn">Performer</a></div>
    """
    session = Mock()

    with patch.object(pornhub, "load_ph_page", return_value=html) as load:
        info = pornhub.get_video_info(
            session, "https://example.test/watch?id=42", scrapper_key="key"
        )

    load.assert_called_once_with(
        "https://example.test/watch?id=42&utm_source=twitter",
        session,
        3,
        "key",
        5,
    )
    assert info == {
        "page": "https://example.test/watch?id=42&utm_source=twitter",
        "title": "Sample title",
        "categories": ["Category A", "Category B"],
        "tags": ["Tag A"],
        "pornstars": ["Performer"],
        "error": None,
    }


def test_get_video_info_returns_structured_error_when_loading_fails():
    with patch.object(pornhub, "load_ph_page", return_value=None):
        info = pornhub.get_video_info(Mock(), "https://example.test/watch")

    assert info["page"] == "https://example.test/watch?utm_source=twitter"
    assert info["error"] == "Failed to load page"
    assert info["title"] is None
    assert info["categories"] == []
    assert info["tags"] == []
    assert info["pornstars"] == []


def test_parse_pornhub_url_normalizes_links_and_filters_non_videos():
    html = """
        <ul>
          <li class="videoBox"><a href="/view_video.php?viewkey=one">One</a></li>
          <li class="videoBox"><a href="view_video.php?viewkey=two">Two</a></li>
          <li class="videoBox"><a href="/channels/example">Channel</a></li>
        </ul>
    """

    with patch.object(pornhub, "load_ph_page", return_value=html):
        urls = pornhub.parse_pornhub_url(
            Mock(), "https://example.test/list", "https://example.test"
        )

    assert urls == [
        "https://example.test/view_video.php?viewkey=one",
        "https://example.test/view_video.php?viewkey=two",
    ]


def test_search_videos_quotes_query_builds_each_page_and_waits_between_pages():
    session = Mock()

    with (
        patch.object(
            pornhub,
            "parse_pornhub_url",
            side_effect=[["https://video/one"], ["https://video/two"]],
        ) as parse,
        patch.object(pornhub.time, "sleep") as sleep,
    ):
        urls = pornhub.search_videos(
            session,
            "two words",
            pages=[1, 2],
            recent=True,
            wait_time=3,
        )

    assert urls == ["https://video/one", "https://video/two"]
    expected_base = (
        "https://www.pornhub.com/video/search?"
        "search=two%20words&o=mr&p=homemade&page="
    )
    assert parse.call_args_list == [
        call(
            session,
            expected_base + "1",
            "https://www.pornhub.com",
            False,
            scrapper_key=None,
        ),
        call(
            session,
            expected_base + "2",
            "https://www.pornhub.com",
            False,
            scrapper_key=None,
        ),
    ]
    sleep.assert_called_once_with(3)
