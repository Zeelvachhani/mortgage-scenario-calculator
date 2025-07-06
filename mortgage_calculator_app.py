import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Mortgage Scenario Dashboard", layout="wide")

# --- Sidebar inputs ---
st.sidebar.title("🏠 Mortgage Parameters")
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

calculate = st.sidebar.button("🔄 Calculate Scenarios")

# --- Explanation Section ---
st.markdown("""
### 📘 How Calculations Work

#### 🧮 Monthly Principal & Interest (P&I)
The **monthly mortgage payment** (excluding taxes and fees) is calculated using this formula:

**Monthly P&I = (Loan Amount × Monthly Interest Rate × (1 + Monthly Interest Rate)^n) ÷ ((1 + Monthly Interest Rate)^n - 1)**

Where:
- **Loan Amount** = Principal borrowed  
- **Monthly Interest Rate** = Annual Rate ÷ 12  
- **n** = Total number of payments (loan term × 12)

#### 🔢 Example
- Borrowing **$200,000** at **5%** for **30 years** results in a monthly P&I of approximately **$1,073**

#### 💸 Discount Points
- Each point = **1%** of the loan amount  
  - Example: 2 points on $200,000 = $4,000  
- **Buying points** reduces your interest rate

#### 💼 Closing Costs
- Estimated as a **percentage of the loan amount**, based on how many discount points you select

#### 💡 DTI (Debt-to-Income Ratio)
- **Formula:** (Total Monthly Housing Payment + Monthly Liabilities) ÷ Monthly Income  
- Lenders prefer a DTI ≤ your maximum allowed (e.g., 36%)

#### 💵 Total Monthly Payment Includes:
- Principal & Interest  
- Property Tax  
- Homeowner’s Insurance  
- HOA Fees (if any)  
- PMI (if down payment < 20%)
""")
