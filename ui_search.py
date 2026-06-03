import streamlit as st
import yfinance as yf
from stock_search import search_krx_by_name
from data_fetch import get_highly_secure_session


def render_search_ui(L, market):
    search_col1, search_col2 = st.columns([1, 2])
    ticker_final = "AAPL" if market == "us" else "005380"

    with search_col1:
        search_type = st.radio(L["search_method"], [L["by_ticker"], L["by_name"]], index=0, horizontal=True)

    with search_col2:
        if market == "us":
            if search_type == L["by_ticker"]:
                ticker_input = st.text_input(L["enter_ticker"], "AAPL", label_visibility="collapsed").upper().strip()
                ticker_final = ticker_input if ticker_input else "AAPL"
            else:
                company_input = st.text_input(L["enter_name"], "Oracle", label_visibility="collapsed").strip()
                if company_input:
                    try:
                        custom_session = get_highly_secure_session()
                        search_results = yf.Search(company_input, max_results=5, session=custom_session).quotes
                        if search_results:
                            options = {f"{q['symbol']} - {q.get('longname', q.get('shortname', 'Unknown'))}": q['symbol'] for q in search_results}
                            selected_display = st.selectbox(L["select_company"], list(options.keys()), label_visibility="collapsed")
                            ticker_final = options[selected_display]
                    except Exception:
                        st.error(L["search_error"])
        else:
            if search_type == L["by_ticker"]:
                kr_code_input = st.text_input(L["enter_ticker_kr"], "005380", label_visibility="collapsed", placeholder="예: 005380").strip()
                ticker_final = kr_code_input.zfill(6) if kr_code_input else "005380"
            else:
                name_col_input, name_col_btn = st.columns([5, 1])
                with name_col_input:
                    kr_name_input = st.text_input(L["enter_name_kr"], "", label_visibility="collapsed").strip()
                with name_col_btn:
                    do_search = st.button("검색", use_container_width=True)

                if do_search and kr_name_input:
                    st.session_state["kr_search_query"] = kr_name_input
                    st.session_state["kr_search_results"] = search_krx_by_name(kr_name_input)

                kr_options = st.session_state.get("kr_search_results", {})
                if kr_options:
                    selected_kr = st.selectbox(L["select_company"], list(kr_options.keys()), label_visibility="collapsed")
                    ticker_final = kr_options[selected_kr]
                else:
                    ticker_final = "005380"

    st.markdown("---")
    return ticker_final
