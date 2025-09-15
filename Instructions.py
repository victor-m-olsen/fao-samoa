import streamlit as st
from database.db_setup import init_database

# Initialize DB on startup
init_database()

st.set_page_config(
    page_title="Instructions - Agricultural Management System",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Agricultural Management System")
st.markdown("""
Welcome! Use the pages in the left sidebar to register crop production, map field boundaries, and review collected data.
""")

st.markdown("""
### What you can do
- 🌾 **Register Crop Production**: record crop type, inputs, and yield
- 🗺️ **Register Field Boundaries**: draw field boundaries for each crop on an interactive map
- 📊 **View Data**: browse and download survey data and boundaries
""")

st.markdown("""
---
**Instructions**
1. Open **Register Crops** to enter production data and map boundaries per crop.
2. Review and export datasets in **View Data**.
""")