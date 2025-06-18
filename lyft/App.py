import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Driver LTV Prediction", layout="wide")
st.title("🚗 Driver Lifetime Value (LTV) Prediction - Lyft Case Study")

# --- File Uploads ---
st.sidebar.header("Upload Data Files")
driver_file = st.sidebar.file_uploader("Upload driver_ids.csv", type="csv")
ride_file = st.sidebar.file_uploader("Upload ride_ids.csv", type="csv")
timestamp_file = st.sidebar.file_uploader("Upload ride_timestamps.csv", type="csv")

if driver_file and ride_file and timestamp_file:
    driver_df = pd.read_csv(driver_file)
    ride_df = pd.read_csv(ride_file)
    ts_df = pd.read_csv(timestamp_file)

    # --- Process Timestamps ---
    ts_df['timestamp'] = pd.to_datetime(ts_df['timestamp'])
    dropoff_df = ts_df[ts_df['event'] == 'dropped_off_at']
    ride_df = pd.merge(ride_df, dropoff_df[['ride_id', 'timestamp']], on='ride_id', how='left')
    ride_df.rename(columns={'timestamp': 'dropoff_time'}, inplace=True)

    # --- Merge Driver Info ---
    ride_driver_df = pd.merge(ride_df, driver_df, on='driver_id', how='left')
    ride_driver_df['driver_onboard_date'] = pd.to_datetime(ride_driver_df['driver_onboard_date'])
    ride_driver_df['dropoff_time'] = pd.to_datetime(ride_driver_df['dropoff_time'])

    # --- Revenue Estimation ---
    BASE_FARE = 2.00
    PER_MILE = 1.15 / 1609.34  # meters to miles
    PER_MIN = 0.22 / 60
    SERVICE_FEE = 1.75
    MIN_FARE = 5.00

    ride_driver_df['estimated_revenue'] = (
        BASE_FARE +
        PER_MILE * ride_driver_df['ride_distance'] +
        PER_MIN * ride_driver_df['ride_duration'] +
        (ride_driver_df['ride_prime_time'] / 100) * (
            BASE_FARE + PER_MILE * ride_driver_df['ride_distance'] + PER_MIN * ride_driver_df['ride_duration']
        ) - SERVICE_FEE
    )
    ride_driver_df['estimated_revenue'] = ride_driver_df['estimated_revenue'].clip(lower=MIN_FARE)

    # --- Weekly Aggregates ---
    ride_driver_df = ride_driver_df.dropna(subset=['dropoff_time']).copy()
    ride_driver_df['week'] = ride_driver_df['dropoff_time'].dt.to_period('W').apply(lambda r: r.start_time if pd.notnull(r) else pd.NaT)
    ride_driver_df['onboard_week'] = ride_driver_df['driver_onboard_date'].dt.to_period('W').apply(lambda r: r.start_time if pd.notnull(r) else pd.NaT)

    # --- LTV Metrics ---
    revenue_per_driver = ride_driver_df.groupby('driver_id')['estimated_revenue'].mean().reset_index(name='avg_ride_revenue')
    rides_per_week = ride_driver_df.groupby('driver_id')['ride_id'].count().div(12).reset_index(name='rides_per_week')
    lifespan_weeks = ride_driver_df.groupby('driver_id').agg({
        'dropoff_time': lambda x: (x.max() - x.min()).days / 7
    }).reset_index().rename(columns={'dropoff_time': 'lifespan_weeks'})

    ltv_df = revenue_per_driver.merge(rides_per_week, on='driver_id')
    ltv_df = ltv_df.merge(lifespan_weeks, on='driver_id')
    ltv_df['driver_ltv'] = ltv_df['avg_ride_revenue'] * ltv_df['rides_per_week'] * ltv_df['lifespan_weeks']

    # --- Display LTV Table ---
    st.subheader("🔍 Driver Lifetime Value Table")
    st.dataframe(ltv_df.sort_values(by='driver_ltv', ascending=False).round(2))

    # --- Bar Chart: Top 10 LTV Drivers ---
    st.subheader("📊 Top 10 Drivers by LTV")
    top10 = ltv_df.sort_values(by='driver_ltv', ascending=False).head(10)
    fig, ax = plt.subplots()
    ax.barh(top10['driver_id'], top10['driver_ltv'], color='mediumseagreen')
    ax.set_xlabel('Driver LTV')
    ax.set_ylabel('Driver ID')
    ax.invert_yaxis()
    st.pyplot(fig)

    # --- Cohort Retention ---
    st.subheader("📈 Driver Cohort Retention Over Time")
    cohort = ride_driver_df.groupby(['onboard_week', 'week'])['driver_id'].nunique().reset_index(name='active_drivers')
    cohort_size = ride_driver_df.groupby('onboard_week')['driver_id'].nunique().reset_index(name='cohort_size')
    cohort = pd.merge(cohort, cohort_size, on='onboard_week')
    cohort['pct_active'] = (cohort['active_drivers'] / cohort['cohort_size']) * 100

    for cohort_week in cohort['onboard_week'].unique():
        df = cohort[cohort['onboard_week'] == cohort_week]
        st.line_chart(df.set_index('week')['pct_active'], height=250, use_container_width=True)

    # --- Lookup Section ---
    st.markdown("## 🔍 Lookup Driver Details")
    driver_ids = ltv_df['driver_id'].unique()
    selected_driver_id = st.selectbox("Select a Driver ID", driver_ids)

    selected_driver = ltv_df[ltv_df['driver_id'] == selected_driver_id]
    driver_rides = ride_driver_df[ride_driver_df['driver_id'] == selected_driver_id]

    if not selected_driver.empty:
        st.subheader("📊 Driver Metrics:")
        st.metric("Lifetime Value (LTV)", f"${selected_driver['driver_ltv'].values[0]:.2f}")
        st.metric("Avg Ride Revenue", f"${selected_driver['avg_ride_revenue'].values[0]:.2f}")
        st.metric("Rides Per Week", f"{selected_driver['rides_per_week'].values[0]:.2f}")
        st.metric("Lifespan (Weeks)", f"{selected_driver['lifespan_weeks'].values[0]:.0f}")

        st.subheader("📅 Weekly Ride Summary:")
        weekly_summary = driver_rides.groupby('week').agg(
            num_rides=('ride_id', 'count'),
            total_distance=('ride_distance', 'sum'),
            total_duration=('ride_duration', 'sum')
        ).reset_index()

        st.dataframe(weekly_summary)

        st.write("### 📈 Weekly Ride Count Chart")
        fig, ax = plt.subplots()
        sns.barplot(data=weekly_summary, x='week', y='num_rides', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("No data available for the selected driver.")

    # --- Download Option ---
    csv = ltv_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download LTV Results as CSV", csv, "driver_ltv_results.csv", "text/csv")
else:
    st.info("Please upload all three data files to get started.")