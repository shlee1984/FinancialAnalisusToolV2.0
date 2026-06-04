import requests
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st


def get_retry_session(retries=3, backoff_factor=0.5, timeout=10):
    session = requests.Session()
    retry_kwargs = {
        'total': retries,
        'backoff_factor': backoff_factor,
        'status_forcelist': [429, 500, 502, 503, 504]
    }
    try:
        retry_kwargs['allowed_methods'] = frozenset(['GET', 'POST'])
    except Exception:
        retry_kwargs['method_whitelist'] = frozenset(['GET', 'POST'])

    retry = Retry(**retry_kwargs)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive'
    })
    return session


GLOBAL_REQUESTS_SESSION = get_retry_session()


_original_requests_get = requests.get

def patched_requests_get(*args, **kwargs):
    kwargs.setdefault('timeout', 10)
    return GLOBAL_REQUESTS_SESSION.get(*args, **kwargs)


_requests_session_request = requests.Session.request

def patched_session_request(self, method, url, **kwargs):
    kwargs.setdefault('timeout', 10)
    return _requests_session_request(self, method, url, **kwargs)


requests.get = patched_requests_get
requests.Session.request = patched_session_request




@st.cache_resource
def get_cached_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive'
    })
    return session





def get_highly_secure_session():
    return get_cached_session()







@st.cache_data(ttl=3600)
def fetch_google_news_rss(ticker_symbol, lang_mode):
    news_items = []
    search_term = ticker_symbol.replace('.KS', '').replace('.KQ', '')
    try:
        hl_gl = 'hl=ko&gl=KR&ceid=KR:ko' if lang_mode == 'ko' else 'hl=en-US&gl=US&ceid=US:en'
        url = f"https://news.google.com/rss/search?q={search_term}+stock&{hl_gl}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall('.//item')[:10]:
                title = item.find('title').text if item.find('title') is not None else 'No Title Available'
                link = item.find('link').text if item.find('link') is not None else '#'
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                source = item.find('source').text if item.find('source') is not None else 'Google News'
                news_items.append({
                    'title': title,
                    'link': link,
                    'publisher': source,
                    'date_str': pub_date
                })
    except Exception:
        pass
    return news_items

