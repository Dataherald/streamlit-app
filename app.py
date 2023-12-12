import requests
import streamlit as st
import time
import random
import pandas as pd
import webbrowser
import threading
from dotenv import load_dotenv
load_dotenv()

from langsmith import Client
from streamlit_feedback import streamlit_feedback
from functools import partial

from pathlib import Path

# Initialize session state variables if they don't exist
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = None

if 'ANSWER' not in st.session_state:
    st.session_state['ANSWER'] = None

LOGO_PATH = Path(__file__).parent / "images" / "chicago2.jpg"
DEFAULT_DATABASE = "chicago"
ANSWER = {}

client = Client()
if 'feedback' in st.session_state:
    del st.session_state['feedback']

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
        print(f"--- print response {response} ")
        return response.json() if response.status_code == 201 else {}
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")
        return {}

def type_text(text, type_speed=0.02):
    text = text.strip()
    answer_container = st.empty()
    for i in range(len(text) + 1):
        answer_container.markdown(text[0:i])
        time.sleep(type_speed)
    st.divider()

def display_text(text):
    text = text.strip()
    answer_container = st.empty()
    answer_container.markdown(text)
    st.divider()

def type_code(text):
    text = text.strip()
    answer_container = st.empty()
    for i in range(len(text) + 1):
        answer_container.code(text[0:i], language="sql")
        time.sleep(0.02)

def display_code(text):
    text = text.strip()
    answer_container = st.empty()
    answer_container.code(text, language="sql")


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

def find_key_by_value(dictionary, target_value):
    for key, value in dictionary.items():
        if value == target_value:
            return key
    return None

def run_answer_question(api_url, db_connection_id, user_input):
    try:
        answer = answer_question(api_url, db_connection_id, user_input)
        print(f"---inside run_answer_question -- small answer \n {answer}\n\n")
        global ANSWER
        ANSWER=answer
    except KeyError:
        st.error("Please connect to a database first.")
        st.stop()


WAITING_TIME_TEXTS = [
    ":wave: Hello. Please, give me a few moments and I'll be back with your answer.",  # noqa: E501
]

INTRODUCTION_TEXT = """
This app is a proof of concept using the Dataherald NL-2-SQL engine using a streamlit front-end and a dataset of US real estate data.
The data available includes: rents, sales prices, listing prices, price per square foot, number of homes sold, inventory and number of pending sales up to June 2023.
"""  # noqa: E501
INTRO_EXAMPLE = """
A sample question you can ask is: How many crimes were reported in 2023?
"""

st.set_page_config(
    page_title="Dataherald",
    page_icon="./images/logo.png",
    layout="wide")


#st.sidebar.subheader("Connect to the engine")
#HOST = st.sidebar.text_input("Engine URI", value="http://34.172.121.180:8080")
HOST = "http://34.30.211.58:8080"
st.session_state["HOST"] = HOST
url = HOST + '/api/v1/heartbeat'
if test_connection(url):
    #st.sidebar.success("Connected to engine.")
    pass
else:
    st.sidebar.error("Connection failed.")

st.sidebar.subheader("Information")
st.sidebar.markdown("""
    This app provides answers to questions based on publicly available datasets from the City of Chicago:<br><br>
        <a href="https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2" target="_blank">1. Chicago Crime dataset</a><br>
        <a href="https://data.cityofchicago.org/en/Service-Requests/311-Service-Requests-Request-Types/dgc7-2pdf" target="_blank">2. Chicago 311 Service Request</a>
    """, unsafe_allow_html=True)

# Setup main page
col1, col2 = st.columns([1, 4])
with col1:
    st.image("images/chicago3.jpg",width=200)
with col2:
    st.markdown("""
    <style>
    .big-font {
        font-size:300% !important;
        font-weight: bold !important;
        color: #4A90E2; /* You can change the color */
        text-shadow: 2px 2px 5px #7f7f7f; /* Optional: Adds a shadow effect */
        text-align: left; /* Aligns the text to the left */
    }
    </style>

    <div class='big-font'>
        Chicago Data Concierge
    </div>
    """, unsafe_allow_html=True)
