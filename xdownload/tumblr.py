# tumblr functions

from pyquery import PyQuery as pq
import requests

def tumblr_login(username, password):
    """Login into tumblr and return requests
    session"""

    login_url = "https://www.tumblr.com/login"
    ses = requests.Session()
    res = ses.get(login_url)
    parsed = pq(res.text)
    form_key = (parsed('input[name=form_key]').attr('value'))
    data = {"user[email]":username, "user[password]":password,
            "form_key":form_key}
    res = ses.post(login_url, data=data)
    return ses
