import streamlit as st
import requests
import json


def get_all_database_connections():
    api_url = HOST + '/api/v1/database-connections'
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            aliases = {}
            for entry in data:
                aliases[entry["alias"]] = entry["id"]
            return aliases
        else:
            st.warning("Could not get database connections. ")
            return {}
    except requests.exceptions.ConnectionError:
        st.error("Connection failed.")
        return {}

def add_golden_records(golden_records_data):
    api_url = HOST + '/api/v1/golden-records'

    try:
        response = requests.post(api_url, json=golden_records_data)
        if response.status_code == 200:
            st.success("Golden records added.")
            return True
        else:
            st.warning(f"Could not add golden records because {response.text}.")
            return False
    except requests.exceptions.RequestException:
        st.error("Connection failed.")
        return False


st.set_page_config(
    page_title="Dataherald",
    page_icon="💾",
    layout="wide",
    initial_sidebar_state="collapsed")

HOST = st.session_state["HOST"]

st.title("Golden Records")

with st.form("Databases"):
    db_connection_id = None
    st.subheader("Choose database connection")
    database_connections = get_all_database_connections()
    db_connection = st.selectbox(
        "Database connection",
        options=list(database_connections.keys()))
    if st.form_submit_button("Select"):
        st.success(f"Connected to {db_connection}.")
        db_connection_id = database_connections[db_connection]
    

if not db_connection_id:
    st.warning("Please select a database connection.")

with st.form("Golden records"):
    add_or_upload = st.radio(
        "Add or upload golden records",
        ("Add", "Upload"))
    add_column, upload_column = st.columns(2)
    add_column.subheader("Add golden records")
    question = add_column.text_input("Question")
    sql_query = add_column.text_input("SQL query")
    added_golden_records_data = [
    {
        "db_connection_id": str(db_connection_id),
        "question": question,
        "sql_query": sql_query
    }
    ]

    upload_column.subheader("Upload golden records")
    uploaded_file = upload_column.file_uploader(
        "Upload jsonl file",
        type=["jsonl"])
    uploaded_golden_records_data = []
    if uploaded_file:
        uploaded_golden_records_data = uploaded_file.readlines()
        uploaded_golden_records_data = [
            json.loads(line)
            for line in uploaded_golden_records_data
        ]
    if st.form_submit_button("Add"):
        if add_or_upload == "Add":
            with st.spinner("Adding golden records..."):
                add_golden_records(added_golden_records_data)
        else:
            with st.spinner("Uploading golden records..."):
                add_golden_records(uploaded_golden_records_data)

