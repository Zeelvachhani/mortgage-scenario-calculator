import streamlit as st
import pandas as pd
import numpy as np
from streamlit.components.v1 import html

st.set_page_config(page_title="Mortgage Scenario Calculator", layout="wide")
st.title("🏠 Mortgage Scenario Calculator")
st.markdown("Enter your mortgage parameters below. Results will appear on the right.")

left_col, right_col = st.columns([1.5, 4])

# --- HTML Inline Input Component ---
def inline_html_input(label, key, input_type="number", required=True, placeholder="", default=""):
    star = '<span style="color:red;">*</span>' if required else ""
    ui = f"""
    <div style="display:flex; align-items:center; margin-bottom:12px;">
      <label for="{key}" style="width:180px; font-weight:600; padding-right:10px;">{label}{star}</label>
      <input id="{key}" name="{key}" type="{input_type}" placeholder="{placeholder}" value="{default}"
             style="flex:1; min-width:120px; padding:6px 10px; border:1px solid #ccc; border-radius:4px; box-sizing:border-box;" />
    </div>
    <script>
      const el = window.document.getElementById("{key}");
      if (el) {{
        el.addEventListener('input', () => {{
          window.parent.postMessage({{isStreamlitMessage: true, type: 'streamlit:setComponentValue', key: '{key}', value: el.value}}, '*');
        }});
      }}
    </script>
    """
    html(ui, height=50)

# --- Inputs on the left panel ---
with left_col:
    st.subheader("📝 Input Parameters")

    # numeric fields
    for label, key, default in [
        ("Home Price $", "home_price", "300000"),
        ("HOA $", "hoa", "200"),
        ("Property Tax %", "tax", "1.2"),
        ("Insurance %", "insurance", "0.5"),
        ("PMI %", "pmi", "0.3"),
        ("Cash Available $", "cash", "60000"),
        ("Interest Rate %", "rate", "5.0"),
        ("Loan Term (Years)", "term", "30"),
        ("Monthly Liability $", "liability", "0"),
        ("Annual Income $", "income", "100000"),
        ("Max DTI %", "dti", "43")
    ]:
        inline_html_input(label, key, input_type="number", required=True, default=default)

    # optional fields
    inline_html_input("Min Down Payment %", "min_dp", input_type="number", required=False)
    inline_html_input("Max Down Payment %", "max_dp", input_type="number", required=False)
    inline_html_input("Max Monthly Expense $", "max_exp", input_type="number", required=False)

    calculate = st.button("🔄 Calculate Scenarios")

# --- Retrieve values from session_state ---
def get_val(key, numeric=True, default=0.0):
    val = st.session_state.get(key, "")
    try:
        return float(val) if numeric else val
    except:
        return default

home_price = get_val("home_price")
hoa = get_val("hoa")
property_tax_rate = get_val("tax") / 100
insurance_rate = get_val("insurance") / 100
pmi_rate = get_val("pmi") / 100
cash_available = get_val("cash")
interest_rate_base = get_val("rate") / 100
loan_term = int(get_val("term", default=30))
monthly_liability = get_val("liability")
annual_income = get_val("income")
max_dti = get_val("dti") / 100

min_down_pct = get_val("min_dp") / 100 if st.session_state.get("min_dp") else 0.0
max_down_pct = get_val("max_dp") / 100 if st.session_state.get("max_dp") else 1.0
max_monthly_expense = get_val("max_exp", numeric=True) if st.session_state.get("max_exp") else None

# --- Calculation ---
def calculate_monthly_payment(P, annual_rate, years):
    r = annual_rate / 12
    n = years * 12
    return P * r * (1 + r) ** n / ((1 + r) ** n - 1)

# --- Results on the right panel ---
with right_col:
    if calculate:
        monthly_income = annual_income / 12
        results = []
        for points in range(11):
            discount = points * 0.0025
            rate_adj = interest_rate_base - discount
            for dp in np.arange(min_down_pct, max_down_pct + 0.01, 0.01):
                down = home_price * dp
                loan_amt = home_price - down
                closing = loan_amt * (points * 0.01)
                if down + closing > cash_available:
                    continue
                pi = calculate_monthly_payment(loan_amt, rate_adj, loan_term)
                prop_tax = home_price * property_tax_rate / 12
                ins = home_price * insurance_rate / 12
                pmi_val = loan_amt * pmi_rate / 12 if dp < 0.20 else 0
                total_m = pi + prop_tax + hoa + ins + pmi_val
                dti = (total_m + monthly_liability) / monthly_income
                if (max_monthly_expense is None or total_m <= max_monthly_expense) and dti <= max_dti:
                    results.append({
                        "Down %": f"{dp*100:.1f}%",
                        "Rate %": f"{rate_adj*100:.3f}%",
                        "Loan $": round(loan_amt),
                        "Monthly $": f"{total_m:.2f}",
                        "DTI %": f"{dti*100:.2f}"
                    })
        if results:
            st.subheader("📊 Results")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No valid scenarios found based on your input.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; font-size:14px; color:#555;">
        ✨ Crafted with care by <strong>You</strong> ✨
    </div>
    """,
    unsafe_allow_html=True,
)
