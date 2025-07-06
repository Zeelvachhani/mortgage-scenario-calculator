import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Mortgage Scenario Dashboard", layout="wide")

# --- Sidebar inputs ---
st.sidebar.title("🏠 Mortgage Parameters")

st.sidebar.markdown("Fields marked with * are required.")

def float_input(label, key, placeholder=""):
    val = st.sidebar.text_input(label, key=key, placeholder=placeholder)
    try:
        return float(val)
    except:
        return None

home_price = float_input("Home Price $ *", "home_price", "e.g. 300000")
hoa = float_input("HOA $", "hoa", "e.g. 250")
property_tax_rate = float_input("Property Tax %", "tax", "e.g. 1.2")
insurance_rate = float_input("Insurance %", "insurance", "e.g. 0.5")
pmi_rate = float_input("PMI %", "pmi", "e.g. 0.5")

cash_available = float_input("Cash Available $ *", "cash", "e.g. 80000")
min_down_pct = float_input("Min Down Payment %", "min_dp", "e.g. 5")
max_down_pct = float_input("Max Down Payment %", "max_dp", "e.g. 20")

interest_rate_base = float_input("Interest Rate % *", "rate", "e.g. 5")
loan_term = st.sidebar.number_input("Loan Term (Years) *", min_value=1, max_value=40, value=30)

monthly_liability = float_input("Monthly Liability $", "liability", "e.g. 500")
annual_income = float_input("Annual Income $ *", "income", "e.g. 85000")
max_dti = float_input("Max DTI % *", "dti", "e.g. 36")
max_monthly_expense = float_input("Max Monthly Expense $", "max_exp", "e.g. 2200")

calculate = st.sidebar.button("🔄 Calculate Scenarios")

# --- Helper Functions ---
def calculate_monthly_payment(loan_amount, interest_rate, years):
    r = interest_rate / 12
    n = years * 12
    if r == 0:
        return loan_amount / n
    return loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)

# Amortization Schedule Calculation
def amortization_schedule(loan_amt, rate, term_years):
    r = rate / 12
    n = term_years * 12
    balance = loan_amt
    schedule = []

    for month in range(1, n + 1):
        interest_payment = balance * r
        principal_payment = calculate_monthly_payment(loan_amt, rate, term_years) - interest_payment
        balance -= principal_payment
        schedule.append({
            'Month': month,
            'Principal Payment $': round(principal_payment, 2),
            'Interest Payment $': round(interest_payment, 2),
            'Remaining Balance $': round(balance, 2)
        })

    return pd.DataFrame(schedule)

def loan_details_table(df):
    """Generate the loan details table with amortization info for each loan scenario."""
    records = []
    for _, row in df.iterrows():
        loan_amt = row["Loan Amount $"]
        rate = row["Interest Rate %"] / 100
        # Use amortization schedule
        schedule = amortization_schedule(loan_amt, rate, loan_term)
        
        # Store amortization data into the loan details table
        for year in [5, 10, 15, 20, 25, 30]:
            remaining_balance = schedule[schedule['Month'] == year * 12]['Remaining Balance $'].values[0]
            total_interest_paid = schedule[schedule['Month'] == year * 12]['Interest Payment $'].sum()
            row[f"Remaining Balance end of Year {year} $"] = remaining_balance
            row[f"Total Interest in Year {year} $"] = total_interest_paid

        records.append(row)

    return pd.DataFrame(records)

# --- Main App Tabs ---
st.title("🏡 Mortgage Scenario Dashboard")
tab1, tab2 = st.tabs(["📊 Scenario Analysis", "📈 Loan Analysis"])

required_fields = [home_price, interest_rate_base, max_dti, annual_income, cash_available]

