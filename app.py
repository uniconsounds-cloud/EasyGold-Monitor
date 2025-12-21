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

st.set_page_config(page_title="Mobile Monitor", page_icon="📱", layout="wide")

# --- GLOBAL CSS STYLING ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Roboto', sans-serif; }
    
    .section-header {
        font-size: 1rem;
        font-weight: 700;
        color: #E0E0E0;
        border-left: 4px solid #29B6F6;
        padding-left: 10px;
        margin-top: 25px;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #1E222D; color: white; border-color: #444;
    }
    
    .metric-card {
        background-color: #1E222D;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS (ย้ายออกมาข้างนอกเพื่อแก้ Error) ---
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        if 'CurrentPrice' not in df.columns: df['CurrentPrice'] = 0.0 
        return df
    except:
        return None

def highlight_type(val):
    """ฟังก์ชันใส่สีตัวอักษรในตาราง"""
    color = '#00C853' if val == 'Buy' else '#D50000'
    return f'color: {color}; font-weight: bold'

# =========================================================
# Main Loop
# =========================================================

df = load_data()

if df is None:
    st.warning("Connecting...")
    time.sleep(2)
    st.rerun()
else:
    try:
        df['AccountID'] = df['AccountID'].astype(str)
        all_accounts = df['AccountID'].unique().tolist()
        
        # --- SECTION 1: ACCOUNT SELECTOR ---
        if len(all_accounts) > 0:
            selected_account = st.selectbox("SELECT ACCOUNT", all_accounts, index=0)
        else:
            selected_account = None
        
        if selected_account:
            target_df = df[df['AccountID'] == selected_account]

            if not target_df.empty:
                latest = target_df.iloc[-1]
                
                current_price = float(latest.get('CurrentPrice', 0.0))
                balance = float(latest.get('Balance', 0.0))
                equity = float(latest.get('Equity', 0.0))
                profit = float(latest.get('TotalProfit', 0.0))
                total_lots = float(latest.get('BuyLots', 0.0)) + float(latest.get('SellLots', 0.0))
                common_font = "Arial, sans-serif"

                # --- SECTION 2: MARKET OVERVIEW ---
                st.markdown('<div class="section-header">Market Overview</div>', unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="metric-card" style="display: flex; justify-content: space-between; align-items: center;">
                    <div style='text-align: left;'>
                        <div style='color: #9E9E9E; font-size: 0.75rem; font-weight: 600;'>GOLD PRICE (BID)</div>
                        <div style='color: #29B6F6; font-size: 1.6rem; font-weight: 800; margin-top: 2px;'>{current_price:,.2f}</div>
                    </div>
                    <div style='width: 1px; height: 40px; background-color: #333;'></div>
                    <div style='text-align: right;'>
                        <div style='color: #9E9E9E; font-size: 0.75rem; font-weight: 600;'>TOTAL EXPOSURE</div>
                        <div style='color: #FFA726; font-size: 1.6rem; font-weight: 800; margin-top: 2px;'>{total_lots:.2f}<span style='font-size: 0.8rem; color: #777; font-weight: 400;'> Lots</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # --- SECTION 3: ACCOUNT HEALTH ---
                st.markdown('<div class="section-header">Account Health</div>', unsafe_allow_html=True)
                
                BAR_FONT_SIZE = 16 

                fig = go.Figure()
                if profit >= 0:
                    fig.add_trace(go.Bar(x=[balance], y=[""], orientation='h', marker_color='#0288D1', hoverinfo='none'))
                    fig.add_trace(go.Bar(x=[profit], y=[""], orientation='h', marker_color='#00C853', hoverinfo='none', 
                                         text=f"Profit<br>{profit:,.0f}", textposition='inside', 
                                         textfont=dict(color='white', size=BAR_FONT_SIZE, family=common_font, weight='bold')))
                else:
                    fig.add_trace(go.Bar(x=[equity], y=[""], orientation='h', marker_color='#0288D1', hoverinfo='none', 
                                         text=f"Equity<br>{equity:,.0f}", textposition='inside', 
                                         textfont=dict(color='white', size=BAR_FONT_SIZE, family=common_font, weight='bold')))
                    fig.add_trace(go.Bar(x=[abs(profit)], y=[""], orientation='h', marker_color='#D50000', hoverinfo='none', 
                                         text=f"Loss<br>{abs(profit):,.0f}", textposition='inside', 
                                         textfont=dict(color='white', size=BAR_FONT_SIZE, family=common_font, weight='bold')))
                
                fig.add_vline(x=balance, line_width=2, line_color="white", opacity=0.8)
                
                fig.add_annotation(x=balance, y=0, yshift=28, text=f"Balance : {balance:,.0f}", xanchor='right', xshift=-5, showarrow=False, 
                                   font=dict(size=BAR_FONT_SIZE, color="white", family=common_font, weight="bold"))
                
                fig.update_layout(
                    barmode='stack', showlegend=False, 
                    xaxis=dict(visible=False, range=[0, max(balance, equity) * 1.15]), 
                    yaxis=dict(visible=False), 
                    margin=dict(l=0, r=0, t=35, b=0), height=90, 
                    paper_bgcolor='#0E1117', plot_bgcolor='#0E1117'
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

                # --- SECTION 4: PORTFOLIO STRUCTURE ---
                st.markdown('<div class="section-header">Portfolio
