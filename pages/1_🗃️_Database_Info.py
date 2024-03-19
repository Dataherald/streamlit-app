import streamlit as st
import requests
import pandas as pd

def get_all_database_connections(api_url):
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            return {entry["alias"]: entry["id"] for entry in data}
        else:
            st.warning("Could not get database connections.")
            return {}
    except requests.exceptions.RequestException:
        st.error("Connection failed.")
        return {}

def scan_database(api_url, db_connection_id, table_name):
    payload = {
        "db_connection_id": db_connection_id,
        "table_names": [table_name]
    }
    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 201:
            st.success("Table scanning started.")
        else:
            st.warning(f"Could not scan tables. {response.text}")
    except requests.exceptions.RequestException:
        st.error("Connection failed.")

def list_table_descriptions(api_url, db_connection_id):
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

HOST = st.session_state.get("HOST", "")

st.title("🗃️ Database Information")
api_url = f"{HOST}/api/v1"

with st.form("database_connection"):
    st.subheader("Connect to an existing database:")
    database_connections = get_all_database_connections(HOST + '/api/v1/database-connections')  # noqa: E501
    database_connection = st.selectbox("Database", database_connections.keys())
    connect = st.form_submit_button("Connect to database")
    if connect:
        st.session_state["database_connection_id"] = database_connections[database_connection]  # noqa: E501
        st.success(f"Connected to {database_connection}.")

with st.form("Scan tables"):
    st.header("Scan tables")
    st.info("Here you can scan a table within a database to extract information from the given table.")  # noqa: E501
    st.warning("Please note that only scanned tables are used by the agent")
    database_connections = get_all_database_connections(f"{api_url}/database-connections")  # noqa: E501
    database_connection = st.selectbox(
        "Choose a database connection",
        database_connections.keys())
    table_name = st.text_input("Table name", value="")
    if st.form_submit_button("Scan table"):
        if table_name:
            with st.spinner("Scanning table..."):
                scan_database(f"{api_url}/table-descriptions/sync-schemas", database_connections[database_connection], table_name)  # noqa: E501
        else:
            st.warning("Please provide a table name.")

with st.form("View scanned tables"):
    st.header("View scanned tables")
    st.info("In this section you can view the tables that have been scanned.")
    database_connections = get_all_database_connections(f"{api_url}/database-connections")  # noqa: E501
    database_connection = st.selectbox(
        "Available Database connections",
        database_connections.keys())
    if st.form_submit_button("Show tables"):
        with st.spinner("Finding table..."):
            table_descriptions = list_table_descriptions(f"{api_url}/table-descriptions", database_connections[database_connection])  # noqa: E501
        st.markdown("### List of Tables")
        if table_descriptions:
            table_info = []
            for table_description in table_descriptions:
                table_info.append([
                    table_description['table_name'],
                    table_description['description'],
                    len(table_description['columns']),
                    table_description['status']
                    ])
            df = pd.DataFrame(
                table_info,
                columns=['Table name', 'Description', 'Number of Columns', 'Status'])
            st.table(df)
        else:
            st.warning("No table descriptions available.")