if calculate and all(field is not None and field > 0 for field in required_fields):
    property_tax_rate = (property_tax_rate or 0) / 100
    insurance_rate = (insurance_rate or 0) / 100
    pmi_rate = (pmi_rate or 0) / 100
    max_dti = max_dti / 100
    min_down_pct = (min_down_pct or 0) / 100
    max_down_pct = (max_down_pct or 100) / 100
    monthly_income = annual_income / 12

    results = []

    for points in range(0, 20):
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
        df = pd.DataFrame(results).reset_index(drop=True)
        df.index += 1

        with tab1:
            st.subheader("📊 Scenario Results")
            st.dataframe(
                df.style.format({
                    "Home Price $": "${:,.0f}",
                    "Down %": "{:.2f}%",
                    "Down $": "${:,.0f}",
                    "Loan Amount $": "${:,.0f}",
                    "Interest Rate %": "{:.2f}%",
                    "Discount Points": "{:,.0f}",
                    "Closing Cost $": "${:,.0f}",
                    "PMI $": "${:.2f}",
                    "Total Cash Used $": "${:,.0f}",
                    "Monthly P&I $": "${:.2f}",
                    "Total Monthly $": "${:.2f}",
                    "DTI %": "{:.2f}%"
                }).set_properties(**{'text-align': 'center'}),
                height=500 if len(df) > 12 else None
            )

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

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Scenarios as CSV", data=csv, file_name="mortgage_scenarios.csv", mime="text/csv")

        with tab2:
            st.subheader("📈 Loan Analysis (30-Year Term)")
            df_loan = loan_details_table(df.copy())
            numeric_cols = df_loan.select_dtypes(include='number').columns
            int_cols = [col for col in numeric_cols if 'Interest' in col or 'Payment' in col or 'Balance' in col or col in ["Home Price $", "Down $", "Loan Amount $", "Discount Points", "Closing Cost $", "Total Cash Used $"]]
            fmt = {col: "${:,.0f}" for col in int_cols}

            # Generate amortization table for hidden use
            amortization_data = []
            for _, row in df_loan.iterrows():
                loan_amt = row["Loan Amount $"]
                rate = row["Interest Rate %"] / 100
                schedule = amortization_schedule(loan_amt, rate, loan_term)

                # Store this hidden amortization data
                amortization_data.append(schedule)

            # Hidden data, will not be displayed
            st.empty()  # Hides the table for amortization

            # --- Remaining Balance vs Interest Paid chart ---
            st.subheader("📊 Remaining Balance & Interest Paid")
            time_years = [5, 10, 15, 20, 25, 30]
            for i, row in df_loan.iterrows():
                balance_data = [row[f"Remaining Balance end of Year {year} $"] for year in time_years]
                interest_data = [row[f"Total Interest in Year {year} $"] for year in time_years]

                fig, ax1 = plt.subplots(figsize=(10, 5))

                ax1.set_xlabel('Years')
                ax1.set_ylabel('Remaining Balance $', color='tab:blue')
                ax1.plot(time_years, balance_data, marker='o', color='tab:blue', label='Remaining Balance')
                ax1.tick_params(axis='y', labelcolor='tab:blue')

                ax2 = ax1.twinx()
                ax2.set_ylabel('Interest Paid $', color='tab:red')
                ax2.plot(time_years, interest_data, marker='s', color='tab:red', label='Interest Paid')
                ax2.tick_params(axis='y', labelcolor='tab:red')

                fig.tight_layout()
                st.pyplot(fig)

            csv_loan = df_loan.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Loan Analysis CSV", data=csv_loan, file_name="loan_analysis.csv", mime="text/csv")

    else:
        st.warning("No valid scenarios found based on your input.")

elif calculate:
    st.error("Please fill in all required fields: Home Price, Interest Rate, Annual Income, Max DTI, Cash Available.")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; font-size: 14px;">
    <p>✨ Crafted with care by <strong>Zeel Vachhani</strong> ✨</p>
    <p>© 2025 Zeel Vachhani. All rights reserved.</p>
    <p><em>This tool is for informational purposes only and should not be considered financial advice.</em></p>
</div>
""", unsafe_allow_html=True)
