import streamlit as st
from modules.models import LibrarySystem
from modules.ui import load_css, render_sidebar
from modules.views import page_home, page_login_register, page_reader_history, page_admin_loans, page_admin_system

st.set_page_config(layout="wide", page_title="LibTech System - V41", page_icon="📚")

if 'lib' not in st.session_state:
    st.session_state.lib = LibrarySystem()

lib = st.session_state.lib

def main():
    load_css()
    if 'page' not in st.session_state: st.session_state.page = "home"
    render_sidebar(lib)
    
    page = st.session_state.page
    user = st.session_state.get('user')

    if page == "home": page_home(lib)
    elif page == "login": page_login_register(lib)
    elif page == "history":
        if user and user.role == 'reader': page_reader_history(lib)
        else: st.session_state.page = "home"; st.rerun()
    elif page == "loans":
        if user and user.role == 'librarian': page_admin_loans(lib)
        else: st.error("Access Denied")
    elif page == "system":
        if user and user.role == 'librarian': page_admin_system(lib)
        else: st.error("Access Denied")
    else: page_home(lib)

if __name__ == "__main__":
    main()