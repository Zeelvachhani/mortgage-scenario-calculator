import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Mortgage Scenario Calculator", layout="wide")
st.title("\U0001F3E1 Mortgage Scenario Calculator")
st.markdown("Enter your mortgage parameters below. Results will appear on the right.")

left_col, right_col = st.columns([1.5, 4])

# --- Helper input functions with required flag ---
def inline_number_input(label, key, required=True, **kwargs):
    col1, col2 = st.columns([1.5, 2.5], gap="small")
    label_text = f"<span style='font-weight:600;'>{label}{' <span style=\"color:red;\">*</span>' if required else ''}</span>"
    col1.markdown(label_text, unsafe_allow_html=True)
    return col2.number_input(label="", key=key, **kwargs)

def inline_text_input(label, key, required=True):
    col1, col2 = st.columns([1.5, 2.5], gap="small")
    label_text = f"<span style='font-weight:600;'>{label}{' <span style=\"color:red;\">*</span>' if required else ''}</span>"
    col1.markdown(label_text, unsafe_allow_html=True)
    return col2.text_input(label="", key=key)

# --- LEFT: Inputs ---
with left_col:
    st.subheader("\U0001F4DD Input Parameters")

    home_price = inline_number_input("Home Price $:", "home_price", min_value=0.0, step=1000.0)
    hoa = inline_number_input("HOA $:", "hoa", min_value=0.0, step=10.0)
    property_tax_rate = inline_number_input("Property Tax %:", "tax", min_value=0.0, step=0.1) / 100
    insurance_rate = inline_number_input("Insurance %:", "insurance", min_value=0.0, step=0.1) / 100
    pmi_rate = inline_number_input("PMI %:", "pmi", min_value=0.0, step=0.1) / 100

    cash_available = inline_number_input("Cash Available $:", "cash", min_value=0.0, step=1000.0)
    min_down_str = inline_text_input("Min Down Payment %:", "min_dp", required=False)
    max_down_str = inline_text_input("Max Down Payment %:", "max_dp", required=False)
    interest_rate_base = inline_number_input("Interest Rate %:", "rate", min_value=0.0, step=0.01) / 100
    loan_term = int(inline_number_input("Loan Term (Years):", "term", min_value=1, step=1, value=30))

    monthly_liability = inline_number_input("Monthly Liability $:", "liability", min_value=0.0, step=100.0)
    annual_income = inline_number_input("Annual Income $:", "income", min_value=0.0, step=1000.0)
    max_dti = inline_number_input("Max DTI %:", "dti", min_value=0.0, max_value=100.0, step=1.0) / 100
    max_monthly_expense_str = inline_text_input("Max Monthly Expense $:", "max_exp", required=False)

    calculate = st.button("\U0001F504 Calculate Scenarios")

# --- Validate optional text inputs ---
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

# --- Calculation logic ---
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
            st.subheader("\U0001F4D8 Results")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="\U0001F4E5 Download as CSV",
                data=csv,
                file_name="mortgage_scenarios.csv",
                mime="text/csv"
            )

            st.subheader("\U0001F4D8 How Calculations Work")
            st.markdown("""
            **How Monthly P&I is Calculated:**

            The **Principal & Interest (P&I)** part of your mortgage payment is calculated based on the following:

            1. **Loan Amount** (P) = The total amount you're borrowing.
            2. **Monthly Interest Rate** (r) = The annual interest rate divided by 12.
            3. **Number of Payments** (n) = The number of months in your loan term (e.g., for a 30-year loan, it’s 360 months).

            The formula is:

            **Monthly P&I = (Loan Amount × Monthly Interest Rate × (1 + Monthly Interest Rate) ^ Number of Payments) ÷ ((1 + Monthly Interest Rate) ^ Number of Payments - 1)**

            ### Example:
            - Borrowing $200,000 at 5% for 30 years gives a monthly P&I of ~$1,073.

            **Discount Points:**
            - Each point equals 1% of your loan amount. More points = lower interest.

            **Closing Costs:**
            - Estimated as a percentage of the loan amount.

            **DTI (Debt-to-Income Ratio):**
            - DTI = (Total Monthly Payments + Monthly Liabilities) ÷ Monthly Income

            **Total Monthly Payment:**
            - Includes P&I, taxes, insurance, HOA, and PMI (if applicable).
            """)

        else:
            st.warning("No valid scenarios found based on your input.")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; font-size: 14px;">
    <p>✨ Crafted with care by <strong>Zeel Vachhani</strong> ✨</p>
    <p>© 2025 Zeel Vachhani. All rights reserved.</p>
    <p><em>This tool is for informational purposes only and should not be considered financial advice.</em></p>
</div>
""", unsafe_allow_html=True)
