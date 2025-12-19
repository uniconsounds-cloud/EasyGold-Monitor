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

# --- CSS ปรับแต่งพิเศษสำหรับมือถือ ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    
    div[data-baseweb="select"] > div {
        background-color: #1E222D;
        color: white;
        border-color: #333;
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
# เริ่มต้นการทำงาน
# =========================================================

df = load_data()

if df is None:
    st.warning("⚠️ กำลังเชื่อมต่อฐานข้อมูล... (Connecting)")
    time.sleep(2)
    st.rerun()
else:
    try:
        df['AccountID'] = df['AccountID'].astype(str)
        all_accounts = df['AccountID'].unique().tolist()
        
        # 1. ตัวเลือกพอร์ต
        if len(all_accounts) > 0:
            selected_account = st.selectbox("📌 เลือกพอร์ต (Select Account):", all_accounts, index=0)
        else:
            st.warning("⏳ รอข้อมูลจาก MT5...")
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

                # 2. Header (Price & Lot) - เอา $ ออก
                st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; background-color: #1E222D; padding: 12px 15px; border-radius: 10px; margin-top: 10px; margin-bottom: 5px; border: 1px solid #333;'><div style='text-align: left; line-height: 1.2;'><span style='color: #9E9E9E; font-size: 0.85rem; font-family: sans-serif;'>PRICE (Bid)</span><br><span style='color: #29B6F6; font-size: 1.5rem; font-weight: 700; font-family: sans-serif;'>{current_price:,.2f}</span></div><div style='text-align: right; line-height: 1.2;'><span style='color: #9E9E9E; font-size: 0.85rem; font-family: sans-serif;'>LOTS</span><br><span style='color: #FFA726; font-size: 1.5rem; font-weight: 700; font-family: sans-serif;'>{total_lots:.2f}</span></div></div>", unsafe_allow_html=True)

                # =========================================================
                # 3. Energy Bar (New Design)
                # =========================================================
                fig = go.Figure()
                
                # Logic การวาดกราฟ (เอา $ ออกจาก text)
                if profit >= 0:
                    # Balance (Blue)
                    fig.add_trace(go.Bar(
                        x=[balance], y=[""], orientation='h', 
                        marker_color='#0288D1', hoverinfo='none', 
                        text="", # ไม่ต้องโชว์ text ในแท่ง Balance เดี๋ยวไปโชว์ที่เส้นแทน
                    ))
                    # Profit (Green)
                    fig.add_trace(go.Bar(
                        x=[profit], y=[""], orientation='h', 
                        marker_color='#00C853', hoverinfo='none', 
                        text=f"+{profit:,.0f}", textposition='inside', 
                        textfont=dict(color='white', size=14, weight='bold')
                    ))
                else:
                    # Equity (Blue)
                    fig.add_trace(go.Bar(
                        x=[equity], y=[""], orientation='h', 
                        marker_color='#0288D1', hoverinfo='none', 
                        text=f"Eq: {equity:,.0f}", textposition='auto', 
                        textfont=dict(color='white', size=14)
                    ))
                    # Loss (Red)
                    fig.add_trace(go.Bar(
                        x=[abs(profit)], y=[""], orientation='h', 
                        marker_color='#D50000', hoverinfo='none', 
                        text=f"-{abs(profit):,.0f}", textposition='inside', 
                        textfont=dict(color='white', size=14)
                    ))

                # เส้น Balance แนวตั้ง
                fig.add_vline(x=balance, line_width=3, line_color="white", opacity=0.9)
                
                # 🔥 Balance Text: ชิดขวาติดเส้นแนวตั้ง (xanchor='right')
                fig.add_annotation(
                    x=balance, y=0,
                    text=f"{balance:,.2f}", # แสดงตัวเลข Balance
                    xanchor='right',        # ให้จุดจบของข้อความอยู่ตรงเส้น
                    xshift=-5,              # ขยับซ้ายนิดนึงไม่ให้ทับเส้น
                    showarrow=False,
                    font=dict(size=16, color="white", family="Arial Black"),
                    bgcolor="rgba(0,0,0,0.3)" # พื้นหลังจางๆ ให้อ่านง่าย
                )

                # ปรับ Layout ให้เต็มจอสุดๆ และเอาเมนูออก
                fig.update_layout(
                    barmode='stack', 
                    showlegend=False, 
                    xaxis=dict(visible=False, range=[0, max(balance, equity) * 1.15]), 
                    yaxis=dict(visible=False), 
                    margin=dict(l=0, r=0, t=10, b=10), # ลดขอบให้เหลือ 0
                    height=80, # ความสูงกำลังดี
                    paper_bgcolor='#0E1117', 
                    plot_bgcolor='#0E1117'
                )
                
                # config={'displayModeBar': False} คือตัวสั่งปิดเมนู!
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

                # 4. Bubble Chart
                st.markdown("---")
                
                orders_str = latest.get('JSON_Data', '[]')
                if pd.isna(orders_str) or orders_str == "": orders_str = '[]'
                
                try:
                    orders = json.loads(orders_str)
                    
                    if len(orders) > 0 and current_price > 0:
                        orders_df = pd.DataFrame(orders)
                        
                        orders_df.rename(columns={'s': 'Symbol', 't': 'Type', 'v': 'Volume', 'p': 'Open Price', 'pl': 'Profit', 'm': 'Magic'}, inplace=True)
                        
                        if 'Magic' in orders_df.columns:
                            orders_df['WeightedVal'] = orders_df['Volume'] * orders_df['Open Price']
                            magic = orders_df.groupby('Magic').agg(
                                Lots=('Volume', 'sum'), SumW=('WeightedVal', 'sum'), Profit=('Profit', 'sum')
                            ).reset_index()
                            magic['Avg'] = magic['SumW'] / magic['Lots']
                            magic['Color'] = magic['Profit'].apply(lambda x: '#00C853' if x >= 0 else '#D50000')

                            fig_b = go.Figure()
                            fig_b.add_hline(y=current_price, line_dash="dash", line_color="#29B6F6")
                            fig_b.add_trace(go.Scatter(
                                x=magic['Magic'].astype(str), y=magic['Avg'], mode='markers+text',
                                marker=dict(size=magic['Lots'], sizemode='area', sizeref=2.*max(magic['Lots'])/(70.**2), sizemin=8, color=magic['Color'], line=dict(width=1, color='white')),
                                text=magic['Magic'], textposition="top center", textfont=dict(color='white')
                            ))
                            fig_b.update_layout(
                                margin=dict(l=10, r=10, t=30, b=10),
                                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='white')),
                                yaxis=dict(gridcolor='#333', tickfont=dict(color='white')),
                                paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', height=400, showlegend=False,
                                title=dict(text="Portfolio Position", font=dict(color='white', size=14))
                            )
                            # ปิดเมนูของกราฟ Bubble ด้วยเหมือนกัน
                            st.plotly_chart(fig_b, use_container_width=True, config={'displayModeBar': False})
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            with st.expander("📄 ดูรายการออเดอร์ (Order Details)"):
                                display_df = orders_df[['Symbol', 'Type', 'Volume', 'Open Price', 'Profit', 'Magic']].copy()
                                display_df['Open Price'] = display_df['Open Price'].map('{:,.2f}'.format)
                                display_df['Profit'] = display_df['Profit'].map('{:,.2f}'.format)
                                display_df['Volume'] = display_df['Volume'].map('{:.2f}'.format)
                                st.dataframe(display_df, use_container_width=True, height=300)
                        else:
                            st.info("⚠️ ไม่พบข้อมูล Magic Number")
                    else:
                        st.info("✅ พอร์ตว่าง (No Active Orders)")
                except Exception as e:
                     st.error(f"Error parsing JSON: {e}")

            else:
                st.warning(f"ไม่พบข้อมูลสำหรับ: {selected_account}")
    except Exception as main_e:
        st.error(f"System Error: {main_e}")

time.sleep(5)
st.rerun()
