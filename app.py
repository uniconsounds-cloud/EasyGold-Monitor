import streamlit as st
import pandas as pd
import json
import time
import plotly.graph_objects as go

# ---------------------------------------------------------
# 🛠 ใส่ SHEET ID ของคุณตรงนี้ 🛠
SHEET_ID = "ใส่_SHEET_ID_ของคุณตรงนี้"
# ---------------------------------------------------------

SHEET_URL = f"https://docs.google.com/spreadsheets/d/1BdkpzNz5lqECpnyc7PgC1BQMc5FeOyqkE_lonF36ANQ/export?format=csv"

st.set_page_config(page_title="Tactical Monitor", page_icon="🛸", layout="wide")

# --- 1. CSS STYLING (Sci-Fi HUD Theme) ---
st.markdown("""
<style>
    .block-container { padding: 0.5rem 0.5rem 3rem 0.5rem; }
    header, footer { visibility: hidden; }
    .stApp { background-color: #050505; color: #e0f7fa; font-family: 'Courier New', Courier, monospace; }

    .hud-box {
        background: #0a0f14;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 0 15px rgba(0, 229, 255, 0.1);
        border-left: 4px solid #00e5ff;
    }
    
    .hud-label { font-size: 0.8rem; color: #546e7a; letter-spacing: 2px; font-weight: bold; }
    .hud-value { font-size: 2.2rem; color: #00e5ff; font-weight: bold; text-shadow: 0 0 10px rgba(0, 229, 255, 0.6); line-height: 1; }
    
    .bar-container { width: 100%; height: 12px; background: #1c2530; margin: 10px 0; position: relative; border-radius: 2px; }
    .bar-fill { height: 100%; transition: width 0.5s; }
    .bar-marker { position: absolute; top: -3px; width: 2px; height: 18px; background: white; z-index: 2; box-shadow: 0 0 5px white; }

    .section-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #E0E0E0;
        border-left: 4px solid #29B6F6;
        padding-left: 10px;
        margin-top: 25px;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        if 'CurrentPrice' not in df.columns: df['CurrentPrice'] = 0.0 
        return df
    except:
        return None

def highlight_type(val):
    color = '#00C853' if val == 'Buy' else '#D50000'
    return f'color: {color}; font-weight: bold'

# =========================================================
# Main Loop
# =========================================================

df = load_data()

if df is None:
    st.warning("Connecting to Satellite...")
    time.sleep(2)
    st.rerun()
else:
    try:
        df['AccountID'] = df['AccountID'].astype(str)
        all_accounts = df['AccountID'].unique().tolist()
        
        if len(all_accounts) > 0:
            selected_account = st.selectbox("MISSION TARGET", all_accounts, index=0)
        else:
            selected_account = None
        
        if selected_account:
            target_df = df[df['AccountID'] == selected_account]

            if not target_df.empty:
                latest = target_df.iloc[-1]
                
                # ดึงข้อมูล
                price = float(latest.get('CurrentPrice', 0.0))
                bal = float(latest.get('Balance', 0.0))
                eq = float(latest.get('Equity', 0.0))
                prof = float(latest.get('TotalProfit', 0.0))
                lots = float(latest.get('BuyLots', 0.0)) + float(latest.get('SellLots', 0.0))
                
                status_color = "#00e676" if prof >= 0 else "#ff1744"
                max_scale = max(bal, eq) * 1.2
                eq_pct = (eq / max_scale) * 100 if max_scale > 0 else 0
                bal_pct = (bal / max_scale) * 100 if max_scale > 0 else 0

                # --- 3. RENDER HUD HEADER (Overview & Health) ---
                h_html = '<div class="hud-box">'
                h_html += '<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px;">'
                h_html += '<div><div class="hud-label">MARKET PRICE</div>'
                h_html += '<div class="hud-value">{:,.2f}</div></div>'.format(price)
                h_html += '<div style="text-align:right;"><div class="hud-label">NET EQUITY</div>'
                h_html += '<div class="hud-value" style="color:{}"> {:,.0f}</div></div>'.format(status_color, eq)
                h_html += '</div>'
                h_html += '<div style="display:flex; justify-content:space-between; font-size:0.7rem; color:#aaa;"><span>0</span><span>BALANCE: {:,.0f}</span></div>'.format(bal)
                h_html += '<div class="bar-container">'
                h_html += '<div class="bar-marker" style="left: {:.2f}%"></div>'.format(bal_pct)
                h_html += '<div class="bar-fill" style="width: {:.2f}%; background: {}; box-shadow: 0 0 8px {};"></div>'.format(eq_pct, status_color, status_color)
                h_html += '</div>'
                h_html += '<div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-top:5px; border-top:1px solid #333; padding-top:5px;">'
                h_html += '<div>TOTAL EXPOSURE: <b style="color:#fff">{:.2f} LOTS</b></div>'.format(lots)
                h_html += '<div>PROFIT/LOSS: <b style="color:{}">{:+,.2f} USD</b></div>'.format(status_color, prof)
                h_html += '</div></div>'
                
                st.markdown(h_html, unsafe_allow_html=True)

                # --- 4. RENDER MIDDLE GRAPH (Portfolio Structure) ---
                st.markdown('<div class="section-title">Portfolio Structure</div>', unsafe_allow_html=True)

                orders_str = latest.get('JSON_Data', '[]')
                if pd.isna(orders_str) or orders_str == "": orders_str = '[]'
                
                try:
                    orders = json.loads(orders_str)
                    if len(orders) > 0:
                        orders_df = pd.DataFrame(orders)
                        orders_df.rename(columns={'s': 'Symbol', 't': 'Type', 'v': 'Volume', 'p': 'Open Price', 'pl': 'Profit', 'm': 'Magic'}, inplace=True)
                        
                        if 'Magic' in orders_df.columns:
                            # คำนวณสถิติ
                            orders_df['WeightedVal'] = orders_df['Volume'] * orders_df['Open Price']
                            magic_stats = orders_df.groupby('Magic').agg(
                                AvgPrice=('WeightedVal', 'sum'), TotalVol=('Volume', 'sum'),
                                MinPrice=('Open Price', 'min'), MaxPrice=('Open Price', 'max'),
                                OrderCount=('Magic', 'count'), OrderType=('Type', 'first')
                            ).reset_index()
                            magic_stats['AvgPrice'] = magic_stats['AvgPrice'] / magic_stats['TotalVol']
                            
                            fig_p = go.Figure()

                            # 1. เส้นราคาตลาด
                            fig_p.add_hline(
                                y=price, line_dash="dash", line_color="#29B6F6", line_width=1,
                                annotation_text="Market Price", annotation_position="top right"
                            )

                            # 2. วาดโครงสร้าง
                            fig_p.add_trace(go.Scatter(x=orders_df['Magic'].astype(str), y=orders_df['Open Price'], mode='markers', marker=dict(symbol='line-ew', size=25, line=dict(width=1, color="rgba(255, 255, 255, 0.25)")), hoverinfo='skip'))
                            fig_p.add_trace(go.Scatter(x=magic_stats['Magic'].astype(str), y=magic_stats['MaxPrice'], mode='markers', marker=dict(symbol='line-ew', size=30, line=dict(width=3, color="#D50000")), hoverinfo='skip'))
                            fig_p.add_trace(go.Scatter(x=magic_stats['Magic'].astype(str), y=magic_stats['MinPrice'], mode='markers', marker=dict(symbol='line-ew', size=30, line=dict(width=3, color="#00C853")), hoverinfo='skip'))
                            fig_p.add_trace(go.Scatter(x=magic_stats['Magic'].astype(str), y=magic_stats['AvgPrice'], mode='markers', marker=dict(symbol='line-ew', size=40, line=dict(width=4, color="#FFD600")), hoverinfo='skip'))
                            
                            # ป้ายชื่อ Magic และข้อมูลออเดอร์ (ยกขึ้นเล็กน้อย)
                            label_texts = []
                            for m, t, c in zip(magic_stats['Magic'], magic_stats['OrderType'], magic_stats['OrderCount']):
                                color_code = "#00C853" if t == "Buy" else "#D50000"
                                text_html = "{}<br><span style='color:{}'>{}</span> : {}".format(m, color_code, t, c)
                                label_texts.append(text_html)

                            fig_p.add_trace(go.Scatter(
                                x=magic_stats['Magic'].astype(str), y=magic_stats['MaxPrice'], mode='text',
                                text=label_texts, textposition="top center",
                                textfont=dict(color='#E0E0E0', size=11),
                                hoverinfo='skip'
                            ))

                            fig_p.update_layout(
                                xaxis=dict(showticklabels=False, type='category', gridcolor='#333'),
                                yaxis=dict(gridcolor='#222', tickfont=dict(color='gray', size=10)),
                                margin=dict(l=40, r=20, t=40, b=20), height=400, showlegend=False,
                                paper_bgcolor='#050505', plot_bgcolor='#050505'
                            )
                            st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})

                            # --- 5. RENDER BOTTOM TABLE (Magic Summary) ---
                            st.markdown('<div class="section-title">Magic Summary Detail</div>', unsafe_allow_html=True)
                            
                            summary_df = magic_stats[['Magic', 'OrderType', 'OrderCount', 'TotalVol', 'AvgPrice']].copy()
                            profit_df = orders_df.groupby('Magic')['Profit'].sum().reset_index()
                            summary_df = summary_df.merge(profit_df, on='Magic')
                            
                            # คำนวณระยะทางถึงจุด BE
                            summary_df['Dist'] = summary_df.apply(lambda r: r['AvgPrice'] - price if r['OrderType'] == 'Buy' else price - r['AvgPrice'], axis=1)
                            
                            summary_df.columns = ['MAGIC', 'TYPE', 'ORDERS', 'LOTS', 'BE PRICE', 'PROFIT', 'DIST']
                            
                            for c in ['LOTS', 'BE PRICE', 'PROFIT', 'DIST']:
                                summary_df[c] = summary_df[c].map('{:,.2f}'.format)
                            
                            st.dataframe(
                                summary_df.style.map(highlight_type, subset=['TYPE']), 
                                use_container_width=True, 
                                height=len(summary_df) * 35 + 38,
                                hide_index=True
                            )
                        else:
                            st.info("NO MAGIC DATA AVAILABLE")
                    else:
                        st.info("NO ACTIVE ORDERS")
                except Exception as e:
                    st.error(f"DATA ERROR: {e}")
            else:
                st.warning("ACCOUNT NOT FOUND.")
    except Exception as main_e:
        st.error(f"SYSTEM FAILURE: {main_e}")

time.sleep(5)
st.rerun()
