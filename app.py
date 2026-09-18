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
# ============================================================
# 9. TOP APPROVAL DAYS
# ============================================================

st.markdown("---")
st.header("Top Approval Days")

st.write(
    "This chart identifies the dates with the highest approval volume "
    "for the selected technician(s) and date range."
)

# Allow the dashboard user to control how many days are displayed.
number_of_top_days = st.sidebar.slider(
    "Number of top approval days",
    min_value=5,
    max_value=20,
    value=10,
    step=1
)

# Create an approval-day variable from the full timestamp.
daily_approval_data = filtered_approvals[
    filtered_approvals["APPROVAL_DATE"].notna()
].copy()

daily_approval_data["Approval Day"] = (
    daily_approval_data["APPROVAL_DATE"].dt.normalize()
)

# Count approvals for each technician on each day.
daily_technician_counts = (
    daily_approval_data
    .groupby(
        ["Approval Day", "PROVIDER_APPROVING_NAME"]
    )
    .size()
    .reset_index(name="Approvals")
)

# Calculate the total approval volume for each day across
# all currently selected technicians.
daily_totals = (
    daily_technician_counts
    .groupby("Approval Day", as_index=False)["Approvals"]
    .sum()
    .sort_values("Approvals", ascending=False)
    .head(number_of_top_days)
)

# Keep technician-level information for only the highest-volume days.
top_day_chart_data = daily_technician_counts[
    daily_technician_counts["Approval Day"].isin(
        daily_totals["Approval Day"]
    )
].copy()

# Add readable date labels.
top_day_chart_data["Approval Day Label"] = (
    top_day_chart_data["Approval Day"].dt.strftime("%B %d, %Y")
)

# Create the horizontal stacked bar chart.
top_days_figure = px.bar(
    top_day_chart_data,
    x="Approvals",
    y="Approval Day Label",
    color="PROVIDER_APPROVING_NAME",
    orientation="h",
    barmode="stack",
    title=f"Top {number_of_top_days} Approval Days",
    labels={
        "Approval Day Label": "Approval Date",
        "PROVIDER_APPROVING_NAME": "Technician"
    },
    color_discrete_map={
        "Gary Arnold": "#EF553B",
        "Juan Mendez": "#636EFA",
        "Matt Shawn": "#00CC96"
    }
)

# Sort the bars so the highest-volume day appears at the top.
top_days_figure.update_yaxes(
    categoryorder="total ascending"
)

top_days_figure.update_layout(
    height=max(450, number_of_top_days * 42),
    legend_title_text="Technician",
    xaxis_title="Number of Approvals",
    yaxis_title="Approval Date"
)

st.plotly_chart(
    top_days_figure,
    use_container_width=True
)

# ============================================================
# 10. TOP APPROVAL DAYS SUMMARY TABLE
# ============================================================

top_days_table = daily_totals.copy()

top_days_table.insert(
    0,
    "Rank",
    range(1, len(top_days_table) + 1)
)

top_days_table["Approval Day"] = (
    top_days_table["Approval Day"].dt.strftime("%B %d, %Y")
)

top_days_table = top_days_table.rename(
    columns={
        "Approval Day": "Approval Date",
        "Approvals": "Total Approvals"
    }
)

st.subheader("Ranked Approval-Day Summary")

st.dataframe(
    top_days_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Rank": st.column_config.NumberColumn(format="%d"),
        "Total Approvals": st.column_config.NumberColumn(format="%d")
    }
)

st.caption(
    "When multiple technicians are selected, the bars show each "
    "technician's contribution to the total approval volume for that day."
)
# ============================================================
# 11. APPROVAL-BLOCK ANALYSIS
# ============================================================

st.markdown("---")
st.header("Approval-Block Analysis")

st.write(
    "A block represents a continuous approval session. A new block "
    "begins whenever the gap between consecutive approvals is "
    "10 minutes or more."
)

# Confirm that blocks remain after applying the dashboard filters.
if filtered_blocks.empty:
    st.warning(
        "No approval blocks are available for the current filters."
    )

