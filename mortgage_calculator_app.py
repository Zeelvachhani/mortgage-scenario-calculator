import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder

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


# Required inputs with *
home_price = float_input("Home Price $", "home_price", "e.g. 300000", required=True)
hoa = float_input("HOA $", "hoa", "e.g. 250", required=True)
property_tax_rate = float_input("Property Tax %", "tax", "e.g. 1.2", required=True)
insurance_rate = float_input("Insurance %", "insurance", "e.g. 0.5", required=True)
pmi_rate = float_input("PMI %", "pmi", "e.g. 0.5", required=True)
interest_rate_base = float_input("Interest Rate %", "rate", "e.g. 5", required=True)
loan_term = st.sidebar.number_input("Loan Term (Years) *", min_value=1, max_value=40, value=30)

cash_available = float_input("Cash Available $", "cash", "e.g. 80000", required=True)
monthly_liability = float_input("Monthly Liability $", "liability", "e.g. 500", required=True)
annual_income = float_input("Annual Income $", "income", "e.g. 85000", required=True)
max_dti = float_input("Max DTI %", "dti", "e.g. 36", required=True)


# Optional inputs (no *)
min_down_pct = float_input("Min Down Payment %", "min_dp", "e.g. 5")
max_down_pct = float_input("Max Down Payment %", "max_dp", "e.g. 20")
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

# --- Amortization Schedule Function ---
def amortization_schedule(loan_amount, interest_rate, loan_term):
    """Generate amortization schedule for a given loan."""
    monthly_payment = calculate_monthly_payment(loan_amount, interest_rate, loan_term)
    balance = loan_amount
    r = interest_rate / 12
    amortization_data = []

    for year in range(1, loan_term + 1):
        total_principal_paid = 0
        total_interest_paid = 0
        for month in range(12):
            interest_payment = balance * r
            principal_payment = monthly_payment - interest_payment
            balance -= principal_payment
            total_interest_paid += interest_payment
            total_principal_paid += principal_payment
        
        amortization_data.append({
            "Year": year,
            "Total Principal Paid $": total_principal_paid,
            "Total Interest Paid $": total_interest_paid,
            "Remaining Balance $": balance
        })

    return amortization_data

