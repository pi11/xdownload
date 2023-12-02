import re
import time
import requests
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from urllib.parse import quote, urljoin

_DOMAIN = "https://24video.promo"
# _DOMAIN = "https://ebl.spreee.pro/"


def login(proxies={}):
    login_url = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/116.0",
        "Referer": "https://www.google.ru/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
    }
    ses = requests.Session()
    ses.headers.update(headers)
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

    # data = ses.get(url).text
    parsed = pq(data)
    embed_url = parsed('meta[property="og:video"]').attr("content")
    if not embed_url:
        print("Embed url is none, skiping")
        time.sleep(3)
        return False
    title = parsed("h1.video-title:first").text()
    tags = [c.text() for c in parsed("p.video-info-tags a").items()]
    desc = parsed("p.desc").text()
    print("Downloading embed url: %s" % embed_url)
    data_embed = False
    retries = 0
    while not data_embed and retries < tries:
        try:
            data_embed = ses.get(embed_url).text
        except ConnectionError:
            retries += 1
            time.sleep(timeout * retries)
            
    p2 = pq(data_embed)
    # mp4 = p2("video.fp-engine").attr("src")
    poster = parsed('meta[property="og:image"]').attr("content")

    mp4_url_re = re.compile(r"video_url: '(.*?)',")
    mp4 = mp4_url_re.findall(data_embed)[0]
    print(f"Mp4: {mp4}")
    if not mp4:
        print("No video found!")
        print(data_embed)

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
    for el in parsed.items("a.list-item"):
        url = el.attr("href")
        print(url)
        if "video/view" in url:
            if DEBUG:
                print("New video url found: %s" % url)
            r_url = urljoin(domain, url)
            result.append(r_url)
    # print(data)
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

    for p in pages:
        url = f"{domain}/video/filter?page={p}&sort_by=rating"

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
