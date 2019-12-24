import re
import time
import requests
from pyquery import PyQuery as pq

def login():
    login_url = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
        }    
    ses = requests.Session()
    return ses

def get_video_info(ses, url):
    data = ses.get(url).text
    parsed = pq(data)
    title = parsed('h1.title:first').text()
    categories = [c.text() for c in parsed('.categoriesWrapper a').items()]
    tags = [c.text() for c in parsed('.tagsWrapper a').items()]
    return {"page":url, "title":title, "categories":categories, "tags":tags}

def parse_pornhub_url(ses, url, domain):
    result = []
    data = ses.get(url).text
    parsed = pq(data)
    for el in parsed.items('li.videoBox a:first'):
        url = el.attr('href')
        if "view_video" in url:
            if DEBUG:
                print('New video url found: %s' % url)
            result.append("%s%s" % (domain, url))
    return result

def search_videos(ses, query, pages=[2, ], rus=False, DEBUG=False):
    if rus:
        domain = "https://rt.pornhub.com"
        b_url = "https://rt.pornhub.com/video/search?search=%s&p=homemade&page=" % query
    else:
        b_url = "https://www.pornhub.com/video/search?search=%s&p=homemade&page=" % query
        domain = "https://www.pornhub.com"
    result = []
    for p in pages:
        url = b_url + str(p)
        if DEBUG:
            print('Loading: %s' % url)
        new = parse_pornhub_url(ses, url, domain)
        if new:
            result += new
        time.sleep(10) # some user behavior emulation
    return result
    
    
def get_recent_videos(ses, pages=[2, ], rus=False, DEBUG=False):
    """ Function return dict with url, title and url for video download

    Input: requests session,
    list of pages to parse"""
    
    result = []
    if rus:
        domain = "https://rt.pornhub.com"
        b_url = "https://rt.pornhub.com/video?p=homemade&o=mv&t=a&cc=us&hd=1&page="
    else:
        domain = "https://www.pornhub.com"
        b_url = "https://www.pornhub.com/video?p=homemade&o=mv&cc=us&page="
                      
    for p in pages:
        url = b_url + str(p)
        if DEBUG:
            print('Loading: %s' % url)
        new = parse_pornhub_url(ses, url, domain)
        if new:
            result += new
        time.sleep(10) # some user behavior emulation
    return result

if __name__ == "__main__":
    ses = login()
    # example usage:
    for v in search_videos(ses, 'blowjob', DEBUG=True)[:5]:
        print("Video:", v)
        print (get_video_info(ses, v))
        time.sleep(5)

    for v in get_recent_videos(ses, DEBUG=True)[:5]:
        print("Video:", v)
        print (get_video_info(ses, v))
        time.sleep(5)
