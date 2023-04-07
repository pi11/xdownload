import re
import time
import requests
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from urllib.parse import quote

try:
    from webscrapper.client import get_page
except ModuleNotFoundError:  # no webscrapper used
    print("Warning not webscrapper module")
    print("You can install it with:")
    print("pip install webscrapper")
    pass


def login():
    login_url = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:103.0) Gecko/20100101 Firefox/103.0",
        "Referer": "https://www.pornhub.com/",
        "Accept-encoding": "gzip, deflate",
    }
    ses = requests.Session()
    ses.cookies.clear()
    ses.headers.update(headers)
    return ses


def load_ph_page(url, ses, tries, scrapper_key=None):
    """Loading PH page using webscrapper or internal session"""
    retries = 0
    data = False
    while not data and retries <= tries:
        if scrapper_key:
            print("Using Scrapper API\n")
            result = get_page(url, api_key=scrapper_key)

            if result["error"]:
                data = False
            else:
                data = result["html"]
        else:
            try:
                r = ses.get(
                    url, cookies={"age_verified": 1, "accessAgeDisclaimerPH": 1}
                )
                data = r.text
            except ConnectionError:
                retries += 1
                print("Connection error, sleeping for %s seconds" % (timeout * retries))
                time.sleep(timeout * retries)
    return data


def get_video_info(ses, url, tries=3, timeout=5, scrapper_key=None):
    url += "&utm_source=twitter"
    data = load_ph_page(url, ses, tries, scrapper_key)
    parsed = pq(data)
    title = parsed("h1.title:first").text()
    categories = [c.text() for c in parsed(".categoriesWrapper a").items()]
    pornstars = [c.text() for c in parsed(".pornstarsWrapper a.pstar-list-btn").items()]
    tags = [c.text() for c in parsed(".tagsWrapper a").items()]
    return {
        "page": url,
        "title": title,
        "categories": categories,
        "tags": tags,
        "pornstars": pornstars,
    }


def parse_pornhub_url(
    ses, url, domain, DEBUG=False, tries=3, timeout=5, scrapper_key=False
):
    """If scrapper key is provided used webscrapper api"""
    result = []
    data = load_ph_page(url, ses, tries, scrapper_key)
    parsed = pq(data)
    items = parsed.items("li.videoBox a:first")
    i = 0
    for el in items:
        i += 1
        url = el.attr("href")
        if "view_video" in url:
            if DEBUG:
                print("New video url found: %s" % url)
            result.append("%s%s" % (domain, url))
    if i == 0:  # no result
        print("Something wrong, here is data:")
        print(data)

    return result


def search_videos(
    ses,
    query,
    pages=[
        2,
    ],
    rus=False,
    recent=False,
    DEBUG=False,
    scrapper_key=None,
):
    if recent:
        recent_query = "&o=mr"
    else:
        recent_query = ""

    if rus:
        www_domain = "rt"
    else:
        www_domain = "www"

    domain = "https://%s.pornhub.com" % www_domain
    b_url = ("https://%s.pornhub.com/video/search?search=" "%s%s&p=homemade&page=") % (
        www_domain,
        quote(query),
        recent_query,
    )
    result = []
    for p in pages:
        url = b_url + str(p)
        if DEBUG:
            print("Loading: %s" % url)
        new = parse_pornhub_url(ses, url, domain, scrapper_key=scrapper_key)
        if new:
            result += new
        time.sleep(10)  # some user behavior emulation
    return result


def get_recent_videos(
    ses,
    pages=[
        2,
    ],
    rus=False,
    DEBUG=False,
    scrapper_key=None,
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
        new = parse_pornhub_url(ses, url, domain, scrapper_key)
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
    scrapper_key=None,
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
        new = parse_pornhub_url(ses, url, domain, scrapper_key)
        if new:
            result += new
        time.sleep(10)  # some user behavior emulation
    return result


if __name__ == "__main__":
    ses = login()
    # example usage:
    for v in search_videos(ses, "blowjob and anal", DEBUG=True)[:5]:
        print("Video:", v)
        print(get_video_info(ses, v))
        time.sleep(5)

    for v in get_recent_videos(ses, DEBUG=True)[:5]:
        print("Video:", v)
        print(get_video_info(ses, v))
        time.sleep(5)
