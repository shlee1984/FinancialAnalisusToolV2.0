import requests
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import FinanceDataReader as fdr
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from opendartreader import OpenDartReader
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


@st.cache_resource
def get_cached_dart_reader(dart_key):
    return OpenDartReader(dart_key)


def get_highly_secure_session():
    return get_cached_session()


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_dart_company_info(dart_key, code):
    try:
        dart = get_cached_dart_reader(dart_key)
        return dart.company(code)
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_dart_finstate_data(dart_key, code, year):
    try:
        dart = get_cached_dart_reader(dart_key)
        for target_year in [year, year - 1]:
            for fs_div in ['CFS', 'OFS']:
                try:
                    fin_df = dart.finstate_all(code, target_year, fs_div=fs_div)
                    if fin_df is not None and not fin_df.empty:
                        return fin_df, target_year
                except Exception:
                    continue
        return None, year
    except Exception:
        return None, year


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


def parse_dart_to_yf_format(dart_df, year):
    if dart_df is None or dart_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    fs_col = 'fs_div' if 'fs_div' in dart_df.columns else 'fs_type' if 'fs_type' in dart_df.columns else None
    if fs_col is None:
        cfs_df = dart_df
    else:
        cfs_df = dart_df[dart_df[fs_col] == 'CFS']
        if cfs_df.empty:
            cfs_df = dart_df[dart_df[fs_col] == 'OFS']

    def safe_float(val):
        try:
            return float(str(val).replace(',', ''))
        except Exception:
            return 0.0

    mapped_data = {}
    for _, row in cfs_df.iterrows():
        acc_name = row['account_nm'].strip()
        cur_amt = safe_float(row['thstrm_amount'])
        pri_amt = safe_float(row['frmtrm_amount'])

        if acc_name == '자산총계':
            mapped_data['Total Assets'] = (cur_amt, pri_amt)
        elif acc_name == '부채총계':
            mapped_data['Total Liabilities'] = (cur_amt, pri_amt)
        elif acc_name == '자본총계':
            mapped_data['Total Stockholders Equity'] = (cur_amt, pri_amt)
        elif acc_name == '유동자산':
            mapped_data['Current Assets'] = (cur_amt, pri_amt)
        elif acc_name == '유동부채':
            mapped_data['Current Liabilities'] = (cur_amt, pri_amt)
        elif acc_name == '비유동자산':
            mapped_data['Total Non Current Assets'] = (cur_amt, pri_amt)
        elif '현금및현금성자산' in acc_name:
            mapped_data['Cash'] = (cur_amt, pri_amt)
        elif '재고자산' in acc_name:
            mapped_data['Inventory'] = (cur_amt, pri_amt)
        elif '매출채권' in acc_name:
            mapped_data['Net Receivables'] = (cur_amt, pri_amt)
        elif acc_name in ['매출액', '영업수익']:
            mapped_data['Total Revenue'] = (cur_amt, pri_amt)
        elif acc_name == '매출원가':
            mapped_data['Cost Of Revenue'] = (cur_amt, pri_amt)
        elif acc_name == '매출총이익':
            mapped_data['Gross Profit'] = (cur_amt, pri_amt)
        elif acc_name in ['판매비와관리비', '영업비용']:
            mapped_data['Selling General And Administrative'] = (cur_amt, pri_amt)
        elif acc_name == '영업이익':
            mapped_data['Operating Income'] = (cur_amt, pri_amt)
        elif acc_name == '당기순이익':
            mapped_data['Net Income'] = (cur_amt, pri_amt)

    col_cur = f"{year}-12-31"
    col_pri = f"{year-1}-12-31"
    combined_df = pd.DataFrame.from_dict(mapped_data, orient='index', columns=[col_cur, col_pri])

    bs_keys = [
        'Total Assets', 'Total Liabilities', 'Total Stockholders Equity',
        'Current Assets', 'Current Liabilities', 'Cash', 'Inventory',
        'Net Receivables', 'Total Non Current Assets'
    ]
    fi_keys = [
        'Total Revenue', 'Cost Of Revenue', 'Gross Profit',
        'Selling General And Administrative', 'Operating Income', 'Net Income'
    ]

    bs_df = combined_df[combined_df.index.isin(bs_keys)]
    fi_df = combined_df[combined_df.index.isin(fi_keys)]

    return bs_df, fi_df


