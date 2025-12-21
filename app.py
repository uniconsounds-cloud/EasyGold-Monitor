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
    /* 1. Reset Container Padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    
    /* 2. Hide Streamlit Elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Roboto', sans-serif; }
    
    /* 3. Custom Section Header Design */
    .section-header {
        font-size: 1rem;
        font-weight: 700;
        color: #E0E0E0;
        border-left: 4px solid #29B6F6; /* เส้นสีฟ้าด้านหน้า */
        padding-left: 10px;
        margin-top: 25px;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* 4. Dropdown Styling */
    div[data-baseweb="select"] > div {
        background-color: #1E222D;
        color: white;
        border-color: #444;
    }
    
    /* 5. Card Container Styling */
    .metric-card {
        background-color: #1E222D;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

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
                
                # Data Preparation
                current_price = float(latest.get('CurrentPrice', 0.0))
                balance = float(latest.get('Balance', 0.0))
                equity = float(latest.get('Equity', 0.0))
                profit = float(latest.get('TotalProfit', 0.0))
                total_lots = float(latest.get('BuyLots', 0.0)) + float(latest.get('SellLots', 0.0))
                common_font = "Arial, sans-serif"

                # --- SECTION 2: MARKET OVERVIEW ---
                st.markdown('<div class="section-header">Market Overview</div>', unsafe_allow_html=True)
                
                # HTML Card Design (Clean & Symmetric)
                st.markdown(f"""
                <div class="metric-card" style="display: flex; justify-content: space-between; align-items: center;">
                    <div style='text-align: left;'>
                        <div style='color: #9E9E9E; font-size: 0.75rem; font-weight: 600;'>GOLD PRICE (BID)</div>
                        <div style='color: #29B6F6; font-size: 1.6rem; font-weight: 800; margin-top: 2px;'>{current_price:,.2f}</div>
                    </div>
                    <div style='width: 1px; height: 40px; background-color: #333;'></div> <div style='text-align: right;'>
                        <div style='color: #9E9E9E; font-size: 0.75rem; font-weight: 600;'>TOTAL EXPOSURE</div>
                        <div style='color: #FFA726; font-size: 1.6rem; font-weight: 800; margin-top: 2px;'>{total_lots:.2f}<span style='font-size: 0.8rem; color: #777; font-weight: 400;'> Lots</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # --- SECTION 3: ACCOUNT HEALTH ---
                st.markdown('<div class="section-header">Account Health</div>', unsafe_allow_html=True)
                
                fig = go.Figure()
                if profit >= 0:
                    fig.add_trace(go.Bar(x=[balance], y=[""], orientation='h', marker_color='#0288D1', hoverinfo='none'))
                    fig.add_trace(go.Bar(x=[profit], y=[""], orientation='h', marker_color='#00C853', hoverinfo='none', text=f"Profit<br>{profit:,.0f}", textposition='inside', textfont=dict(color='white', size=13, family=common_font)))
                else:
                    fig.add_trace(go.Bar(x=[equity], y=[""], orientation='h', marker_color='#0288D1', hoverinfo='none', text=f"Equity<br>{equity:,.0f}", textposition='inside', textfont=dict(color='white', size=13, family=common_font)))
                    fig.add_trace(go.Bar(x=[abs(profit)], y=[""], orientation='h', marker_color='#D50000', hoverinfo='none', text=f"Loss<br>{abs(profit):,.0f}", textposition='inside', textfont=dict(color='white', size=12, family=common_font)))
                
                fig.add_vline(x=balance, line_width=2, line_color="white", opacity=0.8)
                fig.add_annotation(x=balance, y=0, yshift=28, text=f"Balance : {balance:,.0f}", xanchor='right', xshift=-5, showarrow=False, font=dict(size=14, color="white", family=common_font, weight="bold"))
                
                fig.update_layout(
                    barmode='stack', showlegend=False, 
                    xaxis=dict(visible=False, range=[0, max(balance, equity) * 1.15]), 
                    yaxis=dict(visible=False), 
                    margin=dict(l=0, r=0, t=35, b=0), 
                    height=90, 
                    paper_bgcolor='#0E1117', plot_bgcolor='#0E1117'
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

                # --- SECTION 4: PORTFOLIO STRUCTURE ---
                st.markdown('<div class="section-header">Portfolio Structure</div>', unsafe_allow_html=True)
                
                orders_str = latest.get('JSON_Data', '[]')
                if pd.isna(orders_str) or orders_str == "": orders_str = '[]'
                
                try:
                    orders = json.loads(orders_str)
                    if len(orders) > 0 and current_price > 0:
                        orders_df = pd.DataFrame(orders)
                        orders_df.rename(columns={'s': 'Symbol', 't': 'Type', 'v': 'Volume', 'p': 'Open Price', 'pl': 'Profit', 'm': 'Magic'}, inplace=True)
                        
                        if 'Magic' in orders_df.columns:
                            # Calculate Stats
                            orders_df['WeightedVal'] = orders_df['Volume'] * orders_df['Open Price']
                            magic_stats = orders_df.groupby('Magic').agg(
                                AvgPrice=('WeightedVal', 'sum'),
                                TotalVol=('Volume', 'sum'),
                                MinPrice=('Open Price', 'min'),
                                MaxPrice=('Open Price', 'max'),
                                OrderCount=('Magic', 'count'), 
                                OrderType=('Type', 'first')
                            ).reset_index()
                            magic_stats['AvgPrice'] = magic_stats['AvgPrice'] / magic_stats['TotalVol']
                            
                            # Create Chart
                            fig_p = go.Figure()

                            # 1. Market Price Line
                            fig_p.add_hline(
                                y=current_price, line_dash="dash", line_color="#29B6F6", line_width=1,
                                annotation_text=f"Market: {current_price:,.2f}", annotation_position="top right", annotation_font=dict(color="#29B6F6", size=10)
                            )

                            # 2. Structure Elements
                            # A. Orders (Small dots)
                            fig_p.add_trace(go.Scatter(
                                x=orders_df['Magic'].astype(str), y=orders_df['Open Price'], mode='markers',
                                marker=dict(symbol='line-ew', size=25, line=dict(width=1, color="rgba(255, 255, 255, 0.25)")),
                                hoverinfo='skip'
                            ))
                            # B. Top (Red)
                            fig_p.add_trace(go.Scatter(
                                x=magic_stats['Magic'].astype(str), y=magic_stats['MaxPrice'], mode='markers',
                                marker=dict(symbol='line-ew', size=30, line=dict(width=3, color="#D50000")),
                                hoverinfo='skip'
                            ))
                            # C. Bottom (Green)
                            fig_p.add_trace(go.Scatter(
                                x=magic_stats['Magic'].astype(str), y=magic_stats['MinPrice'], mode='markers',
                                marker=dict(symbol='line-ew', size=30, line=dict(width=3, color="#00C853")),
                                hoverinfo='skip'
                            ))
                            # D. Avg Price (Yellow)
                            fig_p.add_trace(go.Scatter(
                                x=magic_stats['Magic'].astype(str), y=magic_stats['AvgPrice'], mode='markers',
                                marker=dict(symbol='line-ew', size=40, line=dict(width=4, color="#FFD600")),
                                hoverinfo='skip'
                            ))
                            
                            # E. Labels (Magic + Count)
                            label_texts = [f"M: {m}<br>({c} Orders)" for m, c in zip(magic_stats['Magic'], magic_stats['OrderCount'])]
                            fig_p.add_trace(go.Scatter(
                                x=magic_stats['Magic'].astype(str), y=magic_stats['MaxPrice'], mode='text',
                                text=label_texts, textposition="top center",
                                textfont=dict(color='#E0E0E0', size=11, family=common_font),
                                hoverinfo='skip'
                            ))

                            fig_p.update_layout(
                                xaxis=dict(showticklabels=False, type='category', gridcolor='#333'),
                                yaxis=dict(title="Price Level", gridcolor='#222', tickfont=dict(color='gray', size=10)),
                                margin=dict(l=40, r=20, t=50, b=20),
                                height=400, showlegend=False,
                                paper_bgcolor='#0E1117', plot_bgcolor='#0E1117'
                            )
                            st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})

                            # --- SECTION 5: MAGIC SUMMARY TABLE ---
                            st.markdown('<div class="section-header">Magic Summary</div>', unsafe_allow_html=True)
                            
                            # Prepare Data
                            display_df = magic_stats[['Magic', 'OrderType', 'TotalVol', 'MinPrice', 'MaxPrice', 'AvgPrice']].copy()
                            profit_df = orders_df.groupby('Magic')['Profit'].sum().reset_index()
                            display_df = display_df.merge(profit_df, on='Magic')
                            
                            # Rename for Display
                            display_df.columns = ['MAGIC', 'TYPE', 'LOTS', 'MIN', 'MAX', 'AVG', 'PROFIT']
                            
                            # Formatting
                            for c in ['LOTS', 'MIN', 'MAX', 'AVG', 'PROFIT']:
                                display_df[c] = display_df[c].map('{:,.2f}'.format)
                                
                            # Styling Function
                            def highlight_type(val):
                                color = '#00C853' if val == 'Buy' else '#D50000'
                                return f'color: {color}; font-weight: bold'
                            
                            # Show Table (No Expander)
                            st.dataframe(
                                display_df.style.map(highlight_type, subset=['TYPE']), 
                                use_container_width=True, 
                                height=len(display_df) * 35 + 38, # ปรับความสูงอัตโนมัติตามจำนวนแถว
                                hide_index=True
                            )

                        else:
                            st.info("No Magic Number Data")
                    else:
                        st.info("No Active Orders")
                except Exception as e:
                     st.error(f"Data Error: {e}")
            else:
                st.warning("Account not found.")
    except Exception as main_e:
        st.error(f"System Error: {main_e}")

time.sleep(5)
st.rerun()
