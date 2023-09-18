import streamlit as st
import requests
import json
import pandas as pd


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
    
def scan_database(db_connection_id, table_names):
    api_url = HOST + '/api/v1/table-descriptions/scan'
    payload = {
        "db_connection_id": db_connection_id,
        "table_names": [table_names]
    }
    try:
        response = requests.post(api_url, data=json.dumps(payload))
        if response.status_code == 200:
            st.success("Table scanned.")
        else:
           st.warning(f"Could not scan tables. {response.text}")
    except requests.exceptions.RequestException:
        st.error("Connection failed.")

def list_table_descriptions(db_connection_id): 
    api_url = HOST + '/api/v1/table-descriptions'

    params = {
        'db_connection_id': db_connection_id,
    }
    try:
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.warning("Could not get table descriptions.")
            return None
    except requests.exceptions.RequestException:
        st.error("Connection failed.")
        return None

st.set_page_config(
    page_title="Dataherald",
    page_icon="./images/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed")

HOST = st.session_state["HOST"]

st.title("🗃️ Database Informaton")
with st.form("Scan tables"):
    st.header("Scan tables")
    database_connections = get_all_database_connections()
    database_connection = st.selectbox(
        "Choose a database connection",
        database_connections.keys())
    table_name = st.text_input("Table name", value="")
    if st.form_submit_button("Scan table"):
        if table_name:
            with st.spinner("Scanning table..."):
                scan_database(
                    database_connections[database_connection],
                    table_name)
        else:
            st.warning("Please provide a table name.")

with st.form("View scanned tables"):
    st.header("View scanned tables")
    database_connections = get_all_database_connections()
    database_connection = st.selectbox(
        "Available Database connections",
        database_connections.keys())
    if st.form_submit_button("show tables"):
        table_descriptions = list_table_descriptions(
            database_connections[database_connection])
        st.markdown("### List of Tables")
        table_info = []
        for table_description in table_descriptions:
            table_info.append([
                table_description['table_name'],
                table_description['description'],
                len(table_description['columns']),
                ])
        df = pd.DataFrame(
            table_info,
            columns=['Table name', 'Description', 'Number of Columns'])
        st.table(df)
    
    