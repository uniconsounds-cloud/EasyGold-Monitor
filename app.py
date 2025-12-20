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
        background-color: #1E222D; color: white; border-color: #333;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. ตัวแปรจำค่า (Session State) ---
# ตัวแปรนี้คือ "พระเอก" ที่จะเชื่อมกราฟกับ Dropdown เข้าด้วยกัน
if 'focused_magic' not in st.session_state:
    st.session_state.focused_magic = None

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
        
        # 1. Select Account
        if len(all_accounts) > 0:
            selected_account = st.selectbox("📌 เลือกพอร์ต (Select Account):", all_accounts, index=0)
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

                # 2. Header
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

                # --- 4. BUBBLE CHART PREP ---
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
                                OrderType=('Type', 'first'), OrderCount=('Magic', 'count'), TotalLots=('Volume', 'sum'),
                                MinPrice=('Open Price', 'min'), MaxPrice=('Open Price', 'max'),
                                SumWeighted=('WeightedVal', 'sum'), TotalProfit=('Profit', 'sum')
                            ).reset_index()
                            magic_summary['AvgPrice'] = magic_summary['SumWeighted'] / magic_summary['TotalLots']
                            
                            buy_group = magic_summary[magic_summary['OrderType'] == 'Buy']
                            sell_group = magic_summary[magic_summary['OrderType'] == 'Sell']

                            fig_b = go.Figure()
                            fig_b.add_hline(y=current_price, line_dash="dash", line_color="#29B6F6", annotation_text=f"Market: {current_price:,.2f}", annotation_position="top left", annotation_font=dict(color="#29B6F6", size=12))

                            if not buy_group.empty:
                                fig_b.add_trace(go.Scatter(
                                    x=["BUY Zone"] * len(buy_group), y=buy_group['AvgPrice'], mode='markers+text', name='Buy',
                                    marker=dict(size=buy_group['TotalLots'], sizemode='area', sizeref=2.*max(magic_summary['TotalLots'])/(70.**2), sizemin=18, color='#00C853', line=dict(width=1, color='white')),
                                    text=buy_group['OrderCount'], textposition="middle center", textfont=dict(color='white', family=common_font, weight='bold'),
                                    hovertemplate="<b>Magic: %{customdata[0]}</b><br>Orders: %{customdata[4]}<br>Lots: %{marker.size:.2f}<br>Avg: %{y:,.2f}<br>Min: %{customdata[2]:,.2f}<br>Max: %{customdata[3]:,.2f}<br>Profit: %{customdata[1]:,.2f}<extra></extra>",
                                    customdata=buy_group[['Magic', 'TotalProfit', 'MinPrice', 'MaxPrice', 'OrderCount']]
                                ))

                            if not sell_group.empty:
                                fig_b.add_trace(go.Scatter(
                                    x=["SELL Zone"] * len(sell_group), y=sell_group['AvgPrice'], mode='markers+text', name='Sell',
                                    marker=dict(size=sell_group['TotalLots'], sizemode='area', sizeref=2.*max(magic_summary['TotalLots'])/(70.**2), sizemin=18, color='#D50000', line=dict(width=1, color='white')),
                                    text=sell_group['OrderCount'], textposition="middle center", textfont=dict(color='white', family=common_font, weight='bold'),
                                    hovertemplate="<b>Magic: %{customdata[0]}</b><br>Orders: %{customdata[4]}<br>Lots: %{marker.size:.2f}<br>Avg: %{y:,.2f}<br>Min: %{customdata[2]:,.2f}<br>Max: %{customdata[3]:,.2f}<br>Profit: %{customdata[1]:,.2f}<extra></extra>",
                                    customdata=sell_group[['Magic', 'TotalProfit', 'MinPrice', 'MaxPrice', 'OrderCount']]
                                ))

                            fig_b.update_layout(
                                title=dict(text="Portfolio Split (Tap to Inspect)", font=dict(color='white', size=14, family=common_font)),
                                margin=dict(l=20, r=20, t=40, b=20),
                                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='white', size=14, family=common_font, weight='bold'), side='bottom'),
                                yaxis=dict(title="Price Level", gridcolor='#333', tickfont=dict(color='white', family=common_font)),
                                paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', height=450, showlegend=False,
                                clickmode='event+select'
                            )
                            
                            # 🔥 รับค่า Touch Event
                            event = st.plotly_chart(fig_b, use_container_width=True, config={'displayModeBar': False}, on_select="rerun", key="bubble_chart_main")
                            
                            # 🔥 LOGIC 1: เช็คว่ามีการแตะกราฟไหม
                            if event and event.selection and len(event.selection['points']) > 0:
                                try:
                                    clicked_magic = event.selection['points'][0]['customdata'][0]
                                    # ถ้าค่าที่คลิก ไม่ตรงกับค่าปัจจุบัน -> อัปเดตและสั่งรีเฟรชหน้าจอทันที
                                    if clicked_magic != st.session_state.focused_magic:
                                        st.session_state.focused_magic = clicked_magic
                                        st.rerun() # 👈 สำคัญมาก: รีเฟรชเพื่อไปบังคับ Dropdown ในรอบถัดไป
                                except:
                                    pass

                            # --- 6. PRICE STRUCTURE & SYNCED DROPDOWN ---
                            
                            # เตรียมลิสต์สำหรับ Dropdown
                            magic_list = sorted(magic_summary['Magic'].unique().tolist())
                            
                            # 🔥 LOGIC 2: คำนวณ Index ของ Dropdown จากค่า focused_magic
                            current_index = 0
                            if st.session_state.focused_magic in magic_list:
                                current_index = magic_list.index(st.session_state.focused_magic)
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            col_sel1, col_sel2 = st.columns([1, 2])
                            with col_sel1: st.caption("Selected Magic:")
                            with col_sel2:
                                # สร้าง Dropdown โดยบังคับ Index
                                manual_select = st.selectbox(
                                    "🔍 เจาะลึก Magic Number", 
                                    magic_list, 
                                    index=current_index, # 👈 บังคับให้เด้งไปที่ค่าที่เลือก
                                    key="manual_dropdown_widget"
                                )
                                
                                # 🔥 LOGIC 3: ถ้าคนเปลี่ยน Dropdown ด้วยมือ ก็ให้อัปเดตกลับไปที่ focused_magic ด้วย
                                if manual_select != st.session_state.focused_magic:
                                    st.session_state.focused_magic = manual_select
                                    st.rerun()

                            # ใช้ค่าจากตัวแปรหลักมาแสดงผล
                            final_magic = st.session_state.focused_magic

                            if final_magic:
                                st.markdown(f"##### 🎯 Structure of Magic: {final_magic}")
                                specific_orders = orders_df[orders_df['Magic'] == final_magic].copy()
                                
                                if not specific_orders.empty:
                                    max_p = specific_orders['Open Price'].max()
                                    min_p = specific_orders['Open Price'].min()
                                    sum_w = (specific_orders['Volume'] * specific_orders['Open Price']).sum()
                                    avg_p = sum_w / specific_orders['Volume'].sum()
                                    
                                    fig_s = go.Figure()
                                    fig_s.add_trace(go.Scatter(x=[0.5]*len(specific_orders), y=specific_orders['Open Price'], mode='markers', marker=dict(symbol='line-ew', size=300, line=dict(width=1, color="rgba(255, 255, 255, 0.4)")), name='Orders', hoverinfo='y'))
                                    fig_s.add_trace(go.Scatter(x=[0.5], y=[max_p], mode='markers+text', marker=dict(symbol='line-ew', size=300, line=dict(width=4, color="#D50000")), text=[f"Top: {max_p:,.2f}"], textposition="top center", textfont=dict(color="#D50000"), name='Top'))
                                    fig_s.add_trace(go.Scatter(x=[0.5], y=[min_p], mode='markers+text', marker=dict(symbol='line-ew', size=300, line=dict(width=4, color="#00C853")), text=[f"Bot: {min_p:,.2f}"], textposition="bottom center", textfont=dict(color="#00C853"), name='Bottom'))
                                    fig_s.add_trace(go.Scatter(x=[0.5], y=[avg_p], mode='markers+text', marker=dict(symbol='line-ew', size=300, line=dict(width=2, color="#FFD600")), text=[f"Avg: {avg_p:,.2f}"], textposition="middle right", textfont=dict(color="#FFD600"), name='Avg'))

                                    fig_s.update_layout(xaxis=dict(visible=False, range=[0, 1]), yaxis=dict(title="Price", gridcolor='#333', tickfont=dict(color='white')), margin=dict(l=40, r=40, t=30, b=20), height=300, showlegend=False, paper_bgcolor='#0E1117', plot_bgcolor='#0E1117')
                                    st.plotly_chart(fig_s, use_container_width=True, config={'displayModeBar': False})

                            # --- 7. Summary Table ---
                            st.markdown("<br>", unsafe_allow_html=True)
                            with st.expander("📊 ดูสรุปตาม Magic Number (Summary)", expanded=False):
                                display_df = magic_summary[['Magic', 'OrderType', 'OrderCount', 'TotalLots', 'MinPrice', 'MaxPrice', 'AvgPrice', 'TotalProfit']].copy()
                                display_df.columns = ['Magic', 'Type', 'Count', 'Lots', 'Min', 'Max', 'Avg Price', 'Profit']
                                for c in ['Lots', 'Min', 'Max', 'Avg Price', 'Profit']: display_df[c] = display_df[c].map('{:,.2f}'.format)
                                def highlight_type(val): return f'color: {"#00C853" if val == "Buy" else "#D50000"}; font-weight: bold'
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
