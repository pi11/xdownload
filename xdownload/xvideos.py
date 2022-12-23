import re
import time
import html
import requests
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from urllib.parse import quote


def login():
    login_url = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
    }
    ses = requests.Session()
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
    title = html.unescape(parsed('meta[property="og:title"]:first').attr("content"))
    tags_list = parsed("div.video-metadata:first ul li").items()
    tags = []
    for t in tags_list:
        if t.text().strip() != "+":
            tags.append(t.text().strip().lower())
    categories = []
    pornstars = []
    return {
        "page": url,
        "title": title,
        "categories": categories,
        "tags": tags,
        "pornstars": pornstars,
    }


def parse_xvideos_url(ses, url, domain, DEBUG=False, tries=3, timeout=5):
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
    for el in parsed.items("div.thumb a:first"):
        url = el.attr("href")
        if "/video" in url:
            if DEBUG:
                print("New video url found: %s" % url)
            result.append("%s%s" % (domain, url))
    return result


def search_videos(
    ses,
    query,
    pages=[1, 2],
    DEBUG=False,
):
    domain = "https://www.xvideos.com"
    result = []
    for p in pages:
        url = f"{domain}?k={query}&p={p}&datef=6month&sort=rating"
        if DEBUG:
            print(f"Loading: {url}")
        new = parse_xvideos_url(ses, url, domain)
        if new:
            result += new
        time.sleep(4)  # some user behavior emulation
    return result


def get_recent_videos(
    ses,
    pages=[
        2,
    ],
    rus=False,
    DEBUG=False,
):
    """Function return dict with url, title and url for video download

    Input: requests session,
    list of pages to parse"""

    result = []
    if rus:
        domain = "https://rt.pornhub.com"
        b_url = "https://rt.pornhub.com/video?p=homemade&o=mv&t=a&cc=ru&hd=1&page="
    else:
        domain = "https://www.pornhub.com"
        b_url = "https://www.pornhub.com/video?p=homemade&o=mv&cc=ru&page="

    for p in pages:
        url = b_url + str(p)
        if DEBUG:
            print("Loading: %s" % url)
        new = parse_pornhub_url(ses, url, domain)
        if new:
            result += new
        time.sleep(10)  # some user behavior emulation
    return result


def get_hot_videos(
    ses,
    pages=[
        2,
    ],
    hm=True,
    country=False,
    DEBUG=False,
    mv=False,
):
    """Function return dict with url, title and url for video download"""

    result = []
    domain = "https://www.pornhub.com"
    if mv:
        b_url = "%s/video?o=mv" % domain  # top videos
    else:
        b_url = "%s/video?o=ht" % domain  # top videos
    if hm:
        b_url = "%s&p=homemade" % b_url
    if country:
        b_url = "%s&cc=%s" % (b_url, country)
    b_url = "%s&page=" % b_url
    for p in pages:
        url = b_url + str(p)
        if DEBUG:
            print("Loading: %s" % url)
        new = parse_pornhub_url(ses, url, domain)
        if new:
            result += new
        time.sleep(10)  # some user behavior emulation
    return result


if __name__ == "__main__":
    ses = login()
    # example usage:
    #for v in search_videos(ses, "blowjob and anal", DEBUG=True):
    #    print("Video:", v)
    #    print(get_video_info(ses, v))
    #    time.sleep(5)

    # for v in get_recent_videos(ses, DEBUG=True)[:5]:
    #    print("Video:", v)
    #    print (get_video_info(ses, v))
    #    time.sleep(5)

    # print(get_video_info(ses, url='https://www.xvideos.com/video23666982/lesbian_sorority_sisters_try_to_get_in'))
