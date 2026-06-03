import numpy as np
import streamlit as st


def get_row_values_robust(df, keys_list):
    idx_clean = {str(k).strip().lower(): k for k in df.index}
    for key in keys_list:
        key_lower = str(key).strip().lower()
        if key_lower in idx_clean:
            vals = df.loc[idx_clean[key_lower]].values
            v1 = float(vals[0]) if not np.isnan(vals[0]) else 0.0
            v2 = float(vals[1]) if not np.isnan(vals[1]) else 0.0
            return v1, v2
    return 0.0, 0.0


def calc_growth_raw(current, prior):
    if prior and prior != 0:
        return f"{((current - prior) / prior) * 100:.1f}%"
    return "N/A"


def compute_financial_metrics(balance_sheet, financials, market_metrics, hist_df, lang):
    has_fundamentals = balance_sheet.shape[1] >= 2 and financials.shape[1] >= 2

    current_year = "N/A"
    prior_year = "N/A"
    if balance_sheet.shape[1] >= 1:
        current_year = balance_sheet.columns[0][:7] if len(balance_sheet.columns[0]) > 4 else balance_sheet.columns[0]
    if balance_sheet.shape[1] >= 2:
        prior_year = balance_sheet.columns[1][:7] if len(balance_sheet.columns[1]) > 4 else balance_sheet.columns[1]

    sales_cur, sales_pri = get_row_values_robust(financials, ['Total Revenue', 'Revenue', 'Operating Revenue'])
    cogs_cur, cogs_pri = get_row_values_robust(financials, ['Cost Of Revenue', 'Cost of Goods Sold'])
    gp_cur, gp_pri = get_row_values_robust(financials, ['Gross Profit'])
    if gp_cur == 0 and sales_cur != 0:
        gp_cur, gp_pri = sales_cur - cogs_cur, sales_pri - cogs_pri

    sga_cur, sga_pri = get_row_values_robust(financials, ['Selling General And Administrative'])
    op_cur, op_pri = get_row_values_robust(financials, ['Operating Income', 'EBIT'])
    ebitda_cur, ebitda_pri = get_row_values_robust(financials, ['Normalized EBITDA', 'EBITDA'])
    net_cur, net_pri = get_row_values_robust(financials, ['Net Income', 'Net Income Common Stockholders'])

    cash_cur, cash_pri = get_row_values_robust(balance_sheet, ['Cash And Cash Equivalents', 'Cash'])
    inv_cur, inv_pri = get_row_values_robust(balance_sheet, ['Inventory', 'Inventories'])
    ar_cur, ar_pri = get_row_values_robust(balance_sheet, ['Receivables', 'Accounts Receivable', 'Net Receivables'])
    ap_cur, ap_pri = get_row_values_robust(balance_sheet, ['Payables And Accrued Expenses', 'Accounts Payable'])

    ca_cur, ca_pri = get_row_values_robust(balance_sheet, ['Current Assets', 'Total Current Assets'])
    ppe_cur, ppe_pri = get_row_values_robust(balance_sheet, ['Properties', 'Net PPE', 'Property Plant And Equipment'])
    ta_cur, ta_pri = get_row_values_robust(balance_sheet, ['Total Assets', 'Assets'])
    cl_cur, cl_pri = get_row_values_robust(balance_sheet, ['Current Liabilities', 'Total Current Liabilities'])
    tl_cur, tl_pri = get_row_values_robust(balance_sheet, ['Total Liabilities Net Minority Interest', 'Total Liabilities'])
    re_cur, re_pri = get_row_values_robust(balance_sheet, ['Retained Earnings'])
    te_cur, te_pri = get_row_values_robust(balance_sheet, ['Stockholders Equity', 'Total Stockholders Equity'])

    sales_growth_val = ((sales_cur - sales_pri) / sales_pri * 100) if sales_pri != 0 else 0.0
    net_growth_val = ((net_cur - net_pri) / net_pri * 100) if net_pri != 0 else 0.0

    de_ratio_cur = (tl_cur / te_cur * 100) if te_cur != 0 else 0.0
    de_ratio_pri = (tl_pri / te_pri * 100) if te_pri != 0 else 0.0

    debt_ratio_cur = (tl_cur / ta_cur * 100) if ta_cur != 0 else 0.0
    debt_ratio_pri = (tl_pri / ta_pri * 100) if ta_pri != 0 else 0.0

    current_ratio_cur = (ca_cur / cl_cur) if cl_cur != 0 else 0.0
    current_ratio_pri = (ca_pri / cl_pri) if cl_pri != 0 else 0.0
    quick_ratio_cur = ((ca_cur - inv_cur) / cl_cur) if cl_cur != 0 else 0.0
    quick_ratio_pri = ((ca_pri - inv_pri) / cl_pri) if cl_pri != 0 else 0.0

    avg_inv_cur = (inv_cur + inv_pri) / 2 if (inv_cur + inv_pri) != 0 else inv_cur
    avg_ar_cur = (ar_cur + ar_pri) / 2 if (ar_cur + ar_pri) != 0 else ar_cur
    avg_ap_cur = (ap_cur + ap_pri) / 2 if (ap_cur + ap_pri) != 0 else ap_cur

    avg_inv_pri = inv_pri
    avg_ar_pri = ar_pri
    avg_ap_pri = ap_pri

    inv_turnover_cur = (cogs_cur / avg_inv_cur) if avg_inv_cur != 0 else 0.0
    inv_turnover_pri = (cogs_pri / avg_inv_pri) if avg_inv_pri != 0 else 0.0
    ar_turnover_cur = (sales_cur / avg_ar_cur) if avg_ar_cur != 0 else 0.0
    ar_turnover_pri = (sales_pri / avg_ar_pri) if avg_ar_pri != 0 else 0.0
    ap_turnover_cur = (cogs_cur / avg_ap_cur) if avg_ap_cur != 0 else 1.0
    ap_turnover_pri = (cogs_pri / avg_ap_pri) if avg_ap_pri != 0 else 1.0

    days_inv_cur = 365 / inv_turnover_cur if inv_turnover_cur != 0 else 0.0
    days_ar_cur = 365 / ar_turnover_cur if ar_turnover_cur != 0 else 0.0
    days_ap_cur = 365 / ap_turnover_cur
    ccc_cur = (days_inv_cur + days_ar_cur) - days_ap_cur

    days_inv_pri = 365 / inv_turnover_pri if inv_turnover_pri != 0 else 0.0
    days_ar_pri = 365 / ar_turnover_pri if ar_turnover_pri != 0 else 0.0
    days_ap_pri = 365 / ap_turnover_pri
    ccc_pri = (days_inv_pri + days_ar_pri) - days_ap_pri

    fixed_cost_cur = sga_cur if sga_cur > 0 else max(gp_cur - op_cur, sales_cur * 0.2)
    fixed_cost_pri = sga_pri if sga_pri > 0 else max(gp_pri - op_pri, sales_pri * 0.2)

    cm_cur = sales_cur - cogs_cur
    cm_pri = sales_pri - cogs_pri
    cm_rate_cur = (cm_cur / sales_cur) if sales_cur != 0 else 0.0
    cm_rate_pri = (cm_pri / sales_pri) if sales_pri != 0 else 0.0
    bep_sales_cur = (fixed_cost_cur / cm_rate_cur) if cm_rate_cur != 0 else 0.0
    bep_sales_pri = (fixed_cost_pri / cm_rate_pri) if cm_rate_pri != 0 else 0.0

    shares_out = market_metrics.get('sharesOutstanding', 1.0)
    eps_cur = market_metrics.get('trailingEps', 0.0) or (net_cur / shares_out if shares_out else 0.0)
    eps_pri = net_pri / shares_out if shares_out else 0.0
    bps_cur = market_metrics.get('bookValue', 0.0) or (te_cur / shares_out if shares_out else 0.0)
    cur_price = market_metrics.get('currentPrice', 0.0)
    per_cur = market_metrics.get('trailingPE', 0.0) or (cur_price / eps_cur if eps_cur != 0 else 0.0)
    pbr_cur = market_metrics.get('priceToBook', 0.0) or (cur_price / bps_cur if bps_cur != 0 else 0.0)

    CURRENCY = '₩' if market_metrics.get('currency') == 'KRW' else '$'

    ichimoku_ready = False
    ichimoku_text = "📊 데이터 축적량이 부족하여 기술적 지표 진단을 생성할 수 없습니다." if lang == 'ko' else "📊 Data is insufficient to generate Ichimoku analysis."
    signal_badge = "🔄 분석중" if lang == 'ko' else "🔄 Processing"
    t_curr = k_curr = sa_curr = sb_curr = 0.0
    cloud_status = position_status = cross_status = lagging_status = ""

    if not hist_df.empty and len(hist_df) >= 52:
        low_9 = hist_df['Low'].rolling(window=9).min()
        high_9 = hist_df['High'].rolling(window=9).max()
        hist_df['Tenkan_Sen'] = (low_9 + high_9) / 2
        low_26 = hist_df['Low'].rolling(window=26).min()
        high_26 = hist_df['High'].rolling(window=26).max()
        hist_df['Kijun_Sen'] = (low_26 + high_26) / 2
        hist_df['Senkou_Span_A'] = ((hist_df['Tenkan_Sen'] + hist_df['Kijun_Sen']) / 2).shift(26)
        low_52 = hist_df['Low'].rolling(window=52).min()
        high_52 = hist_df['High'].rolling(window=52).max()
        hist_df['Senkou_Span_B'] = ((low_52 + high_52) / 2).shift(26)

        t_curr = hist_df['Tenkan_Sen'].iloc[-1]
        k_curr = hist_df['Kijun_Sen'].iloc[-1]
        sa_curr = hist_df['Senkou_Span_A'].dropna().iloc[-1] if not hist_df['Senkou_Span_A'].dropna().empty else 0.0
        sb_curr = hist_df['Senkou_Span_B'].dropna().iloc[-1] if not hist_df['Senkou_Span_B'].dropna().empty else 0.0
        chikou_current = hist_df['Close'].iloc[-1]
        past_close_26 = hist_df['Close'].iloc[-26] if len(hist_df) >= 26 else chikou_current

        if sa_curr != 0.0 and sb_curr != 0.0:
            ichimoku_ready = True
            if lang == 'ko':
                if cur_price > max(sa_curr, sb_curr):
                    cloud_status, position_status = f"구름대 상단({CURRENCY}{max(sa_curr, sb_curr):,.2f}) 위", "확고한 정배열형 상승 추세"
                elif cur_price < min(sa_curr, sb_curr):
                    cloud_status, position_status = f"구름대 하단({CURRENCY}{min(sa_curr, sb_curr):,.2f}) 아래", "매물대 저항 압박에 직면한 하락 위험"
                else:
                    cloud_status, position_status = f"구름대 가두리권 범위({CURRENCY}{min(sa_curr, sb_curr):,.2f} ~ {CURRENCY}{max(sa_curr, sb_curr):,.2f}) 내부", "단기 방향성 탐색을 위한 횡보 조정"

                cross_status = f"🔼 **호전 지속:** 전환선({CURRENCY}{t_curr:,.2f})이 기준선({CURRENCY}{k_curr:,.2f}) 위에 위치하여 매수세가 우세합니다." if t_curr > k_curr else (f"🔽 **역전 발생:** 전환선({CURRENCY}{t_curr:,.2f})이 기준선({CURRENCY}{k_curr:,.2f})을 하회하여 가격 조정 중입니다." if t_curr < k_curr else f"🔀 **수렴:** 전환선과 기준선이 {CURRENCY}{t_curr:,.2f} 부근에서 결집 중입니다.")
                lagging_status = f"🟢 **후행스팬 상승우위:** 현재 종가({CURRENCY}{chikou_current:,.2f})가 26봉 전 가격({CURRENCY}{past_close_26:,.2f})을 상회, 매수 모멘텀이 우세합니다." if chikou_current > past_close_26 else f"🚨 **후행스팬 하락부담:** 현재 종가({CURRENCY}{chikou_current:,.2f})가 26봉 전 가격({CURRENCY}{past_close_26:,.2f}) 아래, 매물 소화 압력이 존재합니다."
            else:
                if cur_price > max(sa_curr, sb_curr):
                    cloud_status, position_status = f"Above Cloud Top ({CURRENCY}{max(sa_curr, sb_curr):,.2f})", "Strong Bullish Uptrend"
                elif cur_price < min(sa_curr, sb_curr):
                    cloud_status, position_status = f"Below Cloud Bottom ({CURRENCY}{min(sa_curr, sb_curr):,.2f})", "Bearish Risk with Heavy Resistance"
                else:
                    cloud_status, position_status = f"Inside Cloud Bounds ({CURRENCY}{min(sa_curr, sb_curr):,.2f} ~ {CURRENCY}{max(sa_curr, sb_curr):,.2f})", "Neutral Consolidation Phase"

                cross_status = f"🔼 **Bullish Cross:** Tenkan ({CURRENCY}{t_curr:,.2f}) is above Kijun ({CURRENCY}{k_curr:,.2f}), buying momentum dominates." if t_curr > k_curr else (f"🔽 **Bearish Cross:** Tenkan ({CURRENCY}{t_curr:,.2f}) broke below Kijun ({CURRENCY}{k_curr:,.2f}), undergoing correction." if t_curr < k_curr else f"🔀 **Convergence:** Lines are merging around {CURRENCY}{t_curr:,.2f}.")
                lagging_status = f"🟢 **Chikou Bullish:** Current close ({CURRENCY}{chikou_current:,.2f}) is above price 26 periods ago ({CURRENCY}{past_close_26:,.2f}), confirming upward momentum." if chikou_current > past_close_26 else f"🚨 **Chikou Bearish:** Current close ({CURRENCY}{chikou_current:,.2f}) is below price 26 periods ago ({CURRENCY}{past_close_26:,.2f}), indicating overhead supply pressure."

            score = 0
            if cur_price > max(sa_curr, sb_curr):
                score += 2
            elif cur_price >= min(sa_curr, sb_curr):
                score += 1
            if t_curr > k_curr:
                score += 1
            if chikou_current > past_close_26:
                score += 1

            if score >= 3:
                signal_badge = "🟢 매수 우위" if lang == 'ko' else "🟢 Bullish Trend"
            elif score == 2:
                signal_badge = "🟡 관망/중립" if lang == 'ko' else "🟡 Neutral Box"
            else:
                signal_badge = "🚨 리스크 관리" if lang == 'ko' else "🚨 Bearish Shock"

            if lang == 'ko':
                ichimoku_text = f"""
                    * **구름대 위치 진단:** 현재 주가는 {cloud_status}에 위치하고 있으며, 현재 구간은 **{position_status}** 국면으로 해석됩니다.
                    * **추세 교차 시그널:** {cross_status}
                    * **매물대 지지선 파악:** 선행스팬A는 `{CURRENCY}{sa_curr:,.2f}`, 선행스팬B는 `{CURRENCY}{sb_curr:,.2f}`에 형성되어 있습니다.
                    * **후행스팬(Chikou) 검증:** {lagging_status}
                    """
            else:
                ichimoku_text = f"""
                    * **Cloud Position Diagnostic:** Stock price is {cloud_status}, indicating a **{position_status}** state.
                    * **Trend Cross Signal:** {cross_status}
                    * **Support/Resistance Bounds:** Senkou Span A is `{CURRENCY}{sa_curr:,.2f}`, Senkou Span B is `{CURRENCY}{sb_curr:,.2f}`.
                    * **Chikou Span Validation:** {lagging_status}
                    """

    return {
        'has_fundamentals': has_fundamentals,
        'current_year': current_year,
        'prior_year': prior_year,
        'sales_cur': sales_cur,
        'sales_pri': sales_pri,
        'cogs_cur': cogs_cur,
        'cogs_pri': cogs_pri,
        'gp_cur': gp_cur,
        'gp_pri': gp_pri,
        'sga_cur': sga_cur,
        'sga_pri': sga_pri,
        'op_cur': op_cur,
        'op_pri': op_pri,
        'ebitda_cur': ebitda_cur,
        'ebitda_pri': ebitda_pri,
        'net_cur': net_cur,
        'net_pri': net_pri,
        'cash_cur': cash_cur,
        'cash_pri': cash_pri,
        'inv_cur': inv_cur,
        'inv_pri': inv_pri,
        'ar_cur': ar_cur,
        'ar_pri': ar_pri,
        'ap_cur': ap_cur,
        'ap_pri': ap_pri,
        'ca_cur': ca_cur,
        'ca_pri': ca_pri,
        'ppe_cur': ppe_cur,
        'ppe_pri': ppe_pri,
        'ta_cur': ta_cur,
        'ta_pri': ta_pri,
        'cl_cur': cl_cur,
        'cl_pri': cl_pri,
        'tl_cur': tl_cur,
        'tl_pri': tl_pri,
        're_cur': re_cur,
        're_pri': re_pri,
        'te_cur': te_cur,
        'te_pri': te_pri,
        'sales_growth_val': sales_growth_val,
        'net_growth_val': net_growth_val,
        'de_ratio_cur': de_ratio_cur,
        'de_ratio_pri': de_ratio_pri,
        'debt_ratio_cur': debt_ratio_cur,
        'debt_ratio_pri': debt_ratio_pri,
        'current_ratio_cur': current_ratio_cur,
        'current_ratio_pri': current_ratio_pri,
        'quick_ratio_cur': quick_ratio_cur,
        'quick_ratio_pri': quick_ratio_pri,
        'inv_turnover_cur': inv_turnover_cur,
        'inv_turnover_pri': inv_turnover_pri,
        'ar_turnover_cur': ar_turnover_cur,
        'ar_turnover_pri': ar_turnover_pri,
        'ap_turnover_cur': ap_turnover_cur,
        'ap_turnover_pri': ap_turnover_pri,
        'days_inv_cur': days_inv_cur,
        'days_ar_cur': days_ar_cur,
        'days_ap_cur': days_ap_cur,
        'ccc_cur': ccc_cur,
        'days_inv_pri': days_inv_pri,
        'days_ar_pri': days_ar_pri,
        'days_ap_pri': days_ap_pri,
        'ccc_pri': ccc_pri,
        'fixed_cost_cur': fixed_cost_cur,
        'fixed_cost_pri': fixed_cost_pri,
        'cm_cur': cm_cur,
        'cm_pri': cm_pri,
        'cm_rate_cur': cm_rate_cur,
        'cm_rate_pri': cm_rate_pri,
        'bep_sales_cur': bep_sales_cur,
        'bep_sales_pri': bep_sales_pri,
        'eps_cur': eps_cur,
        'eps_pri': eps_pri,
        'bps_cur': bps_cur,
        'per_cur': per_cur,
        'pbr_cur': pbr_cur,
        'cur_price': cur_price,
        'CURRENCY': CURRENCY,
        'ichimoku_ready': ichimoku_ready,
        'ichimoku_text': ichimoku_text,
        'signal_badge': signal_badge,
        't_curr': t_curr,
        'k_curr': k_curr,
        'sa_curr': sa_curr,
        'sb_curr': sb_curr,
        'cloud_status': cloud_status,
        'position_status': position_status,
        'cross_status': cross_status,
        'lagging_status': lagging_status,
        'hist_df': hist_df
    }
