import streamlit as st
from utils.api import api_post, api_get
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(page_title="Forecast", page_icon="📈", layout="wide")
if not st.session_state.get("is_authed"):
    st.switch_page("Login.py")

st.title("📈 Advanced Cashflow Forecast")

# Load portfolios for dropdown
@st.cache_data
def load_portfolios():
    try:
        portfolios = api_get("/portfolios")
        return portfolios
    except Exception as e:
        st.error(f"Failed to load portfolios: {e}")
        return []

portfolios = load_portfolios()

# Input controls
col1, col2, col3 = st.columns(3)

with col1:
    if portfolios:
        portfolio_options = {f"{p['name']} (ID: {p['id']})": p['id'] for p in portfolios}
        selected_portfolio = st.selectbox(
            "Select Portfolio",
            options=list(portfolio_options.keys()),
            index=0 if portfolios else None,
            help="Choose which portfolio to forecast"
        )
        pid = portfolio_options[selected_portfolio]
    else:
        st.warning("No portfolios found. Create a portfolio first.")
        pid = None
    
    months = st.slider("Forecast Period (months)", 6, 36, 12)

with col2:
    growth_scenario = st.selectbox(
        "Growth Scenario",
        ["conservative", "moderate", "optimistic", "pessimistic"],
        index=1,
        help="Conservative: 0% growth, Moderate: 2% growth, Optimistic: 5% growth, Pessimistic: -5% growth"
    )
    reinvest = st.checkbox("Reinvest Dividends (DRIP)", True)

with col3:
    rec_dep = st.number_input("Recurring Deposit ($/month)", min_value=0.0, value=0.0, step=50.0)
    show_scenarios = st.checkbox("Show All Scenarios", True)

if st.button("🚀 Run Enhanced Forecast", type="primary", disabled=pid is None):
    if pid is None:
        st.error("Please select a portfolio first.")
    else:
        with st.spinner("Analyzing dividend patterns and calculating projections..."):
            res = api_post("/forecasts/monthly", json={
                "portfolio_id": int(pid),
                "months": int(months),
                "assume_reinvest": bool(reinvest),
                "recurring_deposit": float(rec_dep),
                "growth_scenario": growth_scenario
            })
        
        series = res.get("series", [])
        patterns = res.get("patterns", {})
        scenarios = res.get("scenarios", {})
        assumptions = res.get("assumptions", {})
        
        if series:
            # Create enhanced visualization
            st.subheader("📊 Monthly Dividend Income Forecast")
            
            # Prepare data
            df = pd.DataFrame(series)
            df['month'] = pd.to_datetime(df['month'])
            
            # Create subplot with secondary y-axis
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Monthly Dividend Income", "Cumulative Income"),
                vertical_spacing=0.1,
                row_heights=[0.6, 0.4]
            )
            
            # Monthly income bars
            colors = ['#2E8B57' if has_div else '#FFB6C1' for has_div in df['has_dividend']]
            fig.add_trace(
                go.Bar(
                    x=df['month'],
                    y=df['income'],
                    name="Monthly Income",
                    marker_color=colors,
                    hovertemplate="<b>%{x|%B %Y}</b><br>Income: $%{y:,.2f}<br>%{customdata}<extra></extra>",
                    customdata=[f"{'Dividend Month' if has_div else 'No Dividends'}" for has_div in df['has_dividend']]
                ),
                row=1, col=1
            )
            
            # Cumulative line
            fig.add_trace(
                go.Scatter(
                    x=df['month'],
                    y=df['cumulative'],
                    mode='lines+markers',
                    name="Cumulative Income",
                    line=dict(color='#4169E1', width=3),
                    marker=dict(size=6),
                    hovertemplate="<b>%{x|%B %Y}</b><br>Cumulative: $%{y:,.2f}<extra></extra>"
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                height=600,
                showlegend=True,
                title_text=f"📈 {growth_scenario.title()} Scenario Forecast ({months} months)"
            )
            
            fig.update_xaxes(title_text="Month", row=2, col=1)
            fig.update_yaxes(title_text="Monthly Income ($)", row=1, col=1)
            fig.update_yaxes(title_text="Cumulative Income ($)", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Projected Income", f"${res.get('total', 0):,.2f}")
            
            with col2:
                avg_monthly = res.get('total', 0) / months
                st.metric("Average Monthly", f"${avg_monthly:,.2f}")
            
            with col3:
                dividend_months = sum(1 for s in series if s['has_dividend'])
                st.metric("Dividend Months", f"{dividend_months}/{months}")
            
            with col4:
                if reinvest:
                    st.metric("Strategy", "DRIP (Reinvest)")
                else:
                    st.metric("Strategy", "Cash Dividends")
            
            # Dividend patterns analysis
            if patterns:
                st.subheader("🔍 Dividend Pattern Analysis")
                
                pattern_cols = st.columns(len(patterns))
                for i, (symbol, pattern) in enumerate(patterns.items()):
                    with pattern_cols[i]:
                        st.write(f"**{symbol}**")
                        st.write(f"Frequency: {pattern['frequency']}x/year")
                        st.write(f"Months: {pattern['payment_months']}")
                        st.write(f"Growth: {pattern['growth_rate']}%/year")
            
            # Scenario comparison
            if show_scenarios and scenarios:
                st.subheader("📊 Scenario Comparison")
                
                scenario_data = []
                for scenario, total in scenarios.items():
                    scenario_data.append({
                        "Scenario": scenario.title(),
                        "Total Income": f"${total:,.2f}",
                        "Difference": f"${total - res.get('total', 0):,.2f}"
                    })
                
                # Add current scenario
                scenario_data.append({
                    "Scenario": f"{growth_scenario.title()} (Current)",
                    "Total Income": f"${res.get('total', 0):,.2f}",
                    "Difference": "$0.00"
                })
                
                st.dataframe(scenario_data, use_container_width=True)
            
            # Assumptions
            st.subheader("⚙️ Forecast Assumptions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Reinvestment:** {'Yes' if assumptions.get('reinvest') else 'No'}")
                st.write(f"**Growth Scenario:** {assumptions.get('growth_scenario', 'moderate').title()}")
            
            with col2:
                st.write(f"**Recurring Deposits:** ${assumptions.get('recurring_deposit', 0):,.2f}/month")
                st.write(f"**Forecast Period:** {months} months")
            
            with col3:
                st.write(f"**Portfolio:** {selected_portfolio}")
                st.write(f"**Based on:** Historical dividend patterns")
        
        else:
            st.info("No dividend data found. Add holdings and sync dividend data on the Portfolio page.")