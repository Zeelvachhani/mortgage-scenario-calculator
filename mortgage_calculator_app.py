import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Mortgage Scenario Dashboard", layout="wide")

# --- Sidebar inputs ---
st.sidebar.title("🏠 Mortgage Parameters")

st.sidebar.markdown("**Note:** Leave fields blank if unsure.")

# Using text_input to allow blank defaults, then converting later
def float_input(label, key, placeholder=""):
    val = st.sidebar.text_input(label, key=key, placeholder=placeholder)
    try:
        return float(val)
    except:
        return None

home_price = float_input("Home Price $:", "home_price", "e.g. 300000")
hoa = float_input("HOA $:", "hoa", "e.g. 250")
property_tax_rate = float_input("Property Tax %:", "tax", "e.g. 1.2")
insurance_rate = float_input("Insurance %:", "insurance", "e.g. 0.5")
pmi_rate = float_input("PMI %:", "pmi", "e.g. 0.5")

cash_available = float_input("Cash Available $:", "cash", "e.g. 80000")
min_down_pct = float_input("Min Down Payment %:", "min_dp", "e.g. 5")
max_down_pct = float_input("Max Down Payment %:", "max_dp", "e.g. 20")

interest_rate_base = float_input("Interest Rate %:", "rate", "e.g. 5")
loan_term = st.sidebar.number_input("Loan Term (Years):", min_value=1, max_value=40, value=30)

monthly_liability = float_input("Monthly Liability $:", "liability", "e.g. 500")
annual_income = float_input("Annual Income $:", "income", "e.g. 85000")
max_dti = float_input("Max DTI %:", "dti", "e.g. 36")
max_monthly_expense = float_input("Max Monthly Expense $ (Optional):", "max_exp", "e.g. 2200")

calculate = st.sidebar.button("🔄 Calculate Scenarios")

# --- Helper function ---
def calculate_monthly_payment(loan_amount, interest_rate, years):
    r = interest_rate / 12
    n = years * 12
    if r == 0:
        return loan_amount / n
    return loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)

# --- Main App ---
st.title("🏡 Mortgage Scenario Dashboard")

