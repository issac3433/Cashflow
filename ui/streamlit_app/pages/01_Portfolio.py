import streamlit as st
from utils.api import api_get, api_post, api_delete
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Portfolio", page_icon="📁", layout="wide")

if not st.session_state.get("is_authed"):
    st.switch_page("Login.py")

st.title("📁 Portfolio Management")

# ----------------- Portfolio Selector -----------------
@st.cache_data(ttl=60)
def load_portfolios():
    """Load user portfolios with caching."""
    try:
        return api_get("/portfolios")
    except Exception as e:
        st.error(f"Failed to load portfolios: {e}")
        return []

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
                result = api_post("/portfolios", json={
                    "name": name,
                    "portfolio_type": portfolio_type
                })
                st.success(f"Created {portfolio_type} portfolio: {result['name']}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create portfolio: {e}")

# ----------------- Portfolio Overview -----------------
portfolio_type_display = selected_portfolio.get('portfolio_type', 'individual').title()
st.subheader(f"📊 {selected_portfolio['name']} ({portfolio_type_display}) Overview")

@st.cache_data(ttl=30)
def load_portfolio_details(portfolio_id):
    """Load detailed portfolio information with error handling."""
    try:
        return api_get(f"/portfolios/{portfolio_id}")
    except Exception as e:
        st.error(f"Failed to load portfolio details: {e}")
        # Return a fallback structure
        return {
            "portfolio": {"id": portfolio_id, "name": "Unknown", "created_at": "Unknown"},
            "holdings": [],
            "total_value": 0.0,
            "holdings_count": 0
        }

portfolio_data = load_portfolio_details(selected_portfolio['id'])

if portfolio_data:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Value", f"${portfolio_data['total_value']:,.2f}")
    with col2:
        st.metric("Holdings", portfolio_data['holdings_count'])
    with col3:
        avg_value = portfolio_data['total_value'] / max(portfolio_data['holdings_count'], 1)
        st.metric("Avg Position", f"${avg_value:,.2f}")
    with col4:
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
    original_market_value = holdings_df['market_value'].copy()
    
    # Format columns for display
    holdings_df['avg_price'] = holdings_df['avg_price'].apply(lambda x: f"${x:.2f}")
    holdings_df['latest_price'] = holdings_df['latest_price'].apply(lambda x: f"${x:.2f}")
    holdings_df['market_value'] = holdings_df['market_value'].apply(lambda x: f"${x:,.2f}")
    holdings_df['gain_loss'] = holdings_df['gain_loss'].apply(lambda x: f"${x:,.2f}")
    holdings_df['gain_loss_pct'] = holdings_df['gain_loss_pct'].apply(lambda x: f"{x:.1f}%")
    
    # Display table with delete buttons
    st.write("**Holdings Table:**")
    
    # Create columns for each holding with delete button
    for idx, row in holdings_df.iterrows():
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 1, 1, 1, 1, 1, 0.5])
        
        with col1:
            st.write(f"**{row['symbol']}**")
        with col2:
            st.write(f"{row['shares']}")
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
            # Delete button
            if st.button("🗑️", key=f"delete_{row['id']}", help="Delete this holding"):
                try:
                    # Use the holding ID directly from the dataframe
                    holding_id = row['id']
                    api_delete(f"/holdings/{holding_id}")
                    st.success(f"Deleted {row['symbol']} holding")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete holding: {e}")
    
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
    
    if st.button("Add Holding"):
        selected_symbol = st.session_state.get("selected_stock_symbol")
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
                st.success(f"Added {shares} shares of {selected_symbol} at ${result.get('quote_used', 'current')} per share")
                
                # Clear search state after successful add
                st.session_state["stock_search_query"] = ""
                st.session_state["stock_search_results"] = []
                st.session_state["selected_stock_symbol"] = None
                
                st.cache_data.clear()  # Clear cache to refresh data
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add holding: {e}")

# ----------------- Actions -----------------
st.subheader("🔄 Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

with col2:
    if st.button("📊 Go to Profile"):
        st.switch_page("pages/03_Profile.py")

with col3:
    if st.button("📈 Go to Forecast"):
        st.switch_page("pages/02_Forecast.py")