else:
    # Calculate overall block-level KPIs.
    selected_block_count = len(filtered_blocks)

    total_block_approvals = (
        filtered_blocks["Cases_In_Block"].sum()
    )

    average_cases_per_block = (
        filtered_blocks["Cases_In_Block"].mean()
    )

    largest_block = (
        filtered_blocks["Cases_In_Block"].max()
    )

    # Weighted observed time per case:
    # total time inside all blocks divided by total approvals.
    weighted_observed_seconds = (
        filtered_blocks["Block_Duration_Seconds"].sum()
        / total_block_approvals
        if total_block_approvals > 0
        else np.nan
    )

    # Display the principal block KPIs.
    block_kpi_1, block_kpi_2, block_kpi_3, block_kpi_4 = st.columns(4)

    block_kpi_1.metric(
        "Approval Blocks",
        f"{selected_block_count:,}"
    )

    block_kpi_2.metric(
        "Average Cases per Block",
        f"{average_cases_per_block:,.2f}"
    )

    block_kpi_3.metric(
        "Largest Block",
        f"{largest_block:,.0f} cases"
    )

    block_kpi_4.metric(
        "Observed Seconds per Case",
        f"{weighted_observed_seconds:,.2f} sec"
    )

    st.caption(
        f"The current selection contains "
        f"{total_block_approvals:,.0f} approvals organized into "
        f"{selected_block_count:,} blocks."
    )


    # ========================================================
    # 12. TECHNICIAN BLOCK SUMMARY
    # ========================================================

    st.subheader("Block Summary by Technician")

    technician_block_summary = (
        filtered_blocks
        .groupby("PROVIDER_APPROVING_NAME")
        .agg(
            Approval_Blocks=("BLOCK_ID", "nunique"),
            Active_Days=(
                "Block_Start",
                lambda values: values.dt.normalize().nunique()
            ),
            Total_Approvals=("Cases_In_Block", "sum"),
            Average_Cases_Per_Block=("Cases_In_Block", "mean"),
            Median_Cases_Per_Block=("Cases_In_Block", "median"),
            Largest_Block=("Cases_In_Block", "max"),
            Total_Block_Duration_Seconds=(
                "Block_Duration_Seconds",
                "sum"
            ),
            Average_Fast_Under_10_Ratio=(
                "Fast_Under_10_Ratio",
                "mean"
            ),
            Median_Potential_PreReview_Seconds=(
                "Potential_PreReview_Seconds_Per_Case",
                "median"
            )
        )
        .reset_index()
    )

    # Calculate block frequency.
    technician_block_summary["Blocks_Per_Active_Day"] = (
        technician_block_summary["Approval_Blocks"]
        / technician_block_summary["Active_Days"]
    )

    # Calculate weighted observed seconds per case.
    technician_block_summary["Observed_Seconds_Per_Case"] = (
        technician_block_summary["Total_Block_Duration_Seconds"]
        / technician_block_summary["Total_Approvals"]
    )

    # Convert the fast ratio from a decimal to a percentage.
    technician_block_summary["Fast_Under_10_Percent"] = (
        technician_block_summary["Average_Fast_Under_10_Ratio"]
        * 100
    )

    # Select and rename the columns displayed on the dashboard.
    technician_block_summary = technician_block_summary[
        [
            "PROVIDER_APPROVING_NAME",
            "Approval_Blocks",
            "Active_Days",
            "Blocks_Per_Active_Day",
            "Total_Approvals",
            "Average_Cases_Per_Block",
            "Median_Cases_Per_Block",
            "Largest_Block",
            "Observed_Seconds_Per_Case",
            "Fast_Under_10_Percent",
            "Median_Potential_PreReview_Seconds"
        ]
    ].rename(
        columns={
            "PROVIDER_APPROVING_NAME": "Technician",
            "Approval_Blocks": "Approval Blocks",
            "Active_Days": "Active Days",
            "Blocks_Per_Active_Day": "Blocks per Active Day",
            "Total_Approvals": "Total Approvals",
            "Average_Cases_Per_Block": "Average Cases per Block",
            "Median_Cases_Per_Block": "Median Cases per Block",
            "Largest_Block": "Largest Block",
            "Observed_Seconds_Per_Case":
                "Observed Seconds per Case",
            "Fast_Under_10_Percent":
                "Fast Under 10 Seconds (%)",
            "Median_Potential_PreReview_Seconds":
                "Median Potential Pre-Review Seconds per Case"
        }
    )

    st.dataframe(
        technician_block_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Approval Blocks":
                st.column_config.NumberColumn(format="%d"),
            "Active Days":
                st.column_config.NumberColumn(format="%d"),
            "Blocks per Active Day":
                st.column_config.NumberColumn(format="%.2f"),
            "Total Approvals":
                st.column_config.NumberColumn(format="%d"),
            "Average Cases per Block":
                st.column_config.NumberColumn(format="%.2f"),
            "Median Cases per Block":
                st.column_config.NumberColumn(format="%.2f"),
            "Largest Block":
                st.column_config.NumberColumn(format="%d"),
            "Observed Seconds per Case":
                st.column_config.NumberColumn(format="%.2f"),
            "Fast Under 10 Seconds (%)":
                st.column_config.NumberColumn(format="%.2f%%"),
            "Median Potential Pre-Review Seconds per Case":
                st.column_config.NumberColumn(format="%.2f")
        }
    )


    # ========================================================
    # 13. LARGEST APPROVAL BLOCKS
    # ========================================================

    st.subheader("Largest Approval Blocks")

    number_of_blocks_to_show = st.sidebar.slider(
        "Number of largest blocks",
        min_value=5,
        max_value=30,
        value=15,
        step=1
    )

    # Select the largest blocks under the current filters.
    largest_blocks = (
        filtered_blocks
        .nlargest(
            number_of_blocks_to_show,
            "Cases_In_Block"
        )
        .copy()
    )

    # Create a readable block label.
    largest_blocks["Block Label"] = (
        largest_blocks["PROVIDER_APPROVING_NAME"]
        + " | Block "
        + largest_blocks["BLOCK_ID"].astype(str)
        + " | "
        + largest_blocks["Block_Start"].dt.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    largest_blocks_figure = px.bar(
        largest_blocks,
        x="Cases_In_Block",
        y="Block Label",
        color="PROVIDER_APPROVING_NAME",
        orientation="h",
        title=(
            f"Largest {number_of_blocks_to_show} Approval Blocks"
        ),
        labels={
            "Cases_In_Block": "Cases Approved in Block",
            "Block Label": "Approval Block",
            "PROVIDER_APPROVING_NAME": "Technician"
        },
        hover_data={
            "BLOCK_ID": True,
            "Block_Start": True,
            "Block_End": True,
            "Block_Duration_Minutes": ":,.2f",
            "Observed_Seconds_Per_Case": ":,.2f",
            "Fast_Under_10_Ratio": ":.2%",
            "Potential_PreReview_Seconds_Per_Case": ":,.2f",
            "Block Label": False
        },
        color_discrete_map={
            "Gary Arnold": "#EF553B",
            "Juan Mendez": "#636EFA",
            "Matt Shawn": "#00CC96"
        }
    )

    # Place the largest block at the top.
    largest_blocks_figure.update_yaxes(
        categoryorder="total ascending"
    )

    largest_blocks_figure.update_layout(
        height=max(
            500,
            number_of_blocks_to_show * 38
        ),
        legend_title_text="Technician",
        xaxis_title="Number of Cases",
        yaxis_title=""
    )

    st.plotly_chart(
        largest_blocks_figure,
        use_container_width=True
    )


    # ========================================================
    # 14. LARGEST-BLOCK DETAIL TABLE
    # ========================================================

    st.subheader("Largest Block Details")

    block_detail_table = largest_blocks[
        [
            "PROVIDER_APPROVING_NAME",
            "BLOCK_ID",
            "Block_Start",
            "Block_End",
            "Cases_In_Block",
            "Block_Duration_Minutes",
            "Observed_Seconds_Per_Case",
            "Fast_Under_10_Ratio",
            "Potential_PreReview_Seconds_Per_Case"
        ]
    ].copy()

    block_detail_table["Fast_Under_10_Ratio"] = (
        block_detail_table["Fast_Under_10_Ratio"] * 100
    )

    block_detail_table = block_detail_table.rename(
        columns={
            "PROVIDER_APPROVING_NAME": "Technician",
            "BLOCK_ID": "Block ID",
            "Block_Start": "Block Start",
            "Block_End": "Block End",
            "Cases_In_Block": "Cases in Block",
            "Block_Duration_Minutes": "Block Duration (Minutes)",
            "Observed_Seconds_Per_Case":
                "Observed Seconds per Case",
            "Fast_Under_10_Ratio":
                "Fast Under 10 Seconds (%)",
            "Potential_PreReview_Seconds_Per_Case":
                "Potential Pre-Review Seconds per Case"
        }
    )

    st.dataframe(
        block_detail_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Block ID":
                st.column_config.NumberColumn(format="%d"),
            "Cases in Block":
                st.column_config.NumberColumn(format="%d"),
            "Block Duration (Minutes)":
                st.column_config.NumberColumn(format="%.2f"),
            "Observed Seconds per Case":
                st.column_config.NumberColumn(format="%.2f"),
            "Fast Under 10 Seconds (%)":
                st.column_config.NumberColumn(format="%.2f%%"),
            "Potential Pre-Review Seconds per Case":
                st.column_config.NumberColumn(format="%.2f")
        }
    )


    # ========================================================
    # 15. BLOCK-ANALYSIS INTERPRETATION
    # ========================================================

    st.info(
        "Observed seconds per case measures approval activity occurring "
        "between the first and last approvals in a block. Potential "
        "pre-review seconds per case provides a generous estimate that "
        "allocates the preceding inactive gap across the cases in the "
        "block. Neither measure proves that a review occurred because "
        "the data contain approval timestamps rather than case-opening "
        "or review-start timestamps."
    )
