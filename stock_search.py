import FinanceDataReader as fdr
import streamlit as st





def get_currency_symbol(market: str) -> str:
    return "₩" if market == "kr" else "$"
