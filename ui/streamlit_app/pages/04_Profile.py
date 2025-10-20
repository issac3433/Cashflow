import streamlit as st
from utils.api import api_get, api_post
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")
if not st.session_state.get("is_authed"):
    st.switch_page("Login.py")

st.title("👤 User Profile")

# Debug section (collapsible)
with st.expander("🔧 Debug Info", expanded=False):
    st.write("**Session State:**")
    st.write(f"- is_authed: {st.session_state.get('is_authed', False)}")
    st.write(f"- jwt_token: {'Present' if st.session_state.get('jwt_token') else 'Missing'}")
    st.write(f"- supabase_user: {'Present' if st.session_state.get('supabase_user') else 'Missing'}")
    
    if st.session_state.get('jwt_token'):
        # Show first 50 chars of token for debugging
        token_preview = st.session_state['jwt_token'][:50] + "..."
        st.write(f"- Token preview: {token_preview}")
    
    if st.button("🔄 Refresh Authentication"):
        from utils.supabase_auth import check_supabase_auth
        check_supabase_auth()
        st.rerun()

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
        
        # Add year and month columns for filtering
        df_dividends['year'] = df_dividends['pay_date'].dt.year
        df_dividends['month'] = df_dividends['pay_date'].dt.month
        df_dividends['month_name'] = df_dividends['pay_date'].dt.strftime('%B')
        
        # Ensure we have valid data
        if df_dividends.empty:
            st.info("No dividend payments processed yet. Sync dividend data and process payments to see history.")
            st.stop()
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_dividends = df_dividends['total_amount'].sum()
            st.metric("💰 Total Received", f"${total_dividends:,.2f}")
        
        with col2:
            avg_per_payment = df_dividends['total_amount'].mean()
            st.metric("📊 Avg Payment", f"${avg_per_payment:,.2f}")
        
        with col3:
            unique_symbols = df_dividends['symbol'].nunique()
            st.metric("📈 Paying Stocks", f"{unique_symbols}")
        
        with col4:
            total_payments = len(df_dividends)
            st.metric("📅 Total Payments", f"{total_payments}")
        
        st.divider()
        
        # Filters
        st.write("**🔍 Filter Options**")
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            # Year filter
            available_years = sorted(df_dividends['year'].unique(), reverse=True)
            if available_years:
                selected_years = st.multiselect(
                    "Select Years",
                    options=available_years,
                    default=available_years[:3] if len(available_years) >= 3 else available_years,
                    key="year_filter"
                )
            else:
                selected_years = []
        
        with col_filter2:
            # Symbol filter
            available_symbols = sorted(df_dividends['symbol'].unique())
            if available_symbols:
                selected_symbols = st.multiselect(
                    "Select Stocks",
                    options=available_symbols,
                    default=available_symbols,
                    key="symbol_filter"
                )
            else:
                selected_symbols = []
        
        with col_filter3:
            # Amount range filter
            if not df_dividends.empty:
                min_amount = df_dividends['total_amount'].min()
                max_amount = df_dividends['total_amount'].max()
                amount_range = st.slider(
                    "Amount Range ($)",
                    min_value=float(min_amount),
                    max_value=float(max_amount),
                    value=(float(min_amount), float(max_amount)),
                    step=0.01,
                    key="amount_filter"
                )
            else:
                amount_range = (0.0, 0.0)
        
        # Apply filters (only if we have data and selections)
        if not df_dividends.empty and (selected_years or selected_symbols):
            filtered_df = df_dividends[
                (df_dividends['year'].isin(selected_years) if selected_years else True) &
                (df_dividends['symbol'].isin(selected_symbols) if selected_symbols else True) &
                (df_dividends['total_amount'] >= amount_range[0]) &
                (df_dividends['total_amount'] <= amount_range[1])
            ].copy()
        else:
            filtered_df = df_dividends.copy()
        
        if not filtered_df.empty:
            # Charts section
            chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📊 Timeline", "🥧 By Stock", "📈 Trends"])
            
            with chart_tab1:
                # Timeline chart
                try:
                    # Ensure dates are properly formatted
                    timeline_df = filtered_df.copy()
                    timeline_df['pay_date_str'] = timeline_df['pay_date'].dt.strftime('%Y-%m-%d')
                    
                    fig_timeline = px.bar(
                        timeline_df,
                        x='pay_date',
                        y='total_amount',
                        color='symbol',
                        title="Dividend Payments Timeline",
                        labels={'pay_date': 'Payment Date', 'total_amount': 'Amount ($)'},
                        hover_data=['ex_date', 'shares_owned', 'amount_per_share']
                    )
                    fig_timeline.update_layout(
                        xaxis_title="Payment Date",
                        yaxis_title="Amount ($)",
                        hovermode='x unified',
                        xaxis=dict(type='date')
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating timeline chart: {e}")
                    st.write("Raw data preview:")
                    st.dataframe(filtered_df.head())
            
            with chart_tab2:
                # Pie chart by stock
                stock_totals = filtered_df.groupby('symbol')['total_amount'].sum().reset_index()
                fig_pie = px.pie(
                    stock_totals,
                    values='total_amount',
                    names='symbol',
                    title="Dividend Income by Stock",
                    hover_data=['total_amount']
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with chart_tab3:
                # Monthly trends
                try:
                    monthly_totals = filtered_df.groupby(['year', 'month'])['total_amount'].sum().reset_index()
                    monthly_totals['year_month'] = monthly_totals['year'].astype(str) + '-' + monthly_totals['month'].astype(str).str.zfill(2)
                    monthly_totals = monthly_totals.sort_values(['year', 'month'])
                    
                    fig_trends = px.line(
                        monthly_totals,
                        x='year_month',
                        y='total_amount',
                        title="Monthly Dividend Income Trends",
                        labels={'year_month': 'Month', 'total_amount': 'Amount ($)'},
                        markers=True
                    )
                    fig_trends.update_layout(
                        xaxis_title="Month",
                        yaxis_title="Amount ($)",
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig_trends, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating trends chart: {e}")
                    st.write("Monthly data preview:")
                    st.dataframe(monthly_totals.head() if 'monthly_totals' in locals() else "No data")
            
            st.divider()
            
            # Enhanced data table
            st.write("**📋 Detailed Dividend History**")
            
            # Format the dataframe for better display
            display_df = filtered_df.copy()
            display_df['ex_date'] = display_df['ex_date'].dt.strftime('%Y-%m-%d')
            display_df['pay_date'] = display_df['pay_date'].dt.strftime('%Y-%m-%d')
            display_df['total_amount'] = display_df['total_amount'].round(2)
            display_df['amount_per_share'] = display_df['amount_per_share'].round(4)
            
            # Rename columns for better display
            display_df = display_df.rename(columns={
                'symbol': 'Stock',
                'ex_date': 'Ex-Date',
                'pay_date': 'Pay-Date',
                'shares_owned': 'Shares',
                'amount_per_share': 'Div/Share',
                'total_amount': 'Amount ($)'
            })
            
            # Sort by pay date (most recent first)
            display_df = display_df.sort_values('Pay-Date', ascending=False)
            
            # Display with better formatting
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Export option
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"dividend_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        else:
            st.warning("No dividend payments match the selected filters.")
            
    else:
        st.info("No dividend payments processed yet. Sync dividend data and process payments to see history.")
        
except Exception as e:
    error_msg = str(e)
    if "401" in error_msg or "Unauthorized" in error_msg:
        st.error("🔐 Authentication Error: Please sign out and sign in again to refresh your session.")
        st.info("💡 This usually happens when your session token has expired.")
    elif "Could not connect" in error_msg:
        st.error("🌐 Connection Error: Cannot connect to the backend server.")
        st.info("💡 Make sure the backend is running on http://localhost:8000")
    else:
        st.error(f"❌ Failed to load dividend history: {error_msg}")

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
