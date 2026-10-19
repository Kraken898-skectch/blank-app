import streamlit as st
import sqlite3
import pandas as pd
import os

# 1. Database Setup (SQLite - local file database)
conn = sqlite3.connect('ledger.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor TEXT NOT NULL,
        amount REAL NOT NULL,
        notes TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Setup Streamlit Page Config
st.set_page_config(page_title="Vendor Ledger", page_icon="💰")

# 2. Logo Management
LOGO_PATH = "uploaded_logo.png"

def display_logo():
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=200)
    else:
        st.info("No logo uploaded yet.")

# 3. Simple Authentication / Role Switcher
st.sidebar.title("Login Settings")
user_role = st.sidebar.radio("Select Role:", ["Merchant (Read-Only)", "Admin (Edit/Upload)"])

# 4. Display Header & Logo
display_logo()
st.title("Vendor Payment Ledger")

# 5. Admin Section: Logo Upload & Add Payment
if user_role == "Admin (Edit/Upload)":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Admin Settings")
    
    # Logo Upload Component
    uploaded_file = st.sidebar.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        with open(LOGO_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.sidebar.success("Logo updated!")
        st.rerun()

    # Form to add payments
    st.subheader("➕ Record New Payment")
    with st.form("add_payment_form", clear_on_submit=True):
        vendor = st.text_input("Vendor Name")
        amount = st.number_input("Amount Paid ($)", min_value=0.0, step=10.0)
        notes = st.text_area("Notes (e.g., Invoice #, Check ID)")
        submitted = st.form_submit_button("Add to Ledger")

        if submitted and vendor and amount > 0:
            c.execute("INSERT INTO ledger (vendor, amount, notes) VALUES (?, ?, ?)", (vendor, amount, notes))
            conn.commit()
            st.success(f"Recorded payment of ${amount} for {vendor}")
            st.rerun()

else:
    st.info("🔒 Logged in as **Merchant**. You have read-only access.")

st.markdown("---")

# 6. Display Totals & Ledger Table for Both Roles
df = pd.read_sql_query("SELECT id, date, vendor, notes, amount FROM ledger ORDER BY id DESC", conn)

total_paid = df["amount"].sum() if not df.empty else 0.0
st.metric(label="Total Received Across All Vendors", value=f"${total_paid:,.2f}")

st.subheader("Payment History")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.write("No payment records found.")
