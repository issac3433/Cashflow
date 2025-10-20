# ui/streamlit_app/pages/05_Risk_Analysis.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from utils.api import api_get, api_post

st.set_page_config(
    page_title="Risk Analysis",
    page_icon="⚠️",
    layout="wide"
)

# Authentication check
if not st.session_state.get("is_authed") or not st.session_state.get("jwt_token"):
    st.error("Please log in to view risk analysis.")
    st.link_button("Go to Login", "http://localhost:8501")
    st.stop()

st.title("⚠️ Portfolio Risk Analysis")
st.caption("Comprehensive risk assessment and management insights")

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

if not portfolios:
    st.warning("No portfolios found. Create a portfolio first.")
    st.stop()

# Portfolio selection
portfolio_options = {f"{p['name']} (ID: {p['id']})": p['id'] for p in portfolios}
selected_portfolio = st.selectbox(
    "Select Portfolio",
    options=list(portfolio_options.keys()),
    index=0,
    help="Choose which portfolio to analyze"
)
portfolio_id = portfolio_options[selected_portfolio]

# Analysis controls
col1, col2, col3 = st.columns(3)

with col1:
    analysis_type = st.selectbox(
        "Analysis Type",
        ["Comprehensive", "Quick Overview"],
        help="Choose the depth of risk analysis"
    )

with col2:
    if st.button("🔍 Run Risk Analysis", type="primary"):
        st.session_state.run_analysis = True

with col3:
    if st.button("📊 Export Report"):
        st.session_state.export_report = True

# Run risk analysis with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def run_risk_analysis_cached(portfolio_id, analysis_type):
    """Cached risk analysis to avoid repeated API calls."""
    try:
        if analysis_type == "Comprehensive":
            return api_get(f"/risk/analysis/{portfolio_id}")
        else:
            return api_get(f"/risk/metrics/{portfolio_id}")
    except Exception as e:
        st.error(f"Risk analysis failed: {e}")
        return None

if st.session_state.get("run_analysis", False):
    with st.spinner("Analyzing portfolio risk... (This may take a moment)"):
        risk_data = run_risk_analysis_cached(portfolio_id, analysis_type)
        if risk_data:
            st.session_state.risk_data = risk_data
    st.session_state.run_analysis = False

