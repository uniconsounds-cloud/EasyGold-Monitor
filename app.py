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

                # 3. Energy Bar
                fig = go.Figure()
                if profit >= 0:
                    fig.add_trace(go.Bar(x=[balance], y=[""], orientation='h', marker_color='#0288D1', hoverinfo='none', text=""))
                    fig.add_trace(go.Bar(x=[profit], y=[""], orientation='h', marker_color='#00C853', hoverinfo='none', text=f"Profit<br>{profit:,.0f}", textposition='inside', textfont=dict(color='white', size=14, family=common_font)))
                else:
                    fig.add_trace(go.Bar(x=[equity], y=[""], orientation='h', marker_color='#0288D1', hoverinfo='none', text=f"Equity<br>{equity:,.0f}", textposition='inside', textfont=dict(color='white', size=14, family=common_font)))
                    fig.add_trace(go.Bar(x=[abs(profit)], y=[""], orientation='h', marker_color='#D50000', hoverinfo='none', text=f"Loss<br>{abs(profit):,.0f}", textposition='inside', textfont=dict(color='white', size=13, family=common_font)))

                fig.add_vline(x=balance, line_width=2, line_color="white", opacity=0.8)
                fig.add_annotation(x=balance, y=0, yshift=25, text=f"Balance : {balance:,.0f}", xanchor='right', xshift=-5, showarrow=False, font=dict(size=14, color="white", family=common_font, weight="bold"))
                fig.update_layout(barmode='stack', showlegend=False, xaxis=dict(visible=False, range=[0, max(balance, equity) * 1.15]), yaxis=dict(visible=False), margin=dict(l=0, r=0, t=30, b=10), height=100, paper_bgcolor='#0E1117', plot_bgcolor='#0E1117')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

                # 4. Bubble Chart & Summary Table (Revised)
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
                            
                            magic_summary = orders_df.groupby('Magic').agg(
                                OrderType=('Type', 'first'),
                                OrderCount=('Magic', 'count'),
                                TotalLots=('Volume', 'sum'),
                                MinPrice=('Open Price', 'min'),
                                MaxPrice=('Open Price', 'max'),
                                SumWeighted=('WeightedVal', 'sum'),
                                TotalProfit=('Profit', 'sum')
                            ).reset_index()
                            
                            magic_summary['AvgPrice'] = magic_summary['SumWeighted'] / magic_summary['TotalLots']
                            
                            buy_group = magic_summary[magic_summary['OrderType'] == 'Buy']
                            sell_group = magic_summary[magic_summary['OrderType'] == 'Sell']

                            # --- วาด Bubble Chart ---
                            fig_b = go.Figure()

                            # 1. เส้นราคาปัจจุบัน (แสดงราคาด้วย)
                            fig_b.add_hline(
                                y=current_price, 
                                line_dash="dash", line_color="#29B6F6", 
                                annotation_text=f"Market: {current_price:,.2f}", # แสดงราคาตรงนี้
                                annotation_position="top left",
                                annotation_font=dict(color="#29B6F6", size=12)
                            )

                            # 2. BUY Zone
                            if not buy_group.empty:
                                fig_b.add_trace(go.Scatter(
                                    x=["BUY Zone"] * len(buy_group),
                                    y=buy_group['AvgPrice'],
                                    mode='markers+text',
                                    name='Buy',
                                    marker=dict(
                                        size=buy_group['TotalLots'], 
                                        sizemode='area', sizeref=2.*max(magic_summary['TotalLots'])/(70.**2), sizemin=15, # เพิ่ม sizemin ให้อ่านตัวเลขออก
                                        color='#00C853', line=dict(width=1, color='white')
                                    ),
                                    # แสดงจำนวนไม้ตรงกลาง Bubble
                                    text=buy_group['OrderCount'], 
                                    textposition="middle center", 
                                    textfont=dict(color='white', family=common_font, weight='bold'),
                                    
                                    # Tooltip: Magic, Lots, Profit, Min, Max
                                    hovertemplate=
                                    "<b>Magic: %{customdata[0]}</b><br>" +
                                    "Type: BUY<br>" +
                                    "Orders: %{text}<br>" +
                                    "Lots: %{marker.size:.2f}<br>" +
                                    "Avg: %{y:,.2f}<br>" +
                                    "Min: %{customdata[2]:,.2f}<br>" +
                                    "Max: %{customdata[3]:,.2f}<br>" +
                                    "Profit: %{customdata[1]:,.2f}<extra></extra>",
                                    # ส่งข้อมูล Magic, Profit, Min, Max เข้าไปใน customdata เพื่อดึงมาแสดง
                                    customdata=buy_group[['Magic', 'TotalProfit', 'MinPrice', 'MaxPrice']]
                                ))

                            # 3. SELL Zone
                            if not sell_group.empty:
                                fig_b.add_trace(go.Scatter(
                                    x=["SELL Zone"] * len(sell_group),
                                    y=sell_group['AvgPrice'],
                                    mode='markers+text',
                                    name='Sell',
                                    marker=dict(
                                        size=sell_group['TotalLots'], 
                                        sizemode='area', sizeref=2.*max(magic_summary['TotalLots'])/(70.**2), sizemin=15, 
                                        color='#D50000', line=dict(width=1, color='white')
                                    ),
                                    text=sell_group['OrderCount'], # แสดงจำนวนไม้
                                    textposition="middle center", 
                                    textfont=dict(color='white', family=common_font, weight='bold'),
                                    
                                    hovertemplate=
                                    "<b>Magic: %{customdata[0]}</b><br>" +
                                    "Type: SELL<br>" +
                                    "Orders: %{text}<br>" +
                                    "Lots: %{marker.size:.2f}<br>" +
                                    "Avg: %{y:,.2f}<br>" +
                                    "Min: %{customdata[2]:,.2f}<br>" +
                                    "Max: %{customdata[3]:,.2f}<br>" +
                                    "Profit: %{customdata[1]:,.2f}<extra></extra>",
                                    customdata=sell_group[['Magic', 'TotalProfit', 'MinPrice', 'MaxPrice']]
                                ))

                            fig_b.update_layout(
                                title=dict(text="Portfolio Split (Buy vs Sell)", font=dict(color='white', size=14, family=common_font)),
                                margin=dict(l=20, r=20, t=40, b=20),
                                xaxis=dict(
                                    showgrid=False, zeroline=False, 
                                    tickfont=dict(color='white', size=14, family=common_font, weight='bold'),
                                    side='bottom'
                                ),
                                yaxis=dict(
                                    title="Price Level",
                                    gridcolor='#333', 
                                    tickfont=dict(color='white', family=common_font)
                                ),
                                paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', height=500, showlegend=False
                            )
                            st.plotly_chart(fig_b, use_container_width=True, config={'displayModeBar': False})
                            
                            # --- 5. ตารางสรุป (เพิ่มช่อง Profit) ---
                            st.markdown("<br>", unsafe_allow_html=True)
                            with st.expander("📊 ดูสรุปตาม Magic Number (Summary)", expanded=True):
                                
                                # เพิ่ม TotalProfit เข้ามาในตารางแสดงผล
                                display_df = magic_summary[['Magic', 'OrderType', 'OrderCount', 'TotalLots', 'MinPrice', 'MaxPrice', 'AvgPrice', 'TotalProfit']].copy()
                                display_df.columns = ['Magic', 'Type', 'Count', 'Lots', 'Min', 'Max', 'Avg Price', 'Profit']
                                
                                display_df['Lots'] = display_df['Lots'].map('{:,.2f}'.format)
                                display_df['Min'] = display_df['Min'].map('{:,.2f}'.format)
                                display_df['Max'] = display_df['Max'].map('{:,.2f}'.format)
                                display_df['Avg Price'] = display_df['Avg Price'].map('{:,.2f}'.format)
                                display_df['Profit'] = display_df['Profit'].map('{:,.2f}'.format) # Format Profit
                                
                                def highlight_type(val):
                                    color = '#00C853' if val == 'Buy' else '#D50000'
                                    return f'color: {color}; font-weight: bold'

                                st.dataframe(display_df.style.map(highlight_type, subset=['Type']), use_container_width=True, height=300)

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
