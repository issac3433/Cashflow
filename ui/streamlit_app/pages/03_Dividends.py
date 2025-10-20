# ui/streamlit_app/pages/03_Dividends.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import calendar
from utils.api import api_get, api_post

st.set_page_config(
    page_title="Dividend Calendar",
    page_icon="📅",
    layout="wide"
)

# Authentication check
if not st.session_state.get("is_authed") or not st.session_state.get("jwt_token"):
    st.error("Please log in to view dividend information.")
    st.link_button("Go to Login", "http://localhost:8501")
    st.stop()

st.title("📅 Dividend Calendar")
st.caption("Track your upcoming dividend payments and income")

# Get dividend calendar data
try:
    with st.spinner("Loading dividend calendar..."):
        calendar_data = api_get("/calendar")
        events = calendar_data.get("events", [])
    
    if not events:
        st.info("No dividend events found. Add some holdings to see upcoming dividends!")
        st.stop()
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(events)
    df['ex_date'] = pd.to_datetime(df['ex_date'])
    df['pay_date'] = pd.to_datetime(df['pay_date'])
    
    # Show ALL dividend payments (past and future)
    today = date.today()
    upcoming_df = df[df['pay_date'].dt.date >= today].copy()
    past_df = df[df['pay_date'].dt.date < today].copy()

    # Combine all dividends for display
    display_df = df.copy()  # Show all dividends
    display_df = display_df.sort_values('pay_date')
    
    if display_df.empty:
        st.info("No dividend payments found.")
        st.stop()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_all = display_df['cash'].sum()
        st.metric("💰 Total Dividends", f"${total_all:,.2f}")
    
    with col2:
        total_upcoming = upcoming_df['cash'].sum()
        st.metric("➡️ Upcoming", f"${total_upcoming:,.2f}")
    
    with col3:
        unique_symbols = display_df['symbol'].nunique()
        st.metric("📈 Paying Stocks", f"{unique_symbols}")
    
    with col4:
        total_payments = len(display_df)
        st.metric("📊 Total Payments", f"{total_payments}")
    
    st.divider()
    
    # Calendar View
    st.subheader("📅 Dividend Calendar View")
    
    # Create a monthly calendar view with navigation
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # Initialize session state for calendar navigation
    if 'calendar_year' not in st.session_state:
        st.session_state.calendar_year = current_year
    if 'calendar_month' not in st.session_state:
        st.session_state.calendar_month = current_month
    
    # Navigation controls
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
    with col1:
        if st.button("⬅️", key="prev_month", help="Previous month"):
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            else:
                st.session_state.calendar_month -= 1
            st.rerun()
    
    with col2:
        # Month selector with actual month names
        month_names = [calendar.month_name[i] for i in range(1, 13)]
        selected_month_idx = st.selectbox(
            "Month", 
            range(12), 
            index=st.session_state.calendar_month - 1,
            format_func=lambda x: month_names[x],
            key="month_selector"
        )
        st.session_state.calendar_month = selected_month_idx + 1
    
    with col3:
        # Year selector
        selected_year = st.selectbox(
            "Year", 
            range(current_year, current_year + 3), 
            index=st.session_state.calendar_year - current_year,
            key="year_selector"
        )
        st.session_state.calendar_year = selected_year
    
    with col4:
        if st.button("➡️", key="next_month", help="Next month"):
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            else:
                st.session_state.calendar_month += 1
            st.rerun()
    
    # Display calendar for selected month/year
    selected_year = st.session_state.calendar_year
    selected_month = st.session_state.calendar_month
    
    # Create calendar for selected month
    cal = calendar.monthcalendar(selected_year, selected_month)
    month_name = calendar.month_name[selected_month]
    
    # Create a calendar grid
    st.write(f"**{month_name} {selected_year}**")
    
    # Filter events for selected month (show ALL dividends)
    month_events = display_df[
        (display_df['pay_date'].dt.year == selected_year) & 
        (display_df['pay_date'].dt.month == selected_month)
    ].copy()
    
    # Create calendar HTML
    calendar_html = f"""
    <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; margin: 10px 0;">
        <div style="padding: 8px; text-align: center; font-weight: bold; background-color: #f0f2f6;">Sun</div>
        <div style="padding: 8px; text-align: center; font-weight: bold; background-color: #f0f2f6;">Mon</div>
        <div style="padding: 8px; text-align: center; font-weight: bold; background-color: #f0f2f6;">Tue</div>
        <div style="padding: 8px; text-align: center; font-weight: bold; background-color: #f0f2f6;">Wed</div>
        <div style="padding: 8px; text-align: center; font-weight: bold; background-color: #f0f2f6;">Thu</div>
        <div style="padding: 8px; text-align: center; font-weight: bold; background-color: #f0f2f6;">Fri</div>
        <div style="padding: 8px; text-align: center; font-weight: bold; background-color: #f0f2f6;">Sat</div>
    """
    
    # Add days
    for week in cal:
        for day in week:
            if day == 0:
                calendar_html += '<div style="padding: 8px; text-align: center;"></div>'
            else:
                # Check if this day has dividend payments
                day_events = month_events[month_events['pay_date'].dt.day == day]
                
                if not day_events.empty:
                    total_amount = day_events['cash'].sum()
                    symbols = ', '.join(day_events['symbol'].unique())
                    
                    # Check if this is a future or past dividend
                    day_date = pd.Timestamp(f"{selected_year}-{selected_month:02d}-{day:02d}").date()
                    is_future = day_date >= today
                    
                    if is_future:
                        # Future dividend - green
                        bg_color = "#e8f5e8"
                        border_color = "#4caf50"
                        text_color = "#2e7d32"
                        status_text = "📅"
                    else:
                        # Past dividend - blue
                        bg_color = "#e3f2fd"
                        border_color = "#2196f3"
                        text_color = "#1565c0"
                        status_text = "✅"
                    
                    calendar_html += f'''
                    <div style="padding: 8px; text-align: center; background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 4px;">
                        <div style="font-weight: bold;">{day}</div>
                        <div style="font-size: 0.8em; color: {text_color};">{status_text} ${total_amount:.2f}</div>
                        <div style="font-size: 0.7em; color: #666;">{symbols}</div>
                    </div>
                    '''
                else:
                    calendar_html += f'<div style="padding: 8px; text-align: center;">{day}</div>'
    
    calendar_html += "</div>"
    st.markdown(calendar_html, unsafe_allow_html=True)
    
    st.divider()
    
    # Dividend Processing Section
    st.subheader("⚙️ Dividend Processing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Sync Dividend Data**")
        st.caption("Fetch latest dividend information from APIs")
        if st.button("🔄 Sync Dividends", key="sync_dividends"):
            try:
                with st.spinner("Syncing dividend data..."):
                    result = api_post("/sync/all")
                    st.success(f"Synced {result.get('inserted', 0)} dividend events")
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to sync dividends: {e}")
    
    with col2:
        st.write("**Process Payments**")
        st.caption("Convert dividend events to cash in your account")
        if st.button("💰 Process Dividends", key="process_dividends"):
            try:
                with st.spinner("Processing dividend payments..."):
                    result = api_post("/dividends/process")
                    st.success(f"Processed {result.get('processed', 0)} dividend payments")
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to process dividends: {e}")

except Exception as e:
    st.error(f"Failed to load dividend calendar: {e}")
    st.write("Make sure the backend API is running and you have some holdings.")
