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
        padding-top: 0.5rem;
        padding-bottom: 0rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
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
    st.header("⚙️ Settings")
    user_input = st.text_input("Account ID", "")

# --- Main Page ---
placeholder = st.empty()

while True:
    df = load_data()
    
    with placeholder.container():
        if df is None:
            st.error("Connecting...")
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
                # ส่วนที่ 1: Compact Header (แก้บั๊กกรอบขาว 100%)
                # =========================================================
                # เทคนิค: เขียน HTML ต่อกันเป็นบรรทัดเดียว ไม่เว้นวรรคบรรทัดใหม่
                header_html = f"<div style='display: flex; justify-content: space-between; align-items: center; background-color: #1E222D; padding: 12px 15px; border-radius: 10px; margin-bottom: 5px; border: 1px solid #333;'><div style='text-align: left; line-height: 1.2;'><span style='color: #9E9E9E; font-size: 0.85rem; font-family: sans-serif;'>PRICE (Bid)</span><br><span style='color: #29B6F6; font-size: 1.5rem; font-weight: 700; font-family: sans-serif;'>${current_price:,.2f}</span></div><div style='text-align: right; line-height: 1.2;'><span style='color: #9E9E9E; font-size: 0.85rem; font-family: sans-serif;'>LOTS</span><br><span style='color: #FFA726; font-size: 1.5rem; font-weight: 700; font-family: sans-serif;'>{total_lots:.2f}</span></div></div>"
                
                st.markdown(header_html, unsafe_allow_html=True)

                # =========================================================
                # ส่วนที่ 2: Smart Bar Chart
                # =========================================================
                fig = go.Figure()
                
                if profit >= 0:
                    # กำไร: ฟ้า(Balance) + เขียว(Profit)
                    fig.add_trace(go.Bar(
                        x=[balance], y=[""], orientation='h',
                        marker_color='#0288D1', hoverinfo='none',
                        text=f"Bal: ${balance:,.0f}", textposition='auto',
                        textfont=dict(color='white', size=14)
                    ))
                    fig.add_trace(go.Bar(
                        x=[profit], y=[""], orientation='h',
                        marker_color='#00C853', hoverinfo='none',
                        text=f"+${profit:,.0f}", textposition='inside',
                        textfont=dict(color='white', size=14, weight='bold')
                    ))
                else:
                    # ขาดทุน: ฟ้า(Equity) + แดง(Loss)
                    fig.add_trace(go.Bar(
                        x=[equity], y=[""], orientation='h',
                        marker_color='#0288D1', hoverinfo='none',
                        text=f"Eq: ${equity:,.0f}", textposition='auto',
                        textfont=dict(color='white', size=14)
                    ))
                    fig.add_trace(go.Bar(
                        x=[abs(profit)], y=[""], orientation='h',
                        marker_color='#D50000', hoverinfo='none',
                        text=f"-${abs(profit):,.0f}", textposition='inside',
                        textfont=dict(color='white', size=14)
                    ))

                # เส้น Balance
                fig.add_vline(x=balance, line_width=2, line_color="white", opacity=0.8)
                
                # Equity Label
                fig.add_annotation(
                    x=equity, y=0,
                    text=f"Equity: ${equity:,.2f}",
                    showarrow=False,
                    yshift=35,
                    font=dict(size=18, color="white", family="Arial Black"),
                    bgcolor="#0E1117", opacity=1
                )

                fig.update_layout(
                    barmode='stack', showlegend=False,
                    xaxis=dict(visible=False, range=[0, max(balance, equity) * 1.15]),
                    yaxis=dict(visible=False),
                    margin=dict(l=0, r=0, t=45, b=0),
                    height=110,
                    paper_bgcolor='#0E1117', plot_bgcolor='#0E1117'
                )
                
                st.plotly_chart(fig, use_container_width=True, key=f"bar_{time.time()}")

                # =========================================================
                # ส่วนที่ 3: Bubble Chart
                # =========================================================
                st.markdown("---")
                try:
                    orders = json.loads(latest['JSON_Data'])
                    if len(orders) > 0 and current_price > 0:
                        orders_df = pd.DataFrame(orders)
                        orders_df.rename(columns={'v': 'Volume', 'p': 'Open Price', 'pl': 'Profit', 'm': 'Magic'}, inplace=True)
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
                            st.plotly_chart(fig_b, use_container_width=True, key=f"bub_{time.time()}")
                except:
                    pass

            elif user_input:
                st.warning(f"Not found: {user_input}")
            else:
                st.info("Enter Account ID in Sidebar")

    time.sleep(5)
