import requests
import streamlit as st
import webbrowser
import time

from pathlib import Path

LOGO_PATH = Path(__file__).parent / "images" / "logo.png"
DEFAULT_DATABASE = "RealEstate"

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
        "llm_config": {
            "llm_name": "gpt-4-turbo-preview"
        },
        "prompt": {
            "text": question,
            "db_connection_id": db_connection_id,
        }
    }
    try:
        with requests.post(api_url, json=request_body, stream=True) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=2048):
                if chunk:
                    response = chunk.decode("utf-8")
                    yield response + "\n"
                    time.sleep(0.1)
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")

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

def find_key_by_value(dictionary, target_value):
    for key, value in dictionary.items():
        if value == target_value:
            return key
    return None


WAITING_TIME_TEXTS = [
    ":wave: Hello. Please, give me a few moments and I'll be back with your answer.",  # noqa: E501
]

INTRODUCTION_TEXT = """
This app is a proof of concept using the Dataherald NL-2-SQL engine using a streamlit front-end and a dataset of US real estate data.
The data available includes: rents, sales prices, listing prices, price per square foot, number of homes sold, inventory and number of pending sales up to June 2023.
"""  # noqa: E501
INTRO_EXAMPLE = """
A sample question you can ask is: Did property prices increase or decrease in the US in 2020?
"""

st.set_page_config(
    page_title="Dataherald",
    page_icon="./images/logo.png",
    layout="wide")

# Setup environment settings
st.sidebar.title("Dataherald")
st.sidebar.write("Query your structured database in natural language.")
st.sidebar.write("Enable business users to get answers to ad hoc data questions in seconds.")  # noqa: E501
st.sidebar.page_link("https://www.dataherald.com/", label="Visit our website", icon="🌐")
st.sidebar.subheader("Connect to the engine")
HOST = st.sidebar.text_input("Engine URI", value="https://streamlit.dataherald.ai")
st.session_state["HOST"] = HOST
if st.sidebar.button("Connect"):
    url = HOST + '/api/v1/heartbeat'
    if test_connection(url):
        st.sidebar.success("Connected to engine.")
    else:
        st.sidebar.error("Connection failed.")

# Setup main page
st.image("images/dataherald.png", width=500)
if not test_connection(HOST + '/api/v1/heartbeat'):
    st.error("Could not connect to engine. Please connect to the engine on the left sidebar.")  # noqa: E501
    st.stop()
else:
    database_connections = get_all_database_connections(HOST + '/api/v1/database-connections')  # noqa: E501
    if st.session_state.get("database_connection_id", None) is None:
        st.session_state["database_connection_id"] = database_connections[DEFAULT_DATABASE]  # noqa: E501
    db_name = find_key_by_value(database_connections, st.session_state["database_connection_id"])  # noqa: E501
    st.warning(f"Connected to {db_name} database.")
    st.info(INTRODUCTION_TEXT)  # noqa: E501
    st.info(INTRO_EXAMPLE)

output_container = st.empty()
user_input = st.chat_input("Ask your question")
output_container = output_container.container()
if user_input:
    output_container.chat_message("user").write(user_input)
    answer_container = output_container.chat_message("assistant")
    with st.spinner("Agent starts..."):
        st.write_stream(answer_question(HOST + '/api/v1/stream-sql-generation', st.session_state["database_connection_id"], user_input))