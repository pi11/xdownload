import re
import time
import requests
import traceback
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from urllib.parse import quote, urljoin

_DOMAIN = "https://sex-studentki.live"


def login(proxies=None):
    # print(proxies)
    # login_url = ""
    ses = requests.Session()
    ses.verify = False
    if proxies:
        print(f"Proxies: {proxies}")
        ses.proxies = proxies

    ses.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
        }
    )
    return ses


def get_video_info(ses, url, tries=3, timeout=15):

    for attempt in range(1, tries + 1):
        try:
            r = ses.get(url, timeout=timeout)
            r.raise_for_status()
            data = r.text
            break
        except RequestException:
            print(f"Request failed, sleeping {timeout * attempt}s")
            print(traceback.format_exc())
            time.sleep(timeout * attempt)
    else:
        raise RuntimeError("All retries failed")

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


def parse_url(ses, url, domain, DEBUG=False, tries=3, timeout=15):
    result = []
    retries = 1
    data = False
    while not data and retries <= tries:
        try:
            data = ses.get(url, timeout=timeout).text
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
        if p == 0:
            url = _DOMAIN

        if DEBUG:
            print("Loading: %s" % url)
        new = parse_url(ses, url, domain)
        if new:
            result += new
        time.sleep(10)  # some user behavior emulation
    return result


if __name__ == "__main__":
    ses = login(
        proxies={
            "http": "http://Y9whdp:XXKUf1@185.111.25.123:8000",
            "https": "http://Y9whdp:XXKUf1@185.111.25.123:8000",
        }
        # proxies={
        # "https": "http://btDGFW:13UrM1@95.181.163.220:9267",
        # "http": "http://btDGFW:13UrM1@95.181.163.220:9267",
        # }
    )
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
