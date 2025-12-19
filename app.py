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

# โหลด CSS เพื่อซ่อน index ตาราง และปรับแต่ง Dark Mode
st.markdown("""
<style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    .stApp { background-color: #0E1117; color: #FAFAFA; }
</style>
""", unsafe_allow_html=True)

def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        # ตรวจสอบว่ามีคอลัมน์ CurrentPrice หรือยัง
        if 'CurrentPrice' not in df.columns:
             df['CurrentPrice'] = 0.0 
        return df
    except:
        return None

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Control Panel")
    user_input = st.text_input("🔑 Account ID Filter", "")
    st.caption("Visualization by Magic Number")

# --- Main Page ---
st.title("🎯 Portfolio Visualizer (Infographic)")

placeholder = st.empty()

while True:
    df = load_data()
    
    with placeholder.container():
        if df is None:
            st.error("⚠️ Connecting to database...")
        else:
            df['AccountID'] = df['AccountID'].astype(str)
            target_df = df[df['AccountID'] == user_input] if user_input else df.tail(1)

            if not target_df.empty:
                latest = target_df.iloc[-1]
                current_market_price = float(latest.get('CurrentPrice', 0.0))

                # Top Metrics
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Current Market Price", f"${current_market_price:,.2f}")
                c2.metric("Equity", f"${latest['Equity']:,.2f}")
                c3.metric("Total Profit", f"${latest['TotalProfit']:,.2f}", delta=latest['TotalProfit'])
                c4.metric("Total Lots", f"{latest['BuyLots'] + latest['SellLots']:.2f}")
                
                st.markdown("---")

                # --- Data Processing for Visuals ---
                try:
                    orders = json.loads(latest['JSON_Data'])
                    if len(orders) > 0 and current_market_price > 0:
                        orders_df = pd.DataFrame(orders)
                        orders_df.rename(columns={'v': 'Volume', 'p': 'Open Price', 'pl': 'Profit', 'm': 'Magic'}, inplace=True)

                        if 'Magic' in orders_df.columns:
                            # คำนวณราคาเฉลี่ยถ่วงน้ำหนัก
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
                            
                            # --- สร้าง Infographic (Plotly Bubble Chart) ---
                            fig = go.Figure()

                            # 1. เส้นราคาปัจจุบัน
                            fig.add_hline(y=current_market_price, line_dash="dash", line_color="#29B6F6", annotation_text=f"Current: {current_market_price:.2f}", annotation_position="top right")

                            # 2. Bubble Magic Number
                            fig.add_trace(go.Scatter(
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
                                hovertemplate="<b>Magic: %{x}</b><br>Avg Price: %{y:,.2f}<br>Total Lots: %{marker.size:.2f}<br>Total Profit: %{customdata:,.2f}<extra></extra>",
                                customdata=magic_summary['Total_Profit']
                            ))

                            fig.update_layout(
                                title="Portfolio Positioning",
                                xaxis=dict(title="Magic Groups", showgrid=False, zeroline=False, tickfont=dict(color='white')),
                                yaxis=dict(title="Price", gridcolor='#333333', tickfont=dict(color='white')),
                                plot_bgcolor='#0E1117',
                                paper_bgcolor='#0E1117',
                                font=dict(color='white'),
                                height=600,
                                showlegend=False
                            )

                            # --- 🔥 แก้ไขตรงนี้ครับ (ใส่ key=time.time()) ---
                            st.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}")
                            # ----------------------------------------------

                            with st.expander("📊 Data Table"):
                                display_df = magic_summary[['Magic', 'Orders_Count', 'Total_Lots', 'Avg_Price', 'Total_Profit']].copy()
                                display_df['Avg_Price'] = display_df['Avg_Price'].map('{:,.2f}'.format)
                                display_df['Total_Profit'] = display_df['Total_Profit'].map('{:,.2f}'.format)
                                display_df['Total_Lots'] = display_df['Total_Lots'].map('{:,.2f}'.format)
                                st.dataframe(display_df, use_container_width=True)

                        else:
                            st.warning("⚠️ ข้อมูลยังไม่มี Magic Number")
                    else:
                        st.info("✅ พอร์ตว่าง หรือรอราคาตลาด")

                except Exception as e:
                    # พิมพ์ error ลงหน้าเว็บเพื่อให้เห็นชัดๆ (ถ้ามี)
                    st.error(f"Error visualization: {e}")

            elif user_input:
                st.warning(f"Account not found: {user_input}")
            else:
                st.info("Please enter Account ID.")

    time.sleep(5)
