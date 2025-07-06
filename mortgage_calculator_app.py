import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Mortgage Scenario Dashboard", layout="wide")

# --- Sidebar inputs ---
st.sidebar.title("\U0001F3E0 Mortgage Parameters")

st.sidebar.markdown("Fields marked with * are required.")

def float_input(label, key, placeholder="", required=False):
    if required:
        label += " *"
    val = st.sidebar.text_input(label, key=key, placeholder=placeholder)
    try:
        return float(val)
    except:
        return None

home_price = float_input("Home Price $", "home_price", "e.g. 300000", required=True)
hoa = float_input("HOA $", "hoa", "e.g. 250")
property_tax_rate = float_input("Property Tax %", "tax", "e.g. 1.2")
insurance_rate = float_input("Insurance %", "insurance", "e.g. 0.5")
pmi_rate = float_input("PMI %", "pmi", "e.g. 0.5")

cash_available = float_input("Cash Available $", "cash", "e.g. 80000", required=True)
min_down_pct = float_input("Min Down Payment %", "min_dp", "e.g. 5")
max_down_pct = float_input("Max Down Payment %", "max_dp", "e.g. 20")

interest_rate_base = float_input("Interest Rate %", "rate", "e.g. 5", required=True)
loan_term = st.sidebar.number_input("Loan Term (Years) *", min_value=1, max_value=40, value=30)

monthly_liability = float_input("Monthly Liability $", "liability", "e.g. 500")
annual_income = float_input("Annual Income $", "income", "e.g. 85000", required=True)
max_dti = float_input("Max DTI %", "dti", "e.g. 36", required=True)
max_monthly_expense = float_input("Max Monthly Expense $", "max_exp", "e.g. 2200")

calculate = st.sidebar.button("\U0001F504 Calculate Scenarios")

# The rest of the code remains unchanged...

# (The rest of the script is unchanged and follows your original logic)