# Display results
if st.session_state.get("risk_data"):
    risk_data = st.session_state.risk_data
    
    # Risk Score Overview
    st.subheader("🎯 Risk Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_score = risk_data.get("risk_score", 0)
        risk_level = risk_data.get("overall_risk_level", "Unknown")
        
        # Color coding for risk score
        if risk_score >= 70:
            color = "green"
        elif risk_score >= 50:
            color = "orange"
        else:
            color = "red"
        
        st.metric(
            "Risk Score", 
            f"{risk_score:.1f}/100",
            help="Lower scores indicate higher risk"
        )
    
    with col2:
        st.metric("Risk Level", risk_level)
    
    with col3:
        volatility = risk_data.get("volatility", 0)
        st.metric("Volatility", f"{volatility:.1%}")
    
    with col4:
        sharpe_ratio = risk_data.get("sharpe_ratio", 0)
        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
    
    # Additional earnings risk metrics
    if "avg_earnings_risk" in risk_data:
        col5, col6 = st.columns(2)
        
        with col5:
            avg_earnings_risk = risk_data.get("avg_earnings_risk", 0)
            st.metric("Avg Earnings Risk", f"{avg_earnings_risk:.1f}")
        
        with col6:
            earnings_data_available = sum(1 for risk in risk_data.get("earnings_risks", {}).values() 
                                        if risk.get("earnings_data_available", False))
            total_holdings = len(risk_data.get("earnings_risks", {}))
            st.metric("Earnings Data Coverage", f"{earnings_data_available}/{total_holdings}")
    
    # Risk Score Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = risk_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Overall Risk Score"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 30], 'color': "lightgray"},
                {'range': [30, 70], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 30
            }
        }
    ))
    
    fig_gauge.update_layout(height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    st.divider()
    
    # Detailed Risk Metrics
    st.subheader("📊 Risk Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Market Risk**")
        
        metrics_data = {
            "Metric": ["Volatility", "Beta", "Sharpe Ratio", "Max Drawdown", "VaR (95%)", "VaR (99%)"],
            "Value": [
                f"{risk_data.get('volatility', 0):.1%}",
                f"{risk_data.get('beta', 1):.2f}",
                f"{risk_data.get('sharpe_ratio', 0):.2f}",
                f"{risk_data.get('max_drawdown', 0):.1%}",
                f"${risk_data.get('var_95', 0):,.0f}",
                f"${risk_data.get('var_99', 0):,.0f}"
            ],
            "Interpretation": [
                "Portfolio price volatility",
                "Market correlation (1.0 = market)",
                "Risk-adjusted return",
                "Worst loss period",
                "95% confidence loss limit",
                "99% confidence loss limit"
            ]
        }
        
        df_metrics = pd.DataFrame(metrics_data)
        st.dataframe(df_metrics, use_container_width=True)
    
    with col2:
        st.write("**Concentration Risk**")
        
        concentration = risk_data.get("concentration", {})
        
        concentration_data = {
            "Metric": ["Max Weight", "Top 5 Weight", "Herfindahl Index", "Holdings Count"],
            "Value": [
                f"{concentration.get('max_weight', 0):.1%}",
                f"{concentration.get('top_5_weight', 0):.1%}",
                f"{concentration.get('herfindahl_index', 0):.3f}",
                f"{concentration.get('num_holdings', 0)}"
            ],
            "Risk Level": [
                "High" if concentration.get('max_weight', 0) > 0.4 else "Low",
                "High" if concentration.get('top_5_weight', 0) > 0.8 else "Low",
                "High" if concentration.get('herfindahl_index', 0) > 0.25 else "Low",
                "Low" if concentration.get('num_holdings', 0) > 10 else "High"
            ]
        }
        
        df_concentration = pd.DataFrame(concentration_data)
        st.dataframe(df_concentration, use_container_width=True)
    
    # Holdings Analysis
    if "holdings" in risk_data:
        st.subheader("📈 Holdings Breakdown")
        
        holdings_df = pd.DataFrame(risk_data["holdings"])
        
        # Portfolio allocation pie chart
        fig_pie = px.pie(
            holdings_df, 
            values='value', 
            names='symbol',
            title="Portfolio Allocation",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Holdings table
            holdings_display = holdings_df[['symbol', 'shares', 'price', 'value', 'weight']].copy()
            holdings_display['weight'] = holdings_display['weight'].apply(lambda x: f"{x:.1%}")
            holdings_display['price'] = holdings_display['price'].apply(lambda x: f"${x:.2f}")
            holdings_display['value'] = holdings_display['value'].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(holdings_display, use_container_width=True)
    
    # Dividend Risk Analysis
    if "dividend_risks" in risk_data:
        st.subheader("💰 Dividend Risk Analysis")
        
        dividend_risks = risk_data["dividend_risks"]
        
        if dividend_risks:
            dividend_data = []
            for symbol, risk_info in dividend_risks.items():
                dividend_data.append({
                    "Symbol": symbol,
                    "Risk Level": risk_info["risk_level"],
                    "Sustainability Score": f"{risk_info['sustainability_score']:.1f}/100",
                    "Volatility": f"{risk_info['volatility']:.3f}",
                    "Growth Trend": f"{risk_info['growth_trend']:.1%}"
                })
            
            df_dividend = pd.DataFrame(dividend_data)
            
            # Color code risk levels
            def color_risk_level(val):
                if val == "Low":
                    return "background-color: lightgreen"
                elif val == "Medium":
                    return "background-color: lightyellow"
                elif val == "High":
                    return "background-color: lightcoral"
                else:
                    return "background-color: pink"
            
            styled_df = df_dividend.style.applymap(color_risk_level, subset=['Risk Level'])
            st.dataframe(styled_df, use_container_width=True)
    
    # Earnings Risk Analysis
    if "earnings_risks" in risk_data:
        st.subheader("📈 Earnings Risk Analysis")
        
        earnings_risks = risk_data["earnings_risks"]
        
        if earnings_risks:
            # Create earnings risk summary
            earnings_data = []
            for symbol, risk_info in earnings_risks.items():
                surprise = risk_info.get("surprise_analysis", {})
                revenue = risk_info.get("revenue_analysis", {})
                profitability = risk_info.get("profitability_analysis", {})
                guidance = risk_info.get("guidance_analysis", {})
                valuation = risk_info.get("valuation_analysis", {})
                
                earnings_data.append({
                    "Symbol": symbol,
                    "Overall Risk": risk_info["overall_risk_level"],
                    "Earnings Score": risk_info["earnings_risk_score"],
                    "Beat Rate": f"{surprise.get('beat_rate', 0):.1%}" if surprise else "N/A",
                    "Revenue Growth": f"{revenue.get('avg_growth', 0):.1%}" if revenue else "N/A",
                    "Margin Trend": f"{profitability.get('margin_trend', 0):.1%}" if profitability else "N/A",
                    "Guidance Accuracy": f"{guidance.get('guidance_accuracy', 0):.1%}" if guidance else "N/A",
                    "PEG Ratio": f"{valuation.get('peg_ratio', 0):.1f}" if valuation else "N/A"
                })
            
            df_earnings = pd.DataFrame(earnings_data)
            
            # Color code risk levels
            def color_earnings_risk(val):
                if val == "Low":
                    return "background-color: lightgreen"
                elif val == "Medium":
                    return "background-color: lightyellow"
                else:
                    return "background-color: lightcoral"
            
            styled_earnings_df = df_earnings.style.applymap(color_earnings_risk, subset=['Overall Risk'])
            st.dataframe(styled_earnings_df, use_container_width=True)
            
            # Detailed earnings analysis for each stock
            st.write("**Detailed Earnings Analysis**")
            
            for symbol, risk_info in earnings_risks.items():
                with st.expander(f"📊 {symbol} - {risk_info['overall_risk_level']} Risk"):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Earnings Surprise Analysis**")
                        surprise = risk_info.get("surprise_analysis", {})
                        if surprise and "error" not in surprise:
                            st.write(f"Beat Rate: {surprise.get('beat_rate', 0):.1%}")
                            st.write(f"Avg Surprise: {surprise.get('avg_surprise', 0):.1%}")
                            st.write(f"Risk Level: {surprise.get('risk_level', 'Unknown')}")
                        else:
                            st.write("No surprise data available")
                        
                        st.write("**Revenue Analysis**")
                        revenue = risk_info.get("revenue_analysis", {})
                        if revenue and "error" not in revenue:
                            st.write(f"Avg Growth: {revenue.get('avg_growth', 0):.1%}")
                            st.write(f"Growth Volatility: {revenue.get('growth_volatility', 0):.1%}")
                            st.write(f"Risk Level: {revenue.get('risk_level', 'Unknown')}")
                        else:
                            st.write("No revenue data available")
                    
                    with col2:
                        st.write("**Profitability Analysis**")
                        profitability = risk_info.get("profitability_analysis", {})
                        if profitability and "error" not in profitability:
                            st.write(f"Avg Margin: {profitability.get('avg_margin', 0):.1%}")
                            st.write(f"Margin Trend: {profitability.get('margin_trend', 0):.1%}")
                            st.write(f"Risk Level: {profitability.get('risk_level', 'Unknown')}")
                        else:
                            st.write("No profitability data available")
                        
                        st.write("**Valuation Analysis**")
                        valuation = risk_info.get("valuation_analysis", {})
                        if valuation:
                            st.write(f"Forward P/E: {valuation.get('forward_pe', 0):.1f}")
                            st.write(f"PEG Ratio: {valuation.get('peg_ratio', 0):.1f}")
                            st.write(f"Risk Level: {valuation.get('risk_level', 'Unknown')}")
    
    # Risk Recommendations
    if "recommendations" in risk_data:
        st.subheader("💡 Risk Management Recommendations")
        
        recommendations = risk_data["recommendations"]
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
        else:
            st.info("No specific recommendations at this time. Portfolio risk appears manageable.")
    
    # Risk Visualization
    st.subheader("📊 Risk Visualization")
    
    # Create risk radar chart
    if analysis_type == "Comprehensive":
        categories = ['Volatility', 'Concentration', 'Dividend Risk', 'Market Risk', 'Liquidity Risk']
        
        # Normalize values for radar chart (0-1 scale)
        values = [
            min(risk_data.get('volatility', 0) * 20, 1),  # Scale volatility
            min(concentration.get('max_weight', 0) * 2, 1),  # Scale concentration
            1 - (risk_data.get('risk_score', 50) / 100),  # Invert risk score
            min(risk_data.get('beta', 1) / 2, 1),  # Scale beta
            0.5  # Placeholder for liquidity risk
        ]
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Risk Profile',
            line_color='red'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Risk Profile Radar Chart"
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    
    # Export functionality
    if st.session_state.get("export_report", False):
        st.subheader("📄 Export Risk Report")
        
        # Create comprehensive report
        report_data = {
            "Portfolio": selected_portfolio,
            "Analysis Date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "Risk Score": risk_score,
            "Risk Level": risk_level,
            "Key Metrics": risk_data,
            "Recommendations": recommendations if "recommendations" in risk_data else []
        }
        
        # Convert to JSON for download
        import json
        report_json = json.dumps(report_data, indent=2, default=str)
        
        st.download_button(
            label="📥 Download Risk Report (JSON)",
            data=report_json,
            file_name=f"risk_report_{portfolio_id}_{pd.Timestamp.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
        
        st.session_state.export_report = False

else:
    st.info("👆 Click 'Run Risk Analysis' to analyze your portfolio risk.")
    
    # Show sample risk metrics for demonstration
    st.subheader("📊 Sample Risk Metrics")
    
    sample_data = {
        "Metric": ["Risk Score", "Volatility", "Beta", "Sharpe Ratio", "Max Drawdown"],
        "Your Portfolio": ["--", "--", "--", "--", "--"],
        "Benchmark (S&P 500)": ["50.0", "15.0%", "1.00", "0.50", "20.0%"],
        "Conservative": ["75.0", "8.0%", "0.60", "0.80", "10.0%"],
        "Aggressive": ["25.0", "25.0%", "1.40", "0.30", "35.0%"]
    }
    
    df_sample = pd.DataFrame(sample_data)
    st.dataframe(df_sample, use_container_width=True)
    
    st.caption("Run the analysis to see your actual portfolio metrics compared to benchmarks.")
