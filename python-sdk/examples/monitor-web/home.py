import streamlit as st

st.set_page_config(
    page_title="Retis Monitor",
    page_icon="🔍",
    layout="wide"
)

st.title("Retis Monitor")
st.markdown("""
Welcome to Retis Monitor. Please select a page from the sidebar:
- **Plaza Status**: Monitor the current status of plazas
- **Pathway Editor**: Create and edit pathways
- **Pathfinder**: Execute and monitor pathfinder operations
""")
