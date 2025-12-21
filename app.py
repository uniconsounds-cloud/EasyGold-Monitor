import streamlit as st
import pandas as pd
import json
import time
import textwrap  # เพิ่ม module นี้เพื่อแก้ปัญหา HTML ย่อหน้า

# ---------------------------------------------------------
# 🛠 ใส่ SHEET ID ของคุณตรงนี้ 🛠
SHEET_ID = "ใส่_SHEET_ID_ของคุณตรงนี้"
# ---------------------------------------------------------

SHEET_URL = f"https://docs.google.com/spreadsheets/d/1BdkpzNz5lqECpnyc7PgC1BQMc5FeOyqkE_lonF36ANQ/export?format=csv"

st.set_page_config(page_title="Tactical Monitor", page_icon="🛸", layout="wide")

# =========================================================
# 1. CSS STYLING
# =========================================================
css_styles = """
<style>
    /* Main Layout */
    .block-container { padding: 0.5rem 0.5rem 3rem 0.5rem; }
    header, footer { visibility: hidden; }
    .stApp { background-color: #050505; color: #e0f7fa; font-family: 'Courier New', Courier, monospace; }

    /* HUD Box Container */
    .hud-box {
        background: #0a0f14;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 0 15px rgba(0, 229, 255, 0.1);
        border-left: 4px solid #00e5ff;
        position: relative;
    }
    
    /* Typography */
    .hud-label { font-size: 0.8rem; color: #546e7a; letter-spacing: 2px; font-weight: bold; margin-bottom: 2px; }
    .hud-value { font-size: 2.2rem; color: #00e5ff; font-weight: bold; text-shadow: 0 0 10px rgba(0, 229, 255, 0.6); line-height: 1; }
    
    /* Health Bar */
    .bar-container { width: 100%; height: 10px; background: #1c2530; margin: 10px 0; position: relative; border-radius: 2px; }
    .bar-fill { height: 100%; transition: width 0.5s; }
    .bar-marker { position: absolute; top: -3px; width: 2px; height: 16px; background: white; z-index: 2; box-shadow: 0 0 5px white; }

    /* Magic Card List */
    .magic-row {
        display: flex; align-items: center; justify-content: space-between;
        background: rgba(255, 255, 255, 0.03);
        margin-bottom: 8px; padding: 10px;
        border-radius: 2px; border-right: 3px solid #333;
    }
    .badge { padding: 3px 8px; font-size: 0.75rem; font-weight: bold; border-radius: 2px; min-width: 50px; text-align: center; }
    .badge-buy { background: rgba(0, 230, 118, 0.15); color: #00e676; border: 1px solid #00e676; }
    .badge-sell { background: rgba(255, 23, 68, 0.15); color: #ff1744; border: 1px solid #ff1744; }

    /* Diverging Bar */
    .div-bar-track { flex-grow: 1; height: 6px; background: #222; margin: 0 20px; position: relative; display: flex; align-items: center; }
    .div-bar-center { position: absolute; left: 50%; width: 1px; height: 10px; background: #666; }
    .div-bar-fill { height: 100%; position: absolute; opacity: 0.9; }
</style>
"""
st.markdown(css_styles, unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        if 'CurrentPrice' not in df.columns: df['CurrentPrice'] = 0.0 
        return df
    except:
        return None

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
        
        # --- SELECTOR ---
        if len(all_accounts) > 0:
            selected_account = st.selectbox("MISSION TARGET", all_accounts, index=0)
        else:
            selected_account = None
        
        if selected_account:
            target_df = df[df['AccountID'] == selected_account]

            if not target_df.empty:
                latest = target_df.iloc[-1]
                
                # Extract Data
                current_price = float(latest.get('CurrentPrice', 0.0))
                balance = float(latest.get('Balance', 0.0))
                equity = float(latest.get('Equity', 0.0))
                profit = float(latest.get('TotalProfit', 0.0))
                total_lots = float(latest.get('BuyLots', 0.0)) + float(latest.get('SellLots', 0.0))
                
                # Logic for Visuals
                status_color = "#00e676" if profit >= 0 else "#ff1744"
                max_scale = max(balance, equity) * 1.2
                if max_scale == 0: max_scale = 1
                eq_pct = (equity / max_scale) * 100
                bal_pct = (balance / max_scale) * 100

                # ==========================================
                # 3. RENDER HUD HEADER (Overview)
                # ==========================================
                
                # ใช้ textwrap.dedent เพื่อลบช่องว่างข้างหน้าทิ้ง ป้องกัน Markdown มองเป็น Code Block
                header_html = textwrap.dedent(f"""
                    <div class="hud-box">
                        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px;">
                            <div>
                                <div class="hud-label">MARKET PRICE</div>
                                <div class="hud-value">{current_price:,.2f}</div>
                            </div>
                            <div style="text-align:right;">
                                <div class="hud-label">NET EQUITY</div>
                                <div class="hud-value" style="color: {status_color};">{equity:,.0f}</div>
                            </div>
                        </div>
                        
                        <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:#aaa;">
                            <span>0</span>
                            <span>BALANCE: {balance:,.0f}</span>
                        </div>
                        <div class="bar-container">
                            <div class="bar-marker" style="left: {bal_pct}%;"></div>
                            <div class="bar-fill" style="width: {eq_pct}%; background: {status_color}; box-shadow: 0 0 8px {status_color};"></div>
                        </div>
                        
                        <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-top:5px; border-top:1px solid #333; padding-top:5px;">
                            <div>TOTAL LOTS: <b style="color:#fff">{total_lots:.2f}</b></div>
                            <div>P/L: <b style="color:{status_color}">{profit:+,.2f}</b></div>
                        </div>
                    </div>
                """)
                st.markdown(header_html, unsafe_allow_html=True)

                # ==========================================
                # 4. RENDER ACTIVE MODULES (List)
                # ==========================================
                st.markdown('<div class="hud-label" style="margin-top:20px; margin-bottom:10px;">ACTIVE MODULES</div>', unsafe_allow_html=True)

                orders_str = latest.get('JSON_Data', '[]')
                if pd.isna(orders_str) or orders_str == "": orders_str = '[]'
                
                try:
                    orders = json.loads(orders_str)
                    if len(orders) > 0:
                        orders_df = pd.DataFrame(orders)
                        orders_df.rename(columns={'s': 'Symbol', 't': 'Type', 'v': 'Volume', 'p': 'Open Price', 'pl': 'Profit', 'm': 'Magic'}, inplace=True)
                        
                        if 'Magic' in orders_df.columns:
                            magic_stats = orders_df.groupby('Magic').agg(
                                OrderType=('Type', 'first'),
                                OrderCount=('Magic', 'count'),
                                TotalLots=('Volume', 'sum'),
                                TotalProfit=('Profit', 'sum')
                            ).reset_index()

                            max_abs_profit = magic_stats['TotalProfit'].abs().max()
                            if max_abs_profit == 0: max_abs_profit = 1
                            
                            rows_html = ""
                            
                            for index, row in magic_stats.iterrows():
                                m_id = row['Magic']
                                m_type = row['OrderType']
                                m_count = row['OrderCount']
                                m_lots = row['TotalLots']
                                m_profit = row['TotalProfit']
                                
                                if m_type == "Buy":
                                    badge_cls = "badge-buy"
                                    border_col = "#00e676"
                                else:
                                    badge_cls = "badge-sell"
                                    border_col = "#ff1744"
                                
                                pct_len = (abs(m_profit) / max_abs_profit) * 50
                                bar_col = "#00e676" if m_profit >= 0 else "#ff1744"
                                
                                if m_profit >= 0:
                                    bar_div = f'<div class="div-bar-fill" style="left: 50%; width: {pct_len}%; background: {bar_col};"></div>'
                                else:
                                    bar_div = f'<div class="div-bar-fill" style="right: 50%; width: {pct_len}%; background: {bar_col};"></div>'

                                # ใช้ textwrap.dedent ในลูปย่อยด้วย
                                rows_html += textwrap.dedent(f"""
                                    <div class="magic-row" style="border-left: 3px solid {border_col};">
                                        <div style="text-align:center; min-width:60px;">
                                            <div style="font-weight:bold; color:#b0bec5; font-size:1rem;">{m_id}</div>
                                            <div class="badge {badge_cls}">{m_type}</div>
                                        </div>
                                        
                                        <div class="div-bar-track">
                                            <div class="div-bar-center"></div>
                                            {bar_div}
                                        </div>
                                        
                                        <div style="text-align:right; min-width:80px;">
                                            <div style="font-weight:bold; color:#fff;">{m_lots:.2f} <span style="font-size:0.7rem; color:#777;">LOT</span></div>
                                            <div style="color:{bar_col}; font-weight:bold;">{m_profit:+,.0f} $</div>
                                            <div style="font-size:0.7rem; color:#555;">CNT: {m_count}</div>
                                        </div>
                                    </div>
                                """)
                            
                            st.markdown(rows_html, unsafe_allow_html=True)
                            
                        else:
                            st.info("NO MAGIC DATA AVAILABLE")
                    else:
                        st.info("NO ACTIVE ORDERS")
                
                except Exception as e:
                    st.error(f"DATA PARSE ERROR: {e}")

            else:
                st.warning("WAITING FOR SIGNAL...")
    except Exception as main_e:
        st.error(f"SYSTEM ERROR: {main_e}")

time.sleep(5)
st.rerun()
