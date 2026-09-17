# ============================================================
# CLEARCHECK TECHNOLOGIES — APPROVAL RISK DASHBOARD
# BDA 640 Mini Case
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="ClearCheck Approval Risk Dashboard",
    page_icon="🔍",
    layout="wide"
)


# ============================================================
# 2. DASHBOARD TITLE
# ============================================================

st.title("ClearCheck Technologies")
st.subheader("Approval Timing and Review-Risk Dashboard")

st.markdown(
    """
    This dashboard examines approval-timing patterns for three
    ClearCheck technicians.

    Approval duration is estimated as the time between consecutive
    approvals completed by the same technician.
    """
)

# ============================================================
# 3. LOAD THE DASHBOARD DATA
# ============================================================

@st.cache_data
def load_data():
    """
    Load the four processed ClearCheck datasets.
    """

    approvals = pd.read_csv(
        "clearcheck_approvals_processed.csv"
    )

    blocks = pd.read_csv(
        "clearcheck_blocks.csv"
    )

    kpis = pd.read_csv(
        "clearcheck_kpis.csv"
    )

    payout_tests = pd.read_csv(
        "clearcheck_payout_tests.csv"
    )

    # Convert approval timestamps from text to datetime.
    approvals["APPROVAL_DATE"] = pd.to_datetime(
        approvals["APPROVAL_DATE"],
        errors="coerce"
    )

    # Convert block timestamps from text to datetime.
    blocks["Block_Start"] = pd.to_datetime(
        blocks["Block_Start"],
        errors="coerce"
    )

    blocks["Block_End"] = pd.to_datetime(
        blocks["Block_End"],
        errors="coerce"
    )

    return approvals, blocks, kpis, payout_tests


# Attempt to load the datasets.
try:
    approvals, blocks, kpis, payout_tests = load_data()

except FileNotFoundError:
    st.error(
        "One or more dashboard files could not be found. "
        "Confirm that all four CSV files are in the same "
        "folder as app.py."
    )
    st.stop()


# Confirm successful loading.
st.success(
    f"Data loaded successfully: {len(approvals):,} approval records "
    f"and {len(blocks):,} approval blocks."
)