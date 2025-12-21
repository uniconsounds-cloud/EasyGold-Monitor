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

# --- HUD CSS STYLING (The Sci-Fi Look) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;700&display=swap');

    /* 1. Reset & Main Theme */
    .block-container { padding: 0.5rem 0.5rem 3rem 0.5rem; }
    header, footer { visibility: hidden; }
    .stApp { background-color: #050505; }
    
    /* 2. HUD Container */
    .hud-container {
        font-family: 'Rajdhani', sans-serif;
        color: #e0f7fa;
        background: #0a0f14;
        border: 1px solid #1c2530;
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 15px;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.05);
        position: relative;
    }
    
    /* Corner Accents (ขีดมุมฉากแบบในหนัง) */
    .hud-container::before {
        content: ""; position: absolute; top: -1px; left: -1px; width: 20px; height: 20px;
        border-top: 2px solid #00e5ff; border-left: 2px solid #00e5ff;
    }
    .hud-container::after {
        content: ""; position: absolute; bottom: -1px; right: -1px; width: 20px; height: 20px;
        border-bottom: 2px solid #00e5ff; border-right: 2px solid #00e5ff;
    }

    /* 3. Header Section (Price & Balance) */
    .hud-header {
        display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 10px;
    }
    .hud-price-box { text-align: left; }
    .hud-label { font-size: 0.8rem; color: #546e7a; text-transform: uppercase; letter-spacing: 2px; }
    .hud-value-big { 
        font-family: 'Share Tech Mono', monospace; 
        font-size: 2.2rem; color: #00e5ff; 
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.6);
    }
    
    /* 4. Health Bar (หลอดพลังงาน) */
    .health-bar-container {
        width: 100%; height: 8px; background: #1c2530; margin: 5px 0 15px 0; position: relative;
    }
    .health-fill { height: 100%; transition: width 0.5s; box-shadow: 0 0 8px currentColor; }
    .health-marker { 
        position: absolute; top: -4px; width: 2px; height: 16px; background: #fff; z-index: 10;
        box-shadow: 0 0 5px white;
    }

    /* 5. Magic Module Grid */
    .magic-grid { display: grid; gap: 8px; }
    
    /* 6. Magic Card (แต่ละแถว) */
    .magic-card {
        background: rgba(255, 255, 255, 0.02);
        border-left: 3px solid #333;
        padding: 8px 10px;
        display: flex; align-items: center; justify-content: space-between;
    }
    .magic-id { font-family: 'Share Tech Mono', monospace; font-size: 1.1rem; color: #b0bec5; width: 60px; }
    
    /* Badge (Buy/Sell) */
    .badge { 
        padding: 2px 6px; font-size: 0.7rem; font-weight: bold; border-radius: 2px; 
        text-transform: uppercase; width: 40px; text-align: center; display: inline-block;
    }
    .badge-buy { background: rgba(0, 200, 83, 0.2); color: #00e676; border: 1px solid #00e676; }
    .badge-sell { background: rgba(213, 0, 0, 0.2); color: #ff1744; border: 1px solid #ff1744; }

    /* Bar Chart in Card (Diverging Bar) */
    .bar-wrapper { flex-grow: 1; margin: 0 15px; height: 6px; background: #1c2530; position: relative; display: flex; align-items: center; }
    .bar-center-line { position: absolute; left: 50%; width: 1px; height: 100%; background: #555; z-index: 1; }
    .bar-fill { height: 100%; opacity: 0.8; }
    
    .stats-group { text-align: right; min-width: 80px; }
    .stat-lot { font-size: 0.9rem; font-weight: bold; color: #fff; }
    .stat-profit { font-size: 0.8rem; font-family: 'Share Tech Mono'; }
    
    /* Utility Colors */
    .c-green { color: #00e676; }
    .c-red { color: #ff1744; }
    .c-blue { color: #00e5ff; }

</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
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
    st.warning("Establishing Link...")
    time.sleep(2)
    st.rerun()
else:
    try:
        df['AccountID'] = df['AccountID'].astype(str)
        all_accounts = df['AccountID'].unique().tolist()
        
        # --- SELECTOR (Hidden in plain sight style) ---
        if len(all_accounts) > 0:
            selected_account = st.selectbox("MISSION TARGET", all_accounts, index=0)
        else:
            selected_account = None
        
        if selected_account:
            target_df = df[df['AccountID'] == selected_account]

            if not target_df.empty:
                latest = target_df.iloc[-1]
                
                # --- DATA EXTRACTION ---
                current_price = float(latest.get('CurrentPrice', 0.0))
                balance = float(latest.get('Balance', 0.0))
                equity = float(latest.get('Equity', 0.0))
                profit = float(latest.get('TotalProfit', 0.0))
                total_lots = float(latest.get('BuyLots', 0.0)) + float(latest.get('SellLots', 0.0))
                
                # Health Bar Logic
                health_color = "#00e676" if profit >= 0 else "#ff1744"
                max_val = max(balance, equity) * 1.2
                eq_percent = (equity / max_val) * 100 if max_val > 0 else 0
                bal_percent = (balance / max_val) * 100 if max_val > 0 else 0

                # --- 1. HUD HEADER SECTION ---
                html_header = f"""
                <div class="hud-container">
                    <div class="hud-header">
                        <div class="hud-price-box">
                            <div class="hud-label">MARKET PRICE</div>
                            <div class="hud-value-big">{current_price:,.2f}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="hud-label">NET EQUITY</div>
                            <div class="hud-value-big" style="color: {health_color}; font-size: 1.8rem;">{equity:,.0f}</div>
                        </div>
                    </div>
                    
                    <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:#777; margin-bottom:2px;">
                        <span>0</span>
                        <span>BALANCE: {balance:,.0f}</span>
                    </div>
                    <div class="health-bar-container">
                        <div class="health-marker" style="left: {bal_percent}%;"></div>
                        <div class="health-fill" style="width: {eq_percent}%; background-color: {health_color};"></div>
                    </div>
                    
                    <div style="display:flex; justify-content:space-between; margin-top:5px;">
                         <div><span class="hud-label">TOTAL LOTS:</span> <span style="color:#fff; font-weight:bold;">{total_lots:.2f}</span></div>
                         <div><span class="hud-label">P/L:</span> <span style="color:{health_color}; font-weight:bold;">{profit:+,.2f}</span></div>
                    </div>
                </div>
                """
                st.markdown(html_header, unsafe_allow_html=True)

                # --- 2. MAGIC MODULES (INFOGRAPHIC LIST) ---
                
                orders_str = latest.get('JSON_Data', '[]')
                if pd.isna(orders_str) or orders_str == "": orders_str = '[]'
                
                try:
                    orders = json.loads(orders_str)
                    if len(orders) > 0:
                        orders_df = pd.DataFrame(orders)
                        orders_df.rename(columns={'s': 'Symbol', 't': 'Type', 'v': 'Volume', 'p': 'Open Price', 'pl': 'Profit', 'm': 'Magic'}, inplace=True)
                        
                        if 'Magic' in orders_df.columns:
                            # Group Data
                            magic_stats = orders_df.groupby('Magic').agg(
                                OrderType=('Type', 'first'),
                                OrderCount=('Magic', 'count'),
                                TotalLots=('Volume', 'sum'),
                                TotalProfit=('Profit', 'sum')
                            ).reset_index()
                            
                            # Find Max Abs Profit for Scaling Bars
                            max_abs_profit = magic_stats['TotalProfit'].abs().max()
                            if max_abs_profit == 0: max_abs_profit = 1

                            st.markdown('<div class="hud-label" style="margin-bottom:8px;">ACTIVE MODULES</div>', unsafe_allow_html=True)
                            
                            html_magic_rows = '<div class="magic-grid">'
                            
                            for index, row in magic_stats.iterrows():
                                m_id = row['Magic']
                                m_type = row['OrderType']
                                m_count = row['OrderCount']
                                m_lots = row['TotalLots']
                                m_profit = row['TotalProfit']
                                
                                # Badge Style
                                badge_class = "badge-buy" if m_type == "Buy" else "badge-sell"
                                border_color = "#00e676" if m_type == "Buy" else "#ff1744"
                                
                                # Bar Logic (Diverging Bar)
                                # 50% is center. 
                                # Profit moves right (50% -> 100%), Loss moves left (50% -> 0%)
                                bar_percent = (abs(m_profit) / max_abs_profit) * 50
                                bar_color = "#00e676" if m_profit >= 0 else "#ff1744"
                                
                                bar_html = ""
                                if m_profit >= 0:
                                    # Profit: Start at 50%, width goes right
                                    bar_html = f'<div class="bar-fill" style="position:absolute; left:50%; width:{bar_percent}%; background:{bar_color}; box-shadow: 0 0 5px {bar_color};"></div>'
                                else:
                                    # Loss: End at 50%, width goes left
                                    bar_html = f'<div class="bar-fill" style="position:absolute; right:50%; width:{bar_percent}%; background:{bar_color}; box-shadow: 0 0 5px {bar_color};"></div>'

                                row_html = f"""
                                <div class="magic-card" style="border-left-color: {border_color};">
                                    <div style="display:flex; flex-direction:column; align-items:center; margin-right:10px;">
                                        <div class="magic-id">{m_id}</div>
                                        <div class="badge {badge_class}">{m_type}</div>
                                    </div>
                                    
                                    <div class="bar-wrapper">
                                        <div class="bar-center-line"></div>
                                        {bar_html}
                                    </div>
                                    
                                    <div class="stats-group">
                                        <div class="stat-lot">{m_lots:,.2f} <span style="font-size:0.7rem; color:#777;">LOT</span></div>
                                        <div class="stat-profit" style="color: {bar_color};">{m_profit:+,.0f} <span style="font-size:0.7rem; color:#777;">$</span></div>
                                        <div style="font-size:0.7rem; color:#555;">CNT: {m_count}</div>
                                    </div>
                                </div>
                                """
                                html_magic_rows += row_html
                            
                            html_magic_rows += "</div>"
                            st.markdown(html_magic_rows, unsafe_allow_html=True)
                            
                        else:
                            st.info("NO DATA STREAM")
                except Exception as e:
                    st.error(f"PARSING ERROR: {e}")

            else:
                st.warning("WAITING FOR SIGNAL...")
    except Exception as main_e:
        st.error(f"SYSTEM FAILURE: {main_e}")

time.sleep(5)
st.rerun()
