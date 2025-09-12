import streamlit as st
import sqlite3
from database.db_setup import init_database

# Initialize database on startup
init_database()

st.set_page_config(page_title="Instructions - Agricultural Management System",
                   page_icon="📋",
                   layout="wide")

# Page namespace and state cleanup
PAGE_PREFIX = "instructions"
k = lambda name: f"{PAGE_PREFIX}:{name}"

def cleanup_foreign_keys(current_page):
    """Remove session state keys from other pages to prevent UI bleeding"""
    keys_to_delete = []
    for key in st.session_state.keys():
        if isinstance(key, str) and ":" in key:
            if not key.startswith(f"{current_page}:"):
                keys_to_delete.append(key)
    
    for key in keys_to_delete:
        del st.session_state[key]

# Clean up state from other pages
cleanup_foreign_keys(PAGE_PREFIX)

st.title("📋 Instructions")
st.markdown("""
Welcome to the Cropland Registration System! This application helps you:

- 🌾 **Register Crop Production**: Key crop information such a crop type, planting material sources and yield
- 🗺️ **Register Field Boundaries**: Draw field boundaries for each crop type on an interactive map
- 📊 **View Data**: View and download all collected survey data and field boundaries


""")

st.markdown("""
---
**Instructions:**
1. Use the **Register Crops** page to enter production data and map field boundaries for each crop type.
2. Review all collected data and insights in the **View Data** page
""")
