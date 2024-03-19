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
    api_url = f'{HOST}/api/v1/golden-sqls'

    try:
        response = requests.post(api_url, json=data)
        
        if response.status_code == 201:
            st.success("Golden record(s) added successfully.")
            return True
        else:
            st.warning(f"Could not add golden records because {response.text}.")
            return False
    except requests.exceptions.RequestException:
        st.error("Connection failed.")
        return False

def get_golden_records(db_connection_id, page=1, limit=sys.maxsize):
    api_url = f'{HOST}/api/v1/golden-sqls'
    params = {
        'db_connection_id': db_connection_id,
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
    api_url = f'{HOST}/api/v1/golden-sqls/{golden_record_id}'

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

def find_key_by_value(dictionary, target_value):
    for key, value in dictionary.items():
        if value == target_value:
            return key
    return None

st.set_page_config(
    page_title="Dataherald",
    page_icon="./images/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed")

HOST = st.session_state["HOST"]

st.title("🧈 Golden Record Management")
database_connections = get_all_database_connections()
db_name = find_key_by_value(database_connections, st.session_state["database_connection_id"])  # noqa: E501
st.info(f"You are connected to {db_name}. Change the database connection from the Database Information page.")  # noqa: E501

with st.form("Golden records"):
    st.info("Here you can add or upload golden records. Golden records are used to improve the accuracy of the engine.")  # noqa: E501
    add_or_upload = st.radio(
        "Add or upload golden records",
        ("Add", "Upload"))
    add_column, upload_column = st.columns(2)
    add_column.subheader("Add a golden record")
    prompt_text = add_column.text_input("Prompt text")
    sql = add_column.text_input("SQL")
    upload_column.subheader("Upload golden records")
    uploaded_file = upload_column.file_uploader(
        "Upload jsonl file (JSONL should contain prompt_text and sql keys))",
        type=["jsonl"])
    if st.form_submit_button("Upsert"):
        if add_or_upload == "Add":
            with st.spinner("Adding golden record..."):
                try:
                    data = {
                        "db_connection_id": st.session_state["database_connection_id"],
                        "prompt_text": prompt_text,
                        "sql": sql
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
                            if "prompt_text" in line_data and "sql" in line_data:
                                uploaded_data.append({
                                    "db_connection_id": st.session_state["database_connection_id"],  # noqa: E501
                                    "prompt_text": line_data["prompt_text"],
                                    "sql": line_data["sql"]
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
    golden_records = get_golden_records(st.session_state["database_connection_id"])
    st.write(f"Total golden records: {len(golden_records)}")
    search_query = st.text_input("Search by question or SQL query", "")
    default_limit_value = min(10, len(golden_records))
    page = st.number_input("Page",
                            value=1,
                            min_value=1
                        )
    limit = st.number_input("Limit",
                            min_value=0,
                            max_value=len(golden_records),
                            value=default_limit_value,
                        )
    if st.form_submit_button("View"):
        with st.spinner("Loading golden records..."):
            if search_query:
                golden_records = [
                    record
                    for record in golden_records
                    if search_query.lower() in record["question"].lower()
                    or search_query.lower() in record["sql_query"].lower()
                ]
            if len(golden_records) > 0:
                df = pd.DataFrame(golden_records)
                try:
                    df = df[df['db_connection_id'] == st.session_state["database_connection_id"]]  # noqa: E501
                except KeyError:
                    st.warning("Please select a database connection.")
                df = df.iloc[(page-1)*limit:page*limit]
                df.drop(columns=["db_connection_id"], inplace=True)
                df.reset_index(drop=True, inplace=True)
                if golden_records:
                    st.dataframe(df)
                else:
                    st.warning("No golden records found.")
            else:
                st.warning("No golden records found.")

with st.form("Delete golden record"):
    st.subheader("Delete golden record")
    st.info("Here you can delete a golden record by providing the golden record ID.")  # noqa: E501
    golden_record_id = st.text_input("Golden record ID")
    if st.form_submit_button("Delete"):
        if golden_record_id:
            with st.spinner("Deleting golden record..."):
                delete_golden_record(golden_record_id)
        else:
            st.warning("Please provide a golden record ID.")
