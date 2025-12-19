import streamlit as st
import pandas as pd
import json
import time

# --- 🛠 แก้ไขตรงนี้: ใส่ ID ของ Google Sheet คุณ 🛠 ---
# ตัวอย่าง: ถ้าลิงก์คือ .../d/1A2b3C.../edit ก็เอาแค่ 1A2b3C... มาใส่
SHEET_ID = "ใส่_SHEET_ID_ของคุณตรงนี้" 
# --------------------------------------------------

SHEET_URL = f"https://docs.google.com/spreadsheets/d/1BdkpzNz5lqECpnyc7PgC1BQMc5FeOyqkE_lonF36ANQ/export?format=csv"

st.set_page_config(page_title="Forex Monitor", layout="wide")

def load_data():
    try:
        # อ่าน CSV จาก Google Sheet
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns] # ลบช่องว่างหัวตาราง
        return df
    except Exception as e:
        return None

st.title("🌐 Live Portfolio Monitor")

# ช่องกรอกเลขพอร์ต (ใส่เลขพอร์ตเริ่มต้นไว้ให้ User เห็นได้เลย)
user_input = st.text_input("🔍 กรอกเลขบัญชี (Account ID)", "") 

placeholder = st.empty()

while True:
    df = load_data()
    
    with placeholder.container():
        if df is None:
            st.warning("⏳ กำลังเชื่อมต่อ... (ถ้าค้างนานเช็ค Sheet ID หรือ Permission)")
        else:
            # แปลง AccountID เป็นตัวหนังสือเพื่อให้เทียบง่าย
            df['AccountID'] = df['AccountID'].astype(str)
            
            # กรองข้อมูลตามเลขพอร์ตที่กรอก
            if user_input:
                target_df = df[df['AccountID'] == user_input]
            else:
                # ถ้าไม่กรอก โชว์บรรทัดล่าสุด
                target_df = df.tail(1)

            if not target_df.empty:
                latest = target_df.iloc[-1]
                
                # แสดงเวลาอัปเดต
                st.info(f"Update: {latest['UpdateTime']}")
                
                # แสดงสถานะการเงิน
                c1, c2, c3 = st.columns(3)
                c1.metric("Balance", f"{latest['Balance']:,.2f}")
                c2.metric("Equity", f"{latest['Equity']:,.2f}")
                c3.metric("Profit", f"{latest['TotalProfit']:,.2f}", 
                          delta=latest['TotalProfit'], delta_color="normal")
                
                st.markdown("---")

                # แสดงยอด Buy/Sell
                col1, col2 = st.columns(2)
                col1.success(f"BUY: {latest['BuyCount']} ไม้ ({latest['BuyLots']} Lot)")
                col2.error(f"SELL: {latest['SellCount']} ไม้ ({latest['SellLots']} Lot)")

                # แสดงตารางออเดอร์
                try:
                    orders = json.loads(latest['JSON_Data'])
                    if len(orders) > 0:
                        st.subheader("📋 รายละเอียดออเดอร์")
                        st.dataframe(orders)
                    else:
                        st.info("ไม่มีออเดอร์ค้าง")
                except:
                    pass
            
            elif user_input:
                st.error(f"❌ ไม่พบข้อมูลพอร์ต: {user_input}")

    time.sleep(5) # อัปเดตทุก 5 วินาที
