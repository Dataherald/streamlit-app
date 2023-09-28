import streamlit as st
import requests
import sys
import pandas as pd


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
    
def add_instruction(api_url, db_connection_id, instruction):
    request_body = {
        "db_connection_id": db_connection_id,
        "instruction": instruction
    }
    try:
        response = requests.post(api_url, json=request_body)

        if response.status_code == 201:
            return response.json()
        else:
            st.error(f"Failed to add instruction. Status code: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")
        return {}
    
def get_instructions(api_url, db_connection_id, page=1, limit=sys.maxsize):
    params = {
        "db_connection_id": db_connection_id,
        "page": page,
        "limit": limit
    }
    try:
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to retrieve instructions. Status code: {response.status_code}")  # noqa: E501
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")
        return []
    
def delete_instruction(api_url, instruction_id):
    endpoint = f"{api_url}/{instruction_id}"

    try:
        response = requests.delete(endpoint)

        if response.status_code == 200:
            return True
        else:
            st.error(f"Failed to delete instruction. Status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")
        return False
    
def update_instruction(api_url, instruction_id, new_instruction):
    endpoint = f"{api_url}/{instruction_id}"

    request_body = {
        "instruction": new_instruction
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.put(endpoint, json=request_body, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to update instruction. Status code: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")
        return {}


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


st.title("📜 Instructions")
database_connections = get_all_database_connections()
db_name = find_key_by_value(database_connections, st.session_state["database_connection_id"])  # noqa: E501
st.info(f"You are connected to {db_name}. Change the database connection from the Database Information page.")  # noqa: E501

with st.form("add_instruction"):
    st.subheader("Add an instruction:")
    instruction = st.text_input("Instruction")
    if st.form_submit_button("Add"):
        api_url = f'{HOST}/api/v1/instructions'
        instruction = add_instruction(api_url, st.session_state["database_connection_id"], instruction)
        if instruction:
            st.success("Instruction added successfully.")

with st.form("View all instructions"):
    st.subheader("View all instructions:")
    if st.form_submit_button("View"):
        instructions = get_instructions(f'{HOST}/api/v1/instructions', st.session_state["database_connection_id"])
        if instructions:
            df = pd.DataFrame(instructions)
            st.dataframe(df)
        else:
            st.warning("No instructions found.")

with st.form("Update instruction"):
    st.subheader("Update an instruction:")
    instruction_id = st.text_input("Instruction ID")
    new_instruction = st.text_input("New instruction")
    if st.form_submit_button("Update"):
        instruction = update_instruction(f'{HOST}/api/v1/instructions', instruction_id, new_instruction)
        if instruction:
            st.success("Instruction updated successfully.")
        else:
            st.warning("Could not update instruction.")

with st.form("Delete instruction"):
    st.subheader("Delete an instruction:")
    instruction_id = st.text_input("Instruction ID")
    if st.form_submit_button("Delete"):
        if delete_instruction(f'{HOST}/api/v1/instructions', instruction_id):
            st.success("Instruction deleted successfully.")
        else:
            st.warning("Could not delete instruction.")

