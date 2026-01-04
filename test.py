import streamlit as st
import os

st.title("🔥 STREAMLIT FILE TEST 🔥")
st.write("CURRENT FILE:", __file__)
st.write("CURRENT WORKING DIR:", os.getcwd())
st.sidebar.error("THIS IS zzz_test.py — IF YOU SEE THIS, PATH IS CORRECT")
