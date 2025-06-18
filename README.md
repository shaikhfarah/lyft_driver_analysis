# 🚗 Driver Lifetime Value (LTV) Prediction - Lyft Case Study

This Streamlit web app is a case study focused on predicting the **Lifetime Value (LTV)** of Lyft drivers using real ride and driver data. It allows users to upload CSV datasets, visualize performance metrics, and inspect driver-specific insights.

---

## 📌 Objective

To calculate and visualize the **Lifetime Value (LTV)** of drivers based on their ride history.

**Formula Used:**
LTV = Average Ride Revenue × Rides per Week × Lifespan (in weeks)

![image](https://github.com/user-attachments/assets/52500e07-6207-4665-9947-7dee0407ba81)

### 1. 📊 LTV Table View
![image](https://github.com/user-attachments/assets/9480563e-3c03-4ab8-b895-1bd0f5f5b3c1)

### 2. 🔍 Individual Driver Lookup

![image](https://github.com/user-attachments/assets/ea6810b1-d3a3-420a-9fd5-18d9531fe3e5)

## 📁 Expected CSV Files
Upload these three CSVs in the app interface:

- `driver_ids.csv` — Contains unique driver IDs
- `ride_ids.csv` — Contains ride-level data like duration and distance
- `ride_timestamps.csv` — Contains timestamp details for each ride

---

## ⚙️ Features

- Upload custom CSVs
- Automatically computes:
  - Lifetime Value (LTV)
  - Avg. Ride Revenue
  - Rides per Week
  - Lifespan in Weeks
- Lookup specific drivers by ID
- View weekly ride summaries

---

## 💻 Technologies Used

- **Python**
- **Streamlit** – Web App Framework
- **Pandas, NumPy** – Data Processing
- **CSV files** – Input Format

---

## ▶️ Run Locally

```bash
pip install streamlit pandas numpy 
streamlit run App.py

