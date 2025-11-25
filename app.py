import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
st.set_page_config(
    page_title="Dashboard System", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FOLDER = "data"
# Load DATABASE_URL from .env file (không commit password lên git!)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    st.error("⚠️ DATABASE_URL not found in .env file!")
    st.stop()

# Custom CSS to hide number input spinners and prevent non-numeric input
st.markdown("""
<style>
    /* Hide spin buttons for number inputs */
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    input[type=number] {
        -moz-appearance: textfield;
    }
    /* Disable autocomplete for all inputs */
    input {
        autocomplete: off !important;
    }
</style>
""", unsafe_allow_html=True)
# Load database
@st.cache_data
def load_database():
    """Load data from Supabase PostgreSQL"""
    try:
        # Kết nối Supabase
        engine = create_engine(DATABASE_URL)
        
        # Đọc data từ bảng ro_items
        query = "SELECT item_code, avg_consume FROM ro_items ORDER BY item_code"
        df = pd.read_sql(query, engine)
        
        # Đổi tên cột để khớp với code cũ
        df.columns = ['Item_Code', 'Avg_Consume']
        
        # Loại bỏ dòng trống
        df = df.dropna()
        
        return df, []
        
    except Exception as e:
        return None, [f"Lỗi kết nối Supabase: {str(e)}"]
    return combined, []

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Function:",
    ["ISC _ DO system tracking", "Inventory Management", "Sales Analysis", "Reports", "Settings"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info(f"Current Page: **{page}**")

# Main content based on selection
if page == "ISC _ DO system tracking":
    # ========== RO/DO DECISION PAGE ==========
    st.title("ISC _ DO system tracking")
    # st.markdown("Check if ordering is required based on stock and average consumption")
    st.markdown("---")
    
    # Load data
    df, errors = load_database()
    
    if df is None:
        st.error("Error: No data found in 'data' folder")
        if errors:
            st.error("Details:")
            for error in errors:
                st.write(f"- {error}")
        st.info("""
        Required:
        - Create 'data' folder in the same directory as app.py
        - Add Excel files with columns: 'Item Code' and 'Avg Consume'
        - Header must be in row 2
        - Make sure Excel files are not open or locked
        """)
        st.stop()
    
    # Database info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Database Info")
    st.sidebar.metric("Total Items", len(df))
    if st.sidebar.button("Reload Database"):
        st.cache_data.clear()
        st.rerun()
    
    # Main form - 2 columns layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Input Information")
        
        item_code = st.selectbox(
            "Item Code:",
            options=[""] + df['Item_Code'].astype(str).tolist(),
            key="item_code_select"
        )
        
        stock_input = st.number_input(
            "Pick to Light Stock:",
            min_value=0.0,
            value=None,
            step=1.0,
            format="%.0f",
            placeholder="Enter pick to light stock",
            help="Numbers only",
            key="stock_input"
        )
        
        ro_input = st.number_input(
            "Requested Quantity:",
            min_value=0.0,
            value=None,
            step=1.0,
            format="%.0f",
            placeholder="Enter requested quantity",
            help="Numbers only",
            key="ro_input"
        )
        
        st.markdown("---")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            process_btn = st.button("Check Decision", type="primary", use_container_width=True)
        
        with col_btn2:
            reset_btn = st.button("Reset", use_container_width=True)
    
    if reset_btn:
        # Clear all widget states
        for key in ['item_code_select', 'item_code_manual', 'stock_input', 'ro_input', 'show_result', 'decision_text', 'decision_type']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    with col2:
        st.subheader("Decision Result")
        
        # Placeholder for result
        result_placeholder = st.empty()
        
        if 'show_result' not in st.session_state:
            st.session_state.show_result = False
            st.session_state.decision_text = ""
            st.session_state.decision_type = ""
        
        if st.session_state.show_result:
            if st.session_state.decision_type == "YES":
                result_placeholder.success(st.session_state.decision_text)
            else:
                result_placeholder.error(st.session_state.decision_text)
    
    if process_btn:
        if stock_input is None or ro_input is None:
            st.warning("Please enter both Finished Stock and RO Quantity")
            st.session_state.show_result = False
        elif not item_code:
            st.warning("Please select or enter Item Code")
            st.session_state.show_result = False
        else:
            stock = stock_input
            ro = ro_input
            result_df = df[df['Item_Code'].astype(str) == str(item_code)]
            
            if len(result_df) == 0:
                st.error(f"Item Code '{item_code}' not found in database")
                st.session_state.show_result = False
            else:
                avg_consume = abs(float(result_df['Avg_Consume'].iloc[0]))
                total = stock + ro
                threshold = 2 * avg_consume
                decision = total <= threshold
                
                if decision:
                    st.session_state.decision_text = "YES"
                    st.session_state.decision_type = "YES"
                else:
                    st.session_state.decision_text = "NO"
                    st.session_state.decision_type = "NO"
                
                st.session_state.show_result = True
                st.rerun()
    
    # Database view
    st.markdown("---")
    with st.expander("View Full Database"):
        st.dataframe(df, use_container_width=True)

elif page == "Inventory Management":
    # ========== INVENTORY MANAGEMENT (PENDING) ==========
    st.title("Inventory Management")
    st.markdown("---")
    
    st.info("This feature is under development")
    
    st.write("""
    **Planned Features:**
    - Real-time inventory tracking
    - Stock level monitoring
    - Low stock alerts
    - Inventory reports
    """)
    
    # Placeholder content
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Items", "Pending", delta="TBD")
    with col2:
        st.metric("Low Stock Items", "Pending", delta="TBD")
    with col3:
        st.metric("Out of Stock", "Pending", delta="TBD")

elif page == "Sales Analysis":
    # ========== SALES ANALYSIS (PENDING) ==========
    st.title("Sales Analysis")
    st.markdown("---")
    
    st.info("This feature is under development")
    
    st.write("""
    **Planned Features:**
    - Sales trends
    - Top selling items
    - Revenue analysis
    - Forecasting
    """)
    
    # Placeholder chart
    st.subheader("Sales Trend (Sample)")
    chart_data = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        'Sales': [100, 150, 130, 180, 200]
    })
    st.line_chart(chart_data.set_index('Month'))

elif page == "Reports":
    # ========== REPORTS (PENDING) ==========
    st.title("Reports")
    st.markdown("---")
    
    st.info("This feature is under development")
    
    st.write("""
    **Planned Features:**
    - Generate custom reports
    - Export to Excel/PDF
    - Scheduled reports
    - Email notifications
    """)
    
    report_type = st.selectbox(
        "Select Report Type:",
        ["Daily Summary", "Weekly Inventory", "Monthly Sales", "Custom Report"]
    )
    
    date_range = st.date_input("Date Range:", [])
    
    st.button("Generate Report", disabled=True)

elif page == "Settings":
    # ========== SETTINGS (PENDING) ==========
    st.title("Settings")
    st.markdown("---")
    
    st.info("This feature is under development")
    
    st.write("""
    **Planned Features:**
    - User preferences
    - Data source configuration
    - Notification settings
    - System parameters
    """)
    
    st.subheader("Configuration")
    
    st.text_input("Data Folder Path:", value=DATA_FOLDER, disabled=True)
    st.number_input("Refresh Interval (minutes):", value=30, disabled=True)
    st.checkbox("Enable notifications", disabled=True)
    st.checkbox("Auto-refresh database", disabled=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    <p>Dashboard System v1.0</p>
</div>
""", unsafe_allow_html=True)