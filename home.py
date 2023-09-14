from PIL import Image
from pathlib import Path

import requests
import streamlit as st
import time

LOGO_PATH = Path(__file__).parent / "images" / "logo.png"

@st.cache_resource
def load_image(LOGO_PATH):
    img =  Image.open(LOGO_PATH)
    return img

st.set_page_config(
    page_title="Dataherald",
    page_icon=":bar_chart:",
    layout="wide")

st.image(load_image(LOGO_PATH))

# Setup environment settings
st.sidebar.title("Dataherald")
st.sidebar.write("Ask questions about your data.")
st.sidebar.subheader("Connect to the engine")
st.sidebar.text_input("Engine URL", value="http://localhost:8000")
if st.sidebar.button("Connect"):
    url = 'http://localhost/api/v1/heartbeat'
    response = requests.get(url)
    if response.status_code == 200:
        st.sidebar.success("Connected to engine.")
    else:
        st.sidebar.error("Connection failed.")