# ============================================================
# 16. PAYOUT POLICY CHANGE
# ============================================================

st.markdown("---")
st.header("Payout Policy Change")

st.write(
    "The payout decreased from $50 to $17 per approval in June 2020. "
    "Gary Arnold is the only technician with records from both the "
    "pre-policy and post-policy periods."
)

policy_change_date = pd.Timestamp("2020-06-01")

# Use Gary's complete dataset for the policy comparison.
gary_policy_data = approvals[
    (approvals["PROVIDER_APPROVING_NAME"] == "Gary Arnold")
    & approvals["APPROVAL_DURATION_SEC"].notna()
    & (approvals["APPROVAL_DURATION_SEC"] >= 0)
].copy()

gary_policy_data["Policy Period"] = np.where(
    gary_policy_data["APPROVAL_DATE"] < policy_change_date,
    "Before June 2020 ($50)",
    "June 2020 and After ($17)"
)

# Restrict the principal comparison to within-block intervals.
# Gaps of 10 minutes or more represent new approval sessions.
gary_within_block = gary_policy_data[
    gary_policy_data["APPROVAL_DURATION_SEC"] < 600
].copy()

policy_summary = (
    gary_within_block
    .groupby("Policy Period")
    .agg(
        Approval_Intervals=("APPROVAL_DURATION_SEC", "size"),
        Mean_Seconds=("APPROVAL_DURATION_SEC", "mean"),
        Median_Seconds=("APPROVAL_DURATION_SEC", "median"),
        Fast_Under_5_Percent=(
            "APPROVAL_DURATION_SEC",
            lambda values: (values < 5).mean() * 100
        ),
        Fast_Under_10_Percent=(
            "APPROVAL_DURATION_SEC",
            lambda values: (values < 10).mean() * 100
        )
    )
    .reset_index()
)