# --- Main App Tabs ---
st.title("🏡 Mortgage Scenario Dashboard")
tab1, tab2, tab3 = st.tabs(["📊 Scenario Analysis", "📈 Loan Analysis", "📉 Amortization Analysis"])

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

            st.subheader("📘 How Calculations Work")

            st.markdown("""
            #### 📌 Monthly Principal & Interest (P&I)
            The monthly **Principal & Interest (P&I)** payment is calculated using the standard amortization formula:

            Monthly Payment = (P × r × (1 + r)^n) / ((1 + r)^n - 1)
                       
            Where:
            - **P** = Loan Amount  
            - **r** = Monthly Interest Rate (Annual Rate ÷ 12)  
            - **n** = Total Number of Payments (Loan Term in Months)
            
            #### 🔍 Example:
            A loan of **$200,000** at an interest rate of **5%** over a **30-year term** results in an estimated monthly P&I payment of approximately **$1,073**.
            
            ---
            
            #### 💡 Discount Points
            - Discount points are optional upfront fees paid to reduce the interest rate on a loan.
            - In this tool:
              - **1 point** is equal to **1% of the loan amount**.
              - Each point reduces the base interest rate by **0.25%**.
              - More points result in a lower interest rate, but increase initial closing costs.
              - **Cost = Loan Amount × (Discount Points × 1%)**
              - **Interest Rate Reduction = Discount Points × 0.25%**
            
            ---
            
            #### 💰 Closing Costs
            - Closing costs are estimated as a percentage of the loan amount.
            - In this model, closing costs are derived from the number of discount points:
              - **Closing Cost = Loan Amount × (Discount Points × 1%)**
            
            ---
            
            #### 📊 Debt-to-Income Ratio (DTI)
            - The **DTI ratio** is a key factor in mortgage qualification.
            - **Formula:**  

            DTI = (Total Monthly Housing Costs + Monthly Liabilities) / Monthly Gross Income

            - A lower DTI indicates a more favorable financial position.
            - Many lenders prefer a DTI of **36% or less**.
            
            ---
            
            #### 💸 Total Monthly Payment Includes:
            - **Principal & Interest (P&I)**  
            - **Property Taxes**  
            - **Homeowner’s Insurance**  
            - **HOA Fees** (if applicable)  
            - **PMI (Private Mortgage Insurance)** — applies when the down payment is less than 20%
            """)
            

        with tab2:
            st.subheader("📈 Loan Analysis (30-Year Term)")
            st.markdown("""
                        <style>
                        /* Wrap headers for Loan Analysis table */
                        .css-1q2zygl th {
                            white-space: normal !important;
                            word-wrap: break-word !important;
                            text-align: center !important;
                            vertical-align: middle !important;
                            max-width: 140px;
                            font-size: 13px;
                            padding: 8px;
                        }
                        </style>
                        """, unsafe_allow_html=True)

            df_loan = loan_details_table(df.copy())
            df_loan.index = range(1, len(df_loan) + 1)  # Set index starting from 1
            numeric_cols = df_loan.select_dtypes(include='number').columns
            int_cols = [col for col in numeric_cols if 'Interest' in col or 'Payment' in col or 'Balance' in col or col in ["Home Price $", "Down $", "Loan Amount $", "Discount Points", "Closing Cost $", "Total Cash Used $"]]
            fmt = {}
            for col in df_loan.columns:
                if col in ["PMI $", "Monthly P&I $", "Total Monthly $"]:
                    fmt[col] = "${:,.2f}"
                elif col in ["Down %", "Interest Rate %", "DTI %"]:
                    fmt[col] = "{:,.2f}%"
                elif col in ["Home Price $", "Loan Amount $", "Down $", "Closing Cost $", "Total Cash Used $", 
                             "Total Payment (includes PMI if applicable) $", "Total Interest $"] or \
                             "Payment" in col or "Interest" in col or "Balance" in col:
                    fmt[col] = "${:,.0f}"
                elif col in ["Discount Points"]:
                    fmt[col] = "{:,.0f}"

            # Compute dynamic height
            max_height = "600px" if len(df_loan) > 15 else "auto"



            df_loan = loan_details_table(df.copy())
            df_loan.index = range(1, len(df_loan) + 1)  # Set index starting from 1
            
            # Build grid options with sorting, filtering, resizing enabled
            # gb = GridOptionsBuilder.from_dataframe(df_loan.drop(columns=["Loan ID"]))
            # gb.configure_default_column(sortable=True, filter=True, resizable=True, min_width=250, header_class="header-wrap-center")
            
            # # Increase header height (set to 60 pixels)
            # gb.configure_grid_options(headerHeight=60)
            
            # gridOptions = gb.build()
            
            # AgGrid(
            #     df_loan.drop(columns=["Loan ID"]),
            #     gridOptions=gridOptions,
            #     enable_enterprise_modules=False,
            #     height=500 if len(df_loan) > 12 else None,
            #     fit_columns_on_grid_load=True,
            # )
            
           

            st.dataframe(
                df_loan.drop(columns=["Loan ID"]).style
                .format(fmt)
                .set_properties(**{'text-align': 'center'}),
                height=500 if len(df_loan) > 12 else None
             )
           
            
            # Inject scrollable container and wrapped headers
            # st.markdown(f"""
            #     <style>
            #     .scroll-table-container {{
            #         max-height: {max_height};
            #         overflow-y: auto;
            #         border: 1px solid #ccc;
            #         padding: 0;
            #     }}
            #     table {{
            #         width: 100%;
            #         table-layout: auto;
            #         border-collapse: collapse;
            #     }}
            #     th {{
            #         word-wrap: break-word;
            #         white-space: normal;
            #         text-align: center !important; 
            #         vertical-align: middle !important;
            #         font-size: 13px;
            #         padding: 6px;
            #         background-color: #f0f0f0;
            #         border: 1px solid #ddd;
            #         min-width: 140px;
            #     }}
            #     td {{
            #         text-align: center;
            #         font-size: 13px;
            #         padding: 6px;
            #         border: 1px solid #eee;
            #         min-width: 140px;
            #     }}
            #     </style>
            # """, unsafe_allow_html=True)
            
            # Format your DataFrame
            # styled_df = df_loan.drop(columns=["Loan ID"]).copy()
            # for col, f in fmt.items():
            #     if col in styled_df.columns:
            #         styled_df[col] = styled_df[col].map(lambda x: f.format(x) if pd.notnull(x) else "")
            
            # # Show the table in a scrollable container
            # st.markdown(f'<div class="scroll-table-container">{styled_df.to_html(index=True, escape=False)}</div>', unsafe_allow_html=True)

           
            csv_loan = df_loan.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Loan Analysis CSV", data=csv_loan, file_name="loan_analysis.csv", mime="text/csv")

        with tab3:
            st.subheader("📉 Amortization Schedule by Year")

            # Generate amortization schedule for each loan scenario
            amortization_data = []
            for i, row in df.iterrows():
                loan_amt = row["Loan Amount $"]
                rate = row["Interest Rate %"] / 100
                yearly_schedule = amortization_schedule(loan_amt, rate, loan_term)
                for year_data in yearly_schedule:
                    amortization_data.append({
                        "Loan ID": i,  # Numeric Loan ID
                        "Home Price $": round(home_price),  # Home Price formatted to 0 decimal places
                        "Loan Amount $": round(loan_amt),  # Loan Amount formatted to 0 decimal places
                        "Down Payment $": round(down_payment),  # Down Payment formatted to 0 decimal places
                        "PMI $": round(pmi, 2),  # PMI formatted to 2 decimal places
                        "Year": year_data["Year"],
                        "Total Principal Paid $": year_data["Total Principal Paid $"],
                        "Total Interest Paid $": year_data["Total Interest Paid $"],
                        "Remaining Balance $": year_data["Remaining Balance $"]
                    })

            # Create a DataFrame for amortization schedule
            df_amortization = pd.DataFrame(amortization_data)

            # Ensure the first column in df_amortization is 1-based index
            df_amortization.index = range(1, len(df_amortization) + 1)
            
            st.dataframe(df_amortization.style.format({
                "Home Price $": "${:,.0f}",  # Home Price formatted to 0 decimals
                "Loan Amount $": "${:,.0f}",  # Loan Amount formatted to 0 decimals
                "Down Payment $": "${:,.0f}",  # Down Payment formatted to 0 decimals
                "PMI $": "${:,.2f}",  # PMI formatted to 2 decimals
                "Total Principal Paid $": "${:,.0f}",
                "Total Interest Paid $": "${:,.0f}",
                "Remaining Balance $": "${:,.0f}"
            }).set_properties(**{'text-align': 'center'}), height=500 if len(df_amortization) > 12 else None)

            # Add option to download the amortization schedule
            csv_amortization = df_amortization.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Amortization Schedule CSV", data=csv_amortization, file_name="amortization_schedule.csv", mime="text/csv")
    
            # Reset the DataFrame index so that it starts from 1
            df_amortization.index = range(1, len(df_amortization) + 1)  # Fix: Starts from 1
        
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
