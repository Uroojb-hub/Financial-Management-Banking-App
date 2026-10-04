import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine

st.set_page_config(page_title="PaySim Banking App", layout="wide")

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

st.title("💳 PaySim - Financial Management & Banking")

# Import auth safely inside a try-except block so UI never breaks
try:
    import auth
    auth_loaded = True
except Exception as e:
    auth_loaded = False
    st.error(f"Error loading auth module: {e}")

# 1. AUTHENTICATION UI
if not st.session_state['logged_in']:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab1:
        st.subheader("User Login")
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login"):
            if auth_loaded:
                success, message = auth.login_user(login_user, login_pass)
                if success:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = login_user
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with tab2:
        st.subheader("Create New Account")
        new_user = st.text_input("Username", key="new_user")
        new_email = st.text_input("Email", key="new_email")
        new_pass = st.text_input("Password", type="password", key="new_pass")
        
        if st.button("Sign Up"):
            if auth_loaded:
                if new_user and new_email and new_pass:
                    success, message = auth.register_user(new_user, new_email, new_pass)
                    if success:
                        st.success("Account created successfully! Please log in.")
                    else:
                        st.error(message)
                else:
                    st.warning("Please fill in all fields.")

# 2. DASHBOARD & REST API FRAUD UI
else:
    st.sidebar.success(f"Logged in as: {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.rerun()

    dash_tab, predict_tab = st.tabs(["📊 Transaction Dashboard", "🤖 Fraud Detection via REST API"])

    engine = create_engine("mysql+pymysql://root:Yonkoluffy$3B@localhost:3306/paysim")

# NO SPACES IN FRONT OF @st.cache_data
@st.cache_data
def load_transaction_data():
    try:
        engine = create_engine("mysql+pymysql://root:Yonkoluffy$3B@localhost:3306/paysim", connect_args={"connect_timeout": 2})
        df = pd.read_sql("SELECT * FROM transactions LIMIT 5000", engine)
        return df
    except Exception:
        return pd.read_csv("paysim_sample.csv")
        
    with dash_tab:
        if not df.empty:
            st.sidebar.header("Filter Options")
            selected_type = st.sidebar.selectbox("Select Transaction Type", ["ALL"] + list(df['type'].unique()))

            filtered_df = df if selected_type == "ALL" else df[df['type'] == selected_type]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Transactions", len(filtered_df))
            col2.metric("Total Volume ($)", f"${filtered_df['amount'].sum():,.2f}")
            col3.metric("Flagged Fraud Cases", int(filtered_df['isFraud'].sum()))

            st.subheader("Transaction Records")
            st.dataframe(filtered_df, use_container_width=True)

    with predict_tab:
        st.subheader("Score Transaction via FastAPI REST Service")
        
        c1, c2 = st.columns(2)
        with c1:
            step = st.number_input("Step (Hour)", min_value=1, value=1)
            amount = st.number_input("Transaction Amount ($)", min_value=0.0, value=999999.0)
            oldbalanceOrg = st.number_input("Sender Initial Balance ($)", min_value=0.0, value=1000000.0)
        with c2:
            newbalanceOrig = st.number_input("Sender New Balance ($)", min_value=0.0, value=1.0)
            oldbalanceDest = st.number_input("Receiver Initial Balance ($)", min_value=0.0, value=0.0)
            newbalanceDest = st.number_input("Receiver New Balance ($)", min_value=0.0, value=999999.0)

        if st.button("Send API Request"):
            payload = {
                "step": int(step),
                "amount": float(amount),
                "oldbalanceOrg": float(oldbalanceOrg),
                "newbalanceOrig": float(newbalanceOrig),
                "oldbalanceDest": float(oldbalanceDest),
                "newbalanceDest": float(newbalanceDest)
            }
            
            api_url = "http://localhost:8000/predict_fraud"
            
            try:
                response = requests.post(api_url, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    is_fraud = result["is_fraud"]
                    prob = result["fraud_probability"] * 100
                    risk = result["risk_level"]

                   # NEW USER-FRIENDLY UI
                    st.divider()
                    st.subheader("📋 Transaction Risk Analysis Summary")

                    m1, m2, m3 = st.columns(3)

                    with m1:
                        st.metric(label="Decision", value="🚨 FLAG FRAUD" if is_fraud else "✅ APPROVED")

                    with m2:
                        st.metric(label="Risk Rating", value=f"{risk}")

                    with m3:
                        st.metric(label="Calculated Risk Probability", value=f"{prob:.1f}%")

                    # Visual Risk Progress Bar
                    st.write("**Risk Probability Meter:**")
                    st.progress(float(result["fraud_probability"]))

                    if is_fraud:
                        st.error("⚠️ **Action Required:** This transaction exhibits abnormal balance movement patterns and has been held for manual compliance review.")
                    else:
                        st.success("🎉 **Transaction Clear:** No suspicious patterns detected. Funds can be processed safely.")
            except Exception as api_err:
                st.error(f"Could not connect to FastAPI server at `{api_url}`: {api_err}")
