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

st.set_page_config(page_title="Visual Magic Monitor", page_icon="🎯", layout="wide")

# --- CSS ปรับแต่งหน้าจอให้ชิดขอบบนสุด (Mobile Friendly) ---
st.markdown("""
<style>
    /* ลดพื้นที่ว่างด้านบนสุด */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    /* ซ่อน index ตาราง */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    /* พื้นหลัง Dark Mode */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
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

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Control Panel")
    user_input = st.text_input("🔑 Account ID Filter", "")
    st.caption("Visualization by Magic Number")

# --- Main Page ---

placeholder = st.empty()

while True:
    df = load_data()
    
    with placeholder.container():
        if df is None:
            st.error("⚠️ Connecting...")
        else:
            df['AccountID'] = df['AccountID'].astype(str)
            target_df = df[df['AccountID'] == user_input] if user_input else df.tail(1)

            if not target_df.empty:
                latest = target_df.iloc[-1]
                current_price = float(latest.get('CurrentPrice', 0.0))
                balance = float(latest['Balance'])
                equity = float(latest['Equity'])
                profit = float(latest['TotalProfit'])
                total_lots = latest['BuyLots'] + latest['SellLots']

                # =========================================================
                # ส่วนที่ 1: Market Info (ราคาและ Lot) - เน้นดูง่าย
                # =========================================================
                c_price, c_lots = st.columns([2, 1]) # แบ่งสัดส่วน 2:1 ให้ราคาเด่นกว่า
                
                with c_price:
                    st.metric("Current Price (Bid)", f"${current_price:,.2f}")
                with c_lots:
                    st.metric("Total Volume", f"{total_lots:.2f} Lots")

                # =========================================================
                # ส่วนที่ 2: Finance Infographic (Bullet Chart)
                # รวม Balance, Equity, Profit ไว้ในกราฟเดียว
                # =========================================================
                
                # กำหนดสี: ถ้า Profit บวกเป็นสีเขียว ถ้าลบเป็นสีแดง
                bar_color = "#00C853" if profit >= 0 else "#D50000"
                
                fig_finance = go.Figure(go.Indicator(
                    mode = "number+gauge+delta",
                    value = equity,
                    delta = {'reference': balance, 'position': "top", 'valueformat': ",.2f", 'prefix': "$"},
                    number = {'prefix': "$", 'valueformat': ",.2f", 'font': {'size': 40}}, # ขนาดตัวเลข Equity
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "<b>Equity Status</b><br><span style='font-size:0.8em;color:gray'>Compared to Balance</span>"},
                    gauge = {
                        'shape': "bullet", # กราฟทรงกระสุน (แนวนอน) ประหยัดที่
                        'axis': {'range': [None, max(balance, equity) * 1.1]}, # ปรับสเกลอัตโนมัติ
                        'threshold': { # เส้นขีดสีขาว คือ Balance
                            'line': {'color': "white", 'width': 3},
                            'thickness': 0.75,
                            'value': balance
                        },
                        'bar': {'color': bar_color}, # สีแท่งคือ Equity
                        'bgcolor': "rgba(255,255,255,0.1)"
                    }
                ))
                
                # ปรับความสูงให้เตี้ยที่สุด เพื่อไม่ให้กินที่มือถือ
                fig_finance.update_layout(height=180, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='#0E1117')
                
                # แสดงกราฟ Finance
                st.plotly_chart(fig_finance, use_container_width=True, key=f"fin_{time.time()}")

                # =========================================================
                # ส่วนที่ 3: Magic Number Bubble Chart (เหมือนเดิม)
                # =========================================================
                st.markdown("---")
                try:
                    orders = json.loads(latest['JSON_Data'])
                    if len(orders) > 0 and current_price > 0:
                        orders_df = pd.DataFrame(orders)
                        orders_df.rename(columns={'v': 'Volume', 'p': 'Open Price', 'pl': 'Profit', 'm': 'Magic'}, inplace=True)

                        if 'Magic' in orders_df.columns:
                            orders_df['WeightedVal'] = orders_df['Volume'] * orders_df['Open Price']
                            magic_summary = orders_df.groupby('Magic').agg(
                                Total_Lots=('Volume', 'sum'),
                                Sum_Weighted=('WeightedVal', 'sum'),
                                Total_Profit=('Profit', 'sum'),
                                Min_Price=('Open Price', 'min'),
                                Max_Price=('Open Price', 'max'),
                                Orders_Count=('Magic', 'count')
                            ).reset_index()
                            
                            magic_summary['Avg_Price'] = magic_summary['Sum_Weighted'] / magic_summary['Total_Lots']
                            magic_summary['Color'] = magic_summary['Total_Profit'].apply(lambda x: '#00C853' if x >= 0 else '#D50000')
                            
                            fig_bubble = go.Figure()

                            fig_bubble.add_hline(y=current_price, line_dash="dash", line_color="#29B6F6", 
                                               annotation_text=f"Market: {current_price:.2f}", annotation_position="top right")

                            fig_bubble.add_trace(go.Scatter(
                                x=magic_summary['Magic'].astype(str), 
                                y=magic_summary['Avg_Price'],         
                                mode='markers+text',
                                marker=dict(
                                    size=magic_summary['Total_Lots'], 
                                    sizemode='area',
                                    sizeref=2.*max(magic_summary['Total_Lots'])/(80.**2), 
                                    sizemin=10, 
                                    color=magic_summary['Color'], 
                                    line=dict(width=2, color='white') 
                                ),
                                text=magic_summary['Magic'], 
                                textposition="top center",
                                textfont=dict(color='white'),
                                hovertemplate="Magic: %{x}<br>Avg: %{y:,.2f}<br>Lots: %{marker.size:.2f}<br>Profit: %{customdata:,.2f}<extra></extra>",
                                customdata=magic_summary['Total_Profit']
                            ))

                            fig_bubble.update_layout(
                                title="Portfolio Positions",
                                xaxis=dict(title="Magic Groups", showgrid=False, zeroline=False, tickfont=dict(color='white')),
                                yaxis=dict(title="Price Level", gridcolor='#333333', tickfont=dict(color='white')),
                                plot_bgcolor='#0E1117',
                                paper_bgcolor='#0E1117',
                                font=dict(color='white'),
                                height=500, # ลดความสูงลงนิดนึงจะได้ดูง่ายบนมือถือ
                                showlegend=False,
                                margin=dict(l=20, r=20, t=40, b=20)
                            )

                            st.plotly_chart(fig_bubble, use_container_width=True, key=f"bub_{time.time()}")
                            
                            with st.expander("📊 Data Details"):
                                st.dataframe(magic_summary[['Magic', 'Total_Lots', 'Avg_Price', 'Total_Profit']], use_container_width=True)
                except Exception as e:
                    pass

            elif user_input:
                st.warning(f"Account not found: {user_input}")
            else:
                st.info("Please enter Account ID.")

    time.sleep(5)
