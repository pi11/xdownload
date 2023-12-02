import re
import time
import requests
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from urllib.parse import quote, urljoin

_DOMAIN = "https://ru.sex-studentki.guru/"


def login(proxies={}):
    login_url = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
    }
    ses = requests.Session()
    ses.proxies = proxies
    return ses


def get_video_info(ses, url, tries=3, timeout=5):
    retries = 1
    data = False
    while not data and retries <= tries:
        try:
            data = ses.get(url).text
        except ConnectionError:
            retries += 1
            print("Connection error, sleeping for %s seconds" % (timeout * retries))
            time.sleep(timeout * retries)

    data = ses.get(url).text
    parsed = pq(data)
    parsed.make_links_absolute(_DOMAIN)
    title = parsed("title").text()
    tags = [c.text() for c in parsed(".tags-alt a").items()]
    desc = ""  # parsed("p.desc").text()
    # embed_url = parsed('meta[property="og:video"]').attr("content")
    mp4 = parsed("video:first source:first").attr("src")
    if not mp4:
        print("No video found!")
        print(data)
        # sys.exit()
    poster = urljoin(_DOMAIN, parsed("video:first").attr("poster"))

    return {
        "page": url,
        "title": title,
        "tags": tags,
        "description": desc,
        "mp4": mp4,
        "poster": poster,
    }


def parse_url(ses, url, domain, DEBUG=False, tries=3, timeout=5):
    result = []
    retries = 1
    data = False
    while not data and retries <= tries:
        try:
            data = ses.get(url).text
        except ConnectionError:
            retries += 1
            print("Connection error, sleeping for %s seconds" % (timeout * retries))
            time.sleep(timeout * retries)

    parsed = pq(data)
    for el in parsed.items(".videos-page .video a"):
        url = el.attr("href")
        # print("Url:", url)
        if "/video/" in url:
            if DEBUG:
                print("New video url found: %s" % url)
            r_url = urljoin(domain, url)
            result.append(r_url)
    return result


def get_recent_videos(
    ses,
    pages=[
        1,
    ],
    rus=False,
    DEBUG=False,
):
    """Function return dict with url, title and url for video download

    Input: requests session,
    list of pages to parse"""

    result = []
    domain = _DOMAIN
    b_url = "%s/videos?page=" % domain

    for p in pages:
        url = b_url + str(p)
        if DEBUG:
            print("Loading: %s" % url)
        new = parse_url(ses, url, domain)
        if new:
            result += new
        time.sleep(10)  # some user behavior emulation
    return result


if __name__ == "__main__":
    ses = login()
    # v = get_video_info(ses, 'https://www.24video.vip/video/view/2706767')
    # print(v)
    # example usage:
    # for v in search_videos(ses, 'blowjob and anal', DEBUG=True)[:5]:
    #    print("Video:", v)
    #    print (get_video_info(ses, v))
    #    time.sleep(5)

    for v in get_recent_videos(ses, DEBUG=True)[:5]:
        print("Video:", v)
        print(get_video_info(ses, v))
        time.sleep(5)