@st.cache_data(ttl=300)
def fetch_raw_financial_data(ticker_symbol, market, dart_key):
    try:
        if market == 'us':
            session = get_highly_secure_session()
            stock = yf.Ticker(ticker_symbol, session=session)
            bs = stock.balance_sheet
            fi = stock.financials
            if bs is None or bs.empty or fi is None or fi.empty:
                return None
            info = stock.info
            hist_df = stock.history(period='1y')
            market_metrics = {
                'trailingEps': info.get('trailingEps', 0.0),
                'bookValue': info.get('bookValue', 0.0),
                'sharesOutstanding': info.get('sharesOutstanding', 1.0),
                'trailingPE': info.get('trailingPE', 0.0),
                'priceToBook': info.get('priceToBook', 0.0),
                'currentPrice': info.get('currentPrice', float(hist_df['Close'].iloc[-1]) if not hist_df.empty else 0.0),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', float(hist_df['High'].max()) if not hist_df.empty else 0.0),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', float(hist_df['Low'].min()) if not hist_df.empty else 0.0),
                'fiftyDayAverage': info.get('fiftyDayAverage', float(hist_df['Close'].tail(50).mean()) if not hist_df.empty else 0.0),
                'longName': info.get('longName', ticker_symbol),
                'currency': info.get('currency', 'USD')
            }
            bs_df = pd.DataFrame(bs.values, index=bs.index.astype(str), columns=bs.columns.astype(str))
            fi_df = pd.DataFrame(fi.values, index=fi.index.astype(str), columns=fi.columns.astype(str))
            return {"balance_sheet": bs_df, "financials": fi_df, "metrics": market_metrics, "history": hist_df}

        elif market == 'kr':
            if not dart_key:
                return 'NO_API_KEY'
            code = ticker_symbol.zfill(6)
            end_date = datetime.today()
            start_date = end_date - pd.DateOffset(years=1)
            hist_df = fdr.DataReader(code, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            if hist_df.empty:
                return None
            
            corp_name = code
            company_info = fetch_dart_company_info(dart_key, code)
            if company_info and 'corp_name' in company_info:
                corp_name = company_info['corp_name']

            target_year = end_date.year - 1
            bs_df = pd.DataFrame()
            fi_df = pd.DataFrame()

            dart_fs, actual_year = fetch_dart_finstate_data(dart_key, code, target_year)
            if dart_fs is not None:
                bs_df, fi_df = parse_dart_to_yf_format(dart_fs, actual_year)
            else:
                st.warning("DART 데이터가 현재 제한되어 있습니다. 잠시 후 다시 시도해 주세요.")
            cur_price = float(hist_df['Close'].iloc[-1])
            high_52 = float(hist_df['High'].max())
            low_52 = float(hist_df['Low'].min())
            avg_50 = float(hist_df['Close'].tail(50).mean())
            shares_out = 10000000
            market_metrics = {
                'trailingEps': 0.0,
                'bookValue': 0.0,
                'sharesOutstanding': shares_out,
                'trailingPE': 0.0,
                'priceToBook': 0.0,
                'currentPrice': cur_price,
                'fiftyTwoWeekHigh': high_52,
                'fiftyTwoWeekLow': low_52,
                'fiftyDayAverage': avg_50,
                'longName': corp_name,
                'currency': 'KRW'
            }
            return {"balance_sheet": bs_df, "financials": fi_df, "metrics": market_metrics, "history": hist_df}
    except Exception as e:
        print(f"Data Fetch Error: {e}")
        return None
