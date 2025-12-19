import streamlit as st
import pandas as pd
import json
import time

# ---------------------------------------------------------
# 🛠 ใส่ SHEET ID ของคุณตรงนี้ 🛠
SHEET_ID = "ใส่_SHEET_ID_ของคุณตรงนี้"
# ---------------------------------------------------------

SHEET_URL = f"https://docs.google.com/spreadsheets/d/1BdkpzNz5lqECpnyc7PgC1BQMc5FeOyqkE_lonF36ANQ/export?format=csv"

# ตั้งค่าหน้าเว็บให้เป็น Wide Mode (เต็มจอ) และใส่ Title
st.set_page_config(
    page_title="EASYGold Monitor",
    page_icon="🏆",
    layout="wide"
)

# แต่ง CSS นิดหน่อยให้ตารางสวยขึ้น (ซ่อน index)
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
st.markdown(hide_table_row_index, unsafe_allow_html=True)

def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return None

# --- ส่วน Sidebar (เมนูซ้าย) ---
with st.sidebar:
    st.header("⚙️ Settings")
    user_input = st.text_input("🔑 Account ID", "", placeholder="กรอกเลขพอร์ตที่นี่...")
    
    st.markdown("---")
    st.caption("Auto-refresh every 5 seconds")
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()

# --- ส่วนหน้าจอหลัก ---
st.title("🏆 EASYGold Portfolio Monitor")
st.markdown("ระบบติดตามพอร์ตลงทุนทองคำ Real-time")

placeholder = st.empty()

while True:
    df = load_data()
    
    with placeholder.container():
        if df is None:
            st.error("⚠️ ไม่สามารถเชื่อมต่อกับฐานข้อมูลได้")
        else:
            df['AccountID'] = df['AccountID'].astype(str)
            
            # กรองข้อมูล
            if user_input:
                target_df = df[df['AccountID'] == user_input]
            else:
                target_df = df.tail(1) # ถ้าไม่กรอก เอาล่าสุดมาโชว์

            if not target_df.empty:
                latest = target_df.iloc[-1]
                
                # แสดงเวลา Update ล่าสุด
                st.caption(f"🕒 Last Update: {latest['UpdateTime']} | Account: {latest['AccountID']}")
                st.markdown("---")

                # --- ส่วนที่ 1: การเงิน (Metrics) ---
                c1, c2, c3, c4 = st.columns(4)
                
                c1.metric("💰 Balance", f"${latest['Balance']:,.2f}")
                c2.metric("🛡 Equity", f"${latest['Equity']:,.2f}")
                
                # คำนวณ Margin Level (สมมติ) หรือโชว์ Profit
                profit = latest['TotalProfit']
                c3.metric("📊 Total Profit", f"${profit:,.2f}", 
                          delta=profit, delta_color="normal")
                
                # แสดงจำนวนออเดอร์รวม
                total_orders = latest['BuyCount'] + latest['SellCount']
                c4.metric("📝 Total Orders", f"{total_orders} ไม้")

                # --- ส่วนที่ 2: แบ่ง Tab เพื่อความสะอาดตา ---
                tab1, tab2 = st.tabs(["📈 Overview (ภาพรวม)", "📋 Order Details (รายการ)"])
                
                with tab1:
                    # สร้างกราฟแท่งเปรียบเทียบ Buy vs Sell
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        st.info("🟢 BUY SIDE")
                        st.write(f"Volume: **{latest['BuyLots']:.2f} Lot**")
                        st.write(f"Count: **{latest['BuyCount']} Orders**")
                        # Progress bar จำลอง
                        if total_orders > 0:
                            st.progress(latest['BuyCount'] / total_orders)
                        
                    with col_chart2:
                        st.error("🔴 SELL SIDE")
                        st.write(f"Volume: **{latest['SellLots']:.2f} Lot**")
                        st.write(f"Count: **{latest['SellCount']} Orders**")
                        if total_orders > 0:
                            st.progress(latest['SellCount'] / total_orders)

                with tab2:
                    # ตารางออเดอร์
                    try:
                        orders = json.loads(latest['JSON_Data'])
                        if len(orders) > 0:
                            orders_df = pd.DataFrame(orders)
                            # เปลี่ยนชื่อคอลัมน์ให้สวยงาม
                            orders_df.rename(columns={
                                's': 'Symbol', 't': 'Type', 
                                'v': 'Volume', 'p': 'Open Price', 
                                'pl': 'Profit'
                            }, inplace=True)
                            
                            # ไฮไลท์สีในตาราง (ถ้าทำได้) หรือโชว์ปกติ
                            st.dataframe(orders_df, use_container_width=True)
                        else:
                            st.info("✅ พอร์ตว่าง (No open positions)")
                    except:
                        st.warning("ไม่มีข้อมูลรายละเอียดออเดอร์")

            elif user_input:
                st.warning(f"❌ ไม่พบข้อมูลพอร์ต: {user_input}")
            else:
                st.info("👈 กรุณากรอกเลข Account ID ที่เมนูด้านซ้าย")

    # หน่วงเวลา 5 วินาที
    time.sleep(5)
