import re
import requests
from pyquery import PyQuery as pq

def login():
    ses = requests.Session()
    return ses

def get_video_info(ses, url):
    data = ses.get(url).text
    parsed = pq(data)
    mp4_url = parsed('article#video-player video:first source:first').attr('src')
    poster = parsed('article#video-player video:first').attr('poster')
    title = parsed('nav.n4 h1:first').text()
    return {"page":url, "mp4":mp4_url, "title":title, "poster":poster}
    
def get_recent_videos(ses, pages=[2, ]):
    """ Function return dict with url, title and url for video download

    Input: requests session,
    list of pages to parse"""
    
    result = []
    for p in pages:
        data = ses.get('https://updatetube.com/%s' % p).text
        parsed = pq(data)
        for el in parsed.items('figure a:first'):
            url = el.attr('href')
            result.append(url)
    return result

if __name__ == "__main__":
    ses = login()
    for v in get_recent_videos(ses):
        print (v)
        print (get_video_info(ses, v))
