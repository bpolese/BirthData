import streamlit as st
import pandas as pd

# Safe Plotly import handling (STEP 9 requirement: never crash)
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ModuleNotFoundError:
    PLOTLY_AVAILABLE = False

# STEP 2 — Page Config
st.set_page_config(layout="wide")
st.title("Provisional Natality Data Dashboard")
st.subheader("Birth Analysis by State and Gender")

# STEP 3 — Load Data
try:
    df = pd.read_csv("Provisional_Natality_2025_CDC.csv")
except FileNotFoundError:
    st.error("Dataset file not found in repository.")
    st.stop()
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()

# Normalize column names
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Required logical fields
required_fields = [
    "state_of_residence",
    "month",
    "month_code",
    "year_code",
    "sex_of_infant",
    "births"
]

missing_fields = [field for field in required_fields if field not in df.columns]
if missing_fields:
    st.error(f"Missing required logical fields: {missing_fields}")
    st.write(df.columns)
    st.stop()

# Convert births to numeric
df["births"] = pd.to_numeric(df["births"], errors="coerce")
df = df.dropna(subset=["births"])

# STEP 4 — Sidebar Filters
st.sidebar.header("Filters")

month_options = ["All"] + sorted(df["month"].dropna().unique().tolist())
gender_options = ["All"] + sorted(df["sex_of_infant"].dropna().unique().tolist())
state_options = ["All"] + sorted(df["state_of_residence"].dropna().unique().tolist())

selected_months = st.sidebar.multiselect(
    "Select Month(s)",
    options=month_options,
    default=["All"]
)

selected_genders = st.sidebar.multiselect(
    "Select Gender(s)",
    options=gender_options,
    default=["All"]
)

selected_states = st.sidebar.multiselect(
    "Select State(s)",
    options=state_options,
    default=["All"]
)

# STEP 5 — Filtering Logic
filtered_df = df.copy()

if "All" not in selected_months:
    filtered_df = filtered_df[filtered_df["month"].isin(selected_months)]

if "All" not in selected_genders:
    filtered_df = filtered_df[filtered_df["sex_of_infant"].isin(selected_genders)]

if "All" not in selected_states:
    filtered_df = filtered_df[filtered_df["state_of_residence"].isin(selected_states)]

# STEP 9 — Edge Case Handling
if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

try:
    # STEP 6 — Aggregation
    aggregated_df = (
        filtered_df
        .groupby(["state_of_residence", "sex_of_infant"], as_index=False)["births"]
        .sum()
        .sort_values(by="state_of_residence")
    )

    if aggregated_df.empty:
        st.warning("No aggregated results available after filtering.")
        st.stop()

    # STEP 7 — Plot (with graceful fallback)
    if PLOTLY_AVAILABLE:
        fig = px.bar(
            aggregated_df,
            x="state_of_residence",
            y="births",
            color="sex_of_infant",
            title="Total Births by State and Gender",
            labels={
                "state_of_residence": "State",
                "births": "Total Births",
                "sex_of_infant": "Gender"
            }
        )

        fig.update_layout(
            template="plotly_white",
            legend_title_text="Gender",
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Plotly is not installed in this environment. Please add 'plotly' to requirements.txt.")
        st.stop()

    # STEP 8 — Show Filtered Table
    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

except Exception as e:
    st.error(f"An unexpected error occurred while rendering the dashboard: {e}")
    st.stop()
