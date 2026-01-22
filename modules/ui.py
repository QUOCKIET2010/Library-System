import streamlit as st
import math
from datetime import datetime
import time

def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1f2937; }
        .hero-box { text-align: center; padding: 2rem 1rem; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); border-radius: 12px; margin-bottom: 25px; color: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .hero-title { font-size: 2.2rem; font-weight: 800; margin: 0; }
        .quote-text { font-style: italic; opacity: 0.9; margin-top: 5px; font-size: 1rem; }
        div[data-testid="stVerticalBlockBorderWrapper"] { border: 1px solid #e5e7eb; border-radius: 12px; background-color: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 1.5rem; padding: 15px; transition: box-shadow 0.2s; }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border-color: #818cf8; }
        .card-label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }
        .card-value { font-size: 0.95rem; color: #111827; font-weight: 500; line-height: 1.4; }
        .card-value-bold { font-size: 1rem; color: #111827; font-weight: 700; }
        .id-badge { font-family: monospace; font-weight: 700; color: #4338ca; background: #e0e7ff; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; }
        .status-badge { padding: 4px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; display: inline-block; }
        .st-active { background: #dbeafe; color: #1e40af; } .st-overdue { background: #fee2e2; color: #991b1b; } .st-process { background: #fef9c3; color: #854d0e; } .st-done { background: #f3f4f6; color: #374151; }    
        .modern-card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .detail-frame { padding: 15px; background: #fff; }
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stButton button { border-radius: 8px; }
        div[data-testid="column"] button { padding: 0.1rem 0.5rem !important; height: 36px !important; font-size: 14px !important; line-height: 1 !important; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

def show_badge_css(button_index):
    st.markdown(f"""<style>
        div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] button:nth-of-type({button_index}) {{ position: relative; overflow: visible !important; }}
        div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] button:nth-of-type({button_index})::after {{ content: ""; position: absolute; top: 0px; right: 0px; width: 10px; height: 10px; background-color: #ef4444; border-radius: 50%; border: 2px solid white; box-shadow: 0 1px 2px rgba(0,0,0,0.2); z-index: 99; }}
    </style>""", unsafe_allow_html=True)

def get_paginated_items(items, items_per_page, key_prefix):
    if not items: return [], 1, 0
    total_pages = math.ceil(len(items) / items_per_page)
    current_page = st.session_state.get(f"{key_prefix}_page", 1)
    if current_page > total_pages: current_page = total_pages
    if current_page < 1: current_page = 1
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    return items[start_idx:end_idx], current_page, total_pages

def render_pagination_footer(current_page, total_pages, key_prefix):
    if total_pages <= 1: return
    st.markdown("<br>", unsafe_allow_html=True)
    start_p = max(1, current_page - 2)
    end_p = min(total_pages, current_page + 2)
    if end_p - start_p < 4:
        if start_p == 1: end_p = min(5, total_pages)
        elif end_p == total_pages: start_p = max(1, total_pages - 4)
    num_buttons = (end_p - start_p + 1) + 2 
    _, center_col, _ = st.columns([5, 3, 5])
    with center_col:
        cols = st.columns(num_buttons, gap="small")
        if cols[0].button("◀", key=f"{key_prefix}_prev", disabled=(current_page==1), use_container_width=True):
            st.session_state[f"{key_prefix}_page"] = current_page - 1
            st.rerun()
        col_idx = 1
        for p in range(start_p, end_p + 1):
            is_active = (p == current_page)
            if cols[col_idx].button(str(p), key=f"{key_prefix}_p{p}", type="primary" if is_active else "secondary", use_container_width=True):
                st.session_state[f"{key_prefix}_page"] = p
                st.rerun()
            col_idx += 1
        if cols[col_idx].button("▶", key=f"{key_prefix}_next", disabled=(current_page==total_pages), use_container_width=True):
            st.session_state[f"{key_prefix}_page"] = current_page + 1
            st.rerun()

def render_sidebar(lib):
    if 'seen_pages' not in st.session_state: st.session_state.seen_pages = set()
    if st.session_state.get('page'): st.session_state.seen_pages.add(st.session_state.page)

    with st.sidebar:
        st.markdown("### 🏛️ LIBTECH SYSTEM")
        if st.session_state.get('user'):
            u = st.session_state.user
            st.info(f"👤 **{u.name}**\n\nID: `{u.uid}`")
            if st.button("🏠 Trang chủ", use_container_width=True): st.session_state.page="home"; st.rerun()
            
            if u.role == 'reader':
                overdue_count = sum(1 for s in lib.slips if s.user_uid == u.uid and s.status == 'active' and datetime.now() > s.due_date)
                if overdue_count > 0 and 'history' not in st.session_state.seen_pages: show_badge_css(2)
                if st.button("🎫 Phiếu mượn của tôi", use_container_width=True): st.session_state.page="history"; st.rerun()
            elif u.role == 'librarian':
                pending = sum(1 for s in lib.slips if s.status == 'processing')
                if pending > 0 and 'loans' not in st.session_state.seen_pages: show_badge_css(2)
                if st.button("📂 Quản lý Mượn/Trả", use_container_width=True): st.session_state.page="loans"; st.rerun()
                
                new_usr = sum(1 for usr in lib.users.values() if usr.role != 'librarian' and (datetime.now() - usr.created_at).days < 1)
                if new_usr > 0 and 'system' not in st.session_state.seen_pages: show_badge_css(3)
                if st.button("🛠️ Quản trị hệ thống", use_container_width=True): st.session_state.page="system"; st.rerun()
            
            st.divider()
            if st.button("🚪 Đăng xuất", type="primary", use_container_width=True): 
                st.session_state.user=None; st.session_state.page="home"; st.session_state.seen_pages = set()
                st.toast("Đã đăng xuất!", icon="👋"); time.sleep(1); st.rerun()
        else:
            if st.button("🏠 Trang chủ", use_container_width=True): st.session_state.page="home"; st.rerun()
            if st.button("🔐 Đăng nhập", type="primary", use_container_width=True): st.session_state.page="login"; st.rerun()
            if st.button("📝 Đăng ký", use_container_width=True): st.session_state.page="login"; st.session_state.auth_mode='register'; st.rerun()