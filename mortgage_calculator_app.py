import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Mortgage Scenario Calculator", layout="wide")
st.title("🏡 Mortgage Scenario Calculator")
st.markdown("Enter your mortgage parameters below. Leave any field blank if not applicable.")

# Input fields
col1, col2, col3 = st.columns(3)

with col1:
    home_price = st.number_input("Home Price $", min_value=0.0, step=1000.0, format="%.2f")
    hoa = st.number_input("HOA $", min_value=0.0, step=10.0, format="%.2f")
    property_tax_rate = st.number_input("Property Tax %", min_value=0.0, step=0.1, format="%.2f") / 100
    insurance_rate = st.number_input("Insurance %", min_value=0.0, step=0.1, format="%.2f") / 100
    pmi_rate = st.number_input("PMI %", min_value=0.0, step=0.1, format="%.2f") / 100

with col2:
    cash_available = st.number_input("Cash Available $", min_value=0.0, step=1000.0, format="%.2f")

    min_down_str = st.text_input("Min Down Payment % (optional)", "")
    max_down_str = st.text_input("Max Down Payment % (optional)", "")
    interest_rate_base = st.number_input("Interest Rate %", min_value=0.0, step=0.1, format="%.3f") / 100
    loan_term = st.number_input("Loan Term (Years)", min_value=1, step=1, value=30)

with col3:
    monthly_liability = st.number_input("Monthly Liability $", min_value=0.0, step=100.0, format="%.2f")
    annual_income = st.number_input("Annual Income $", min_value=0.0, step=1000.0, format="%.2f")
    max_dti = st.number_input("Max DTI %", min_value=0.0, max_value=100.0, step=1.0, format="%.2f") / 100
    max_monthly_expense_str = st.text_input("Max Monthly Expense $ (optional)", "")

# Convert optional inputs safely
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

# Monthly payment formula
def calculate_monthly_payment(loan_amount, interest_rate, years):
    r = interest_rate / 12
    n = years * 12
    return loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)

# Button to calculate
if st.button("Calculate Scenarios"):
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
                    "DTI %": f"{dti * 100:.2f}",
                    "Details": {
                        "dp_pct": dp_pct,
                        "adjusted_rate": adjusted_rate,
                        "principal_interest": principal_interest,
                        "property_tax": property_tax,
                        "insurance": insurance,
                        "pmi": pmi,
                        "dti": dti,
                        "total_monthly": total_monthly
                    }
                })

    if results:
        df = pd.DataFrame(results).drop(columns="Details")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download results as Excel (CSV)",
            data=csv,
            file_name="mortgage_scenarios.csv",
            mime="text/csv"
        )

        # Show calculation breakdowns
        st.subheader("📘 Detailed Calculation Explanation")
        for i, r in enumerate(results[:10]):  # show top 10 results with details
            with st.expander(f"📄 Scenario {i+1}: {r['Down %']} down, {r['Interest Rate %']}"):
                d = r["Details"]
                st.markdown(f"""
                **Home Price:** ${home_price:,.0f}  
                **Down Payment ({r['Down %']}):** ${r['Down $']:,.0f}  
                **Loan Amount:** ${r['Loan Amount $']:,.0f}  
                **Interest Rate (after {r['Discount Points']} points):** {r['Interest Rate %']}  
                **Closing Cost:** ${r['Closing Cost $']:,.0f}  
                **PMI:** ${r['PMI $']}  
                **Monthly Principal & Interest:** ${d['principal_interest']:.2f}  
                **Property Tax:** ${d['property_tax']:.2f}  
                **Insurance:** ${d['insurance']:.2f}  
                **HOA:** ${hoa:.2f}  
                **Total Monthly Payment:** ${d['total_monthly']:.2f}  
                **Debt-to-Income (DTI):** {d['dti']*100:.2f}%
                """)
    else:
        st.warning("No valid scenarios found based on your input.")

# Footer with signature and disclaimer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; font-size: 14px;">
        <p>✨ Crafted with care by <strong>Zeel Vachhani</strong> ✨</p>
        <p>© 2025 Zeel Vachhani. All rights reserved.</p>
        <p><em>This tool is for informational purposes only and should not be considered financial advice.</em></p>
    </div>
    """,
    unsafe_allow_html=True
)
