import sys
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 스트림릿이 패키지를 못 찾을 때 경로를 강제로 지정해주는 치트키
python_packages_path = r"C:\Users\shlee\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages"
if python_packages_path not in sys.path:
    sys.path.append(python_packages_path)



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

# --- 사이드바: DART API 설정 (백엔드에서만 작동, UI 숨김) ---
# Streamlit Secrets 또는 환경 변수에서 API 키 로드
try:
    dart_api_key = st.secrets.get("DART_API_KEY", os.getenv("DART_API_KEY", ""))
except:
    dart_api_key = os.getenv("DART_API_KEY", "")

# 3. 타이틀 및 다국어 버튼 레이아웃 구성
title_col, lang_col = st.columns([3, 1])
with title_col:
    st.title(MESSAGES[st.session_state.lang]["title"])
    st.caption(MESSAGES[st.session_state.lang]["subtitle"])

with lang_col:
    st.write("<div class='lang-container'>", unsafe_allow_html=True)
    btn_ko, btn_en = st.columns(2)
    with btn_ko:
        if st.button("한글", use_container_width=True):
            st.session_state.lang = "ko"
            st.rerun()
    with btn_en:
        if st.button("English", use_container_width=True):
            st.session_state.lang = "en"
            st.rerun()
    st.write("</div>", unsafe_allow_html=True)

st.markdown("---")

L = MESSAGES[st.session_state.lang]

# 시장 선택 UI
market_col1, market_col2 = st.columns([1, 3])
with market_col1:
    st.markdown(f"**{L['market_select']}**")
with market_col2:
    m_btn_us, m_btn_kr = st.columns(2)
    with m_btn_us:
        us_type = "primary" if st.session_state.market == "us" else "secondary"
        if st.button(L["market_us"], use_container_width=True, type=us_type):
            st.session_state.market = "us"
            st.rerun()
    with m_btn_kr:
        kr_type = "primary" if st.session_state.market == "kr" else "secondary"
        if st.button(L["market_kr"], use_container_width=True, type=kr_type):
            st.session_state.market = "kr"
            st.rerun()

st.markdown("---")

ticker_final = render_search_ui(L, st.session_state.market)

data_bundle = fetch_raw_financial_data(ticker_final, st.session_state.market, dart_api_key)
stock_news = fetch_google_news_rss(ticker_final, st.session_state.lang)

if data_bundle == "NO_API_KEY":
    st.error("사이드바에 DART API Key를 입력해야 한국 주식 데이터를 불러올 수 있습니다.")
elif not data_bundle:
    err_key = "fetch_error_kr" if st.session_state.market == "kr" else "fetch_error"
    st.error(L[err_key])
else:
    render_analysis_tabs(
        L,
        ticker_final,
        stock_news,
        data_bundle["balance_sheet"],
        data_bundle["financials"],
        data_bundle["metrics"],
        data_bundle["history"],
    )
