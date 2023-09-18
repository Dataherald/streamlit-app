import streamlit as st
import pandas as pd
import requests
import json
import sys


def get_all_database_connections():
    api_url = f'{HOST}/api/v1/database-connections'
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

def add_golden_records(data):
    api_url = f'{HOST}/api/v1/golden-records'

    try:
        response = requests.post(api_url, json=data)
        
        if response.status_code == 201:
            st.success("Golden record(s) added successfully.")
            st.session_state["connection_id"] = None
            return True
        else:
            st.warning(f"Could not add golden records because {response.text}.")
            return False
    except requests.exceptions.RequestException:
        st.error("Connection failed.")
        return False

def get_golden_records(page=1, limit=sys.maxsize):
    api_url = f'{HOST}/api/v1/golden-records'
    params = {
        'page': page,
        'limit': limit
    }
    try:
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            golden_records = response.json()
            return golden_records
        else:
            st.warning("Could not get golden records.")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")
        return []

def delete_golden_record(golden_record_id):
    api_url = f'{HOST}/api/v1/golden-records/{golden_record_id}'

    try:
        response = requests.delete(api_url)
        if response.status_code == 200:
            st.success("Golden record deleted successfully.")
            return True
        else:
            st.warning(f"Could not delete golden record because {response.text}.")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")
        return False

st.set_page_config(
    page_title="Dataherald",
    page_icon="./images/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed")

HOST = st.session_state["HOST"]

st.title("🧈 Golden Record Management")

with st.form("Databases"):
    st.info("Select a database connection to add or delete golden records.")
    db_connection_id = None
    st.subheader("Choose database connection")
    database_connections = get_all_database_connections()
    db_connection = st.selectbox(
        "Database connection",
        options=list(database_connections.keys()))
    if st.form_submit_button("Select"):
        st.success(f"Connected to {db_connection}.")
        st.session_state["connection_id"] = database_connections[db_connection]
        connection_id = database_connections[db_connection]

with st.form("Golden records"):
    add_or_upload = st.radio(
        "Add or upload golden records",
        ("Add", "Upload"))
    add_column, upload_column = st.columns(2)
    add_column.subheader("Add a golden record")
    question = add_column.text_input("Question")
    sql_query = add_column.text_input("SQL query")
    upload_column.subheader("Upload golden records")
    uploaded_file = upload_column.file_uploader(
        "Upload jsonl file (JSONL should contain question and sql_query fields))",
        type=["jsonl"])
    if st.form_submit_button("Add"):
        if add_or_upload == "Add":
            with st.spinner("Adding golden record..."):
                try:
                    data = {
                        "db_connection_id": st.session_state["connection_id"],
                        "question": question,
                        "sql_query": sql_query
                    }
                except KeyError:
                    st.warning("Please select a database connection.")
                add_golden_records([data])
        else:
            with st.spinner("Uploading golden records..."):
                if uploaded_file is not None:
                    uploaded_data = []
                    for line in uploaded_file:
                        try:
                            line_data = json.loads(line.decode("utf-8").strip())  
                            if "question" in line_data and "sql_query" in line_data:
                                uploaded_data.append({
                                    "db_connection_id": st.session_state["connection_id"],  # noqa: E501
                                    "question": line_data["question"],
                                    "sql_query": line_data["sql_query"]
                                })
                            else:
                                st.warning("Uploaded file contains incomplete data.")
                        except KeyError:
                            st.warning("Uploaded file contains incomplete data.")
                        except json.JSONDecodeError as e:
                            st.warning(
                                f"Invalid JSON format in the uploaded file due to {e}."
                                )
                            
                    add_golden_records(uploaded_data)

with st.form("View golden records"):
    st.subheader("View golden records")
    page = st.number_input("Page", value=1)
    limit = st.slider("Limit", min_value=1, max_value=20, value=10)
    if st.form_submit_button("View"):
        with st.spinner("Loading golden records..."):
            golden_records = get_golden_records()
            df = pd.DataFrame(golden_records)
            try:
                df = df[df['db_connection_id'] == st.session_state["connection_id"]]
            except KeyError:
                st.warning("Please select a database connection.")
            df = df.iloc[(page-1)*limit:page*limit]
            df.drop(columns=["db_connection_id"], inplace=True)
            df.reset_index(drop=True, inplace=True)
            if golden_records:
                st.dataframe(df)
            else:
                st.warning("No golden records found.")

with st.form("Delete golden record"):
    st.subheader("Delete golden record")
    golden_record_id = st.text_input("Golden record ID")
    if st.form_submit_button("Delete"):
        if golden_record_id:
            with st.spinner("Deleting golden record..."):
                delete_golden_record(golden_record_id)
        else:
            st.warning("Please provide a golden record ID.")
