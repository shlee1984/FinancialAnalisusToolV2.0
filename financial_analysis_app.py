import os
import sys

# 앱 루트 경로를 명시적으로 추가하여 Streamlit 배포 환경에서 모듈 import 문제를 방지합니다.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dotenv import load_dotenv
# 환경 변수 로드
load_dotenv()

import streamlit as st
from app_constants import MESSAGES
from data_fetch import fetch_google_news_rss, fetch_raw_financial_data
from ui_search import render_search_ui
from ui_tabs import render_analysis_tabs


# 1. 웹 페이지 기본 설정 및 모바일 맞춤형 CSS 주입
st.set_page_config(page_title="Corporate Financial Analysis Tool", layout="wide")

st.markdown("""
    <style>
    html, body, [data-testid="stMarkdownContainer"] {
        font-size: 15px !important;
    }
    .lang-container {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 10px;
    }
    @media (max-width: 768px) {
        .stDataFrame div {
            font-size: 12px !important;
        }
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.4rem !important; }
        h3 { font-size: 1.1rem !important; }
        .stButton button {
            padding: 0.25rem 0.5rem !important;
            font-size: 13px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# 2. 다국어 및 시장 세션 상태 초기화
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
if "market" not in st.session_state:
    st.session_state.market = "us"
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = None
if "cached_data_bundle" not in st.session_state:
    st.session_state.cached_data_bundle = None
if "cached_news" not in st.session_state:
    st.session_state.cached_news = None


# 3. 타이틀 및 다국어 버튼 레이아웃 구성
title_col, lang_col = st.columns([3, 1])
with title_col:
    st.title(MESSAGES[st.session_state.lang]["title"])
    st.caption(MESSAGES[st.session_state.lang]["subtitle"])

with lang_col:
    st.write("<div class='lang-container'>", unsafe_allow_html=True)
    btn_ko, btn_en, btn_es = st.columns(3)
    with btn_ko:
        if st.button("한글", width='stretch'):
            st.session_state.lang = "ko"
            st.rerun()
    with btn_en:
        if st.button("English", width='stretch'):
            st.session_state.lang = "en"
            st.rerun()
    with btn_es:
        if st.button("Español", width='stretch'):
            st.session_state.lang = "es"
            st.rerun()
    st.write("</div>", unsafe_allow_html=True)

st.markdown("---")

L = MESSAGES[st.session_state.lang]

# 시장 선택 UI
market_col1, market_col2 = st.columns([1, 1])
with market_col1:
    st.markdown(f"**{L['market_select']}**")
with market_col2:
    m_btn_us = st.columns(1)[0]
    with m_btn_us:
        us_type = "primary" if st.session_state.market == "us" else "secondary"
        if st.button(L["market_us"], width='stretch', type=us_type):
            st.session_state.market = "us"
            st.rerun()


st.markdown("---")

ticker_final = render_search_ui(L, st.session_state.market)

# Ticker가 변경되었을 때만 데이터를 fetch
if ticker_final != st.session_state.current_ticker:
    st.session_state.current_ticker = ticker_final
    with st.spinner("데이터를 불러오는 중입니다. 잠시만 기다려주세요..."):
        data_bundle = fetch_raw_financial_data(ticker_final, st.session_state.market)
        stock_news = fetch_google_news_rss(ticker_final)
    st.session_state.cached_data_bundle = data_bundle
    st.session_state.cached_news = stock_news
else:
    # 캐시된 데이터 사용
    data_bundle = st.session_state.cached_data_bundle
    # 캐시된 데이터 사용
    data_bundle = st.session_state.cached_data_bundle
    stock_news = st.session_state.cached_news

if data_bundle == "NO_API_KEY":
    st.error("사이드바에 DART API Key를 입력해야 한국 주식 데이터를 불러올 수 있습니다.")
elif not data_bundle:
    err_key = "fetch_error_kr" if st.session_state.market == "kr" else "fetch_error"

    render_analysis_tabs(
        L,
        ticker_final,
        stock_news,
        data_bundle["balance_sheet"],
        data_bundle["financials"],
        data_bundle["metrics"],
        data_bundle["history"],
    )
