import FinanceDataReader as fdr
import streamlit as st

_KR_TICKERS_BUILTIN = {
    "005930": ("삼성전자", "KOSPI"),
    "000660": ("SK하이닉스", "KOSPI"),
    "005380": ("현대차", "KOSPI"),
    "000270": ("기아", "KOSPI"),
    "035420": ("NAVER", "KOSPI"),
    "035720": ("카카오", "KOSDAQ"),
    "068270": ("셀트리온", "KOSPI"),
    "207940": ("삼성바이오로직스", "KOSPI"),
    "005490": ("POSCO홀딩스", "KOSPI"),
    "051910": ("LG화학", "KOSPI"),
    "006400": ("삼성SDI", "KOSPI"),
    "028260": ("삼성물산", "KOSPI")
}


@st.cache_data(ttl=86400)
def get_krx_listing_cached():
    """KRX 전체 종목 리스트를 캐싱하여 검색 성능 강화"""
    return fdr.StockListing('KRX')

def search_krx_by_name(query: str) -> dict:
    """한국 주식 검색 (내장 데이터 및 외부 API fallback)"""
    query_strip = query.strip()
    if not query_strip:
        return {}

    result = {}
    query_lower = query_strip.lower()

    for code, (name, market) in _KR_TICKERS_BUILTIN.items():
        if query_lower in name.lower():
            result[f"{name} ({code}) [{market}]"] = code
    if result:
        return result

    try:
        krx_df = get_krx_listing_cached()
        matches = krx_df[krx_df['Name'].str.contains(query_strip, case=False, na=False)]
        for _, row in matches.head(10).iterrows():
            result[f"{row['Name']} ({row['Code']}) [{row.get('Market', 'KRX')}]"] = row['Code']
    except Exception:
        pass

    return result


def get_currency_symbol(market: str) -> str:
    return "₩" if market == "kr" else "$"
