import streamlit as st
from utils.api import api_post
import plotly.express as px

st.set_page_config(page_title="Forecast", page_icon="📈", layout="wide")
if not st.session_state.get("is_authed"):
    st.switch_page("Login.py")

st.title("📈 Cashflow Forecast (12–24 months)")

pid = st.number_input("Portfolio ID", min_value=1, step=1, value=1)
months = st.slider("Months", 1, 24, 12)
reinvest = st.checkbox("Reinvest Dividends", True)
rec_dep = st.number_input("Recurring Deposit ($/month)", min_value=0.0, value=0.0, step=50.0)

if st.button("Run Forecast"):
    res = api_post("/forecasts/monthly", json={
        "portfolio_id": int(pid),
        "months": int(months),
        "assume_reinvest": bool(reinvest),
        "recurring_deposit": float(rec_dep)
    })
    series = res.get("series", [])
    if series:
        fig = px.bar(series, x="month", y="income", title="Projected Monthly Income")
        st.plotly_chart(fig, use_container_width=True)
        total = res.get("total", 0.0)
        st.success(f"Total projected income: ${total:,.2f}")
    else:
        st.info("No data yet — add holdings and refresh dividends on the Portfolio page.")