policy_summary_display = policy_summary.rename(
    columns={
        "Policy Period": "Policy Period",
        "Approval_Intervals": "Approval Intervals",
        "Mean_Seconds": "Mean Seconds",
        "Median_Seconds": "Median Seconds",
        "Fast_Under_5_Percent": "Under 5 Seconds (%)",
        "Fast_Under_10_Percent": "Under 10 Seconds (%)"
    }
)

st.subheader("Before-and-After Summary")

st.dataframe(
    policy_summary_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Approval Intervals":
            st.column_config.NumberColumn(format="%d"),
        "Mean Seconds":
            st.column_config.NumberColumn(format="%.2f"),
        "Median Seconds":
            st.column_config.NumberColumn(format="%.2f"),
        "Under 5 Seconds (%)":
            st.column_config.NumberColumn(format="%.2f%%"),
        "Under 10 Seconds (%)":
            st.column_config.NumberColumn(format="%.2f%%")
    }
)
# ============================================================
# 17. PAYOUT POLICY VISUALIZATIONS
# ============================================================

policy_chart_1, policy_chart_2 = st.columns(2)

with policy_chart_1:
    median_policy_figure = px.bar(
        policy_summary,
        x="Policy Period",
        y="Median_Seconds",
        color="Policy Period",
        title="Median Approval Gap",
        labels={
            "Policy Period": "",
            "Median_Seconds": "Median Seconds"
        },
        color_discrete_map={
            "Before June 2020 ($50)": "#636EFA",
            "June 2020 and After ($17)": "#EF553B"
        }
    )

    median_policy_figure.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        median_policy_figure,
        use_container_width=True
    )

