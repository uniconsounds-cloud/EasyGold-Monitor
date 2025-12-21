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

# --- CSS STYLING (Sci-Fi HUD Theme) ---
# ใช้ f-string แยกต่างหากเพื่อป้องกัน error เรื่องวงเล็บปีกกา
css_code = """
<style>
    /* 1. Main Layout & Font */
    .block-container { padding: 0.5rem 0.5rem 3rem 0.5rem; }
    header, footer { visibility: hidden; }
    .stApp { background-color: #050505; color: #e0f7fa; font-family: 'Courier New', Courier, monospace; }

    /* 2. HUD Box Container */
    .hud-box {
        background: #0a0f14;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.1);
        border-left: 3px solid #00e5ff;
    }

    /* 3. Typography */
    .hud-label { font-size: 0.8rem; color: #546e7a; letter-spacing: 1px; font-weight: bold; }
    .hud-value { font-size: 2rem; color: #00e5ff; font-weight: bold; text-shadow: 0 0 8px rgba(0, 229, 255, 0.5); }
    .hud-sub { font-size: 0.8rem; color: #777; }

    /* 4. Health Bar */
    .bar-bg { width: 100%; height: 8px; background: #1c2530; margin-top: 5px; position: relative; }
    .bar-fill { height: 100%; transition: width 0.5s; }
    .bar-marker { position: absolute; top: -3px; width: 2px; height: 14px; background: white; z-index: 2; }

    /* 5. Magic Card Grid */
    .magic-row {
        display: flex; align-items: center; justify-content: space-between;
        background: rgba(255, 255, 255, 0.03);
        margin-bottom: 6px; padding: 8px;
        border-radius: 2px; border-right: 2px solid #333;
    }
    
    /* 6. Badges */
    .badge { padding: 2px 6px; font-size: 0.7rem; font-weight: bold; border-radius: 2px; min-width: 40px; text-align: center; }
    .badge-buy { background: rgba(0, 230, 118, 0.15); color: #00e676; border: 1px solid #00e676; }
    .badge-sell { background: rgba(255, 23, 68, 0.15); color: #ff1744; border: 1px solid #ff1744; }

    /* 7. Diverging Bar */
    .div-bar-container { flex-grow: 1; height: 4px; background: #222; margin: 0 15px; position: relative; display: flex; align-items: center; }
    .div-bar-center { position: absolute; left: 50%; width: 1px; height: 8px; background: #555; }
    .div-bar-fill { height: 100%; position: absolute; }
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

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
                
                # Color Logic
                status_color = "#00e676" if profit >= 0 else "#ff1744"
                
                # Health Bar Calculation
                max_scale = max(balance, equity) * 1.2
                if max_scale == 0: max_scale = 1
                eq_pct = (equity / max_scale) * 100
                bal_pct = (balance / max_scale) * 100

                # ==========================================
                # 1. HEADER HUD (Overview)
                # ==========================================
                header_html = f"""
                <div class="hud-box">
                    <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                        <div>
                            <div class="hud-label">MARKET PRICE</div>
                            <div class="hud-value">{current_price
