import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Mortgage Scenario Calculator", layout="wide")
st.title("🏡 Mortgage Scenario Calculator")
st.markdown("Enter your mortgage parameters below. Results will appear on the right.")

left_col, right_col = st.columns([1, 2])

# --- LEFT: Inputs ---
with left_col:
    st.subheader("📅 Input Parameters")

    home_price = st.number_input("Home Price $:", key="home_price", min_value=0.0, step=1000.0)
    hoa = st.number_input("HOA $:", key="hoa", min_value=0.0, step=10.0)
    property_tax_rate = st.number_input("Property Tax %:", key="tax", min_value=0.0, step=0.1) / 100
    insurance_rate = st.number_input("Insurance %:", key="insurance", min_value=0.0, step=0.1) / 100
    pmi_rate = st.number_input("PMI %:", key="pmi", min_value=0.0, step=0.1) / 100

    cash_available = st.number_input("Cash Available $:", key="cash", min_value=0.0, step=1000.0)
    min_down_str = st.text_input("Min Down Payment % (optional):", key="min_dp")
    max_down_str = st.text_input("Max Down Payment % (optional):", key="max_dp")
    interest_rate_base = st.number_input("Interest Rate %:", key="rate", min_value=0.0, step=0.01) / 100
    loan_term = int(st.number_input("Loan Term (Years):", key="term", min_value=1, step=1, value=30))

    monthly_liability = st.number_input("Monthly Liability $:", key="liability", min_value=0.0, step=100.0)
    annual_income = st.number_input("Annual Income $:", key="income", min_value=0.0, step=1000.0)
    max_dti = st.number_input("Max DTI %:", key="dti", min_value=0.0, max_value=100.0, step=1.0) / 100
    max_monthly_expense_str = st.text_input("Max Monthly Expense $ (optional):", key="max_exp")

    calculate = st.button("🔍 Calculate Scenarios")

try:
    min_down_pct = float(min_down_str) / 100 if min_down_str else 0.0
except:
    st.warning("Min Down Payment % must be a number.")
    min_down_pct = 0.0

try:
    max_down_pct = float(max_down_str) / 100 if max_down_str else 1.0
except:
    st.warning("Max Down Payment % must be a number.")
    max_down_pct = 1.0

try:
    max_monthly_expense = float(max_monthly_expense_str.replace(',', '')) if max_monthly_expense_str else None
except:
    st.warning("Max Monthly Expense must be a number.")
    max_monthly_expense = None

def calculate_monthly_payment(loan_amount, interest_rate, years):
    r = interest_rate / 12
    n = years * 12
    return loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)

# --- RIGHT: Results ---
with right_col:
    if calculate:
        monthly_income = annual_income / 12
        results = []

        for points in range(0, 11):
            discount = points * 0.0025
            adjusted_rate = interest_rate_base - discount

            for dp_pct in np.arange(min_down_pct, max_down_pct + 0.01, 0.01):
                down_payment = home_price * dp_pct
                loan_amt = home_price - down_payment
                closing_cost = loan_amt * (points * 0.01)
                total_cash = down_payment + closing_cost

                if total_cash > cash_available:
                    continue

                principal_interest = calculate_monthly_payment(loan_amt, adjusted_rate, loan_term)
                property_tax = (home_price * property_tax_rate) / 12
                insurance = home_price * insurance_rate / 12
                pmi = (loan_amt * pmi_rate / 12) if dp_pct < 0.20 else 0
                total_monthly = principal_interest + property_tax + hoa + insurance + pmi
                dti = (total_monthly + monthly_liability) / monthly_income

                if (max_monthly_expense is None or total_monthly <= max_monthly_expense) and dti <= max_dti:
                    results.append({
                        "Home Price $": round(home_price),
                        "Down %": f"{dp_pct * 100:.1f}%",
                        "Down $": round(down_payment),
                        "Loan Amount $": round(loan_amt),
                        "Interest Rate %": f"{adjusted_rate * 100:.3f}%",
                        "Discount Points": points,
                        "Closing Cost $": round(closing_cost),
                        "PMI $": f"{pmi:.2f}",
                        "Total Cash Used $": round(total_cash),
                        "Monthly P&I $": f"{principal_interest:.2f}",
                        "Total Monthly $": f"{total_monthly:.2f}",
                        "DTI %": f"{dti * 100:.2f}"
                    })

        if results:
            st.subheader("📊 Best Scenarios")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📅 Download as CSV",
                data=csv,
                file_name="mortgage_scenarios.csv",
                mime="text/csv"
            )

            st.subheader("\ud83d\udcd8 How Calculations Work")
            st.markdown("""
            **Key Formulas Used:**

            - **Monthly P&I** = \( \frac{P \cdot r \cdot (1 + r)^n}{(1 + r)^n - 1} \)
            - **Total Monthly Payment** = P&I + PMI + Insurance + Property Tax + HOA
            - **DTI** = (Total Monthly + Monthly Liabilities) / (Annual Income ÷ 12)
            - **PMI** only applies if Down Payment < 20%
            - **Closing Costs** = Loan Amount × Discount Points × 1%
            """)

        else:
            st.warning("No valid scenarios found based on your input.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; font-size: 14px;">
    <p>✨ Crafted with care by <strong>Zeel Vachhani</strong> ✨</p>
    <p>© 2025 Zeel Vachhani. All rights reserved.</p>
    <p><em>This tool is for informational purposes only and should not be considered financial advice.</em></p>
</div>
""", unsafe_allow_html=True)
