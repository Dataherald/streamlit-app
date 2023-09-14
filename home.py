from PIL import Image
from pathlib import Path

import requests
import json
import streamlit as st

LOGO_PATH = Path(__file__).parent / "images" / "logo.png"

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
            st.warning("Could not get database connections.")
            return {}
    except requests.exceptions.ConnectionError:
        return {}

def add_database_connection(connection_data):
    api_url = HOST + '/api/v1/database-connections'
    data_json = json.dumps(connection_data)
    try:
        response = requests.post(api_url, data=data_json)
        if response.status_code == 200:
            response_data = response.json()
            return response_data
        else:
            st.warning("Could not add database connection.")
            return None
    except requests.exceptions.RequestException:
        return None

def load_image(LOGO_PATH):
    img =  Image.open(LOGO_PATH)
    return img

st.set_page_config(
    page_title="Dataherald",
    page_icon="🧠",
    layout="wide")

# Setup environment settings
st.sidebar.title("Dataherald")
st.sidebar.write("Ask questions about your data.")
st.sidebar.subheader("Connect to the engine")
HOST = st.sidebar.text_input("Engine URI", value="http://localhost")
st.session_state["HOST"] = HOST
if st.sidebar.button("Connect to engine"):
    try:
        url = HOST + '/api/v1/heartbeat'
        response = requests.get(url)
        if response.status_code == 200:
            st.sidebar.success("Connected to engine.")
    except requests.exceptions.ConnectionError:
        st.sidebar.error("Connection failed.")

# Setup main page
st.title("Dataherald engine")
st.info("Please connect to the engine on the left sidebar.")

current_database = ""
with st.form("database_connection"):
    st.subheader("Connect to an existing database:")
    database_connections = get_all_database_connections()
    database_connection = st.selectbox("Database", database_connections.keys())
    connect = st.form_submit_button("Connect to database")
    if connect:
        st.success(f"Connected to {database_connection}.")
        current_database = database_connection