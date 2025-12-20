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

                # --- 4. STRUCTURE CHART (All-in-One) ---
                st.markdown("---")
                orders_str = latest.get('JSON_Data', '[]')
                if pd.isna(orders_str) or orders_str == "": orders_str = '[]'
                
                try:
                    orders = json.loads(orders_str)
                    if len(orders) > 0 and current_price > 0:
                        orders_df = pd.DataFrame(orders)
                        orders_df.rename(columns={'s': 'Symbol', 't': 'Type', 'v': 'Volume', 'p': 'Open Price', 'pl': 'Profit', 'm': 'Magic'}, inplace=True)
                        
                        if 'Magic' in orders_df.columns:
                            # คำนวณ Avg Price ของแต่ละ Magic
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
                            
                            # เตรียมข้อมูลวาดกราฟ
                            fig_p = go.Figure()

                            # 1. เส้น Market Price
                            fig_p.add_hline(
                                y=current_price, line_dash="dash", line_color="#29B6F6", line_width=1,
                                annotation_text=f"Market: {current_price:,.2f}", annotation_position="top right", annotation_font=dict(color="#29B6F6", size=10)
                            )

                            # 2. วาดโครงสร้างทีละส่วน
                            # A. เส้นบาง (Orders)
                            fig_p.add_trace(go.Scatter(
                                x=orders_df['Magic'].astype(str),
                                y=orders_df['Open Price'],
                                mode='markers',
                                name='Orders',
                                marker=dict(symbol='line-ew', size=25, line=dict(width=1, color="rgba(255, 255, 255, 0.3)")),
                                hoverinfo='y+x'
                            ))

                            # B. เส้นหนา - Top
                            fig_p.add_trace(go.Scatter(
                                x=magic_stats['Magic'].astype(str),
                                y=magic_stats['MaxPrice'],
                                mode='markers',
                                name='Top',
                                marker=dict(symbol='line-ew', size=30, line=dict(width=3, color="#D50000")),
                                hovertemplate="Max: %{y:,.2f}<extra></extra>"
                            ))

                            # C. เส้นหนา - Bottom (แก้บรรทัดที่มีปัญหา)
                            fig_p.add_trace(go.Scatter(
                                x=magic_stats['Magic'].astype(str),
                                y=magic_stats['MinPrice'],
                                mode='markers',
                                name='Bottom',
                                marker=dict(symbol='line-ew', size=30, line=dict(width=3, color="#00C853")),
                                hovertemplate="Min: %{y:,.2f}<extra></extra>"
                            ))

                            # D. เส้นหนาพิเศษ - Average
                            fig_p.add_trace(go.Scatter(
                                x=magic_stats['Magic'].astype(str),
                                y=magic_stats['AvgPrice'],
                                mode='markers', 
                                name='Avg Price',
                                marker=dict(symbol='line-ew', size=40, line=dict(width=4, color="#FFD600")), 
                                hovertemplate="Avg: %{y:,.2f}<extra></extra>"
                            ))
                            
                            # E. ป้ายชื่อ Magic + จำนวนไม้ (วางไว้เหนือเส้น Top)
                            label_texts = [f"M: {m}<br>({c} Orders)" for m, c in zip(magic_stats['Magic'], magic_stats['OrderCount'])]
                            
                            fig_p.add_trace(go.Scatter(
                                x=magic_stats['Magic'].astype(str),
                                y=magic_stats['MaxPrice'], 
                                mode='text',
                                text=label_texts,
                                textposition="top center",
                                textfont=dict(color='white', size=11, family=common_font),
                                hoverinfo='skip'
                            ))

                            fig_p.update_layout(
                                title=dict(text="Portfolio Structure (All Magics)", font=dict(color='white', size=14, family=common_font)),
                                xaxis=dict(
                                    showticklabels=False, 
                                    type='category', 
                                    gridcolor='#333'
                                ),
                                yaxis=dict(
                                    title="Price Level", gridcolor='#333', tickfont=dict(color='white')
                                ),
                                margin=dict(l=40, r=20, t=40, b=40),
                                height=450,
                                showlegend=False,
                                paper_bgcolor='#0E1117', plot_bgcolor='#0E1117'
                            )
                            st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})

                            # --- 5. Summary Table ---
                            st.markdown("<br>", unsafe_allow_html=True)
                            with st.expander("📊 ดูสรุปตาม Magic Number (Summary)", expanded=False):
                                display_df = magic_stats[['Magic', 'OrderType', 'TotalVol', 'MinPrice', 'MaxPrice', 'AvgPrice']].copy()
                                profit_df = orders_df.groupby('Magic')['Profit'].sum().reset_index()
                                display_df = display_df.merge(profit_df, on='Magic')
                                
                                display_df.columns = ['Magic', 'Type', 'Lots', 'Min', 'Max', 'Avg Price', 'Profit']
                                for c in ['Lots', 'Min', 'Max', 'Avg Price', 'Profit']: display_df[c] = display_df[c].map('{:,.2f}'.format)
                                
                                def highlight_type(val): return f'color: {"#00C853" if val == "Buy" else "#D50000"}; font-weight: bold'
                                st.dataframe(display_df.style.map(highlight_type, subset=['Type']), use_container_width=True, height=300)

                        else:
                            st.info("⚠️ ไม่พบข้อมูล Magic Number")
                    else:
                        st.info("✅ พอร์ตว่าง (No Active Orders)")

                # End JSON try block
                except Exception as e:
                     st.error(f"Error parsing JSON: {e}")
            else:
                st.warning(f"ไม่พบข้อมูลสำหรับ: {selected_account}")
    except Exception as main_e:
        st.error(f"System Error: {main_e}")

time.sleep(5)
st.rerun()
