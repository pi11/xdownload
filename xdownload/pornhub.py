import re
import time
import requests
from pyquery import PyQuery as pq

def login():
    login_url = "https://www.tube8.com/signin.html"
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
    
def get_recent_videos(ses, pages=[2, ], rus=False):
    """ Function return dict with url, title and url for video download

    Input: requests session,
    list of pages to parse"""
    
    result = []
    for p in pages:
        if rus:
            domain = "https://rt.pornhub.com"
            url = "https://rt.pornhub.com/video?p=homemade&o=mv&t=a&cc=us&hd=1&page="
        else:
            domain = "https://www.pornhub.com"
            url = "https://www.pornhub.com/video?o=mv&cc=us&page="
        data = ses.get('%s%s' % (url, p)).text
        parsed = pq(data)
        for el in parsed.items('li.videoBox a:first'):
            url = el.attr('href')
            result.append("%s%s" % (domain, url))
        time.sleep(10)
    return result

if __name__ == "__main__":
    ses = login()
    for v in get_recent_videos(ses):
        #print(v)
        print (get_video_info(ses, v))
