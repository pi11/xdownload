import re
import requests
from pyquery import PyQuery as pq

def login(username, password):
    login_url = "https://www.tube8.com/signin.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
        }    
    ses = requests.Session()
    check = ses.get(login_url, headers=headers)
    data = {"sign-in-username":username, "password":password,
            "action":"login"}
    res = ses.post(login_url, data=data, headers=headers)
    return ses

def get_video_info(ses, url):
    data = ses.get(url).text
    parsed = pq(data)
    mp4_url_re = re.compile(r'page_params.videoUrlJS = "(.*?)";')
    mp4_url = mp4_url_re.findall(data)[0]
    poster_re = re.compile(r'poster="(.*?)">')
    poster = poster_re.findall(data)[0]
    title = parsed('h1.main-title').text()
    return {"page":url, "mp4":mp4_url, "title":title, "poster":poster}
    
def get_recent_videos(ses, pages=[2, ]):
    """ Function return dict with url, title and url for video download

    Input: requests session,
    list of pages to parse"""
    
    result = []
    for p in pages:
        data = ses.get('https://www.tube8.com/cat/hd/22/page/%s/' % p).text
        parsed = pq(data)
        for el in parsed.items('a.video-thumb-link'):
            url = el.attr('href')
            result.append(url)
    return result

if __name__ == "__main__":
    ses = login("__login", "__pass")
    for v in get_recent_videos(ses):
        print (get_video_info(ses, v))
