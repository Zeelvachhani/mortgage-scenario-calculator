import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Mortgage Scenario Dashboard", layout="wide")

# --- Sidebar inputs ---
st.sidebar.title("🏠 Mortgage Parameters")

home_price = st.sidebar.number_input("Home Price $:", min_value=0.0, step=10000.0, value=300000.0)
hoa = st.sidebar.number_input("HOA $:", min_value=0.0, step=10.0, value=200.0)
property_tax_rate = st.sidebar.number_input("Property Tax %:", min_value=0.0, step=0.1, value=1.2) / 100
insurance_rate = st.sidebar.number_input("Insurance %:", min_value=0.0, step=0.1, value=0.5) / 100
pmi_rate = st.sidebar.number_input("PMI %:", min_value=0.0, step=0.1, value=0.5) / 100

cash_available = st.sidebar.number_input("Cash Available $:", min_value=0.0, step=10000.0, value=80000.0)
min_down_pct = st.sidebar.number_input("Min Down Payment %:", min_value=0.0, max_value=100.0, value=5.0) / 100
max_down_pct = st.sidebar.number_input("Max Down Payment %:", min_value=0.0, max_value=100.0, value=20.0) / 100

interest_rate_base = st.sidebar.number_input("Interest Rate %:", min_value=0.0, step=0.01, value=4.0) / 100
loan_term = st.sidebar.number_input("Loan Term (Years):", min_value=1, max_value=40, value=30)

monthly_liability = st.sidebar.number_input("Monthly Liability $:", min_value=0.0, step=100.0, value=500.0)
annual_income = st.sidebar.number_input("Annual Income $:", min_value=0.0, step=10000.0, value=85000.0)
max_dti = st.sidebar.number_input("Max DTI %:", min_value=0.0, max_value=100.0, step=1.0, value=36.0) / 100
max_monthly_expense = st.sidebar.number_input("Max Monthly Expense $ (Optional):", min_value=0.0, step=100.0, value=0.0)
max_monthly_expense = max_monthly_expense if max_monthly_expense > 0 else None

calculate = st.sidebar.button("🔄 Calculate Scenarios")

# --- Helper function ---
def calculate_monthly_payment(loan_amount, interest_rate, years):
    r = interest_rate / 12
    n = years * 12
    if r == 0:
        return loan_amount / n
    return loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)

# --- Main ---
st.title("🏡 Mortgage Scenario Dashboard")

if calculate:
    monthly_income = annual_income / 12 if annual_income > 0 else 1
    results = []

    for points in range(0, 11):  # Discount points 0 to 10
        discount = points * 0.0025
        adjusted_rate = interest_rate_base - discount

        for dp_pct in np.arange(min_down_pct, max_down_pct + 0.005, 0.005):
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

        # --- Interactive Data Table ---
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

        # --- Line Chart: Monthly Payment vs Down Payment % ---
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

else:
    st.info("Adjust parameters in the sidebar and click 'Calculate Scenarios' to view results.")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; font-size: 14px;">
    <p>✨ Crafted with care by <strong>Zeel Vachhani</strong> ✨</p>
    <p>© 2025 Zeel Vachhani. All rights reserved.</p>
    <p><em>This tool is for informational purposes only and should not be considered financial advice.</em></p>
</div>
""", unsafe_allow_html=True)
