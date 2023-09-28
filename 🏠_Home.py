import requests
import streamlit as st
import time
import random
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
import pandas as pd
import webbrowser
import threading

from pathlib import Path
from clear_results import with_clear_container

LOGO_PATH = Path(__file__).parent / "images" / "logo.png"
DEFAULT_DATABASE = "Redfin"
ANSWER = ""

SYSTEM_TEMPLATE = """ Given a input sentence, paraphrase the sentence.
be friendly and include emojis in your response.
"""

HUMAN_TEMPLATE = """
sentence: {input}
Paraphrased version:
"""

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

def type_text(text, type_speed=0.02):
    text = text.strip()
    answer_container = st.empty()
    for i in range(len(text) + 1):
        answer_container.markdown(text[0:i])
        time.sleep(type_speed)
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

def find_key_by_value(dictionary, target_value):
    for key, value in dictionary.items():
        if value == target_value:
            return key
    return None

def run_answer_question(api_url, db_connection_id, user_input):
    try:
        answer = answer_question(api_url, db_connection_id, user_input)
        global ANSWER
        ANSWER = answer
    except KeyError:
        st.error("Please connect to a database first.")
        st.stop()

@st.cache_resource
def load_chain():
    llm = ChatOpenAI(openai_api_key=st.secrets['OPENAI_API_KEY'])
    system_message_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE)
    human_message_prompt = HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE)
    chat_prompt = ChatPromptTemplate.from_messages(
                [system_message_prompt, human_message_prompt]
    )
    chain = LLMChain(llm=llm, prompt=chat_prompt)
    return chain

def paraphrase_text(chain, input: str) -> str:
    response = chain.run(
        input=input
    )
    return response


WAITING_TIME_TEXTS = [
    ":wave: Hello. Please, give me a few moments and I'll be back with your answer. Next you can see the steps I'm taking to answer your question.",  # noqa: E501
    "🔎 Finding few-shot examples from vector store based on similarity of the golden records to the question",  # noqa: E501,
    "📚 Finding the relevant tables based on the similarity of the question and the schema of the tables in Database",  # noqa: E501
    "🤔 Finding the relevant columns of the tables chosen in the previous step",
    "✨ Filtering the columns by gathering more information from the scanned tables",
    "💭 Locating the entities in the columns",
    "🔍 Retrieving the instructions before generating the SQL query",
    "💡 Generating the SQL query based on previous steps",
]

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
st.image("images/dataherald.png", width=500)
chain = load_chain()
if not test_connection(HOST + '/api/v1/heartbeat'):
    st.error("Could not connect to engine. Please connect to the engine on the left sidebar.")  # noqa: E501
    st.stop()
else:
    database_connections = get_all_database_connections(HOST + '/api/v1/database-connections')  # noqa: E501
    if st.session_state.get("database_connection_id", None) is None:
        st.session_state["database_connection_id"] = database_connections[DEFAULT_DATABASE]  # noqa: E501
    db_name = find_key_by_value(database_connections, st.session_state["database_connection_id"])  # noqa: E501
    st.info(f"You are connected to {db_name}. Change the database connection from the Database Information page.")  # noqa: E501

output_container = st.empty()
user_input = st.chat_input("Ask your question")
output_container = output_container.container()
if user_input:
    output_container.chat_message("user").write(user_input)
    answer_container = output_container.chat_message("assistant")
    answer_thread = threading.Thread(target=run_answer_question, args=(HOST + '/api/v1/question', st.session_state["database_connection_id"], user_input))  # noqa: E501
    answer_thread.start()
    for text in WAITING_TIME_TEXTS:
        random_number = random.uniform(0.05, 0.08)
        type_text(paraphrase_text(chain, text), type_speed=random_number)
    with st.spinner("Finalizing answer..."):
        answer_thread.join()
    try:
        results_from_db = json_to_dataframe(ANSWER["sql_query_result"])
        results_from_db.columns = [f"{i}_{col}" for i, col in enumerate(results_from_db.columns)]  # noqa: E501
        answer_container = st.empty()
        answer_container.dataframe(results_from_db)
        st.divider()
        type_code(ANSWER['sql_query'])
        confidence = f"📊 Confidence: {ANSWER['confidence_score']}"
        type_text(confidence)
        nl_answer = f"🤔 Agent response: {ANSWER['nl_response']}"
        type_text(nl_answer)
    except KeyError:
        st.error("Please connect to a correct database first.")
        st.stop()
