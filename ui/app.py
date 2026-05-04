import streamlit as st
import os
import sys
import ast
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure moneypenny modules are securely in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.engine import Engine

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Moneypenny Investment Agent",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CLEAN CSS ---
st.markdown("""
<style>
    /* Financial Highlights */
    .pos-change { color: #2ecc71; font-weight: bold; }
    .neg-change { color: #e74c3c; font-weight: bold; }

    /* TL;DR Card */
    .tldr-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border: 1px solid #3a7bd5;
        border-left: 4px solid #3a7bd5;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 18px;
        color: #e8eaf6;
        font-size: 0.9rem;
        line-height: 1.7;
        box-shadow: 0 4px 15px rgba(58, 123, 213, 0.15);
    }
    .tldr-card .tldr-header {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #3a7bd5;
        margin-bottom: 10px;
    }
    .tldr-card p, .tldr-card li { color: #c9d1e0; margin: 3px 0; }
    .tldr-card strong { color: #ffffff; }

    /* Adjusted top padding to clear the top bar */
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
if "engine" not in st.session_state or not hasattr(st.session_state.engine, "process_interaction"):
    st.session_state.engine = Engine()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Have Moneypenny proactively ask for profile data if it's missing basic info like Job or Age
    current_prof = st.session_state.engine.db.load_profile()
    if not current_prof or not current_prof.get("Job") or not current_prof.get("Age"):
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Hello! I'm Moneypenny. To give you the best, personalized recommendations, I need to know a bit about your Investor Profile first. What do you do for a living, and how old are you?"
        })

if "notebook_trace" not in st.session_state:
    st.session_state.notebook_trace = []

if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = None

if "current_quote" not in st.session_state:
    st.session_state.current_quote = {}

if "current_data" not in st.session_state:
    st.session_state.current_data = {}

def save_profile(profile_data):
    st.session_state.engine.db.save_profile(profile_data)

# =============================================================================
# SIDEBAR — Investor Profile
# =============================================================================
with st.sidebar:
    # --- Reset Button ---
    if st.button("Reset Session", use_container_width=True):
        st.session_state.engine.db.clear_all()
        for key in ["chat_history", "notebook_trace", "current_ticker", "current_quote", "current_data"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # --- SECTION: Investor Profile ---
    st.header("Investor Profile")
    current_profile = st.session_state.engine.db.load_profile()

    # Safely cast Age
    try:
        age_val = max(18, min(120, int(current_profile.get("Age", 30))))
    except (ValueError, TypeError):
        age_val = 30

    # Safely cast Retirement Age
    try:
        ret_age_val = max(age_val, min(120, int(current_profile.get("Retirement Age", 65))))
    except (ValueError, TypeError):
        ret_age_val = max(age_val, 65)

    # Safely cast Risk
    try:
        risk_val = max(1, min(10, int(current_profile.get("Risk Tolerance", 5))))
    except (ValueError, TypeError):
        risk_val = 5

    # Safely map Selectboxes
    l_opts = ["Beginner", "Intermediate", "Advanced"]
    l_val = current_profile.get("Literacy", "Intermediate")
    l_idx = l_opts.index(l_val) if l_val in l_opts else 1

    age = st.number_input("Age", min_value=18, max_value=120, value=age_val)
    amount = st.number_input("Investment Amount ($)", min_value=0, max_value=100000000, value=int(current_profile.get("Investment Amount", 10000)), step=1000)
    job = st.text_input("Job/Industry", value=str(current_profile.get("Job", "")))
    risk = st.slider("Risk Tolerance (1-10)", 1, 10, risk_val)
    ret_age = st.number_input("Retirement Age", min_value=age, max_value=120, value=ret_age_val)
    literacy = st.selectbox("Financial Literacy", l_opts, index=l_idx)
    bias = st.text_area("Specific Exclusions/Beliefs", placeholder="e.g., No tobacco stocks, bullish on AI", value=str(current_profile.get("Bias", "")))

    profile_data = {
        "Age": age, "Investment Amount": amount, "Job": job, "Risk Tolerance": risk,
        "Retirement Age": ret_age, "Literacy": literacy,
        "Bias": bias
    }

    updated_profile = current_profile.copy()
    updated_profile.update(profile_data)
    if updated_profile != current_profile:
        save_profile(updated_profile)

# =============================================================================
# MAIN AREA — Chat (Left) & Data Visualizations (Right)
# =============================================================================
col_chat, col_viz = st.columns([3, 2])

with col_chat:
    st.header("Moneypenny")

    # Chat history container
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"], unsafe_allow_html=True)

    # Chat input (sits below the scrollable container)
    user_input = st.chat_input("Ask Moneypenny...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Show user message immediately
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input, unsafe_allow_html=True)

        # Process Query
        with st.spinner("Thinking..."):
            response_text, trace, ticker = st.session_state.engine.process_interaction(user_input, st.session_state.chat_history)

            if trace:
                st.session_state.notebook_trace = trace
            if ticker:
                st.session_state.current_ticker = ticker

            # Fail-safe: if response_text is a string that looks like JSON, try to parse it
            if isinstance(response_text, str) and response_text.strip().startswith("{") and response_text.strip().endswith("}"):
                try:
                    import json as pyjson
                    potential_data = pyjson.loads(response_text.strip())
                    if isinstance(potential_data, dict) and "portfolio_weights" in potential_data:
                        response_text = potential_data
                except:
                    pass

            if isinstance(response_text, dict):
                st.session_state.current_data = response_text
                markdown_msg = response_text.get("recommendation_markdown", str(response_text))
            else:
                markdown_msg = response_text

            st.session_state.chat_history.append({"role": "assistant", "content": markdown_msg})
        st.rerun()

with col_viz:
    st.header("Portfolio Summary")
    st.markdown("Easy-to-understand visualization of your latest query.")

    ticker = st.session_state.current_ticker
    data = st.session_state.get("current_data", {})

    if ticker and data and isinstance(data, dict) and "portfolio_weights" in data:
        weights = data.get("portfolio_weights", {})
        total = float(data.get("total_investment", 10000))
        growth = float(data.get("projected_growth_percent", 0.0))

        # Pie Chart — Move to top as requested
        st.markdown("### Portfolio Allocation")
        import pandas as pd
        import altair as alt

        chart_data = {}
        for category, value in weights.items():
            if isinstance(value, dict) and "products" in value:
                for product, pct in value["products"].items():
                    chart_data[product] = float(pct)
            else:
                chart_data[category] = float(value)

        df = pd.DataFrame({"Asset": list(chart_data.keys()), "Weight": list(chart_data.values())})
        chart = alt.Chart(df).mark_arc(innerRadius=40).encode(
            theta=alt.Theta(field="Weight", type="quantitative"),
            color=alt.Color(field="Asset", type="nominal"),
            tooltip=["Asset", "Weight"]
        ).properties(height=300) # Slightly smaller to fit single col
        st.altair_chart(chart, use_container_width=True)

        # Metrics & Breakdown in single column
        # Projected Growth
        st.markdown("### Projected Growth")
        end_value = total * (1 + growth / 100)
        st.metric(label="1-Year Projected Portfolio Value",
                  value=f"${end_value:,.2f}",
                  delta=f"{growth:.2f}% Expected Return")

        # Expandable breakdown
        st.markdown(f"### Breakdown (${total:,.0f} Investment)")
        for category, value in weights.items():
            # Support new nested format: {"weight": 30, "products": {...}}
            if isinstance(value, dict) and "weight" in value:
                cat_weight = float(value["weight"])
                cat_amt = total * (cat_weight / 100)
                products = value.get("products", {})
                with st.expander(f"**{category}** — {cat_weight:.0f}% (${cat_amt:,.2f})"):
                    for product, pct in products.items():
                        p_amt = total * (float(pct) / 100)
                        st.markdown(f"- **{product}**: {pct}% (${p_amt:,.2f})")
            else:
                # Backward compatibility: flat format {"Bonds": 30}
                cat_weight = float(value)
                cat_amt = total * (cat_weight / 100)
                st.markdown(f"- **{category}**: {cat_weight:.0f}% (${cat_amt:,.2f})")

    elif ticker:
        st.info("Looking up real-time statistics...")
    else:
        st.info("Your recommended portfolio will appear here.")
