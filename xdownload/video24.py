import sys
import re
import requests
from pyquery import PyQuery as pq

headers = {"ACCEPT":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "ACCEPT_ENCODING":"gzip, deflate, br",
           "ACCEPT-LANGUAGE":"en-US,en;q=0.5",
           "CONNECTION":"keep-alive",
           "DNT":"1",
           "HOST":"24video.sexy",
           "REFERER":"https://24video.sexy/",
           ##"UPGRADE-INSECURE-REQUESTS":"0",
           "USER-AGENT":"Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0",
           "X-REAL-IP":"163.172.59.10",
           "X-FORWARDED-FOR":"163.172.59.10",
           "X-ACCEL-INTERNAL":""}

def login():
    ses = requests.Session()
    ses.headers.update(headers)
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
    """ Function return dict with url, title, description
    and url for video download

    Input: requests session,
    list of pages to parse"""
    
    result = []
    for p in pages:
        url = 'https://www.24video.sexy' #'video/filter'
        querystring = {"page":p, "sort":3, "time":0}
        print("Loading: %s" % url)
        try:
            ses.max_redirects = 10
            response = ses.get(url, headers=headers, )#.text#, params=querystring).text
        except requests.exceptions.TooManyRedirects as exc:
            if exc.response.history:
                for resp in exc.response.history:
                    print(resp.status_code, resp.url)
                print(exc.response.status_code, exc.response.url)
            else:
                print("Request was not redirected")
            
            print(exc)
            print(exc.response)
            print(exc.response.url)
            from pprint import pprint
            pprint(vars(exc))
            sys.exit()
        print(data)
        parsed = pq(data)
        for el in parsed.items('a.list-item'):
            url = el.attr('href')
            if "http" in url:
                result.append(url)
    return result



"""
def download_24video(url):


    s = requests.session()
    p = s.get(url, headers=headers)
    parse_page = pq(p.content)
    download_url = parse_page('video').attr('src')

    #print("Downloading, please wait...")
    res = s.get(download_url, headers=headers)
    #print(res.headers)
    #print("Len:", len(res.content))

    with open('t.mp4', 'wb+') as f:
        f.write(res.content)
"""

if __name__ == "__main__":
    ses = login()
    for v in get_recent_videos(ses):
        print (v)
        #print (get_video_info(ses, v))
