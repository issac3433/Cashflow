import streamlit as st
from utils.api import api_get, api_post
import pandas as pd

st.set_page_config(page_title="Portfolio", page_icon="📁", layout="wide")
if not st.session_state.get("is_authed"):
    st.switch_page("Login.py")

st.title("📁 Portfolio")

# ----------------- Portfolios -----------------
st.subheader("My Portfolios")

if st.button("Load Portfolios"):
    st.session_state["portfolios"] = api_get("/portfolios")

ports = st.session_state.get("portfolios", [])
if ports:
    df_ports = pd.DataFrame(ports)
    if not df_ports.empty:
        st.dataframe(df_ports, use_container_width=True)
    else:
        st.caption("No portfolios yet.")
else:
    st.caption("Click **Load Portfolios** to fetch.")

with st.expander("Create Portfolio"):
    name = st.text_input("Name", "Default", key="p_name")
    if st.button("Create", key="p_create"):
        p = api_post("/portfolios", json=None if name == "Default" else {"name": name})
        st.success(f"Created portfolio #{p.get('id')}")
        st.session_state.pop("portfolios", None)

st.divider()

# ----------------- Holdings -----------------
st.subheader("Holdings")

pid = st.number_input("Portfolio ID", min_value=1, step=1, value=1, key="pid")

# 🔎 Type-ahead search with prices
st.write("Search and select a symbol/company:")
query = st.text_input(
    "Type to search",
    value=st.session_state.get("search_q", ""),
    key="search_q",
    placeholder="e.g., apple, nvda, msft"
)

suggestions = []
if len(query.strip()) >= 2:
    try:
        res = api_get(f"/symbols/suggest?q={query.strip()}&limit=10")
        suggestions = res.get("results", [])
    except Exception as e:
        st.warning(f"Search error: {e}")

# Build dropdown labels
options = []
for r in suggestions:
    px = r.get("price")
    price_txt = f"${px:,.2f}" if (px is not None) else "n/a"
    label = f"{r['symbol']} — {r.get('name','')[:60]} ({price_txt})"
    options.append(label)

sel = st.selectbox("Matches", options or ["No matches"], index=0, disabled=not options)

# Derive selected symbol + price
selected_symbol = ""
selected_price = None
if options:
    i = options.index(sel)
    selected_symbol = suggestions[i]["symbol"]
    selected_price = suggestions[i].get("price")

# Inputs to add holding
col_a, col_b, col_c = st.columns([1, 1, 1])
with col_a:
    symbol_input = st.text_input("Symbol", value=selected_symbol or "AAPL", key="symbol_input").upper()
with col_b:
    shares = st.number_input("Shares", min_value=0.0, value=5.0, key="shares")
with col_c:
    use_latest = st.checkbox("Use latest price", value=True, key="use_latest")

if selected_symbol:
    st.caption(f"Suggested: {selected_symbol} ≈ {f'${selected_price:,.2f}' if selected_price is not None else 'n/a'}")

avg_price = st.number_input(
    "Avg Price (ignored if 'Use latest price' checked)",
    min_value=0.0,
    value=float(selected_price or 0.0),
    key="avg_price",
    disabled=use_latest
)

# Add holding button
if st.button("Add Holding"):
    payload = {
        "portfolio_id": int(pid),
        "symbol": symbol_input,
        "shares": float(shares),
        "avg_price": None if use_latest else float(avg_price),
    }
    res = api_post("/holdings", json=payload)
    st.success(f"Added holding #{res['holding']['id']} (price used: ${res['quote_used']:,.2f})")

    # Immediate refresh of holdings with quotes
    rows = api_get(f"/holdings/with-quotes?portfolio_id={int(pid)}")
    st.session_state["holdings_q"] = rows

# Load holdings (with quotes)
if st.button("Load Holdings (with quotes)"):
    rows = api_get(f"/holdings/with-quotes?portfolio_id={int(pid)}")
    st.session_state["holdings_q"] = rows

# Display holdings table
holdings = st.session_state.get("holdings_q", [])
if holdings:
    df = pd.DataFrame(holdings)
    cols_order = [
        "id", "symbol", "shares", "avg_price",
        "latest_price", "market_value", "portfolio_id", "reinvest_dividends"
    ]
    df = df[[c for c in cols_order if c in df.columns]]
    st.dataframe(df, use_container_width=True)
else:
    st.caption("Click **Load Holdings (with quotes)** to fetch.")

st.divider()

# ----------------- Dividends -----------------
st.subheader("Dividends")
sym_for_div = st.text_input("Refresh dividends for symbol", "AAPL", key="div_symbol").upper()
if st.button("Refresh Dividends"):
    res = api_post(f"/dividends/refresh/{sym_for_div}")
    st.success(f"Inserted {res.get('inserted', 0)} events")
