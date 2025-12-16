import streamlit as st
from utils.api import api_get, api_post, api_delete
from utils.mobile_css import inject_mobile_css
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Portfolio", page_icon="📁", layout="wide")
inject_mobile_css()

# Force authentication check
if not st.session_state.get("is_authed") or not st.session_state.get("jwt_token"):
    st.error("❌ You must be authenticated to access this page.")
    st.write("Please sign in with your Supabase credentials.")
    if st.button("Go to Login"):
        st.switch_page("Login.py")
    st.stop()

st.title("📁 Portfolio Management")

# Debug authentication status
with st.expander("🔍 Debug Authentication Status", expanded=False):
    st.write(f"**is_authed**: {st.session_state.get('is_authed', False)}")
    st.write(f"**jwt_token**: {'Present' if st.session_state.get('jwt_token') else 'Missing'}")
    st.write(f"**supabase_user**: {st.session_state.get('supabase_user', 'None')}")
    if st.button("🔄 Clear Session & Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ----------------- Portfolio Selector -----------------
@st.cache_data(ttl=120)  # Cache for 2 minutes
def load_portfolios():
    """Load user portfolios with caching."""
    try:
        return api_get("/portfolios")
    except Exception as e:
        st.error(f"Failed to load portfolios: {e}")
        return []

@st.cache_data(ttl=60)  # Cache for 1 minute
def load_user_profile():
    """Load user profile with caching."""
    try:
        return api_get("/profile")
    except Exception:
        return {"cash_balance": 0.0}

portfolios = load_portfolios()

if not portfolios:
    st.warning("No portfolios found. Create your first portfolio below!")
    with st.expander("Create Portfolio", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Portfolio Name", value="My Individual Portfolio")
        with col2:
            portfolio_type = st.selectbox(
                "Portfolio Type",
                ["individual", "retirement"],
                format_func=lambda x: "Individual" if x == "individual" else "Retirement",
                help="Individual: Regular investment account\nRetirement: 401k, IRA, etc."
            )
        
        if st.button("Create Portfolio"):
            try:
                result = api_post("/portfolios", json={
                    "name": name,
                    "portfolio_type": portfolio_type
                })
                st.success(f"Created {portfolio_type} portfolio: {result['name']}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create portfolio: {e}")
    st.stop()

# Portfolio selector
portfolio_options = {f"{p['name']} ({p.get('portfolio_type', 'individual').title()})": p for p in portfolios}
selected_name = st.selectbox(
    "Select Portfolio",
    options=list(portfolio_options.keys()),
    key="portfolio_selector"
)

selected_portfolio = portfolio_options[selected_name]

# Add portfolio creation option if user has less than 2 portfolios
if len(portfolios) < 2:
    st.info(f"💡 You can create up to 2 portfolios: 1 Individual + 1 Retirement. Currently have {len(portfolios)}.")
    with st.expander("Create Another Portfolio"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Portfolio Name", value="My Retirement Portfolio", key="new_portfolio_name")
        with col2:
            # Determine which type to offer
            existing_types = [p.get('portfolio_type', 'individual') for p in portfolios]
            if 'individual' not in existing_types:
                portfolio_type = 'individual'
                st.info("Creating Individual portfolio")
            elif 'retirement' not in existing_types:
                portfolio_type = 'retirement'
                st.info("Creating Retirement portfolio")
            else:
                st.warning("You already have both portfolio types!")
                portfolio_type = None
        
        if portfolio_type and st.button("Create Portfolio", key="create_new_portfolio"):
            try:
                # Validate input
                if not name or not name.strip():
                    st.error("Portfolio name cannot be empty")
                    st.stop()
                
                # Create portfolio payload
                payload = {
                    "name": name.strip(),
                    "portfolio_type": portfolio_type
                }
                
                st.write(f"Creating portfolio with payload: {payload}")
                
                # Debug authentication
                st.write(f"**Auth Debug:**")
                st.write(f"- JWT Token present: {'Yes' if st.session_state.get('jwt_token') else 'No'}")
                if st.session_state.get('jwt_token'):
                    token_preview = st.session_state['jwt_token'][:50] + "..."
                    st.write(f"- Token preview: {token_preview}")
                
                result = api_post("/portfolios", json=payload)
                st.success(f"Created {portfolio_type} portfolio: {result['name']}")
                
                # Clear cache to refresh portfolio list
                load_portfolios.clear()
                load_portfolio_details.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create portfolio: {e}")
                st.write("**Debug Info:**")
                st.write(f"- Name: '{name}'")
                st.write(f"- Type: '{portfolio_type}'")
                st.write(f"- Payload: {payload if 'payload' in locals() else 'Not created'}")

# ----------------- Portfolio Overview -----------------
portfolio_type_display = selected_portfolio.get('portfolio_type', 'individual').title()

@st.cache_data(ttl=60)  # Cache for 1 minute (increased from 30s)
def load_portfolio_details(portfolio_id):
    """Load detailed portfolio information with error handling."""
    try:
        with st.spinner("Loading portfolio..."):
        return api_get(f"/portfolios/{portfolio_id}")
    except Exception as e:
        error_msg = str(e)
        if "timed out" in error_msg.lower():
            st.warning("⚠️ Portfolio loading timed out. Showing cached data or using average prices.")
            # Try to get basic portfolio info without prices
            try:
                # Return basic structure - prices will use avg_price
                return {
                    "portfolio": {"id": portfolio_id, "name": "Loading...", "created_at": "Unknown"},
                    "holdings": [],
                    "total_value": 0.0,
                    "holdings_count": 0,
                    "error": "Price fetch timeout"
                }
            except:
                pass
        st.error(f"Failed to load portfolio details: {error_msg}")
        # Return a fallback structure
        return {
            "portfolio": {"id": portfolio_id, "name": "Unknown", "created_at": "Unknown"},
            "holdings": [],
            "total_value": 0.0,
            "holdings_count": 0
        }

portfolio_data = load_portfolio_details(selected_portfolio['id'])

# Portfolio title with delete button
col_title, col_delete = st.columns([4, 1])
with col_title:
    st.subheader(f"📊 {selected_portfolio['name']} ({portfolio_type_display}) Overview")
with col_delete:
    if st.button("🗑️ Delete", key="delete_portfolio", help="Delete this portfolio"):
        st.session_state["show_delete_confirm"] = True

# Delete confirmation dialog
if st.session_state.get("show_delete_confirm", False):
    st.warning("⚠️ **Are you sure you want to delete this portfolio?**")
    st.write(f"This will permanently delete **{selected_portfolio['name']}** and all its holdings.")
    
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("✅ Yes, Delete Portfolio", type="primary", key="confirm_delete"):
            try:
                # Delete all holdings first
                if portfolio_data and portfolio_data['holdings']:
                    for holding in portfolio_data['holdings']:
                        api_delete(f"/holdings/{holding['id']}")
                
                # Delete the portfolio
                api_delete(f"/portfolios/{selected_portfolio['id']}")
                st.success(f"✅ Portfolio '{selected_portfolio['name']}' deleted successfully!")
                st.session_state["show_delete_confirm"] = False
                
                # Clear the cached portfolio list to refresh the dropdown
                load_portfolios.clear()
                load_portfolio_details.clear()
                load_user_profile.clear()
                
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete portfolio: {e}")
    
    with col_cancel:
        if st.button("❌ Cancel", key="cancel_delete"):
            st.session_state["show_delete_confirm"] = False
            st.rerun()

# Get portfolio cash balance (from portfolio data)
if portfolio_data:
    cash_balance = portfolio_data['portfolio'].get('cash_balance', 0.0)
    
    # Responsive columns - stack on mobile
    col1, col2, col3, col4, col5 = st.columns([1.2, 1, 0.8, 1, 0.8])
    
    with col1:
        st.metric("💰 Cash Balance", f"${cash_balance:,.2f}")
    with col2:
        st.metric("Total Value", f"${portfolio_data['total_value']:,.2f}")
    with col3:
        st.metric("Holdings", portfolio_data['holdings_count'])
    with col4:
        avg_value = portfolio_data['total_value'] / max(portfolio_data['holdings_count'], 1)
        st.metric("Avg Position", f"${avg_value:,.2f}")
    with col5:
        st.metric("Created", portfolio_data['portfolio']['created_at'][:10])

# ----------------- Holdings Table -----------------
st.subheader("📈 Holdings")

if portfolio_data and portfolio_data['holdings']:
    holdings_df = pd.DataFrame(portfolio_data['holdings'])
    
    # Calculate additional columns
    holdings_df['gain_loss'] = (holdings_df['latest_price'] - holdings_df['avg_price']) * holdings_df['shares']
    holdings_df['gain_loss_pct'] = ((holdings_df['latest_price'] - holdings_df['avg_price']) / holdings_df['avg_price'] * 100).round(2)
    
    # Store original values for calculations
    original_avg_price = holdings_df['avg_price'].copy()
    original_latest_price = holdings_df['latest_price'].copy()
    original_shares = holdings_df['shares'].copy()
    
    # Format columns for display
    holdings_df['avg_price'] = holdings_df['avg_price'].apply(lambda x: f"${x:.2f}")
    holdings_df['latest_price'] = holdings_df['latest_price'].apply(lambda x: f"${x:.2f}")
    holdings_df['market_value'] = holdings_df['market_value'].apply(lambda x: f"${x:,.2f}")
    holdings_df['gain_loss'] = holdings_df['gain_loss'].apply(lambda x: f"${x:,.2f}")
    holdings_df['gain_loss_pct'] = holdings_df['gain_loss_pct'].apply(lambda x: f"{x:.1f}%")
    
    # Display table with sell buttons
    st.write("**Holdings Table:**")
    
    # Create columns for each holding with sell button
    for idx, row in holdings_df.iterrows():
        holding_id = row['id']
        symbol = row['symbol']
        shares_owned = float(original_shares.loc[idx])
        
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
        
        with col1:
            st.write(f"**{symbol}**")
        with col2:
            st.write(f"{shares_owned:.2f}")
        with col3:
            st.write(row['avg_price'])
        with col4:
            st.write(row['latest_price'])
        with col5:
            st.write(row['market_value'])
        with col6:
            st.write(row['gain_loss'])
        with col7:
            st.write(row['gain_loss_pct'])
        with col8:
            # Sell button - opens a form
            if st.button("💰 Sell", key=f"sell_btn_{holding_id}", help="Sell this holding"):
                st.session_state[f"sell_holding_{holding_id}"] = True
        
        # Show sell form if button was clicked
        if st.session_state.get(f"sell_holding_{holding_id}", False):
            with st.expander(f"💸 Sell {symbol}", expanded=True):
                st.write(f"**Current holdings:** {shares_owned:.2f} shares")
                current_price = float(original_latest_price.loc[idx])
                st.write(f"**Current price:** ${current_price:.2f}")
                
                col_sell1, col_sell2 = st.columns(2)
                
                with col_sell1:
                    shares_to_sell = st.number_input(
                        "Shares to sell",
                        min_value=0.01,
                        max_value=float(shares_owned),
                        value=float(shares_owned),
                        step=0.01,
                        key=f"sell_shares_{holding_id}"
                    )
                    estimated_proceeds = shares_to_sell * current_price
                    st.info(f"**Estimated proceeds:** ${estimated_proceeds:,.2f}")
                
                with col_sell2:
                    st.write("")  # Spacer
                    if st.button("✅ Confirm Sell", key=f"confirm_sell_{holding_id}", type="primary"):
                        try:
                            result = api_post(f"/holdings/{holding_id}/sell", json={"shares": shares_to_sell})
                            st.success(f"✅ {result['message']}")
                            st.info(f"💰 Added ${result['proceeds']:,.2f} to cash balance")
                            st.session_state[f"sell_holding_{holding_id}"] = False
                            # Clear only relevant caches
                            load_portfolio_details.clear()
                            load_user_profile.clear()
                    st.rerun()
                except Exception as e:
                            st.error(f"Failed to sell: {e}")
                    
                    if st.button("❌ Cancel", key=f"cancel_sell_{holding_id}"):
                        st.session_state[f"sell_holding_{holding_id}"] = False
                        st.rerun()
        
        st.divider()
    
    # Add a separator
    st.divider()
    
    # Portfolio allocation chart
    if len(holdings_df) > 1:
        st.subheader("📊 Portfolio Allocation")
        
        # Create chart data
        chart_data = holdings_df[['symbol', 'market_value']].copy()
        chart_data['market_value'] = chart_data['market_value'].str.replace('$', '').str.replace(',', '').astype(float)
        
        # Create pie chart
        fig = px.pie(
            chart_data, 
            values='market_value', 
            names='symbol',
            title="Portfolio Allocation by Value"
        )
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Value: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Also show a simple breakdown
        st.write("**Holdings Breakdown:**")
        for _, row in chart_data.iterrows():
            percentage = (row['market_value'] / chart_data['market_value'].sum()) * 100
            st.write(f"• {row['symbol']}: ${row['market_value']:,.2f} ({percentage:.1f}%)")
else:
    st.info("No holdings in this portfolio yet. Add some below!")

# ----------------- Add Holdings -----------------
st.subheader("➕ Add Holdings")

with st.expander("Add New Holding", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        # Unified stock search with suggestions
        st.write("**Search for a stock:**")
        
        # Initialize session state for search
        if "stock_search_query" not in st.session_state:
            st.session_state["stock_search_query"] = ""
        if "stock_search_results" not in st.session_state:
            st.session_state["stock_search_results"] = []
        if "selected_stock_symbol" not in st.session_state:
            st.session_state["selected_stock_symbol"] = None
        
        # Search input
        search_query = st.text_input(
            "Type to search",
            value=st.session_state["stock_search_query"],
            key="stock_search_input",
            placeholder="e.g., apple, tesla, microsoft",
            help="Type at least 2 characters and press Enter to search"
        )
        
        # Update search query in session state
        if search_query != st.session_state["stock_search_query"]:
            st.session_state["stock_search_query"] = search_query
            st.session_state["stock_search_results"] = []
            st.session_state["selected_stock_symbol"] = None
        
        # Search for stocks when query is long enough
        if search_query and len(search_query.strip()) >= 2:
            if not st.session_state["stock_search_results"]:
                try:
                    with st.spinner("Searching..."):
                        search_results = api_get(f"/symbols/suggest?q={search_query}&limit=10")
                        st.session_state["stock_search_results"] = search_results.get("results", [])
                        
                        # Show API call status
                        api_status = search_results.get("api_status", {})
                        if api_status:
                            calls_used = api_status.get("calls_used", 0)
                            calls_remaining = api_status.get("calls_remaining", 0)
                            max_calls = api_status.get("max_calls", 5)
                            
                            if calls_remaining <= 1:
                                st.warning(f"⚠️ API calls almost exhausted! {calls_used}/{max_calls} used. {calls_remaining} remaining.")
                            elif calls_remaining <= 2:
                                st.info(f"ℹ️ API calls: {calls_used}/{max_calls} used. {calls_remaining} remaining.")
                            
                            if api_status.get("is_rate_limited"):
                                time_until_reset = api_status.get("time_until_reset", 0)
                                st.error(f"🚫 Rate limit reached! Wait {time_until_reset:.0f} seconds before searching again.")
                except Exception as e:
                    st.error(f"Search error: {e}")
                    st.session_state["stock_search_results"] = []
            
            # Show search results as selectbox
            if st.session_state["stock_search_results"]:
                # Create display options
                options = ["Select a stock..."] + [
                    f"{result['symbol']} - {result['name']} (${result.get('price') or 0:.2f})"
                    for result in st.session_state["stock_search_results"]
                ]
                
                selected_option = st.selectbox(
                    "Choose from results:",
                    options=options,
                    key="stock_selection"
                )
                
                if selected_option and selected_option != "Select a stock...":
                    # Extract symbol from selection
                    symbol = selected_option.split(" - ")[0]
                    st.session_state["selected_stock_symbol"] = symbol
                    st.success(f"✅ Selected: {symbol}")
                else:
                    st.session_state["selected_stock_symbol"] = None
            else:
                st.info("No stocks found. Try a different search term.")
        else:
            st.session_state["selected_stock_symbol"] = None
        
        # Show selected stock
        if st.session_state["selected_stock_symbol"]:
            st.write(f"**Selected Stock:** {st.session_state['selected_stock_symbol']}")
        
        shares = st.number_input("Shares", min_value=0.01, value=1.0, step=0.1)
    
    with col2:
        avg_price = st.number_input("Average Price (leave blank for current price)", min_value=0.0, value=0.0, step=0.01)
        reinvest_dividends = st.checkbox("Reinvest Dividends", value=True)
    
    # Calculate estimated cost and validate cash
        selected_symbol = st.session_state.get("selected_stock_symbol")
    estimated_cost = 0.0
    has_sufficient_cash = True
    
    if selected_symbol and shares > 0:
        # Get price from search results or use avg_price
        estimated_price = avg_price if avg_price > 0 else None
        if not estimated_price and st.session_state.get("stock_search_results"):
            for result in st.session_state["stock_search_results"]:
                if result['symbol'] == selected_symbol:
                    estimated_price = result.get('price', 0)
                    break
        
        if estimated_price:
            estimated_cost = shares * estimated_price
            st.info(f"💰 **Estimated cost:** ${estimated_cost:,.2f}")
            if cash_balance < estimated_cost:
                has_sufficient_cash = False
                st.warning(f"⚠️ **Insufficient cash!** You need ${estimated_cost - cash_balance:,.2f} more.")
            else:
                remaining = cash_balance - estimated_cost
                st.success(f"✅ **Cash after purchase:** ${remaining:,.2f}")
    
    # Disable button if insufficient cash
    button_disabled = not has_sufficient_cash or not selected_symbol or shares <= 0
    
    if st.button("Add Holding", type="primary", disabled=button_disabled):
        if not selected_symbol:
            st.error("Please search and select a stock")
        elif shares <= 0:
            st.error("Please enter a valid number of shares")
        else:
            try:
                payload = {
                    "portfolio_id": selected_portfolio['id'],
                    "symbol": selected_symbol,
                    "shares": shares,
                    "reinvest_dividends": reinvest_dividends
                }
                # Only add avg_price if it's greater than 0
                if avg_price and avg_price > 0:
                    payload["avg_price"] = avg_price
                
                result = api_post("/holdings", json=payload)
                action = result.get('action', 'created')
                if action == 'merged':
                    st.success(f"✅ Merged and updated holding: Added {shares} shares of {selected_symbol} at ${result.get('quote_used', 'current'):.2f} per share")
                    st.info(f"📊 All {selected_symbol} holdings were combined. New average price: ${result['holding']['avg_price']:.2f} | Total shares: {result['holding']['shares']:.2f}")
                elif action == 'updated':
                    st.success(f"✅ Updated holding: Added {shares} shares of {selected_symbol} at ${result.get('quote_used', 'current'):.2f} per share")
                    st.info(f"📊 New average price: ${result['holding']['avg_price']:.2f} | Total shares: {result['holding']['shares']:.2f}")
                else:
                    st.success(f"✅ Added {shares} shares of {selected_symbol} at ${result.get('quote_used', 'current'):.2f} per share")
                st.info(f"💰 Deducted ${result.get('cash_deducted', 0):,.2f} from cash. New balance: ${result.get('new_cash_balance', 0):,.2f}")
                
                # Clear search state after successful add
                st.session_state["stock_search_query"] = ""
                st.session_state["stock_search_results"] = []
                st.session_state["selected_stock_symbol"] = None
                
                # Clear only relevant caches instead of all
                load_portfolio_details.clear()
                load_user_profile.clear()
                st.rerun()
            except Exception as e:
                error_msg = str(e)
                if "Insufficient cash" in error_msg:
                    st.error(f"❌ {error_msg}")
                    st.info("💡 Go to Profile page to add more cash to your account.")
                else:
                st.error(f"Failed to add holding: {e}")

# ----------------- Actions -----------------
st.subheader("🔄 Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Data"):
        # Clear all caches
        load_portfolios.clear()
        load_portfolio_details.clear()
        load_user_profile.clear()
        st.rerun()

with col2:
    if st.button("📊 Go to Profile"):
        st.switch_page("pages/04_Profile.py")

with col3:
    if st.button("📈 Go to Forecast"):
        st.switch_page("pages/02_Forecast.py")
