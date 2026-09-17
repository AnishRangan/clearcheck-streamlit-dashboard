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

# ============================================================
# 4. SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Dashboard Filters")

# Create the list of available technicians.
technician_list = sorted(
    approvals["PROVIDER_APPROVING_NAME"]
    .dropna()
    .unique()
    .tolist()
)

# Allow users to select one or more technicians.
selected_technicians = st.sidebar.multiselect(
    "Select technician(s)",
    options=technician_list,
    default=technician_list
)

# Stop the application if no technician is selected.
if not selected_technicians:
    st.warning(
        "Select at least one technician from the sidebar."
    )
    st.stop()

# Identify the full date range in the dataset.
minimum_date = approvals["APPROVAL_DATE"].min().date()
maximum_date = approvals["APPROVAL_DATE"].max().date()

# Add a date-range filter.
selected_date_range = st.sidebar.date_input(
    "Select approval-date range",
    value=(minimum_date, maximum_date),
    min_value=minimum_date,
    max_value=maximum_date
)

# Use the full date range if only one date is selected.
if len(selected_date_range) == 2:
    selected_start_date = selected_date_range[0]
    selected_end_date = selected_date_range[1]

else:
    selected_start_date = minimum_date
    selected_end_date = maximum_date


# ============================================================
# 5. APPLY THE FILTERS
# ============================================================

filtered_approvals = approvals[
    approvals["PROVIDER_APPROVING_NAME"].isin(
        selected_technicians
    )
].copy()

filtered_approvals = filtered_approvals[
    (
        filtered_approvals["APPROVAL_DATE"].dt.date
        >= selected_start_date
    )
    &
    (
        filtered_approvals["APPROVAL_DATE"].dt.date
        <= selected_end_date
    )
].copy()

# Apply the same filters to the block dataset.
filtered_blocks = blocks[
    blocks["PROVIDER_APPROVING_NAME"].isin(
        selected_technicians
    )
].copy()

filtered_blocks = filtered_blocks[
    (
        filtered_blocks["Block_Start"].dt.date
        >= selected_start_date
    )
    &
    (
        filtered_blocks["Block_Start"].dt.date
        <= selected_end_date
    )
].copy()

# Stop if the filters produce no approval records.
if filtered_approvals.empty:
    st.warning(
        "No approval records match the selected filters."
    )
    st.stop()

# Temporary confirmation that the filters are working.
st.write(
    f"Filtered records: {len(filtered_approvals):,} approvals "
    f"and {len(filtered_blocks):,} blocks."
)

# ============================================================
# 6. CALCULATE DASHBOARD KPIs
# ============================================================

# Keep only records with measurable approval durations.
measurable_durations = filtered_approvals[
    "APPROVAL_DURATION_SEC"
].dropna()

total_approvals = len(filtered_approvals)
total_blocks = len(filtered_blocks)

# Calculate the median approval gap.
median_duration = (
    measurable_durations.median()
    if len(measurable_durations) > 0
    else 0
)

# Calculate the percentage under 10 seconds.
under_10_ratio = (
    (measurable_durations < 10).mean() * 100
    if len(measurable_durations) > 0
    else 0
)

# Calculate the percentage of same-second approvals.
same_second_ratio = (
    (measurable_durations == 0).mean() * 100
    if len(measurable_durations) > 0
    else 0
)

# Calculate average cases per block.
average_cases_per_block = (
    filtered_blocks["Cases_In_Block"].mean()
    if total_blocks > 0
    else 0
)

# Calculate the weighted observed seconds per case.
observed_seconds_per_case = (
    filtered_blocks["Block_Duration_Seconds"].sum()
    / filtered_blocks["Cases_In_Block"].sum()
    if (
        total_blocks > 0
        and filtered_blocks["Cases_In_Block"].sum() > 0
    )
    else 0
)


# ============================================================
# 7. DISPLAY KPI CARDS
# ============================================================

st.markdown("## Selected-Data Overview")

kpi_1, kpi_2, kpi_3 = st.columns(3)

kpi_1.metric(
    label="Total Approvals",
    value=f"{total_approvals:,}"
)

kpi_2.metric(
    label="Median Approval Gap",
    value=f"{median_duration:.1f} sec"
)

kpi_3.metric(
    label="Approvals Under 10 Seconds",
    value=f"{under_10_ratio:.2f}%"
)

kpi_4, kpi_5, kpi_6 = st.columns(3)

kpi_4.metric(
    label="Same-Second Approvals",
    value=f"{same_second_ratio:.2f}%"
)

kpi_5.metric(
    label="Average Cases per Block",
    value=f"{average_cases_per_block:.2f}"
)

kpi_6.metric(
    label="Observed Seconds per Case",
    value=f"{observed_seconds_per_case:.2f} sec"
)

st.caption(
    f"Current selection contains {total_blocks:,} approval blocks."
)

st.info(
    "Timing metrics are risk indicators. Approval timestamps do not "
    "show when a technician opened or began reviewing a case."
)
# ============================================================
# 7. APPROVAL-DURATION DISTRIBUTION
# ============================================================

st.markdown("---")
st.header("Approval-Duration Distribution")

st.write(
    "This section displays the time between consecutive approvals "
    "for the selected technician(s) and dates."
)

