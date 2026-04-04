"""ポータルログイン。"""

from __future__ import annotations

import os
import time

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from scrapers.nendo import YEAR

load_dotenv(override=False)
USERNAME = os.environ.get("USER_ID")
PASSWORD = os.environ.get("USER_PASSWORD")


def login_session() -> requests.Session:
    session = requests.Session()
    payload = {
        "__LASTFOCUS": "",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__SCROLLPOSITIONX": 0,
        "__SCROLLPOSITIONY": 0,
        "ctl00$MainContent$TargetYearList": YEAR,
        "ctl00$MainContent$TargetTermList": 11,
        "ctl00$MainContent$LoginId": USERNAME,
        "ctl00$MainContent$LoginPassword": PASSWORD,
        "ctl00$MainContent$LoginButton": "ログイン",
    }
    hidden = ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]
    r = session.get("https://students.fun.ac.jp/Login", timeout=30)
    r.raise_for_status()
    bs = BeautifulSoup(r.text, "html.parser")
    for name in hidden:
        el = bs.find(attrs={"name": name})
        if el and el.get("value") is not None:
            payload[name] = el["value"]
    r = session.post("https://students.fun.ac.jp/Login", data=payload, timeout=30)
    r.raise_for_status()
    time.sleep(2)
    return session
