import streamlit as st
import sqlite3
import pandas as pd
import os

# Page Config
st.set_page_config(
    page_title="FTC Bank Ledger",
    page_icon="🏦",
    layout="wide"
)

# Custom Banking CSS Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        font-family: 'Inter', sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .metric-label {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #10b981;
        font-size: 2.2rem;
        font-weight: 700;
        margin-top: 5px;
    }
    .role-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .admin-badge {
        background-color: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        border: 1px solid #3b82f6;
    }
    .merchant-badge {
        background-color: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid #f59e0b;
    }
    </style>
""", unsafe_allow_html=True)

# 1. Database Setup
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

LOGO_PATH = "uploaded_logo.png"

# 2. Hardcoded Credentials & Session Management
USER_CREDENTIALS = {
    "admin@bank.com": {"password": "admin123", "role": "Admin"},
    "susan@ftc.com": {"password": "Campbell@123", "role": "Merchant"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_email = None

def login(email, password):
    if email in USER_CREDENTIALS and USER_CREDENTIALS[email]["password"] == password:
        st.session_state.logged_in = True
        st.session_state.role = USER_CREDENTIALS[email]["role"]
        st.session_state.user_email = email
        return True
    return False

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_email = None
    st.rerun()

# 3. Login Screen Render
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🏦 Secure Ledger Sign In")
        st.markdown("Please log in with your assigned credentials.")

        with st.form("login_form"):
            email_input = st.text_input("Email Address", placeholder="Enter your email")
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Sign In")

            if submit_login:
                if login(email_input.strip().lower(), password_input):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
    st.stop()

# 4. Authenticated Dashboard View
st.sidebar.title("👤 Account")
st.sidebar.write(f"Logged in as: **{st.session_state.user_email}**")

if st.sidebar.button("🚪 Sign Out"):
    logout()

st.sidebar.markdown("---")

# Admin-only branding settings
if st.session_state.role == "Admin":
    st.sidebar.subheader("🎨 Custom Branding")
    uploaded_file = st.sidebar.file_uploader("Upload Bank/Company Logo", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        with open(LOGO_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.sidebar.success("Logo updated successfully!")
        st.rerun()

# Header Layout
col_logo, col_title = st.columns([1, 4])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=150)
    else:
        st.markdown("### 🏦 **BANK LOGO**")

with col_title:
    st.title("Deposit Ledger")
    if st.session_state.role == "Admin":
        st.markdown('<span class="role-badge admin-badge">● ADMIN ACCESS - EDIT MODE ENABLED</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="role-badge merchant-badge">🔒 MERCHANT VIEW - READ ONLY</span>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 5. Fetch Ledger Data & Calculate Metrics
df = pd.read_sql_query("SELECT id, date AS 'Transaction Date', vendor AS 'Vendor Name', notes AS 'Reference / Notes', amount AS 'Amount Paid ($)' FROM ledger ORDER BY id DESC", conn)

total_paid = df["Amount Paid ($)"].sum() if not df.empty else 0.0
total_txs = len(df)

m_col1, m_col2 = st.columns(2)

with m_col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Credit Balance Received</div>
            <div class="metric-value">${total_paid:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Transactions Settled</div>
            <div class="metric-value" style="color: #60a5fa;">{total_txs}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 6. Admin Payment Entry Form
if st.session_state.role == "Admin":
    with st.expander("➕ **Post New Vendor Credit Transaction**", expanded=True):
        with st.form("add_payment_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                vendor = st.text_input("Vendor Name", placeholder="e.g. Acme Logistics")
                amount = st.number_input("Amount Paid ($)", min_value=0.0, step=50.0, format="%.2f")
            with f_col2:
                notes = st.text_area("Reference / Memo / Invoice ID", placeholder="e.g. Wire Ref #987123", height=105)
            
            submitted = st.form_submit_button("💳 Deposit to Ledger")
            if submitted:
                if vendor and amount > 0:
                    c.execute("INSERT INTO ledger (vendor, amount, notes) VALUES (?, ?, ?)", (vendor, amount, notes))
                    conn.commit()
                    st.success(f"Successfully posted payment of ${amount:,.2f} for {vendor}")
                    st.rerun()
                else:
                    st.error("Please provide both a valid vendor name and an amount greater than $0.")

# 7. Settlement Records Table
st.subheader("📋 Settlement Records")
if not df.empty:
    df_display = df.copy()
    df_display["Amount Paid ($)"] = df_display["Amount Paid ($)"].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(
        df_display,
        hide_index=True,
        width="stretch"
    )
else:
    st.info("No transaction records found in the ledger database.")
