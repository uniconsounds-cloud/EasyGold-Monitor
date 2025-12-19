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

                common_font = "Arial, sans-serif"

                # 2. Header (Price & Lot)
                st.markdown(f"""
                <div style='display: flex; justify-content: space-between; align-items: center; background-color: #1E222D; padding: 12px 15px; border-radius: 10px; margin-top: 10px; margin-bottom: 5px; border: 1px solid #333;'>
                    <div style='text-align: left; line-height: 1.2;'>
                        <span style='color: #9E9E9E; font-size: 0.85rem; font-family: {common_font};'>PRICE (Bid)</span><br>
                        <span style='color: #29B6F6; font-size: 1.5rem; font-weight: 700; font-family: {common_font};'>{current_price:,.2f}</span>
                    </div>
                    <div style='text-align: right; line-height: 1.2;'>
                        <span style='color: #9E9E9E; font-size: 0.85rem; font-family: {common_font};'>LOTS</span><br>
                        <span style='color: #FFA726; font-size: 1.5rem; font-weight: 700; font-family: {common_font};'>{total_lots:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # =========================================================
                # 3. Energy Bar (Balance on Top)
                # =========================================================
                fig = go.Figure()
                
                # Logic:
                # - ตัวหนังสือในบาร์ (Profit/Equity/Loss) ยังคงเป็น 2 บรรทัดเหมือนเดิม
                # - ตัวหนังสือ Balance ดันขึ้นไปข้างบน +30px
                
                if profit >= 0:
                    # Case กำไร
                    fig.add_trace(go.Bar(
                        x=[balance], y=[""], orientation='h', 
                        marker_color='#0288D1', hoverinfo='none', 
                        text="" 
                    ))
                    fig.add_trace(go.Bar(
                        x=[profit], y=[""], orientation='h', 
                        marker_color='#00C853', hoverinfo='none', 
                        text=f"Profit<br>{profit:,.0f}", 
                        textposition='inside', 
                        textfont=dict(color='white', size=14, family=common_font)
                    ))
                else:
                    # Case ขาดทุน
                    fig.add_trace(go.Bar(
                        x=[equity], y=[""], orientation='h', 
                        marker_color='#0288D1', hoverinfo='none', 
                        text=f"Equity<br>{equity:,.0f}", 
                        textposition='inside', 
                        textfont=dict(color='white', size=14, family=common_font)
                    ))
                    fig.add_trace(go.Bar(
                        x=[abs(profit)], y=[""], orientation='h', 
                        marker_color='#D50000', hoverinfo='none', 
                        text=f"Loss<br>{abs(profit):,.0f}", 
                        textposition='inside', 
                        textfont=dict(color='white', size=13, family=common_font)
                    ))

                # เส้น Balance แนวตั้ง
                fig.add_vline(x=balance, line_width=2, line_color="white", opacity=0.8)
                
                # 🔥 Balance Text: แก้ไขใหม่ตามสั่ง
                # 1. yshift=25 (ดันขึ้นไปข้างบน)
                # 2. xanchor='right' (ชิดขวาเส้น)
                # 3. Format บรรทัดเดียว
                fig.add_annotation(
                    x=balance, y=0,
                    yshift=25,              # ดันขึ้นไปข้างบนบาร์ 25 pixel
                    text=f"Balance : {balance:,.0f}", 
                    xanchor='right',        # ยึดฝั่งขวาไว้ที่เส้น
                    xshift=-5,              # ขยับซ้ายนิดนึง
                    showarrow=False,
                    font=dict(size=14, color="white", family=common_font, weight="bold"),
                    # bgcolor="rgba(0,0,0,0.5)" # (เลือกเปิดได้) ถ้าอยากให้มีพื้นหลังดำจางๆ รองหลังตัวหนังสือ
                )

                fig.update_layout(
                    barmode='stack', 
                    showlegend=False, 
                    xaxis=dict(visible=False, range=[0, max(balance, equity) * 1.15]), 
                    yaxis=dict(visible=False), 
                    margin=dict(l=0, r=0, t=30, b=10), # เพิ่ม t (Top margin) เป็น 30 เพื่อให้ที่ว่างตัวหนังสือ Balance
                    height=100, 
                    paper_bgcolor='#0E1117', 
                    plot_bgcolor='#0E1117'
                )
                
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
                                text=magic['Magic'], textposition="top center", 
                                textfont=dict(color='white', family=common_font)
                            ))
                            fig_b.update_layout(
                                margin=dict(l=10, r=10, t=30, b=10),
                                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='white', family=common_font)),
                                yaxis=dict(gridcolor='#333', tickfont=dict(color='white', family=common_font)),
                                paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', height=400, showlegend=False,
                                title=dict(text="Portfolio Position", font=dict(color='white', size=14, family=common_font))
                            )
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