if not test_connection(HOST + '/api/v1/heartbeat'):
    st.error("Could not connect to engine. Please connect to the engine on the left sidebar.")  # noqa: E501
    st.stop()
else:
    database_connections = get_all_database_connections(HOST + '/api/v1/database-connections')  # noqa: E501
    if st.session_state.get("database_connection_id", None) is None:
        st.session_state["database_connection_id"] = database_connections[DEFAULT_DATABASE]  # noqa: E501
    db_name = find_key_by_value(database_connections, st.session_state["database_connection_id"])  # noqa: E501
    #st.info(INTRO_EXAMPLE)

output_container = st.empty()
user_input = st.chat_input("Ask your question")
output_container = output_container.container()

# print(f"\n\n session state {st.session_state}\n\n")
# if 'feedback_call' in st.session_state and st.session_state['feedback_call']:
#     print("\n\n\n inside feedback if statemnet \n\n\n")
#     ANSWER = st.session_state['ANSWER']
#     output_container.chat_message("user").write(st.session_state['user_input'])
#     answer_container = output_container.chat_message("assistant")
#     results_from_db = json_to_dataframe(ANSWER["sql_query_result"])
#
#     answer_container = st.empty()
#     answer_container.dataframe(results_from_db)
#
#     st.divider()
#     display_code(ANSWER['sql_query'])
#     nl_answer = f"🤔 Agent response: {ANSWER['response']}"
#     display_text(nl_answer)
# else:
if user_input:
    print(f"\n\n\n {user_input}------- \n\n\n")
    st.session_state['feedback_call']=False
    st.session_state['user_input'] = user_input
    output_container.chat_message("user").write(user_input)
    answer_container = output_container.chat_message("assistant")
    answer_thread = threading.Thread(target=run_answer_question, args=(HOST + '/api/v1/questions', st.session_state["database_connection_id"], user_input))  # noqa: E501
    answer_thread.start()

    for text in WAITING_TIME_TEXTS:
        random_number = random.uniform(0.06, 0.09)
        type_text(text, type_speed=random_number)
    with st.spinner("Finalizing answer..."):
        answer_thread.join()
        print(f"ANSWER ----- {ANSWER} ")
        st.session_state['ANSWER'] = ANSWER
        st.session_state['run_id'] = ANSWER['run_id']
    try:
        results_from_db = json_to_dataframe(ANSWER["sql_query_result"])
        results_from_db.columns = [f"{i}_{col}" for i, col in enumerate(results_from_db.columns)]  # noqa: E501
        answer_container = st.empty()
        answer_container.dataframe(results_from_db)
        st.divider()
        type_code(ANSWER['sql_query'])
        nl_answer = f"🤔 Agent response: {ANSWER['response']}"
        type_text(nl_answer)

        #print(f"\n\n\n\n\n run_id is {ANSWER['run_id']}\n\n\n{ANSWER['run_url']}\n\n\n")
        #feedback = streamlit_feedback(**feedback_kwargs, key=f"feedback_1")
        #st.write(feedback)

        st.markdown(f"View trace in [🦜🛠️ LangSmith]({ANSWER['run_url']})")
    except Exception as e :
        st.error(e)
        st.stop()





    # if st.session_state.get("run_id"):
    #     run_id = st.session_state['run_id']
    #     feedback = streamlit_feedback(
    #         feedback_type= "thumbs",
    #         optional_text_label= "[Optional] Please provide an explantion",
    #         key=f"feedback_{run_id}"
    #     )
    #
    #     score_mappings = {
    #         "thumbs": {"👍":1, "👎":0}
    #     }
    #
    #     scores = score_mappings["thumbs"]
    #
    #     if feedback:
    #         score = scores.get(feedback["score"])
    #
    #         if score is not None:
    #             feedback_type_str = f"thumbs {feedback['score']}"
    #
    #             feedback_record= client.create_feedback(
    #                 run_id,
    #                 feedback_type_str,
    #                 score = score,
    #                 comment=feedback.get("text",)
    #             )
    #             st.session_state['feedback_call']=True
    #
    #
    #         else:
    #             st.warning("Invalid feedback score.")
