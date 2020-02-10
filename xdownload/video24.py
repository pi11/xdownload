import re
import time
import requests
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from urllib.parse import quote

_DOMAIN = "https://www.24video.vip"

def login():
    login_url = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
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
    title = parsed('h1.video-title:first').text()
    tags = [c.text() for c in parsed('p.video-info-tags a').items()]
    desc = parsed('p.desc').text()
    return {"page":url, "title":title, "tags":tags, "description":desc}

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
    for el in parsed.items('.list a.list-item'):
        url = el.attr('href')
        print(url)
        if "video/view" in url:
            if DEBUG:
                print('New video url found: %s' % url)
            result.append("%s%s" % (domain, url))
    return result

    
def get_recent_videos(ses, pages=[1, ], rus=False, DEBUG=False):
    """ Function return dict with url, title and url for video download

    Input: requests session,
    list of pages to parse"""
    
    result = []
    domain = _DOMAIN 
    b_url = "%s/video/filter?sort=3&time=0&page=" % domain
                      
    for p in pages:
        url = b_url + str(p)
        if DEBUG:
            print('Loading: %s' % url)
        new = parse_url(ses, url, domain)
        if new:
            result += new
        time.sleep(10) # some user behavior emulation
    return result

if __name__ == "__main__":
    ses = login()
    #v = get_video_info(ses, 'https://www.24video.vip/video/view/2706767')
    #print(v)
    # example usage:
    #for v in search_videos(ses, 'blowjob and anal', DEBUG=True)[:5]:
    #    print("Video:", v)
    #    print (get_video_info(ses, v))
    #    time.sleep(5)

    for v in get_recent_videos(ses, DEBUG=True)[:5]:
        print("Video:", v)
        print (get_video_info(ses, v))
        time.sleep(5)