with policy_chart_2:
    fast_policy_figure = px.bar(
        policy_summary,
        x="Policy Period",
        y="Fast_Under_10_Percent",
        color="Policy Period",
        title="Approvals Under 10 Seconds",
        labels={
            "Policy Period": "",
            "Fast_Under_10_Percent":
                "Approvals Under 10 Seconds (%)"
        },
        color_discrete_map={
            "Before June 2020 ($50)": "#636EFA",
            "June 2020 and After ($17)": "#EF553B"
        }
    )

    fast_policy_figure.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        fast_policy_figure,
        use_container_width=True
    )
# ============================================================
# 18. PAYOUT T-TEST RESULTS
# ============================================================

st.subheader("Payout Policy T-Test Results")

st.write(
    "The two-sample Welch t-test evaluates whether Gary's mean "
    "approval duration changed after the payout reduction."
)

st.dataframe(
    payout_tests,
    use_container_width=True,
    hide_index=True
)

st.info(
    "For within-block approval intervals, the before-and-after "
    "difference is statistically significant, but the effect size is "
    "very small. Gary's median gap decreased from approximately "
    "5 seconds before the policy change to 4 seconds afterward, while "
    "the percentage of rapid approvals increased. This does not show "
    "that the lower payout improved review behavior."
)

st.warning(
    "The policy change occurred during a substantial gap in Gary's "
    "records. Therefore, the analysis identifies an association rather "
    "than proving that the payout reduction caused the behavioral change."
)
# ============================================================
# 19. FINAL CASE CONCLUSION
# ============================================================

st.markdown("---")
st.header("Overall Case Conclusion")

st.error(
    "Overall finding: The approval records support serious concern "
    "about inadequate review behavior—particularly for Gary Arnold—but "
    "approval timestamps alone cannot conclusively prove negligence."
)

st.subheader("Assessment by Technician")

conclusion_col_1, conclusion_col_2, conclusion_col_3 = st.columns(3)

with conclusion_col_1:
    st.markdown("### Gary Arnold")
    st.write(
        "Gary presents the strongest risk indicators. His approval "
        "durations are frequently only a few seconds, rapid approvals "
        "occur across multiple files and time periods, and many large "
        "approval blocks allow very little observed time per case."
    )

with conclusion_col_2:
    st.markdown("### Juan Mendez")
    st.write(
        "Juan generally demonstrates slower approval behavior than Gary "
        "and Matt. His median approval gap is longer and his proportion "
        "of extremely fast approvals is substantially lower. He provides "
        "the strongest comparison against a systematic rapid-approval pattern."
    )

with conclusion_col_3:
    st.markdown("### Matt Shawn")
    st.write(
        "Matt also demonstrates rapid approval behavior, although it is "
        "less extreme than Gary's. Conclusions about Matt should be more "
        "cautious because his records cover only one month and contain "
        "far fewer approvals."
    )
# ============================================================
# 21. NEGLIGENCE-CLAIM POSITION
# ============================================================

st.subheader("Position on the Negligence Claim")

st.markdown(
    """
    **Our results raise serious concerns about Gary’s approval behavior. His typical approval gap was only four seconds, and more than three-quarters of his measurable approvals occurred within ten seconds of the previous approval. However, we cannot conclude from timestamps alone that he failed to review the cases because the data do not show when each review began.**

    The evidence supports the claim because:

    - Gary has a sustained and unusually high rate of rapid approvals.
    - Many approvals occur only seconds apart.
    - The pattern appears across multiple dates and source files.
    - Large approval blocks often contain too little observed time for a
      conventional case-by-case review.
    - Gary's behavior is significantly different from Juan's behavior.
    - The payout reduction did not produce a meaningful improvement in
      review timing.

    The evidence does not conclusively prove negligence because:

    - Approval timestamps do not identify when review started.
    - Technicians may have pre-reviewed some cases.
    - The dataset contains no review-quality or error measurements.
    - The dataset includes approvals but no rejected cases.
    - The technicians have unequal observation periods.
    - Extremely skewed durations complicate mean-based statistical tests.
    """
)
# ============================================================
# 22. RECOMMENDATIONS
# ============================================================

st.subheader("Recommendations")
st.markdown(
    """
    1. **Conduct a targeted quality audit** of Gary's fastest approvals
       and largest approval blocks.

    2. **Compare approval speed with case outcomes**, including errors,
       reversals, complaints, security incidents, and failed updates.

    3. **Capture additional event timestamps**, such as case-open time,
       review-start time, document-view activity, and approval time.
        """
)
st.success(
    "Recommended decision: escalate Gary's records for detailed audit, "
    "continue monitoring Matt, and use Juan as a comparative benchmark. "
    "Gather more evidence before reaching a final legal conclusion."
)
