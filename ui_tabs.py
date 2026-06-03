import streamlit as st
import pandas as pd
from analysis import compute_financial_metrics, calc_growth_raw


def render_analysis_tabs(L, ticker_final, stock_news, balance_sheet, financials, market_metrics, hist_df):
    metrics = compute_financial_metrics(balance_sheet, financials, market_metrics, hist_df, st.session_state.lang)
    if not metrics.get('has_fundamentals', True):
        st.warning(L["partial_data_warning"])
        st.info(L["partial_data_info"])

    comp_name = market_metrics.get("longName", ticker_final)
    st.subheader(f"📈 {comp_name} ({ticker_final})")

    tab_report, tab_overview, tab_ichimoku, tab_bs, tab_ratios, tab_valuation, tab_news = st.tabs([
        L["tab_report"], L["tab_overview"], L["tab_ichimoku"], L["tab_bs"], L["tab_ratios"], L["tab_valuation"], L["tab_news"]
    ])

    with tab_report:
        st.header(L["report_title"])
        st.caption(f"{L['target_comp']}: {comp_name} ({ticker_final})")
        st.markdown("---")

        price_location_pct = ((metrics['cur_price'] - market_metrics.get('fiftyTwoWeekLow', 1.0)) /
                              (market_metrics.get('fiftyTwoWeekHigh', 1.0) - market_metrics.get('fiftyTwoWeekLow', 1.0))) * 100 if (market_metrics.get('fiftyTwoWeekHigh', 1.0) - market_metrics.get('fiftyTwoWeekLow', 1.0)) != 0 else 50.0

        report_col1, report_col2 = st.columns(2)
        with report_col1:
            st.subheader(L["section1"])
            st.metric(label=L["curr_price"], value=f"{metrics['CURRENCY']}{metrics['cur_price']:,.2f}")

            status_text = L["status_high"] if price_location_pct >= 80 else (L["status_low"] if price_location_pct <= 30 else L["status_mid"])
            st.markdown(f"""
            * **{L['range_52']}:** {metrics['CURRENCY']}{market_metrics.get('fiftyTwoWeekLow', 0.0):,.2f} ~ {metrics['CURRENCY']}{market_metrics.get('fiftyTwoWeekHigh', 0.0):,.2f} ({L['at_location']} **{price_location_pct:.1f}%** {L['location_end']})
            * **{L['avg_50']}:** {metrics['CURRENCY']}{market_metrics.get('fiftyDayAverage', 0.0):,.2f}
            * {status_text}
            * **{L['multiple_analysis']} **{metrics['per_cur']:.1f}x**, PBR은 **{metrics['pbr_cur']:.1f}x**입니다.**
            """)
            st.markdown(L["ichimoku_analysis"])
            st.info(metrics['ichimoku_text'])

        with report_col2:
            st.subheader(L["section2"])
            growth_score = 1 if metrics['sales_growth_val'] > 0 else 0
            profit_score = 1 if metrics['net_growth_val'] > 0 else 0
            stability_score = 1 if (metrics['de_ratio_cur'] <= 200 and metrics['debt_ratio_cur'] <= 60) else 0
            liquidity_score = 1 if metrics['current_ratio_cur'] >= 1.2 else 0
            total_score = growth_score + profit_score + stability_score + liquidity_score

            st.markdown(f"""
            * **{L['growth_score']}:** { L['excellent'] if growth_score else L['stagnant'] } ({metrics['sales_growth_val']:+.1f}%)
            * **{L['profit_score']}:** { L['excellent'] if profit_score else L['stagnant'] } ({metrics['net_growth_val']:+.1f}%)
            * **{L['stability_score']}:** { L['safe'] if stability_score else L['high_debt'] } (D/E: {metrics['de_ratio_cur']:.1f}% | Debt: {metrics['debt_ratio_cur']:.1f}%)
            * **{L['liquidity_score']}:** { L['safe'] if liquidity_score else L['caution_cash'] } ({metrics['current_ratio_cur']:.2f})
            * **{L['total_score_text']}:** `{total_score} / 4`
            """)

            if total_score >= 3:
                st.success(L["report_good"])
            elif total_score == 2:
                st.warning(L["report_neutral"])
            else:
                st.error(L["report_bad"])

        st.markdown("---")
        st.subheader(L["section3"])
        st.info(f"""
        {L['guideline_1'].format(currency=metrics['CURRENCY'], bep_sales=metrics['bep_sales_cur'])}
        {L['guideline_2'].format(ccc=metrics['ccc_cur'])}
        {L['guideline_3']}
        """)
        st.markdown("---")
        st.caption(L["disclaimer"])

    with tab_overview:
        st.subheader("Earnings & Comprehensive Income")
        if not metrics.get('has_fundamentals', True):
            st.info(L["insufficient_data"])
            st.write("현재는 주가 및 기술적 지표 위주의 분석만 제공됩니다.")
        else:
            earnings_data = {
                "Item": ["Sales", "COGS", "Gross Profit", "SG&A", "Operating Inc.", "EBITDA", "Net Income"],
                f"Cur ({metrics['current_year']})": [
                    f"{metrics['CURRENCY']}{metrics['sales_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['cogs_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['gp_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['sga_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['op_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['ebitda_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['net_cur']:,.0f}"
                ],
                f"Pri ({metrics['prior_year']})": [
                    f"{metrics['CURRENCY']}{metrics['sales_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['cogs_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['gp_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['sga_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['op_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['ebitda_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['net_pri']:,.0f}"
                ],
                "Growth": [
                    calc_growth_raw(metrics['sales_cur'], metrics['sales_pri']),
                    calc_growth_raw(metrics['cogs_cur'], metrics['cogs_pri']),
                    calc_growth_raw(metrics['gp_cur'], metrics['gp_pri']),
                    calc_growth_raw(metrics['sga_cur'], metrics['sga_pri']),
                    calc_growth_raw(metrics['op_cur'], metrics['op_pri']),
                    calc_growth_raw(metrics['ebitda_cur'], metrics['ebitda_pri']),
                    calc_growth_raw(metrics['net_cur'], metrics['net_pri'])
                ]
            }
            st.dataframe(pd.DataFrame(earnings_data), use_container_width=True, hide_index=True)
            st.bar_chart(pd.DataFrame({'Current': [metrics['sales_cur'], metrics['op_cur'], metrics['net_cur']], 'Prior': [metrics['sales_pri'], metrics['op_pri'], metrics['net_pri']]}, index=['Sales', 'Operating', 'Net Income']))

    with tab_ichimoku:
        st.subheader(f"📐 {ticker_final} {L['ichimoku_title']}")
        if metrics['ichimoku_ready']:
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric(L['curr_price'], f"{metrics['CURRENCY']}{metrics['cur_price']:,.2f}")
            with m_col2:
                st.metric(L['tenkan'], f"{metrics['CURRENCY']}{metrics['t_curr']:,.2f}", f"{metrics['t_curr'] - metrics['k_curr']:+.2f}")
            with m_col3:
                st.metric(L['kijun'], f"{metrics['CURRENCY']}{metrics['k_curr']:,.2f}")
            with m_col4:
                st.metric(L['signal'], metrics['signal_badge'])
            st.markdown("---")

            st.markdown(f"#### {L['detail_feedback']}")
            if "위" in metrics['signal_badge'] or "Bullish" in metrics['signal_badge']:
                st.success(metrics['ichimoku_text'])
            elif "관망" in metrics['signal_badge'] or "Neutral" in metrics['signal_badge']:
                st.warning(metrics['ichimoku_text'])
            else:
                st.error(metrics['ichimoku_text'])

            st.markdown(f"#### {L['chart_trend']}")
            st.line_chart(metrics['hist_df'][['Close', 'Tenkan_Sen', 'Kijun_Sen', 'Senkou_Span_A', 'Senkou_Span_B']].tail(60), use_container_width=True)
        else:
            st.info(metrics['ichimoku_text'])

    with tab_bs:
        st.subheader("Balance Sheet Summary")
        if not metrics.get('has_fundamentals', True):
            st.info(L["insufficient_data"])
            st.write("기본 재무제표 데이터가 부족하여 자산/부채 요약은 표시할 수 없습니다.")
        else:
            bs_summary_data = {
                "Component": [
                    "💵 Cash", "🤝 Receivables", "📦 Inventories", "🗂️ CURRENT ASSETS", "🏢 PPE", "💎 TOTAL ASSETS",
                    "🛑 CURRENT LIAB", "💼 TOTAL LIABILITIES", "📈 Retained Earnings", "🧬 TOTAL EQUITY"
                ],
                f"Cur ({metrics['current_year']})": [
                    f"{metrics['CURRENCY']}{metrics['cash_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['ar_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['inv_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['ca_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['ppe_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['ta_cur']:,.0f}",
                    f"{metrics['CURRENCY']}{metrics['cl_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['tl_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['re_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['te_cur']:,.0f}"
                ],
                f"Pri ({metrics['prior_year']})": [
                    f"{metrics['CURRENCY']}{metrics['cash_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['ar_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['inv_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['ca_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['ppe_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['ta_pri']:,.0f}",
                    f"{metrics['CURRENCY']}{metrics['cl_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['tl_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['re_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['te_pri']:,.0f}"
                ],
                "Var": [
                    calc_growth_raw(metrics['cash_cur'], metrics['cash_pri']),
                    calc_growth_raw(metrics['ar_cur'], metrics['ar_pri']),
                    calc_growth_raw(metrics['inv_cur'], metrics['inv_pri']),
                    calc_growth_raw(metrics['ca_cur'], metrics['ca_pri']),
                    calc_growth_raw(metrics['ppe_cur'], metrics['ppe_pri']),
                    calc_growth_raw(metrics['ta_cur'], metrics['ta_pri']),
                    calc_growth_raw(metrics['cl_cur'], metrics['cl_pri']),
                    calc_growth_raw(metrics['tl_cur'], metrics['tl_pri']),
                    calc_growth_raw(metrics['re_cur'], metrics['re_pri']),
                    calc_growth_raw(metrics['te_cur'], metrics['te_pri'])
                ]
            }
            st.dataframe(pd.DataFrame(bs_summary_data), use_container_width=True, hide_index=True)

    with tab_ratios:
        st.subheader("Liquidity & Cycles")
        if not metrics.get('has_fundamentals', True):
            st.info(L["insufficient_data"])
            st.write("기본 재무지표가 부족하여 주요 비율은 제공되지 않습니다.")
        else:
            ratio_data = {
                "Metric Indicator": [
                    " D/E Ratio (부채/자본)",
                    " Debt Ratio (부채/자산)",
                    " Current Ratio",
                    " Quick Ratio",
                    " Inventory Turnover (avg)",
                    " Receivables Turnover (avg)",
                    " Cash Conversion Cycle"
                ],
                f"Cur ({metrics['current_year']})": [
                    f"{metrics['de_ratio_cur']:.1f}%",
                    f"{metrics['debt_ratio_cur']:.1f}%",
                    f"{metrics['current_ratio_cur']:.2f}",
                    f"{metrics['quick_ratio_cur']:.2f}",
                    f"{metrics['inv_turnover_cur']:.1f}x",
                    f"{metrics['ar_turnover_cur']:.1f}x",
                    f"{metrics['ccc_cur']:.1f} Days"
                ],
                f"Pri ({metrics['prior_year']})": [
                    f"{metrics['de_ratio_pri']:.1f}%",
                    f"{metrics['debt_ratio_pri']:.1f}%",
                    f"{metrics['current_ratio_pri']:.2f}",
                    f"{metrics['quick_ratio_pri']:.2f}",
                    f"{metrics['inv_turnover_pri']:.1f}x",
                    f"{metrics['ar_turnover_pri']:.1f}x",
                    f"{metrics['ccc_pri']:.1f} Days"
                ],
                "Delta": [
                    f"{metrics['de_ratio_cur'] - metrics['de_ratio_pri']:+.1f}%p",
                    f"{metrics['debt_ratio_cur'] - metrics['debt_ratio_pri']:+.1f}%p",
                    f"{metrics['current_ratio_cur'] - metrics['current_ratio_pri']:+.2f}",
                    f"{metrics['quick_ratio_cur'] - metrics['quick_ratio_pri']:+.2f}",
                    f"{metrics['inv_turnover_cur'] - metrics['inv_turnover_pri']:+.1f}x",
                    f"{metrics['ar_turnover_cur'] - metrics['ar_turnover_pri']:+.1f}x",
                    f"{metrics['ccc_cur'] - metrics['ccc_pri']:+.1f} D"
                ],
                "기준 (안전)": [
                    "≤200% (제조업 기준)",
                    "≤60%",
                    "≥1.5",
                    "≥1.0",
                    "높을수록 우수",
                    "높을수록 우수",
                    "낮을수록 우수"
                ]
            }
            st.dataframe(pd.DataFrame(ratio_data), use_container_width=True, hide_index=True)

    with tab_valuation:
        st.subheader("CVP & Valuation Multiples")
        if not metrics.get('has_fundamentals', True):
            st.info(L["insufficient_data"])
            st.write("기본 재무지표가 부족하여 가치평가 지표는 추정치로만 표시됩니다.")
        else:
            val_lev_data = {
                "Parameter Item": [
                    " Gross Margin (CM Proxy) ⚠️",
                    " Break-Even Point Sales (추정)",
                    " EPS",
                    " BPS",
                    " PER",
                    " PBR"
                ],
                f"Cur ({metrics['current_year']})": [
                    f"{metrics['cm_rate_cur']*100:.1f}%", f"{metrics['CURRENCY']}{metrics['bep_sales_cur']:,.0f}", f"{metrics['CURRENCY']}{metrics['eps_cur']:.2f}", f"{metrics['CURRENCY']}{metrics['bps_cur']:.2f}", f"{metrics['per_cur']:.1f}x", f"{metrics['pbr_cur']:.1f}x"
                ],
                f"Pri ({metrics['prior_year']})": [
                    f"{metrics['cm_rate_pri']*100:.1f}%", f"{metrics['CURRENCY']}{metrics['bep_sales_pri']:,.0f}", f"{metrics['CURRENCY']}{metrics['eps_pri']:.2f}", "N/A", "N/A", "N/A"
                ],
                "Description": [
                    "COGS 전체 변동비 가정 (근사치)",
                    "SG&A 기반 고정비 추정",
                    "EPS",
                    "Capital",
                    "Multiples",
                    "Multiples"
                ]
            }
            st.dataframe(pd.DataFrame(val_lev_data), use_container_width=True, hide_index=True)
            st.caption("⚠️ CM(공헌이익)은 외부 재무제표 특성상 매출총이익률로 근사 계산됩니다. BEP는 SG&A를 고정비로 가정한 추정치입니다.")

    with tab_news:
        st.subheader(f"📰 {L['latest_news']}: {ticker_final}")
        if stock_news:
            for article in stock_news[:10]:
                st.markdown(f"""
                <div style="padding: 12px; border-radius: 8px; background-color: rgba(128,128,128,0.1); margin-bottom: 10px;">
                    <a href="{article['link']}" target="_blank" style="text-decoration: none; font-weight: bold; font-size: 15px; color: #1E88E5;">🔗 {article['title']}</a>
                    <p style="margin: 6px 0 0 0; font-size: 12px; color: gray;">🏢 Source: {article['publisher']} | 📅 {article['date_str']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(L["no_news"])
