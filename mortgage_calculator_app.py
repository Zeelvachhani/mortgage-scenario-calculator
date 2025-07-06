import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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

def loan_details_table(df):
    def interest_paid(loan, r, pmt, months):
        balance = loan
        interest = 0
        for _ in range(months):
            int_paid = balance * r
            principal = pmt - int_paid
            balance -= principal
            interest += int_paid
        return interest, balance

    records = []
    for i, row in df.iterrows():
        loan_amt = row["Loan Amount $"]
        rate = row["Interest Rate %"] / 100
        pmt = calculate_monthly_payment(loan_amt, rate, 30)
        pmi = row["PMI $"]
        total_pmt = pmt + pmi

        r = rate / 12

        for year in [5, 10, 15]:
            int_paid, rem_bal = interest_paid(loan_amt, r, pmt, year * 12)
            row[f"Total Payment in {year} Years (includes PMI if applicable) $"] = round(total_pmt * 12 * year)
            row[f"Total Interest in {year} Years $"] = round(int_paid)
            row[f"Remaining Balance end of Year {year} $"] = round(rem_bal)

        total_int, _ = interest_paid(loan_amt, r, pmt, 30 * 12)
        row["Total Payment (includes PMI if applicable) $"] = round(total_pmt * 360)
        row["Total Interest $"] = round(total_int)
        row["Loan ID"] = f"Loan {i+1}"
        records.append(row)

    return pd.DataFrame(records)

# --- Amortization Schedule Helper Function ---
def amortization_schedule(loan_amt, interest_rate, loan_term):
    r = interest_rate / 12  # Monthly interest rate
    n = loan_term * 12      # Total number of months
    schedule = []

    balance = loan_amt
    for month in range(1, n + 1):
        interest_paid = balance * r
        principal_paid = calculate_monthly_payment(loan_amt, interest_rate, loan_term) - interest_paid
        balance -= principal_paid
        schedule.append({
            "Month": month,
            "Principal Paid $": round(principal_paid, 2),
            "Interest Paid $": round(interest_paid, 2),
            "Remaining Balance $": round(balance, 2)
        })

    # Create a summary by year (each 12 months)
    yearly_schedule = []
    for year in range(1, loan_term + 1):
        year_months = year * 12
        year_schedule = [entry for entry in schedule if entry["Month"] <= year_months]
        total_principal_paid = sum(entry["Principal Paid $"] for entry in year_schedule)
        total_interest_paid = sum(entry["Interest Paid $"] for entry in year_schedule)
        remaining_balance = year_schedule[-1]["Remaining Balance $"] if year_schedule else loan_amt
        yearly_schedule.append({
            "Year": year,
            "Total Principal Paid $": round(total_principal_paid, 2),
            "Total Interest Paid $": round(total_interest_paid, 2),
            "Remaining Balance $": round(remaining_balance, 2)
        })

    return yearly_schedule

# --- Main App Tabs ---
st.title("🏡 Mortgage Scenario Dashboard")
tab1, tab2, tab3 = st.tabs(["📊 Scenario Analysis", "📈 Loan Analysis", "📊 Amortization Analysis"])

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

        with tab2:
            st.subheader("📈 Loan Analysis (30-Year Term)")
            df_loan = loan_details_table(df.copy())
            numeric_cols = df_loan.select_dtypes(include='number').columns
            int_cols = [col for col in numeric_cols if 'Interest' in col or 'Payment' in col or 'Balance' in col or col in ["Home Price $", "Down $", "Loan Amount $", "Discount Points", "Closing Cost $", "Total Cash Used $"]]
            fmt = {col: "${:,.0f}" for col in int_cols}
            st.dataframe(df_loan.style.format(fmt).set_properties(**{'text-align': 'center'}), height=500 if len(df_loan) > 12 else None)

        with tab3:
            st.subheader("📊 Amortization Schedule by Year")

            # Generate amortization schedule for each loan scenario
            amortization_data = []
            for i, row in df.iterrows():
                loan_amt = row["Loan Amount $"]
                rate = row["Interest Rate %"] / 100
                yearly_schedule = amortization_schedule(loan_amt, rate, loan_term)
                for year_data in yearly_schedule:
                    amortization_data.append({
                        "Loan ID": f"Loan {i+1}",
                        "Year": year_data["Year"],
                        "Total Principal Paid $": year_data["Total Principal Paid $"],
                        "Total Interest Paid $": year_data["Total Interest Paid $"],
                        "Remaining Balance $": year_data["Remaining Balance $"]
                    })

            # Create a DataFrame for amortization schedule
            df_amortization = pd.DataFrame(amortization_data)
            st.dataframe(df_amortization.style.format({
                "Total Principal Paid $": "${:,.0f}",
                "Total Interest Paid $": "${:,.0f}",
                "Remaining Balance $": "${:,.0f}"
            }).set_properties(**{'text-align': 'center'}), height=500 if len(df_amortization) > 12 else None)

            # Chart for Remaining Balance and Interest Paid for Key Scenarios Only
            # Find the key scenarios to display
            highest_down_payment = df.loc[df["Down %"].idxmax()]
            lowest_interest_rate = df.loc[df["Interest Rate %"].idxmin()]
            highest_discount_points = df.loc[df["Discount Points"].idxmax()]
            lowest_monthly_pni = df.loc[df["Monthly P&I $"].idxmin()]

            scenarios = [highest_down_payment, lowest_interest_rate, highest_discount_points, lowest_monthly_pni]

            fig, ax1 = plt.subplots(figsize=(10, 5))
            color = 'tab:blue'
            ax1.set_xlabel('Year')
            ax1.set_ylabel('Remaining Balance $', color=color)

            # Plot lines for the selected scenarios
            for scenario in scenarios:
                loan_amt = scenario["Loan Amount $"]
                rate = scenario["Interest Rate %"] / 100
                yearly_schedule = amortization_schedule(loan_amt, rate, loan_term)

                ax1.plot(
                    [year_data["Year"] for year_data in yearly_schedule],
                    [year_data["Remaining Balance $"] for year_data in yearly_schedule],
                    label=f"Loan ID {scenario['Loan ID']} Remaining Balance"
                )

            ax1.tick_params(axis='y', labelcolor=color)

            ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
            color = 'tab:red'
            ax2.set_ylabel('Interest Paid $', color=color)

            # Plot lines for interest paid
            for scenario in scenarios:
                loan_amt = scenario["Loan Amount $"]
                rate = scenario["Interest Rate %"] / 100
                yearly_schedule = amortization_schedule(loan_amt, rate, loan_term)

                ax2.plot(
                    [year_data["Year"] for year_data in yearly_schedule],
                    [year_data["Total Interest Paid $"] for year_data in yearly_schedule],
                    label=f"Loan ID {scenario['Loan ID']} Interest Paid",
                    linestyle='--'
                )

            ax2.tick_params(axis='y', labelcolor=color)

            fig.tight_layout()  # make sure there is no clipping
            ax1.legend(loc='upper left')
            ax2.legend(loc='upper right')
            st.pyplot(fig)

            # Add option to download the amortization schedule
            csv_amortization = df_amortization.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Amortization Schedule CSV", data=csv_amortization, file_name="amortization_schedule.csv", mime="text/csv")

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
