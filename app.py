import streamlit as st
import pandas as pd
import plotly.express as px

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

# Normalize column names
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Logical field mapping
required_logical_fields = {
    "state_of_residence": ["state_of_residence", "state", "residence_state"],
    "month": ["month"],
    "sex_of_infant": ["sex_of_infant", "sex", "gender"],
    "births": ["births", "birth"]
}

column_mapping = {}

for logical_name, possible_names in required_logical_fields.items():
    found = None
    for name in possible_names:
        if name in df.columns:
            found = name
            break
    if not found:
        for col in df.columns:
            for name in possible_names:
                if name in col:
                    found = col
                    break
            if found:
                break
    if found:
        column_mapping[logical_name] = found

missing_fields = [field for field in required_logical_fields if field not in column_mapping]

if missing_fields:
    st.error(f"Missing required logical fields: {missing_fields}")
    st.write("Available columns:", df.columns)
    st.stop()

# Rename columns for internal consistency
df = df.rename(columns={
    column_mapping["state_of_residence"]: "state_of_residence",
    column_mapping["month"]: "month",
    column_mapping["sex_of_infant"]: "sex_of_infant",
    column_mapping["births"]: "births"
})

# Convert births to numeric
df["births"] = pd.to_numeric(df["births"], errors="coerce")
df = df.dropna(subset=["births"])

# STEP 4 — Sidebar Filters
st.sidebar.header("Filters")

month_options = ["All"] + sorted(df["month"].dropna().astype(str).unique())
gender_options = ["All"] + sorted(df["sex_of_infant"].dropna().astype(str).unique())
state_options = ["All"] + sorted(df["state_of_residence"].dropna().astype(str).unique())

selected_months = st.sidebar.multiselect("Select Month(s)", month_options, default=["All"])
selected_genders = st.sidebar.multiselect("Select Gender(s)", gender_options, default=["All"])
selected_states = st.sidebar.multiselect("Select State(s)", state_options, default=["All"])

# STEP 5 — Filtering Logic
filtered_df = df.copy()

if "All" not in selected_months:
    filtered_df = filtered_df[filtered_df["month"].astype(str).isin(selected_months)]

if "All" not in selected_genders:
    filtered_df = filtered_df[filtered_df["sex_of_infant"].astype(str).isin(selected_genders)]

if "All" not in selected_states:
    filtered_df = filtered_df[filtered_df["state_of_residence"].astype(str).isin(selected_states)]

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# STEP 6 — Aggregation
aggregated_df = (
    filtered_df
    .groupby(["state_of_residence", "sex_of_infant"], as_index=False)["births"]
    .sum()
    .sort_values("state_of_residence")
)

# STEP 7 — Plot
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
    xaxis_title="State",
    yaxis_title="Total Births",
    autosize=True
)

st.plotly_chart(fig, use_container_width=True)

# STEP 8 — Show Filtered Table
display_columns = ["state_of_residence", "month", "sex_of_infant", "births"]
available_display_columns = [col for col in display_columns if col in filtered_df.columns]

st.dataframe(
    filtered_df[available_display_columns].reset_index(drop=True),
    use_container_width=True
)
