import re
import requests
from pyquery import PyQuery as pq

def login():
    ses = requests.Session()
    return ses

def get_video_info(ses, url):
    print ("Parsing: %s" % url)
    data = ses.get(url).text
    parsed = pq(data)
    mp4_url = parsed('#videoContainer video:first').attr('src')
    poster = parsed('#videoContainer video:first').attr('poster')
    title = parsed('h1#mTitle').text()
    return {"page":url, "mp4":mp4_url, "title":title, "poster":poster}
    
def get_recent_videos(ses, pages=[2, ]):
    """ Function return dict with url, title and url for video download

    Input: requests session,
    list of pages to parse"""
    
    result = []
    for p in pages:
        data = ses.get('https://www.sunporno.com/most-recent/hd/page%s.html' % p).text
        parsed = pq(data)
        for el in parsed.items('.thumb-container a:first'):
            url = el.attr('href')
            if "http" in url:
                result.append(url)
    return result

if __name__ == "__main__":
    ses = login()
    for v in get_recent_videos(ses):
        print (v)
        print (get_video_info(ses, v))
