import streamlit as st
import pandas as pd
import json
import time
import plotly.graph_objects as go
import math

# ---------------------------------------------------------
# 🛠 SHEET ID ฝังให้เรียบร้อยแล้วครับ 🛠
SHEET_ID = "1BdkpzNz5lqECpnyc7PgC1BQMc5FeOyqkE_lonF36ANQ"
# ---------------------------------------------------------

SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="Tactical Monitor Gold v22", page_icon="🛸", layout="wide")

# --- 1. CSS STYLING (Sci-Fi HUD Theme - Green & Gold) ---
st.markdown("""
<style>
.block-container { padding: 0.5rem 0.5rem 3rem 0.5rem; }
header, footer { visibility: hidden; }
.stApp { background-color: #050505; color: #e0f7fa; font-family: 'Courier New', Courier, monospace; }

.hud-box {
    background: #0a0f14; border: 1px solid #333; border-radius: 4px;
    padding: 15px; margin-bottom: 15px; border-left: 4px solid #00e5ff;
}
.hud-label { font-size: 0.75rem; color: #546e7a; letter-spacing: 2px; font-weight: bold; text-transform: uppercase; }
.hud-value-blue { font-size: 2.2rem; color: #00e5ff; font-weight: bold; text-shadow: 0 0 10px rgba(0, 229, 255, 0.6); line-height: 1; }
.hud-value-sub { font-size: 1.2rem; color: #aaa; font-weight: bold; }

.main-bar-container { width: 100%; height: 18px; background: #1c2530; margin: 10px 0; position: relative; border-radius: 2px; overflow: hidden; }
.main-bar-fill-blue { height: 100%; background: #00e5ff; box-shadow: 0 0 10px #00e5ff; position: absolute; z-index: 3; transition: width 0.5s; }
.main-bar-fill-gold { height: 100%; background: #FFD600; box-shadow: 0 0 8px #FFD600; position: absolute; z-index: 2; transition: width 0.5s; }
.main-bar-marker { position: absolute; width: 2px; height: 24px; top: -3px; background: #fff; z-index: 5; box-shadow: 0 0 8px #fff; }

.module-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid #222; border-radius: 4px;
    padding: 12px; margin-bottom: 15px;
}
.id-row { display: flex; gap: 5px; margin-bottom: 12px; align-items: center; }
.square-box {
    padding: 2px 8px; border: 1px solid #444; border-radius: 2px;
    font-weight: bold; font-size: 0.9rem; font-family: monospace;
}
.box-magic { background: rgba(0, 229, 255, 0.1); color: #00e5ff; border-color: #00e5ff; }
.box-buy { background: rgba(0, 230, 118, 0.1); color: #00e676; border-color: #00e676; }
.box-gold { background: rgba(255, 215, 0, 0.1); color: #FFD700; border-color: #FFD700; }
.box-lots { background: rgba(255, 167, 38, 0.1); color: #FFA726; border-color: #FFA726; }
.box-count { background: rgba(255, 255, 255, 0.05); color: #fff; border-color: #555; }
.text-first-lot { font-size: 0.9rem; color: #888; font-weight: bold; margin-left: 5px; font-family: monospace; }

.p-row { display: flex; align-items: center; margin-bottom: 15px; }
.div-track { flex-grow: 1; height: 18px; background: #1a1a1a; position: relative; margin-right: 15px; border-radius: 2px; }
.div-center { position: absolute; left: 50%; width: 2px; height: 24px; top: -3px; background: #fff; z-index: 2; box-shadow: 0 0 8px #fff; }
.div-fill { height: 100%; position: absolute; border-radius: 1px; }

.vu-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px; }
.vu-meter { display: flex; gap: 2px; flex-grow: 1; margin-right: 15px; height: 18px; align-items: center; overflow: hidden; }
.vu-tick { width: 3px; height: 18px; background: #1a1a1a; border-radius: 1px; }
.vu-tick.active-buy { background: #00e676; box-shadow: 0 0 5px #00e676; }
.vu-tick.active-gold { background: #FFD700; box-shadow: 0 0 5px #FFD700; }
.vu-overflow { color: #FFD700; font-size: 1.1rem; margin-left: 5px; font-weight: bold; }

.scale-row { display: flex; align-items: center; justify-content: space-between; }
.price-scale { flex-grow: 1; height: 18px; background: rgba(255,255,255,0.03); margin-right: 15px; position: relative; border-bottom: 1px solid #333; cursor: crosshair; }
.tick-order { position: absolute; width: 1px; height: 12px; background: #555; bottom: 0; }
.tick-main { width: 2px; height: 18px; background: #fff; box-shadow: 0 0 5px #fff; z-index: 3; bottom: 0; }
.tick-be { width: 3px; height: 22px; background: #FFD600; box-shadow: 0 0 8px #FFD600; z-index: 5; bottom: -2px; }
.tick-current { position: absolute; width: 1px; height: 28px; border-left: 1px dashed #00e5ff; top: -5px; z-index: 6; }

.data-text { font-size: 0.9rem; font-weight: bold; white-space: nowrap; font-family: monospace; line-height: 18px; }
.section-title { font-size: 0.9rem; font-weight: 700; color: #E0E0E0; border-left: 4px solid #29B6F6; padding-left: 10px; margin-top: 25px; margin-bottom: 15px; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        if 'CurrentPrice' not in df.columns: df['CurrentPrice'] = 0.0 
        return df
    except: return None

# =========================================================
# Main Loop
# =========================================================

df = load_data()

if df is None:
    st.warning("LINKING SATELLITE...")
    time.sleep(2)
    st.rerun()
else:
    try:
        df['AccountID'] = df['AccountID'].astype(str)
        all_accounts = df['AccountID'].unique().tolist()
        selected_account = st.selectbox("MISSION TARGET", all_accounts, index=0)
        
        if selected_account:
            target_df = df[df['AccountID'] == selected_account]
            if not target_df.empty:
                latest = target_df.iloc[-1]
                
                # Core Data
                price = float(latest.get('CurrentPrice', 0.0))
                bal, eq, prof = float(latest.get('Balance', 0.0)), float(latest.get('Equity', 0.0)), float(latest.get('TotalProfit', 0.0))
                lots = float(latest.get('BuyLots', 0.0)) + float(latest.get('SellLots', 0.0))
                
                # PRICE DIRECTION TRACKER
                if 'prev_price' not in st.session_state: st.session_state.prev_price = price
                prev_p = st.session_state.prev_price
                if price > prev_p:
                    p_arrow = '<span style="color:#00e676; font-size:1.8rem; margin-left:10px; text-shadow:0 0 8px #00e676;">▲</span>'
                elif price < prev_p:
                    p_arrow = '<span style="color:#FFD700; font-size:1.8rem; margin-left:10px; text-shadow:0 0 8px #FFD700;">▼</span>'
                else:
                    p_arrow = '<span style="color:#546e7a; font-size:1.8rem; margin-left:10px;">—</span>'

                max_scale = max(bal, eq) * 1.2
                eq_pct, bal_pct = (eq/max_scale)*100, (bal/max_scale)*100
                gold_bar_html = f'<div class="main-bar-fill-gold" style="left: {eq_pct}%; width: {bal_pct-eq_pct}%;"></div>' if eq < bal else ""
                prof_color = "#00e676" if prof >= 0 else "#FFD700"

                h_html = f"""
<div class="hud-box">
<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px;">
<div><div class="hud-label">MARKET PRICE</div><div style="display:flex; align-items:center;"><div class="hud-value-blue">{price:,.2f}</div>{p_arrow}</div></div>
<div style="text-align:right;"><div class="hud-label">BALANCE</div><div class="hud-value-sub">{bal:,.2f}</div></div>
</div>
<div class="main-bar-container">
<div class="main-bar-marker" style="left: {bal_pct}%" title="BALANCE: {bal:,.2f}"></div>
<div class="main-bar-fill-blue" style="width: {eq_pct}%;" title="EQUITY: {eq:,.2f}"></div>
{gold_bar_html}
</div>
<div style="display:flex; justify-content:space-between; margin-top:10px;">
<div style="text-align:left;">
<div class="hud-label">EQUITY / P&L</div>
<div style="display:flex; align-items:baseline; gap:8px; margin-top:2px;">
<span style="color:#00e5ff; font-size: 1.2rem; font-weight: bold;">{eq:,.2f}</span>
<span style="color:{prof_color}; font-size: 1.2rem; font-weight: bold;">({prof:+,.2f})</span>
</div>
</div>
<div style="text-align:right;">
<div class="hud-label">TOTAL LOTS</div>
<div style="color:#fff; font-size: 1.2rem; font-weight: bold; margin-top:2px;">{lots:,.2f}</div>
</div>
</div>
</div>"""
                st.markdown(h_html, unsafe_allow_html=True)

                st.markdown('<div class="hud-label" style="margin-top:10px; margin-bottom:15px;">ACTIVE MODULE ANALYSIS</div>', unsafe_allow_html=True)
                
                orders_str = latest.get('JSON_Data', '[]')
                orders = json.loads(orders_str if pd.notna(orders_str) and orders_str != "" else "[]")
                
                if orders:
                    orders_df = pd.DataFrame(orders)
                    orders_df.rename(columns={'s': 'Symbol', 't': 'Type', 'v': 'Volume', 'p': 'Open Price', 'pl': 'Profit', 'm': 'Magic'}, inplace=True)
                    
                    orders_df['WVal'] = orders_df['Volume'] * orders_df['Open Price']
                    magic_stats = orders_df.groupby('Magic').agg({
                        'Type': 'first', 'Magic': 'count', 'Volume': 'sum', 'Profit': 'sum', 'Open Price': ['min', 'max']
                    })
                    magic_stats.columns = ['Type', 'Count', 'Lots', 'Profit', 'MinP', 'MaxP']
                    magic_stats = magic_stats.reset_index()
                    
                    be_map = orders_df.groupby('Magic')['WVal'].sum() / orders_df.groupby('Magic')['Volume'].sum()
                    magic_stats['BEP'] = magic_stats['Magic'].map(be_map)
                    
                    max_abs_prof = magic_stats['Profit'].abs().max() or 1
                    max_sqrt_prof = math.sqrt(max_abs_prof)
                    
                    for _, m in magic_stats.iterrows():
                        m_orders = orders_df[orders_df['Magic'] == m['Magic']]
                        first_lot = m_orders.iloc[0]['Volume']
                        
                        p_pct = (math.sqrt(abs(m['Profit'])) / max_sqrt_prof) * 50
                        if abs(m['Profit']) > 0 and p_pct < 2: p_pct = 2 
                        p_col = "#00e676" if m['Profit'] >= 0 else "#FFD700"
                        p_style = f"left:50%; width:{p_pct}%; background:{p_col};" if m['Profit'] >= 0 else f"right:50%; width:{p_pct}%; background:{p_col};"
                        
                        num_ticks = min(m['Count'], 50)
                        active_cls = "active-buy" if m['Type'] == "Buy" else "active-gold"
                        vu_ticks_html = "".join([f'<div class="vu-tick {active_cls}"></div>' for _ in range(num_ticks)])
                        vu_ticks_html += "".join(['<div class="vu-tick"></div>' for _ in range(max(0, 50 - num_ticks))])
                        overflow_html = '<span class="vu-overflow">▶</span>' if m['Count'] > 50 else ''
                        
                        curr_abs_d = abs(m['BEP'] - price)
                        prev_abs_d = abs(m['BEP'] - prev_p)
                        if curr_abs_d < prev_abs_d: d_icon, d_icon_col = '»«', "#00e676"
                        elif curr_abs_d > prev_abs_d: d_icon, d_icon_col = '«»', "#FFD700"
                        else: d_icon, d_icon_col = '↔', "#546e7a"

                        all_vals = [m['MinP'], m['MaxP'], m['BEP'], price]
                        s_min, s_max = min(all_vals), max(all_vals)
                        s_range = (s_max - s_min) or 1
                        def get_pct(v): return ((v - s_min) / s_range) * 100
                        
                        # สร้าง Ticks สำหรับออเดอร์พร้อมฟีเจอร์แสดงราคาเมื่อแตะ
                        order_ticks = ""
                        for op in m_orders['Open Price']:
                            is_main = "tick-main" if op in [m["MinP"], m["MaxP"]] else ""
                            label = "Max Price" if op == m["MaxP"] else ("Min Price" if op == m["MinP"] else "Order Price")
                            order_ticks += f'<div class="tick-order {is_main}" style="left:{get_pct(op)}%" title="{label}: {op:,.2f}"></div>'
                        
                        raw_dist = m['BEP'] - price if m['Type'] == 'Buy' else price - m['BEP']
                        dist_str = f"✅ {abs(raw_dist):,.2f}" if raw_dist <= 0 else f"⚠️ {abs(raw_dist):,.2f}"

                        m_html = f"""
<div class="module-card">
<div class="id-row">
<div class="square-box box-magic">{m['Magic']}</div>
<div class="square-box {"box-buy" if m['Type'] == 'Buy' else "box-gold"}">{m['Type']}</div>
<div class="square-box box-lots">{m['Lots']:,.2f} L</div>
<span class="text-first-lot">({first_lot:,.2f})</span>
</div>
<div class="p-row">
<div class="div-track"><div class="div-center"></div><div class="div-fill" style="{p_style} box-shadow: 0 0 5px {p_col}"></div></div>
<div class="data-text" style="color:{p_col}">{m['Profit']:+,.2f}</div>
</div>
<div class="vu-row">
<div class="vu-meter">{vu_ticks_html}{overflow_html}</div>
<div class="square-box box-count">{m['Count']}</div>
</div>
<div class="scale-row">
<div class="price-scale">
{order_ticks}
<div class="tick-order tick-be" style="left:{get_pct(m['BEP'])}%" title="BE Price: {m['BEP']:,.2f}"></div>
<div class="tick-current" style="left:{get_pct(price)}%" title="Market Price: {price:,.2f}"></div>
</div>
<div class="data-text" style="color:{d_icon_col}"><span style="font-size:1.1rem; vertical-align:middle;">{d_icon}</span> <span style="color:{'#00e676' if raw_dist <= 0 else '#FFD700'}">{dist_str}</span></div>
</div>
</div>"""
                        st.markdown(m_html, unsafe_allow_html=True)

                    st.session_state.prev_price = price

                    # --- PART 3: STRUCTURE GRAPH ---
                    st.markdown('<div class="section-title">PORTFOLIO STRUCTURE MAP</div>', unsafe_allow_html=True)
                    fig_p = go.Figure()
                    fig_p.add_hline(y=price, line_dash="dash", line_color="#29B6F6", line_width=1, annotation_text="Market")
                    fig_p.add_trace(go.Scatter(x=orders_df['Magic'].astype(str), y=orders_df['Open Price'], mode='markers', marker=dict(symbol='line-ew', size=25, line=dict(width=1, color="rgba(255, 255, 255, 0.25)")), hoverinfo='skip'))
                    fig_p.add_trace(go.Scatter(x=magic_stats['Magic'].astype(str), y=magic_stats['MaxP'], mode='markers', marker=dict(symbol='line-ew', size=30, line=dict(width=3, color="#FFD700")), name="Max", hovertemplate="Max: %{y:,.2f}<extra></extra>"))
                    fig_p.add_trace(go.Scatter(x=magic_stats['Magic'].astype(str), y=magic_stats['MinP'], mode='markers', marker=dict(symbol='line-ew', size=30, line=dict(width=3, color="#00C853")), name="Min", hovertemplate="Min: %{y:,.2f}<extra></extra>"))
                    fig_p.add_trace(go.Scatter(x=magic_stats['Magic'].astype(str), y=magic_stats['BEP'], mode='markers', marker=dict(symbol='line-ew', size=40, line=dict(width=4, color="#FFD600")), name="BE", hovertemplate="BE: %{y:,.2f}<extra></extra>"))
                    
                    labels = ["{}<br><span style='color:{}'>{}</span>:{}".format(m_id, ("#00C853" if t=="Buy" else "#FFD700"), t, c) for m_id, t, c in zip(magic_stats['Magic'], magic_stats['Type'], magic_stats['Count'])]
                    fig_p.add_trace(go.Scatter(x=magic_stats['Magic'].astype(str), y=magic_stats['MaxP'], mode='text', text=labels, textposition="top center", textfont=dict(color='#E0E0E0', size=11), hoverinfo='skip'))
                    fig_p.update_layout(xaxis=dict(showticklabels=False, type='category', gridcolor='#333'), yaxis=dict(gridcolor='#222', tickfont=dict(color='gray', size=10)), margin=dict(l=40, r=20, t=40, b=20), height=350, showlegend=False, paper_bgcolor='#050505', plot_bgcolor='#050505')
                    st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})

                    # --- PART 4: SUMMARY TABLE ---
                    st.markdown('<div class="hud-label" style="margin-top:20px; margin-bottom:15px;">MISSION DATA LOG SUMMARY</div>', unsafe_allow_html=True)
                    summary_df = magic_stats[['Magic', 'Type', 'Count', 'Lots', 'BEP', 'Profit']].copy()
                    def get_t_dist(row):
                        d = row['BEP'] - price if row['Type'] == 'Buy' else price - row['BEP']
                        return f"✅ {abs(d):,.2f}" if d <= 0 else f"⚠️ {abs(d):,.2f}"
                    summary_df['DIST'] = summary_df.apply(get_t_dist, axis=1)
                    summary_df.columns = ['MAGIC', 'TYPE', 'ORDERS', 'LOTS', 'BE_PRICE', 'PROFIT', 'DIST']
                    for c in ['LOTS', 'BE_PRICE', 'PROFIT']: summary_df[c] = summary_df[c].map('{:,.2f}'.format)
                    st.dataframe(summary_df.style.map(lambda v: f'color: {"#00C853" if v == "Buy" else "#FFD700"}; font-weight: bold', subset=['TYPE']), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"SYSTEM FAILURE: {e}")

time.sleep(5)
st.rerun()