required_fields = [home_price, interest_rate_base, max_dti, annual_income]
if calculate and all(field is not None and field > 0 for field in required_fields):
    # Convert percentages
    property_tax_rate = (property_tax_rate or 0) / 100
    insurance_rate = (insurance_rate or 0) / 100
    pmi_rate = (pmi_rate or 0) / 100
    max_dti = max_dti / 100
    min_down_pct = (min_down_pct or 0) / 100
    max_down_pct = (max_down_pct or 100) / 100
    monthly_income = annual_income / 12

    results = []

    for points in range(0, 11):  # Discount points 0 to 10
        discount = points * 0.0025
        adjusted_rate = interest_rate_base / 100 - discount

        for dp_pct in np.arange(min_down_pct, max_down_pct + 0.005, 0.005):
            down_payment = home_price * dp_pct
            loan_amt = home_price - down_payment
            closing_cost = loan_amt * (points * 0.01)
            total_cash = down_payment + closing_cost

            if cash_available is not None and total_cash > cash_available:
                continue

            principal_interest = calculate_monthly_payment(loan_amt, adjusted_rate, loan_term)
            property_tax = (home_price * property_tax_rate) / 12
            insurance = home_price * insurance_rate / 12
            pmi = (loan_amt * pmi_rate / 12) if dp_pct < 0.20 else 0
            total_monthly = principal_interest + (hoa or 0) + property_tax + insurance + pmi
            dti = (total_monthly + (monthly_liability or 0)) / monthly_income

            if (max_monthly_expense is None or total_monthly <= max_monthly_expense) and dti <= max_dti:
                results.append({
                    "Home Price $": round(home_price),
                    "Down %": round(dp_pct * 100, 2),
                    "Down $": round(down_payment),
                    "Loan Amount $": round(loan_amt),
                    "Interest Rate %": round(adjusted_rate * 100, 3),
                    "Discount Points": points,
                    "Closing Cost $": round(closing_cost),
                    "PMI $": round(pmi, 2),
                    "Total Cash Used $": round(total_cash),
                    "Monthly P&I $": round(principal_interest, 2),
                    "Total Monthly $": round(total_monthly, 2),
                    "DTI %": round(dti * 100, 2)
                })

    if results:
        df = pd.DataFrame(results)

        # --- Summary Cards ---
        best_payment = df.loc[df["Total Monthly $"].idxmin()]
        best_dti = df.loc[df["DTI %"].idxmin()]
        best_cash = df.loc[df["Total Cash Used $"].idxmin()]

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Lowest Monthly Payment", f"${best_payment['Total Monthly $']:,}")
        col2.metric("📉 Best Debt-to-Income Ratio", f"{best_dti['DTI %']:.2f}%")
        col3.metric("💵 Lowest Total Cash Used", f"${best_cash['Total Cash Used $']:,}")

        # --- Data Table ---
        st.subheader("📊 Scenario Results")
        st.dataframe(df.style.format({
            "Home Price $": "${:,.0f}",
            "Down $": "${:,.0f}",
            "Loan Amount $": "${:,.0f}",
            "Interest Rate %": "{:.3f}%",
            "Closing Cost $": "${:,.0f}",
            "PMI $": "${:.2f}",
            "Total Cash Used $": "${:,.0f}",
            "Monthly P&I $": "${:.2f}",
            "Total Monthly $": "${:.2f}",
            "DTI %": "{:.2f}%",
        }), height=400)

        # --- Line Chart ---
        st.subheader("📈 Monthly Payment vs Down Payment % by Discount Points")
        fig, ax = plt.subplots(figsize=(10, 5))

        for points in df["Discount Points"].unique():
            subset = df[df["Discount Points"] == points]
            ax.plot(subset["Down %"], subset["Total Monthly $"], marker='o', label=f"{points} points")

        ax.set_xlabel("Down Payment %")
        ax.set_ylabel("Total Monthly Payment $")
        ax.set_title("Monthly Payment vs Down Payment %")
        ax.legend(title="Discount Points")
        ax.grid(True)
        st.pyplot(fig)

        # --- Download button ---
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Scenarios as CSV",
            data=csv,
            file_name="mortgage_scenarios.csv",
            mime="text/csv"
        )


    else:
        st.warning("No valid scenarios found based on your input.")

    # --- Explanation section ---
    st.subheader("📘 How Calculations Work")
    st.markdown("""
    **How Monthly P&I is Calculated:**

    The **Principal & Interest (P&I)** part of your mortgage payment is calculated based on the following:

    1. **Loan Amount** (P) = The total amount you're borrowing.
    2. **Monthly Interest Rate** (r) = The annual interest rate divided by 12.
    3. **Number of Payments** (n) = The number of months in your loan term (e.g., for a 30-year loan, it’s 360 months).

    The formula is:

    **Monthly P&I = (Loan Amount × Monthly Interest Rate × (1 + Monthly Interest Rate)^n) ÷ ((1 + Monthly Interest Rate)^n - 1)**

    ### Example:
    - Borrowing $200,000 at 5% for 30 years gives a monthly P&I of ~$1,073.

    **Discount Points:**
    - Each point equals 1% of your loan amount. More points = lower interest.

    **Closing Costs:**
    - Estimated as a percentage of the loan amount (based on discount points).

    **DTI (Debt-to-Income Ratio):**
    - DTI = (Total Monthly Payments + Monthly Liabilities) ÷ Monthly Income

    **Total Monthly Payment:**
    - Includes P&I, taxes, insurance, HOA, and PMI (if applicable).
    """)

elif calculate:
    st.error("Please fill in all required fields: Home Price, Interest Rate, Annual Income, Max DTI.")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; font-size: 14px;">
    <p>✨ Crafted with care by <strong>Zeel Vachhani</strong> ✨</p>
    <p>© 2025 Zeel Vachhani. All rights reserved.</p>
    <p><em>This tool is for informational purposes only and should not be considered financial advice.</em></p>
</div>
""", unsafe_allow_html=True)

