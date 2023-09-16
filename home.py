import requests
import json
import streamlit as st
import time
import pandas as pd

from PIL import Image
from pathlib import Path
from clear_results import with_clear_container


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
    
def answer_question(db_connection_id, question):
    api_url = f'{HOST}/api/v1/question'
    request_body = {
        "db_connection_id": db_connection_id,
        "question": question
    }
    try:
        response = requests.post(api_url, json=request_body)
        if response.status_code == 200:
            response_data = response.json()
            return response_data
        else:
            st.warning(f"Could not answer question because {response.text}.")
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")
        return {}

def load_image(LOGO_PATH):
    img =  Image.open(LOGO_PATH)
    return img

def type_text(text, answer_container):
    text = text.strip()
    answer_container =  st.empty()
    for i in range(len(text) + 1):
        answer_container.markdown(text[0:i])
        time.sleep(0.02)
    st.divider()

def json_to_dataframe(json_data):
    if json_data is None:
        return pd.DataFrame()
    columns = json_data.get("columns", [])
    rows = json_data.get("rows", [])
    df = pd.DataFrame(rows, columns=columns)
    return df

def test_connection():
    try:
        url = HOST + '/api/v1/heartbeat'
        response = requests.get(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.ConnectionError:
        return False

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
if st.sidebar.button("Connect"):
    try:
        url = HOST + '/api/v1/heartbeat'
        response = requests.get(url)
        if response.status_code == 200:
            st.sidebar.success("Connected to engine.")
    except requests.exceptions.ConnectionError:
        st.sidebar.error("Connection failed.")

# Setup main page
st.title("Dataherald Engine")

if not test_connection():
    st.error("Could not connect to engine. Please connect to the engine on the left sidebar.")  # noqa: E501
    st.stop()
else:
    st.info("Connect to a database and ask your question.")

current_database = ""
with st.form("database_connection"):
    st.subheader("Connect to an existing database:")
    database_connections = get_all_database_connections()
    database_connection = st.selectbox("Database", database_connections.keys())
    connect = st.form_submit_button("Connect to database")
    if connect:
        st.success(f"Connected to {database_connection}.")
        st.session_state["database_connection_id"] = database_connections[database_connection]  # noqa: E501

with st.form(key="form"):
    user_input = st.text_input("Ask your question")
    submit_clicked = st.form_submit_button("Submit Question")

output_container = st.empty()
if with_clear_container(submit_clicked):
    output_container = output_container.container()
    output_container.chat_message("user").write(user_input)
    answer_container = output_container.chat_message("assistant")
    introduction = ":wave: Hello. Please, give me a few moments and I'll be back with your answer."  # noqa: E501
    type_text(introduction, answer_container)
    with st.spinner("Thinking..."):
        try:
            answer = answer_question(
                st.session_state["database_connection_id"],
                user_input)  
        except KeyError:
            st.error("Please connect to a database first.")
            st.stop()
    try:
        sql_query = f"📝 Generated SQL Query: {answer['sql_query']}"
        type_text(sql_query, answer_container)
        confidence = f"📊 Confidence: {answer['confidence_score']}"
        type_text(confidence, answer_container)
        nl_answer = f"🤔 Agent response: {answer['nl_response']}"
        type_text(nl_answer, answer_container)
        results_from_db = json_to_dataframe(answer["sql_query_result"])
        answer_container.dataframe(results_from_db)
    except KeyError:
        st.error("Please connect to a correct database first.")
        st.stop()
