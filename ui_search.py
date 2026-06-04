import streamlit as st
import yfinance as yf
from data_fetch import get_highly_secure_session


def render_search_ui(L, market):
    search_col1, search_col2 = st.columns([1, 2])
    ticker_final = "AAPL"

    with search_col1:
        search_type = st.radio(
            L["search_method"],
            [L["by_ticker"], L["by_name"]],
            index=0,
            horizontal=True,
            key="search_type"
        )

    with search_col2:
        if market == "us":
            if search_type == L["by_ticker"]:
                ticker_input = st.text_input(
                    L["enter_ticker"],
                    st.session_state.get("us_ticker_input", "AAPL"),
                    label_visibility="collapsed",
                    key="us_ticker_input"
                ).upper().strip()
                if st.button("검색", key="us_ticker_search", use_container_width=True):
                    st.session_state["us_selected_ticker"] = ticker_input if ticker_input else "AAPL"
                ticker_final = st.session_state.get("us_selected_ticker", ticker_input if ticker_input else "AAPL")
            else:
                company_input = st.text_input(
                    L["enter_name"],
                    st.session_state.get("us_name_input", ""),
                    label_visibility="collapsed",
                    key="us_name_input"
                ).strip()
                if st.button("검색", key="us_name_search", use_container_width=True):
                    if company_input:
                        try:
                            custom_session = get_highly_secure_session()
                            search_results = yf.Search(company_input, max_results=5, session=custom_session).quotes
                            if search_results:
                                options = {f"{q['symbol']} - {q.get('longname', q.get('shortname', 'Unknown'))}": q['symbol'] for q in search_results}
                                st.session_state["us_search_options"] = options
                        except Exception:
                            st.error(L["search_error"])
                us_options = st.session_state.get("us_search_options", {})
                if us_options:
                    selected_display = st.selectbox(L["select_company"], list(us_options.keys()), label_visibility="collapsed")
                    ticker_final = us_options[selected_display]
                else:
                    ticker_final = st.session_state.get("us_selected_ticker", "AAPL")


    st.markdown("---")
    return ticker_final
