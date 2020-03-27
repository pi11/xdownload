import re
import time
import requests
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from urllib.parse import quote

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
    title = parsed('h1.heading2:first').text()
    categories = [] #[c.text() for c in parsed('.categoriesWrapper a').items()]
    pornstars = [] #[c.text() for c in parsed('.pornstarsWrapper a.pstar-list-btn').items()]
    tags = [c.text() for c in parsed('.sizeWrapper a.button').items()]
    return {"page":url, "title":title, "categories":categories, "tags":tags,
            "pornstars":pornstars}

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
    for el in parsed.items('div.video-box a.video-box-image:first'):
        url = el.attr('href')
        if "watch" in url:
            if DEBUG:
                print('New video url found: %s' % url)
            result.append("%s%s" % (domain, url))
    return result

def search_videos(ses, query, pages=[2, ], rus=False, DEBUG=False):
    domain = "https://www.youporn.com"
    b_url = "https://www.youporn.com/search/?query=%s&page=" % quote(query)
    result = []
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
    # example usage:
    for v in search_videos(ses, 'blowjob and anal', DEBUG=True)[:5]:
        print("Video:", v)
        print (get_video_info(ses, v))
        time.sleep(5)
