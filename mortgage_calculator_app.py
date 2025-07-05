import streamlit as st

st.set_page_config(page_title="Mortgage Scenario Calculator", layout="wide")
st.title("🏠 Mortgage Scenario Calculator")
st.markdown("Enter your mortgage parameters below. Results will appear on the right.")

left_col, right_col = st.columns([1.5, 4])

# --- Helper input functions ---
def inline_number_input(label, key, required=True, **kwargs):
    col1, col2 = st.columns([2, 3], gap="small")  # Adjusted column widths
    asterisk = " <span style='color:red;'>*</span>" if required else ""
    col1.markdown(f"**{label}{asterisk}**", unsafe_allow_html=True)
    value = col2.number_input(label="", key=key, **kwargs)
    if not required:
        col2.markdown("<span style='font-size:0.85em; color:gray;'>(optional)</span>", unsafe_allow_html=True)
    return value

def inline_text_input(label, key, required=True):
    col1, col2 = st.columns([2, 3], gap="small")  # Adjusted column widths
    asterisk = " <span style='color:red;'>*</span>" if required else ""
    col1.markdown(f"**{label}{asterisk}**", unsafe_allow_html=True)
    value = col2.text_input(label="", key=key)
    if not required:
        col2.markdown("<span style='font-size:0.85em; color:gray;'>(optional)</span>", unsafe_allow_html=True)
    return value

# --- LEFT: Inputs ---
with left_col:
    st.subheader("📝 Input Parameters")

    home_price = inline_number_input("Home Price $", "home_price", min_value=0.0, step=10000.0)
    hoa = inline_number_input("HOA $", "hoa", min_value=0.0, step=10.0)
    property_tax_rate = inline_number_input("Property Tax %", "tax", min_value=0.0, step=0.1) / 100
    insurance_rate = inline_number_input("Insurance %", "insurance", min_value=0.0, step=0.1) / 100
    pmi_rate = inline_number_input("PMI %", "pmi", min_value=0.0, step=0.1) / 100

    cash_available = inline_number_input("Cash Available $", "cash", min_value=0.0, step=10000.0)
    min_down_str = inline_text_input("Min Down Payment %", "min_dp", required=False)
    max_down_str = inline_text_input("Max Down Payment %", "max_dp", required=False)
    interest_rate_base = inline_number_input("Interest Rate %", "rate", min_value=0.0, step=0.01) / 100
    loan_term = int(inline_number_input("Loan Term (Years)", "term", min_value=1, step=1, value=30))

    monthly_liability = inline_number_input("Monthly Liability $", "liability", min_value=0.0, step=100.0)
    annual_income = inline_number_input("Annual Income $", "income", min_value=0.0, step=10000.0)
    max_dti = inline_number_input("Max DTI %", "dti", min_value=0.0, max_value=100.0, step=1.0) / 100
    max_monthly_expense_str = inline_text_input("Max Monthly Expense $", "max_exp", required=False)

    calculate = st.button("🔄 Calculate Scenarios")
