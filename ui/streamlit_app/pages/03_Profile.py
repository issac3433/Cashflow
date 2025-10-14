import streamlit as st
from utils.api import api_get, api_post
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")
if not st.session_state.get("is_authed"):
    st.switch_page("Login.py")

st.title("👤 User Profile")

# Get user profile data
try:
    profile_data = api_get("/profile")
except Exception as e:
    st.error(f"Failed to load profile: {e}")
    st.stop()

# Display profile summary
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💰 Cash Balance", 
        f"${profile_data['cash_balance']:,.2f}",
        delta=None
    )

with col2:
    st.metric(
        "📈 Portfolio Value", 
        f"${profile_data['total_portfolio_value']:,.2f}",
        delta=None
    )

with col3:
    st.metric(
        "💵 Total Dividends", 
        f"${profile_data['total_dividends_received']:,.2f}",
        delta=None
    )

with col4:
    st.metric(
        "🏦 Net Worth", 
        f"${profile_data['total_net_worth']:,.2f}",
        delta=None
    )

st.divider()

# Cash Management Section
st.subheader("💸 Cash Management")

col_a, col_b = st.columns(2)

with col_a:
    st.write("**Add Cash**")
    add_amount = st.number_input("Amount to add", min_value=0.01, value=100.0, step=0.01, key="add_cash")
    if st.button("Add Cash", key="add_cash_btn"):
        try:
            result = api_post("/profile/cash/add", json={"amount": add_amount})
            st.success(result["message"])
            st.rerun()
        except Exception as e:
            st.error(f"Failed to add cash: {e}")

with col_b:
    st.write("**Withdraw Cash**")
    withdraw_amount = st.number_input("Amount to withdraw", min_value=0.01, value=50.0, step=0.01, key="withdraw_cash")
    if st.button("Withdraw Cash", key="withdraw_cash_btn"):
        try:
            result = api_post("/profile/cash/withdraw", json={"amount": withdraw_amount})
            st.success(result["message"])
            st.rerun()
        except Exception as e:
            st.error(f"Failed to withdraw cash: {e}")

st.divider()

# Dividend Processing Section
st.subheader("📊 Dividend Processing")

col_c, col_d = st.columns(2)

with col_c:
    st.write("**Process Dividend Payments**")
    st.caption("Convert dividend events to cash in your account")
    if st.button("Process Dividends", key="process_dividends"):
        try:
            with st.spinner("Processing dividend payments..."):
                result = api_post("/dividends/process")
            st.success(f"✅ {result['message']}")
            st.info(f"💰 Added ${result['total_added']:,.2f} to your cash balance")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to process dividends: {e}")

with col_d:
    st.write("**Upcoming Dividends**")
    upcoming = profile_data.get('upcoming_dividends', 0)
    st.metric("Expected Income", f"${upcoming:,.2f}")

st.divider()

# Portfolio Summary
st.subheader("📁 Portfolio Summary")

if profile_data['portfolios']:
    df_portfolios = pd.DataFrame(profile_data['portfolios'])
    
    # Create a pie chart of portfolio values
    fig = px.pie(
        df_portfolios, 
        values='value', 
        names='name',
        title="Portfolio Value Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Display portfolio table
    st.dataframe(df_portfolios, use_container_width=True)
else:
    st.info("No portfolios found. Create a portfolio to start tracking your investments.")

st.divider()

# Dividend History
st.subheader("📈 Dividend History")

try:
    dividend_history = api_get("/dividends/history")
    if dividend_history['payments']:
        df_dividends = pd.DataFrame(dividend_history['payments'])
        
        # Convert dates for better display
        df_dividends['ex_date'] = pd.to_datetime(df_dividends['ex_date'])
        df_dividends['pay_date'] = pd.to_datetime(df_dividends['pay_date'])
        
        # Create dividend timeline chart
        fig = px.bar(
            df_dividends,
            x='ex_date',
            y='total_amount',
            color='symbol',
            title="Dividend Payments Over Time",
            labels={'ex_date': 'Ex-Dividend Date', 'total_amount': 'Total Amount ($)'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display dividend table
        st.dataframe(df_dividends, use_container_width=True)
    else:
        st.info("No dividend payments processed yet. Sync dividend data and process payments to see history.")
except Exception as e:
    st.error(f"Failed to load dividend history: {e}")

# Quick Actions
st.subheader("⚡ Quick Actions")

col_e, col_f, col_g = st.columns(3)

with col_e:
    if st.button("🔄 Refresh Profile", key="refresh_profile"):
        st.rerun()

with col_f:
    if st.button("📊 Sync Dividends", key="sync_dividends"):
        try:
            result = api_post("/sync/all")
            st.success(f"Synced {len(result['symbols'])} symbols")
        except Exception as e:
            st.error(f"Failed to sync dividends: {e}")

with col_g:
    if st.button("🏠 Go to Portfolio", key="go_portfolio"):
        st.switch_page("pages/01_Portfolio.py")