# Allow the dashboard user to select the definition of a fast approval.
fast_threshold = st.sidebar.selectbox(
    "Fast-approval threshold",
    options=[2, 5, 10, 30, 60],
    index=2,
    format_func=lambda value: f"Under {value} seconds"
)

# Limit the displayed histogram range because the distribution is
# extremely right-skewed by overnight and between-session gaps.
histogram_max = st.sidebar.selectbox(
    "Histogram maximum duration",
    options=[60, 120, 300, 600],
    index=0,
    format_func=lambda value: f"{value} seconds"
)

# Keep only valid, nonnegative approval durations.
duration_data = filtered_approvals[
    filtered_approvals["APPROVAL_DURATION_SEC"].notna()
    & (filtered_approvals["APPROVAL_DURATION_SEC"] >= 0)
].copy()

# Label each approval according to the selected threshold.
duration_data["Approval Category"] = np.where(
    duration_data["APPROVAL_DURATION_SEC"] < fast_threshold,
    f"Fast: under {fast_threshold} seconds",
    f"Other: {fast_threshold} seconds or more"
)

# The histogram displays only values within the selected range.
# Records outside this range remain part of the other dashboard calculations.
histogram_data = duration_data[
    duration_data["APPROVAL_DURATION_SEC"] <= histogram_max
].copy()

# Create separate panels for the selected technicians.
duration_figure = px.histogram(
    histogram_data,
    x="APPROVAL_DURATION_SEC",
    color="Approval Category",
    facet_col="PROVIDER_APPROVING_NAME",
    facet_col_wrap=3,
    nbins=min(int(histogram_max), 100),
    barmode="stack",
    opacity=0.85,
    color_discrete_map={
        f"Fast: under {fast_threshold} seconds": "#EF553B",
        f"Other: {fast_threshold} seconds or more": "#636EFA"
    },
    labels={
        "APPROVAL_DURATION_SEC": "Approval Duration (seconds)",
        "count": "Number of Approvals"
    },
    title=(
        f"Approval Durations Up to {histogram_max} Seconds "
        f"— Fast Approvals Shown in Red"
    )
)

# Shorten the technician labels above each chart.
duration_figure.for_each_annotation(
    lambda annotation: annotation.update(
        text=annotation.text.split("=")[-1]
    )
)

# Add the selected fast-approval threshold to each panel.
duration_figure.add_vline(
    x=fast_threshold,
    line_dash="dash",
    line_color="darkred",
    line_width=2
)

duration_figure.update_layout(
    height=500,
    legend_title_text="",
    bargap=0.05
)

st.plotly_chart(
    duration_figure,
    use_container_width=True
)

excluded_from_histogram = (
    duration_data["APPROVAL_DURATION_SEC"] > histogram_max
).sum()

st.caption(
    f"The chart displays approval gaps from 0 to {histogram_max} seconds. "
    f"{excluded_from_histogram:,} longer gaps are excluded from the chart "
    "for readability but remain in the dataset."
)

# ============================================================
# 8. FAST-APPROVAL SUMMARY
# ============================================================

st.subheader(
    f"Fast-Approval Summary: Under {fast_threshold} Seconds"
)

fast_summary = (
    duration_data
    .groupby("PROVIDER_APPROVING_NAME")
    .agg(
        Measured_Approvals=("APPROVAL_DURATION_SEC", "size"),
        Fast_Approvals=(
            "APPROVAL_DURATION_SEC",
            lambda values: (values < fast_threshold).sum()
        )
    )
    .reset_index()
)

fast_summary["Fast_Approval_Percent"] = (
    fast_summary["Fast_Approvals"]
    / fast_summary["Measured_Approvals"]
    * 100
)

fast_summary = fast_summary.rename(
    columns={
        "PROVIDER_APPROVING_NAME": "Technician",
        "Measured_Approvals": "Measured Approvals",
        "Fast_Approvals": "Fast Approvals",
        "Fast_Approval_Percent": "Fast Approval Percent"
    }
)

st.dataframe(
    fast_summary,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Measured Approvals": st.column_config.NumberColumn(
            format="%d"
        ),
        "Fast Approvals": st.column_config.NumberColumn(
            format="%d"
        ),
        "Fast Approval Percent": st.column_config.NumberColumn(
            format="%.2f%%"
        )
    }
)

# Show examples of the records classified as fast approvals.
fast_records = duration_data[
    duration_data["APPROVAL_DURATION_SEC"] < fast_threshold
][
    [
        "CASE_NUMBER",
        "PROVIDER_APPROVING_NAME",
        "APPROVAL_DATE",
        "APPROVAL_DURATION_SEC"
    ]
].sort_values(
    by=["APPROVAL_DURATION_SEC", "APPROVAL_DATE"]
)

with st.expander("View highlighted fast-approval records"):
    st.write(
        f"{len(fast_records):,} approvals meet the current "
        f"under-{fast_threshold}-second definition."
    )

    st.dataframe(
        fast_records.head(500),
        use_container_width=True,
        hide_index=True
    )

    if len(fast_records) > 500:
        st.caption(
            "The first 500 records are displayed to keep the "
            "dashboard responsive."
        )
