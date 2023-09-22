import requests
import streamlit as st
import time
import pandas as pd
import webbrowser

from pathlib import Path
from clear_results import with_clear_container

LOGO_PATH = Path(__file__).parent / "images" / "logo.png"

def get_all_database_connections(api_url):
    try:
        response = requests.get(api_url)
        response_data = response.json()
        return {entry["alias"]: entry["id"] for entry in response_data} if response.status_code == 200 else {}  # noqa: E501
    except requests.exceptions.RequestException:
        return {}

def add_database_connection(api_url, connection_data):
    try:
        response = requests.post(api_url, json=connection_data)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def answer_question(api_url, db_connection_id, question):
    request_body = {
        "db_connection_id": db_connection_id,
        "question": question
    }
    try:
        response = requests.post(api_url, json=request_body)
        return response.json() if response.status_code == 200 else {}
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")
        return {}

def type_text(text):
    text = text.strip()
    answer_container = st.empty()
    for i in range(len(text) + 1):
        answer_container.markdown(text[0:i])
        time.sleep(0.02)
    st.divider()

def type_code(text):
    text = text.strip()
    answer_container = st.empty()
    for i in range(len(text) + 1):
        answer_container.code(text[0:i], language="sql")
        time.sleep(0.02)
    st.divider()

def json_to_dataframe(json_data):
    if json_data is None:
        return pd.DataFrame()
    columns = json_data.get("columns", [])
    rows = json_data.get("rows", [])
    df = pd.DataFrame(rows, columns=columns)
    return df

def test_connection(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def create_button_link(text, url):
    button_clicked = st.sidebar.button(text)
    if button_clicked:
        webbrowser.open_new_tab(url)

st.set_page_config(
    page_title="Dataherald",
    page_icon="./images/logo.png",
    layout="wide")

# Setup environment settings
st.sidebar.title("Dataherald")
st.sidebar.write("Query your structured database in natural language.")
st.sidebar.write("Enable business users to get answers to ad hoc data questions in seconds.")  # noqa: E501
link = '[Visit our website](https://www.dataherald.com/)'
st.sidebar.markdown(link, unsafe_allow_html=True)
st.sidebar.subheader("Connect to the engine")
HOST = st.sidebar.text_input("Engine URI", value="http://streamlit_engine.dataherald.ai")
st.session_state["HOST"] = HOST
if st.sidebar.button("Connect"):
    url = HOST + '/api/v1/heartbeat'
    if test_connection(url):
        st.sidebar.success("Connected to engine.")
    else:
        st.sidebar.error("Connection failed.")

# Setup main page
st.image("images/dataherald.png", use_column_width=True)

if not test_connection(HOST + '/api/v1/heartbeat'):
    st.error("Could not connect to engine. Please connect to the engine on the left sidebar.")  # noqa: E501
    st.stop()
else:
    st.info("Connect to a database and ask your question.")

current_database = ""
with st.form("database_connection"):
    st.subheader("Connect to an existing database:")
    database_connections = get_all_database_connections(HOST + '/api/v1/database-connections')  # noqa: E501
    database_connection = st.selectbox("Database", database_connections.keys())
    connect = st.form_submit_button("Connect to database")
    st.session_state["database_connection_id"] = database_connections[database_connection]  # noqa: E501
    if connect:
        st.success(f"Connected to {database_connection}.")

with st.form(key="form"):
    user_input = st.text_input("Ask your question")
    submit_clicked = st.form_submit_button("Submit Question")

output_container = st.empty()
if with_clear_container(submit_clicked):
    output_container = output_container.container()
    output_container.chat_message("user").write(user_input)
    answer_container = output_container.chat_message("assistant")
    introduction = ":wave: Hello. Please, give me a few moments and I'll be back with your answer."  # noqa: E501
    type_text(introduction)
    with st.spinner("Thinking..."):
        try:
            answer = answer_question(HOST + '/api/v1/question', st.session_state["database_connection_id"], user_input)  # noqa: E501
        except KeyError:
            st.error("Please connect to a database first.")
            st.stop()
    try:
        results_from_db = json_to_dataframe(answer["sql_query_result"])
        answer_container.dataframe(results_from_db)
        type_code(answer['sql_query'])
        confidence = f"📊 Confidence: {answer['confidence_score']}"
        type_text(confidence)
        nl_answer = f"🤔 Agent response: {answer['nl_response']}"
        type_text(nl_answer)
    except KeyError:
        st.error("Please connect to a correct database first.")
        st.stop()
