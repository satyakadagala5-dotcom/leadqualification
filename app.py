import io
import pandas as pd
import streamlit as st




from database import (
    initialize_database,
    add_lead,
    get_connection,
    update_sql_conditions,)




from workflow import process_lead

# Initialize database
initialize_database()

# Streamlit page setup
st.set_page_config(
    page_title="Lead Qualification Agent",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Lead Qualification Agent")
st.caption("Manage leads, qualify SQLs, and export appointments.")

# ---------------- ADD LEAD ----------------
st.header("Add New Lead")

with st.form("add_lead_form"):
    lead_id = st.text_input("Lead ID")
    name = st.text_input("Lead Name")
    phone = st.text_input("WhatsApp Phone Number")
    opt_in = st.checkbox("The lead has consented to receive WhatsApp messages")
    interest = st.checkbox("Requirement interest confirmed")
    call_answered = st.checkbox("Call answered confirmed")

    submitted = st.form_submit_button("Add Lead")

    if submitted:
        if not lead_id.strip() or not phone.strip():
            st.error("Lead ID and phone number are required.")
        elif not opt_in:
            st.warning(
                "Record the lead only when you have a lawful basis to do so. "
                "WhatsApp follow-ups require appropriate consent and opt-in."
            )
        else:
            added = add_lead(
                lead_id=lead_id.strip(),
                name=name.strip(),
                phone=phone.strip(),
                requirement_interest=interest,
                call_answered=call_answered,
                opt_in=opt_in,
            )

            if added:
                st.success("Lead added successfully.")
            else:
                st.info("Lead ID already exists. Check the existing lead record.")

# ---------------- UPDATE CONDITIONS ----------------
st.divider()
st.header("Update Lead Qualification")

with get_connection() as connection:
    rows = connection.execute("""
        SELECT lead_id, name, phone, lead_status
        FROM leads
        ORDER BY lead_id
    """).fetchall()

lead_options = [
    f"{row['lead_id']} — {row['name'] or 'Unnamed'}"
    for row in rows
]

if lead_options:
    selected = st.selectbox("Select a lead", lead_options)
    selected_id = selected.split(" — ", 1)[0]

    with get_connection() as connection:
        lead = connection.execute(
            "SELECT * FROM leads WHERE lead_id = ?",
            (selected_id,),
        ).fetchone()

    with st.form("qualification_form"):
        interest = st.checkbox(
            "Requirement interest",
            value=bool(lead["requirement_interest"]),
        )
        response = st.checkbox(
            "WhatsApp reply received",
            value=bool(lead["whatsapp_sms_response"]),
        )
        answered = st.checkbox(
            "Call answered",
            value=bool(lead["call_answered"]),
        )

        update = st.form_submit_button("Save and Qualify Lead")

        if update:
            status = update_sql_conditions(
                selected_id,
                requirement_interest=interest,
                whatsapp_sms_response=response,
                call_answered=answered,
            )

            result = process_lead(selected_id)

            if status == "SQL":
                st.success("Lead qualified as SQL. Ready for appointment processing.")
            elif status == "OPTED_OUT":
                st.warning("Lead has opted out.")
            else:
                st.info("Lead remains MQL.")
                st.caption("Schedule a follow-up if the lead is eligible.")

# ---------------- LEAD TABLE ----------------
st.divider()
st.header("All Leads")

with get_connection() as connection:
    df = pd.read_sql_query(
        "SELECT * FROM leads ORDER BY lead_id DESC",
        connection,
    )

if not df.empty:
    sql_count = int((df["lead_status"] == "SQL").sum())
    mql_count = int((df["lead_status"] == "MQL").sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Leads", len(df))
    col2.metric("MQL Leads", mql_count)
    col3.metric("SQL Leads", sql_count)

    st.dataframe(df, use_container_width=True)

    # Export SQL records for the appointment agent.
    sql_df = df[df["lead_status"] == "SQL"].copy()

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        sql_df.to_excel(writer, index=False, sheet_name="SQL Leads")

    st.download_button(
        label="Download SQL Leads as Excel",
        data=excel_buffer.getvalue(),
        file_name="sql_leads.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("No leads found. Add your first lead above.")
