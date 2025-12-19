import streamlit as st
import pandas as pd
import json
import time

# ---------------------------------------------------------
# 🛠 ใส่ SHEET ID ของคุณตรงนี้ 🛠
SHEET_ID = "ใส่_SHEET_ID_ของคุณตรงนี้"
# ---------------------------------------------------------

SHEET_URL = f"https://docs.google.com/spreadsheets/d/1BdkpzNz5lqECpnyc7PgC1BQMc5FeOyqkE_lonF36ANQ/export?format=csv"

st.set_page_config(
    page_title="Magic Number Monitor",
    page_icon="🔮",
    layout="wide"
)

# ซ่อน index ตารางเพื่อความสวยงาม
hide_table_style = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
st.markdown(hide_table_style, unsafe_allow_html=True)

def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return None

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Filter")
    user_input = st.text_input("🔑 Account ID", "")
    if st.button("🔄 Refresh"):
        st.cache_data.clear()

# --- Main Page ---
st.title("🔮 Portfolio by Magic Number")

placeholder = st.empty()

while True:
    df = load_data()
    
    with placeholder.container():
        if df is None:
            st.error("Connecting to database...")
        else:
            df['AccountID'] = df['AccountID'].astype(str)
            
            if user_input:
                target_df = df[df['AccountID'] == user_input]
            else:
                target_df = df.tail(1)

            if not target_df.empty:
                latest = target_df.iloc[-1]
                
                # Header Stats
                c1, c2, c3 = st.columns(3)
                c1.metric("Balance", f"${latest['Balance']:,.2f}")
                c2.metric("Equity", f"${latest['Equity']:,.2f}")
                c3.metric("Profit", f"${latest['TotalProfit']:,.2f}", delta=latest['TotalProfit'])
                st.markdown("---")

                # --- ส่วนสำคัญ: แปลงข้อมูล JSON และคำนวณแยก Magic Number ---
                try:
                    orders = json.loads(latest['JSON_Data'])
                    
                    if len(orders) > 0:
                        orders_df = pd.DataFrame(orders)
                        
                        # เปลี่ยนชื่อ Column จากตัวย่อเป็นตัวเต็ม (รวมถึง m = Magic)
                        orders_df.rename(columns={
                            's': 'Symbol', 't': 'Type', 
                            'v': 'Volume', 'p': 'Open Price', 
                            'pl': 'Profit', 'm': 'Magic Number'
                        }, inplace=True)

                        # ตรวจสอบว่ามีข้อมูล Magic Number มาหรือยัง
                        if 'Magic Number' in orders_df.columns:
                            
                            st.subheader("📊 สรุปแยกตาม Magic Number")
                            
                            # 1. จัดกลุ่มและคำนวณ (Group By)
                            magic_summary = orders_df.groupby('Magic Number').agg(
                                Orders_Count=('Symbol', 'count'),      # นับจำนวนไม้
                                Total_Lots=('Volume', 'sum'),          # รวม Lot
                                Min_Price=('Open Price', 'min'),       # ราคาต่ำสุด
                                Max_Price=('Open Price', 'max'),       # ราคาสูงสุด
                                Total_Profit=('Profit', 'sum')         # กำไรรวมของชุดนั้น
                            ).reset_index()

                            # จัด format ตัวเลขให้สวยงาม
                            magic_summary['Total_Lots'] = magic_summary['Total_Lots'].map('{:,.2f}'.format)
                            magic_summary['Min_Price'] = magic_summary['Min_Price'].map('{:,.2f}'.format)
                            magic_summary['Max_Price'] = magic_summary['Max_Price'].map('{:,.2f}'.format)
                            magic_summary['Total_Profit'] = magic_summary['Total_Profit'].map('{:,.2f}'.format)

                            # แสดงตารางสรุป
                            st.dataframe(magic_summary, use_container_width=True)
                            
                            st.markdown("---")
                            
                            # แสดงรายการออเดอร์ทั้งหมดด้านล่าง
                            st.subheader("📋 รายละเอียดทุกออเดอร์")
                            st.dataframe(orders_df, use_container_width=True)
                            
                        else:
                            st.warning("⚠️ ข้อมูลยังไม่มี Magic Number (กรุณาอัปเดต EA ใน MT5)")
                            st.dataframe(orders_df)
                            
                    else:
                        st.info("✅ พอร์ตว่าง ไม่มีออเดอร์")
                        
                except Exception as e:
                    st.error(f"Error processing data: {e}")

            elif user_input:
                st.warning(f"ไม่พบข้อมูล Account: {user_input}")
            else:
                st.info("กรุณากรอก Account ID ด้านซ้ายมือ")

    time.sleep(5)
