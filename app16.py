import streamlit as st
import json
import os
import random
import string
from datetime import datetime, timedelta
import time

# ==========================================
# 1. CẤU HÌNH & CSS (GIAO DIỆN CHI TIẾT - FULL INFO)
# ==========================================
st.set_page_config(layout="wide", page_title="LibTech System", page_icon="📚")

QUOTES = [
    "Việc đọc rất quan trọng. Nếu bạn biết cách đọc, cả thế giới sẽ mở ra cho bạn.",
    "Một cuốn sách thực sự hay nên đọc trong tuổi trẻ, rồi đọc lại khi đã trưởng thành.",
    "Sách là giấc mơ bạn cầm trên tay.",
    "Không có người bạn nào trung thành như một cuốn sách.",
    "Thư viện là kho tàng chứa đựng cả thế giới."
]

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1f2937; }

    /* --- HERO SECTION --- */
    .hero-box {
        text-align: center; padding: 2rem 1rem; 
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        border-radius: 12px; margin-bottom: 25px; color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .hero-title { font-size: 2.2rem; font-weight: 800; margin: 0; }
    .quote-text { font-style: italic; opacity: 0.9; margin-top: 5px; font-size: 1rem; }

    /* --- KHUNG THẺ (CARD CONTAINER) --- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        background-color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
        padding: 15px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #818cf8;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    /* --- TYPOGRAPHY TRONG THẺ --- */
    .card-label {
        font-size: 0.75rem; color: #6b7280; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 4px;
    }
    .card-value {
        font-size: 0.95rem; color: #111827; font-weight: 500; line-height: 1.4;
    }
    .card-value-bold {
        font-size: 1rem; color: #111827; font-weight: 700;
    }
    
    /* --- BADGES --- */
    .id-badge {
        font-family: 'Courier New', monospace; font-weight: 700; color: #4338ca;
        background: #e0e7ff; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem;
    }
    
    .status-badge {
        padding: 4px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; display: inline-block;
    }
    .st-active { background: #dbeafe; color: #1e40af; }   
    .st-overdue { background: #fee2e2; color: #991b1b; } 
    .st-process { background: #fef9c3; color: #854d0e; }  
    .st-done { background: #f3f4f6; color: #374151; }    

    /* --- MODERN CARD (GRID VIEW) --- */
    .modern-card {
        background: white; border: 1px solid #e5e7eb; border-radius: 12px;
        overflow: hidden; margin-bottom: 15px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .detail-frame { padding: 15px; background: #fff; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { border-radius: 8px; }
    .stButton button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MODELS & BACKEND
# ==========================================

def safe_parse_date(date_input):
    if isinstance(date_input, datetime): return date_input
    if not date_input: return None
    str_date = str(date_input).strip()
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
    for fmt in formats:
        try: return datetime.strptime(str_date, fmt)
        except ValueError: continue
    return datetime.now()

class Book:
    def __init__(self, id, title, author, category, image, desc, qty, price=100000, year=2020, borrowed=0, **kwargs):
        self.id = id; self.title = title; self.author = author; self.category = category; self.year = year
        self.image = image; self.desc = desc; self.qty = int(qty); self.price = int(price); self.borrowed = int(borrowed)
    def available(self): return self.qty - self.borrowed
    def to_dict(self): return self.__dict__

class User:
    def __init__(self, uid, username, password, name, role="reader", phone="", email="", **kwargs):
        self.uid = uid; self.username = username; self.password = password; self.name = name
        self.role = role; self.phone = phone; self.email = email
    def to_dict(self): return self.__dict__

class BorrowSlip:
    def __init__(self, id, user_uid, user_name, user_phone, user_email, items, borrow_date, due_date, return_date=None, status="active", fine_details=None, total_fine=0, **kwargs):
        self.id = id; self.user_uid = user_uid; self.user_name = user_name; self.user_phone = user_phone; self.user_email = user_email
        self.items = items
        self.borrow_date = safe_parse_date(borrow_date)
        self.due_date = safe_parse_date(due_date)
        self.return_date = safe_parse_date(return_date) if return_date else None
        self.status = status; self.fine_details = fine_details or []; self.total_fine = total_fine
    
    def get_status_info(self):
        if self.status == 'completed': return "ĐÃ HOÀN THÀNH", "st-done"
        if self.status == 'processing': return "CHỜ XỬ LÝ", "st-process"
        if datetime.now() > (self.due_date if self.due_date else datetime.now()): return "QUÁ HẠN", "st-overdue"
        return "ĐANG MƯỢN", "st-active"

    def to_dict(self):
        d = self.__dict__.copy()
        d['borrow_date'] = str(self.borrow_date); d['due_date'] = str(self.due_date)
        d['return_date'] = str(self.return_date) if self.return_date else None
        return d

class LibrarySystem:
    def __init__(self):
        self.files = {'books': 'books.json', 'users': 'users.json', 'slips': 'slips.json'}
        self.books = []; self.users = {}; self.slips = []
        self.load_data()

    def load_data(self):
        if os.path.exists(self.files['books']):
            with open(self.files['books'], 'r', encoding='utf-8') as f: self.books = [Book(**b) for b in json.load(f)]
        else:
            self.books = [
                Book(1, "Clean Code", "Robert Martin", "Công nghệ", "https://images.unsplash.com/photo-1516116216624-53e697fedbea", "Hướng dẫn viết code sạch.", 5, 300000, 2008),
                Book(2, "Đắc Nhân Tâm", "Dale Carnegie", "Kỹ năng", "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c", "Nghệ thuật thu phục lòng người.", 10, 150000, 1936),
                Book(3, "Nhà Giả Kim", "Paulo Coelho", "Văn học", "https://images.unsplash.com/photo-1512820790803-83ca734da794", "Hành trình đi tìm kho báu.", 7, 120000, 1988)
            ]
            self.save_data('books')
        if os.path.exists(self.files['users']):
            with open(self.files['users'], 'r', encoding='utf-8') as f: self.users = {k: User(**v) for k,v in json.load(f).items()}
        else:
            self.users = {'admin': User("AD-001", "admin", "123", "Quản Trị Viên", "librarian", "090999", "admin@lib.com")}
            self.save_data('users')
        if os.path.exists(self.files['slips']):
             with open(self.files['slips'], 'r', encoding='utf-8') as f: self.slips = [BorrowSlip(**s) for s in json.load(f)]

    def save_data(self, type):
        if type == 'books': f, d = self.files['books'], [b.to_dict() for b in self.books]
        elif type == 'users': f, d = self.files['users'], {k:v.to_dict() for k,v in self.users.items()}
        elif type == 'slips': f, d = self.files['slips'], [s.to_dict() for s in self.slips]
        with open(f, 'w', encoding='utf-8') as file: json.dump(d, file, ensure_ascii=False, indent=4)

    # --- LOGIC ---
    def login(self, u, p):
        user = self.users.get(u)
        return user if user and user.password == p else None
    def register(self, d):
        if d['username'] in self.users: return False, "Username đã tồn tại!"
        uid = f"U{len(self.users)+1:03d}"
        self.users[d['username']] = User(uid, d['username'], d['password'], d['name'], "reader", d['phone'], d['email'])
        self.save_data('users'); return True, "Đăng ký thành công!"
    def reset_password(self, username, new_pass):
        if username not in self.users: return False, "Username không tồn tại!"
        self.users[username].password = new_pass
        self.save_data('users'); return True, "Đổi mật khẩu thành công!"
    def add_or_update_book(self, d, book_id=None):
        if book_id:
            book = next((b for b in self.books if b.id == book_id), None)
            if book:
                for k, v in d.items(): setattr(book, k, v)
                self.save_data('books'); return True, "Cập nhật thành công!"
            return False, "Không tìm thấy"
        else:
            new_id = max([b.id for b in self.books] or [0]) + 1
            self.books.append(Book(new_id, **d))
            self.save_data('books'); return True, "Thêm mới thành công!"
    def delete_book(self, book_id):
        book = next((b for b in self.books if b.id == book_id), None)
        if not book: return False, "Không tìm thấy."
        is_borrowed = any(any(i['book_id'] == book_id for i in s.items) for s in self.slips if s.status in ['active', 'processing'])
        if is_borrowed: return False, "Sách đang có người mượn!"
        self.books.remove(book); self.save_data('books'); return True, "Đã xóa sách!"
    def update_user_info(self, old_u, d):
        user = self.users.get(old_u)
        if not user: return False, "User không tồn tại"
        if d['username'] != old_u and d['username'] in self.users: return False, "Username đã tồn tại"
        if d['username'] != old_u: del self.users[old_u]
        for k, v in d.items(): setattr(user, k, v)
        self.users[d['username']] = user; self.save_data('users'); return True, "Cập nhật thành công!"
    def delete_user_logic(self, target_u, admin_uid):
        target = self.users.get(target_u)
        if not target or target.role == 'librarian' or target.uid == admin_uid: return False, "Không thể xóa!"
        if any(s.user_uid == target.uid and s.status in ['active', 'processing'] for s in self.slips): return False, "Đang mượn sách!"
        del self.users[target_u]; self.save_data('users'); return True, "Đã xóa thành viên!"
    def borrow_book(self, bid, user):
        book = next((b for b in self.books if b.id == bid), None)
        if not book or book.available() <= 0: return False, "Sách không khả dụng."
        slip_id = f"M{int(time.time())}" 
        new_slip = BorrowSlip(slip_id, user.uid, user.name, user.phone, user.email,
                                [{'book_id': book.id, 'title': book.title, 'price': book.price}], 
                                datetime.now(), datetime.now() + timedelta(days=7))
        self.slips.append(new_slip)
        book.borrowed += 1
        self.save_data('books'); self.save_data('slips'); return True, f"Mượn '{book.title}' thành công!"
    def request_return(self, slip_id):
        slip = next((s for s in self.slips if s.id == slip_id), None)
        if slip and slip.status == 'active':
            slip.status = 'processing'; self.save_data('slips'); return True, "Đã gửi yêu cầu!"
        return False, "Lỗi trạng thái."
    def confirm_return(self, slip_id, conditions):
        slip = next((s for s in self.slips if s.id == slip_id), None)
        if not slip: return False, "Lỗi."
        slip.return_date = datetime.now()
        total_fine = 0; details = []
        check_date = slip.due_date if slip.due_date else datetime.now()
        if datetime.now() > check_date:
            days = (datetime.now() - check_date).days
            if days > 0:
                fee = days * 5000 * len(slip.items)
                total_fine += fee; details.append(f"Quá hạn {days} ngày: {fee:,}đ")
        for idx, item in enumerate(slip.items):
            cond = conditions.get(f"cond_{idx}", 'normal')
            book = next((b for b in self.books if b.id == item['book_id']), None)
            fee = 0
            if cond == 'dirty': fee = int(item['price']*0.3); details.append(f"Sách '{item['title']}' bẩn: {fee:,}đ")
            elif cond == 'lost': fee = item['price']; details.append(f"Mất sách '{item['title']}': {fee:,}đ")
            total_fine += fee
            if cond != 'lost' and book: book.borrowed = max(0, book.borrowed - 1)
        slip.total_fine = total_fine; slip.fine_details = details; slip.status = 'completed'
        self.save_data('books'); self.save_data('slips'); return True, "Hoàn tất!"

if 'lib' not in st.session_state: st.session_state.lib = LibrarySystem()
lib = st.session_state.lib

# ==========================================
# 3. UI COMPONENTS & DIALOGS
# ==========================================

def render_sidebar():
    with st.sidebar:
        st.markdown("### 🏛️ LIBTECH SYSTEM")
        if st.session_state.get('user'):
            u = st.session_state.user
            st.info(f"👤 **{u.name}**\n\nID: `{u.uid}`")
            if st.button("🏠 Trang chủ", use_container_width=True): st.session_state.page="home"; st.rerun()
            if u.role == 'reader':
                if st.button("🎫 Phiếu mượn của tôi", use_container_width=True): st.session_state.page="history"; st.rerun()
            elif u.role == 'librarian':
                if st.button("📂 Quản lý Mượn/Trả", use_container_width=True): st.session_state.page="loans"; st.rerun()
                if st.button("🛠️ Quản trị hệ thống", use_container_width=True): st.session_state.page="system"; st.rerun()
            st.divider()
            if st.button("🚪 Đăng xuất", type="primary", use_container_width=True): 
                st.session_state.user=None; st.session_state.page="home"
                st.toast("Đã đăng xuất thành công!", icon="👋"); time.sleep(1); st.rerun()
        else:
            if st.button("🏠 Trang chủ", use_container_width=True): st.session_state.page="home"; st.rerun()
            if st.button("🔐 Đăng nhập", type="primary", use_container_width=True): st.session_state.page="login"; st.rerun()
            if st.button("📝 Đăng ký", use_container_width=True): 
                st.session_state.page="login"; st.session_state.auth_mode='register'; st.rerun()

# --- DIALOGS ---

@st.dialog("📘 Chi tiết tác phẩm", width="large")
def modal_book_detail(book):
    st.markdown('<div class="detail-frame">', unsafe_allow_html=True)
    c1, c2 = st.columns([1.2, 2], gap="large")
    with c1:
        st.markdown(f'<div style="padding:5px; border:1px solid #eee; border-radius:8px;"><img src="{book.image}" style="width:100%; border-radius:6px;"></div>', unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; margin-top:10px;'><span class='id-badge'>ID: {book.id}</span></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<h2 style='margin:0 0 5px 0;'>{book.title}</h2>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin-bottom:15px; font-style:italic; color:#555;'>Tác giả: <b>{book.author}</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin-bottom:8px; border-bottom:1px dashed #eee; padding-bottom:5px;'>📂 <b>Thể loại:</b> {book.category}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin-bottom:8px; border-bottom:1px dashed #eee; padding-bottom:5px;'>📅 <b>Năm XB:</b> {book.year}</div>", unsafe_allow_html=True)
        avail = book.available()
        st.markdown(f"<div style='margin-bottom:8px; border-bottom:1px dashed #eee; padding-bottom:5px;'>📦 <b>Kho:</b> Còn <b style='color:#2563eb'>{avail}</b> / {book.qty} cuốn</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin: 15px 0; font-size:1.4rem; color:#dc2626; font-weight:800; padding:10px; background:#fef2f2; border-radius:8px; border:1px solid #fee2e2; width:fit-content;'>{book.price:,} VNĐ</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background:#f9fafb; padding:15px; border-radius:8px; border:1px solid #eee; font-size:0.95rem; line-height:1.6; color:#4b5563;'><b>Mô tả:</b><br>{book.desc}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(2)
    if cols[0].button("Đóng", use_container_width=True): st.rerun()
    if avail > 0:
        if cols[1].button("🚀 Mượn ngay", type="primary", use_container_width=True):
            if not st.session_state.get('user'): st.error("Bạn cần đăng nhập!"); time.sleep(1)
            elif st.session_state.user.role == 'librarian': st.warning("Thủ thư vui lòng dùng quyền Admin.")
            else:
                ok, msg = lib.borrow_book(book.id, st.session_state.user)
                if ok: st.toast(msg, icon="📚"); time.sleep(1); st.rerun()
                else: st.error(msg)
    else: cols[1].button("🚫 Hết hàng", disabled=True, use_container_width=True)

@st.dialog("⚠️ Xác nhận")
def modal_confirm_delete(type, id, name):
    st.write(f"Bạn có chắc chắn muốn xóa **{name}**?")
    c1, c2 = st.columns(2)
    if c1.button("Hủy", use_container_width=True): st.rerun()
    if c2.button("Xóa ngay", type="primary", use_container_width=True):
        if type == 'book': ok, msg = lib.delete_book(id)
        else: ok, msg = lib.delete_user_logic(id, st.session_state.user.uid)
        if ok: st.toast(msg, icon="🗑️"); time.sleep(1); st.rerun()
        else: st.error(msg)

@st.dialog("✏️ Cập nhật Sách")
def modal_edit_book(book):
    with st.form("edit_book_form"):
        st.caption(f"Đang sửa ID: {book.id}")
        t = st.text_input("Tên sách", value=book.title)
        a = st.text_input("Tác giả", value=book.author)
        c1, c2 = st.columns(2)
        cat = c1.selectbox("Thể loại", ["Công nghệ", "Kinh tế", "Văn học", "Kỹ năng", "Khoa học"], index=0)
        y = c2.number_input("Năm XB", value=book.year)
        c3, c4 = st.columns(2)
        q = c3.number_input("Tổng nhập kho", value=book.qty, min_value=1)
        b_count = c4.number_input("Đang được mượn (Thực tế)", value=book.borrowed, min_value=0)
        p = st.number_input("Giá bìa (VNĐ)", value=book.price)
        d = st.text_area("Mô tả", value=book.desc)
        img = st.text_input("Link ảnh", value=book.image)
        if st.form_submit_button("Lưu thay đổi", type="primary"):
            data = {'title':t, 'author':a, 'category':cat, 'year':y, 'qty':q, 'borrowed':b_count, 'price':p, 'desc':d, 'image':img}
            ok, msg = lib.add_or_update_book(data, book_id=book.id)
            st.toast(msg, icon="💾"); time.sleep(1); st.rerun()

@st.dialog("✏️ Cập nhật User")
def modal_edit_user(u_obj):
    with st.form("edit_user_form"):
        st.caption(f"UID: {u_obj.uid}")
        new_name = st.text_input("Họ tên", value=u_obj.name)
        new_phone = st.text_input("SĐT", value=u_obj.phone)
        new_email = st.text_input("Email", value=u_obj.email)
        if st.form_submit_button("Lưu thay đổi", type="primary"):
            d = {'name': new_name, 'phone': new_phone, 'email': new_email, 'username': u_obj.username} 
            ok, msg = lib.update_user_info(u_obj.username, d)
            if ok: st.toast(msg, icon="✅"); time.sleep(1); st.rerun()
            else: st.error(msg)

@st.dialog("💸 Xử lý Trả sách", width="large")
def modal_process_return(slip):
    st.subheader(f"Phiếu: {slip.id}")
    st.caption(f"Người mượn: {slip.user_name} | Hạn trả: {slip.due_date.strftime('%d/%m/%Y')}")
    check_date = slip.due_date if slip.due_date else datetime.now()
    if datetime.now() > check_date:
        days = (datetime.now() - check_date).days
        fee = days * 5000 * len(slip.items)
        st.error(f"⚠️ Quá hạn {days} ngày. Phạt dự kiến: {fee:,}đ")
    with st.form(f"ret_{slip.id}"):
        conds = {}
        for idx, item in enumerate(slip.items):
            c1, c2 = st.columns([2, 1])
            c1.markdown(f"📘 **{item['title']}** (ID: `{item['book_id']}`)")
            conds[f"cond_{idx}"] = c2.selectbox("Tình trạng", ["normal", "dirty", "lost"], key=f"sel_{slip.id}_{idx}",
                                              format_func=lambda x: "✅ Tốt" if x=='normal' else "⚠️ Bẩn (30%)" if x=='dirty' else "❌ Mất (100%)")
        st.markdown("---")
        if st.form_submit_button("Hoàn tất & Tính phí", type="primary"):
            ok, msg = lib.confirm_return(slip.id, conds)
            st.toast(msg, icon="💰"); time.sleep(1.5); st.rerun()

# ==========================================
# 4. TRANG CHỨC NĂNG (GIAO DIỆN FULL DETAIL CHO ADMIN)
# ==========================================

def page_home():
    st.markdown(f"""<div class="hero-box"><h1 class="hero-title">THƯ VIỆN TRI THỨC</h1><div class="quote-text">"{random.choice(QUOTES)}"</div></div>""", unsafe_allow_html=True)
    with st.form("search_form"):
        c_search, c_filter, c_btn = st.columns([3, 1, 0.5])
        search_txt = c_search.text_input("Search", placeholder="Tìm tên sách, tác giả...", label_visibility="collapsed")
        all_cats = ["Tất cả"] + list(set([b.category for b in lib.books]))
        selected_cat = c_filter.selectbox("Category", all_cats, label_visibility="collapsed")
        c_btn.form_submit_button("🔍", use_container_width=True)
    
    filtered = lib.books
    if search_txt: filtered = [b for b in filtered if search_txt.lower() in b.title.lower()]
    if selected_cat != "Tất cả": filtered = [b for b in filtered if b.category == selected_cat]

    cols = st.columns(4)
    for i, book in enumerate(filtered):
        with cols[i % 4]:
            with st.container():
                st.markdown(f"""
                <div class="modern-card">
                    <img src="{book.image}" style="width:100%; height:180px; object-fit:cover;">
                    <div style="padding:12px;">
                        <div style="font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{book.title}</div>
                        <div style="font-size:0.85rem; color:#666;">{book.author}</div>
                        <div style="font-size:0.75rem; color:#999; margin-top:4px;">ID: {book.id}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button("Chi tiết", key=f"d_{book.id}", use_container_width=True): modal_book_detail(book)
                dis = book.available() <= 0
                if b2.button("Mượn", key=f"b_{book.id}", disabled=dis, type="primary" if not dis else "secondary", use_container_width=True):
                    if not st.session_state.get('user'): st.toast("Vui lòng đăng nhập!", icon="🔒")
                    else: 
                        ok, msg = lib.borrow_book(book.id, st.session_state.user)
                        if ok: st.toast(msg, icon="📚"); time.sleep(1); st.rerun()
                        else: st.error(msg)

def page_reader_history():
    st.title("📂 Phiếu mượn của tôi")
    u_uid = st.session_state.user.uid
    tab1, tab2 = st.tabs(["📘 Đang hoạt động", "📜 Lịch sử"])
    
    with tab1:
        active = [s for s in lib.slips if s.user_uid == u_uid and s.status in ['active', 'processing']]
        if not active: st.info("Bạn không có sách nào đang mượn.")
        for s in active:
            st_lbl, st_cls = s.get_status_info()
            # THẺ CHI TIẾT
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 3, 2, 1])
                c1.markdown(f"<div class='card-label'>MÃ PHIẾU</div><span class='id-badge'>#{s.id}</span>", unsafe_allow_html=True)
                
                # Sách
                bk_html = "".join([f"<div>• {i['title']}</div>" for i in s.items])
                c2.markdown(f"<div class='card-label'>SÁCH MƯỢN</div><div class='card-value'>{bk_html}</div>", unsafe_allow_html=True)
                
                # Thời gian
                c3.markdown(f"""
                <div class='card-label'>THỜI GIAN</div>
                <div class='card-value'>Ngày mượn: {s.borrow_date.strftime('%d/%m/%Y')}</div>
                <div class='card-value'>Hạn trả: <b>{s.due_date.strftime('%d/%m/%Y')}</b></div>
                """, unsafe_allow_html=True)
                
                # Nút
                c4.markdown(f"<div style='margin-bottom:5px'><span class='status-badge {st_cls}'>{st_lbl}</span></div>", unsafe_allow_html=True)
                if s.status == 'active':
                    if c4.button("Trả sách", key=f"req_{s.id}", type="primary", use_container_width=True): 
                        lib.request_return(s.id); st.toast("Đã gửi yêu cầu!", icon="📨"); time.sleep(1); st.rerun()
                else: c4.button("⏳", disabled=True, key=f"w_{s.id}")

    with tab2:
        history = [s for s in lib.slips if s.user_uid == u_uid and s.status == 'completed']
        history.sort(key=lambda x: x.return_date, reverse=True)
        if not history: st.info("Chưa có lịch sử.")
        for s in history:
            with st.container(border=True):
                k1, k2, k3, k4 = st.columns([1, 3, 2, 2])
                k1.markdown(f"<div class='card-label'>MÃ PHIẾU</div><span class='id-badge'>#{s.id}</span>", unsafe_allow_html=True)
                
                bk_html = "".join([f"<div>• {i['title']}</div>" for i in s.items])
                k2.markdown(f"<div class='card-label'>SÁCH ĐÃ TRẢ</div><div class='card-value'>{bk_html}</div>", unsafe_allow_html=True)
                
                k3.markdown(f"<div class='card-label'>NGÀY TRẢ</div><div class='card-value'>{s.return_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
                
                # Phạt
                if s.total_fine > 0:
                    k4.markdown(f"<div class='card-label'>PHẠT</div><div style='color:red; font-weight:bold'>{s.total_fine:,}đ</div>", unsafe_allow_html=True)
                    with k4.popover("Chi tiết lỗi"):
                        for r in s.fine_details: st.write(f"- {r}")
                else:
                    k4.markdown("<div class='card-label'>TRẠNG THÁI</div><div style='color:green; font-weight:bold'>Hoàn thành</div>", unsafe_allow_html=True)

def page_admin_loans():
    st.title("📂 Quản lý Phiếu Mượn (Admin)")
    t1, t2 = st.tabs(["⚡ Cần xử lý & Đang mượn", "📜 Lịch sử trả"])
    
    with t1:
        slips = [s for s in lib.slips if s.status in ['active', 'processing']]
        slips.sort(key=lambda x: (0 if x.status == 'processing' else 1, x.due_date or datetime.now()))
        
        if not slips: st.success("Không có phiếu nào.")
        
        for s in slips:
            with st.container(border=True): # KHUNG NỔI RIÊNG BIỆT CHO TỪNG PHIẾU
                st_lbl, st_cls = s.get_status_info()
                is_proc = s.status == 'processing'
                
                # Hàng 1: Header (Mã phiếu + Trạng thái)
                r1_c1, r1_c2 = st.columns([1, 1])
                r1_c1.markdown(f"🎫 **Phiếu #** <span class='id-badge'>{s.id}</span>", unsafe_allow_html=True)
                r1_c2.markdown(f"<div style='text-align:right'><span class='status-badge {st_cls}'>{st_lbl}</span></div>", unsafe_allow_html=True)
                st.divider() # Đường kẻ ngăn cách
                
                # Hàng 2: Thông tin chi tiết (3 Cột)
                c1, c2, c3 = st.columns([1.2, 1.5, 1])
                
                # Cột 1: Người mượn (FULL INFO)
                c1.markdown("<div class='card-label'>👤 NGƯỜI MƯỢN</div>", unsafe_allow_html=True)
                c1.markdown(f"""
                <div class='card-value-bold'>{s.user_name}</div>
                <div class='card-value'>ID: <code>{s.user_uid}</code></div>
                <div class='card-value'>📞 {s.user_phone}</div>
                <div class='card-value'>📧 {s.user_email}</div>
                """, unsafe_allow_html=True)
                
                # Cột 2: Sách & Thời gian (FULL INFO)
                c2.markdown("<div class='card-label'>📘 SÁCH & THỜI GIAN</div>", unsafe_allow_html=True)
                bk_list = "".join([f"<div>• {i['title']} <span style='color:#666; font-size:0.85em'>(Mã: {i['book_id']})</span></div>" for i in s.items])
                c2.markdown(f"<div class='card-value' style='margin-bottom:8px'>{bk_list}</div>", unsafe_allow_html=True)
                
                is_late = datetime.now() > (s.due_date or datetime.now())
                date_color = "#dc2626" if is_late else "#111"
                c2.markdown(f"""
                <div class='card-value'>📅 Ngày mượn: {s.borrow_date.strftime('%d/%m/%Y')}</div>
                <div class='card-value' style='color:{date_color}'>⏳ Hạn trả: <b>{(s.due_date or datetime.now()).strftime('%d/%m/%Y')}</b></div>
                """, unsafe_allow_html=True)
                
                # Cột 3: Hành động
                c3.markdown("<div class='card-label'>THAO TÁC</div>", unsafe_allow_html=True)
                btn_txt = "⚡ Xử lý ngay" if is_proc else "Thu hồi / Trả sách"
                if c3.button(btn_txt, key=f"adm_btn_{s.id}", type="primary" if is_proc else "secondary", use_container_width=True):
                    modal_process_return(s)

    with t2:
        done = [s for s in lib.slips if s.status == 'completed']
        done.sort(key=lambda x: x.return_date, reverse=True)
        
        if not done: st.info("Chưa có dữ liệu.")
        for s in done:
            with st.container(border=True):
                # Hàng 1: ID + Trạng thái
                d1, d2 = st.columns([1, 1])
                d1.markdown(f"✅ **Phiếu #** <span class='id-badge'>{s.id}</span>", unsafe_allow_html=True)
                d2.markdown("<div style='text-align:right'><span class='status-badge st-done'>ĐÃ HOÀN THÀNH</span></div>", unsafe_allow_html=True)
                st.divider()
                
                # Hàng 2: Chi tiết 3 cột
                k1, k2, k3 = st.columns([1.2, 1.5, 1])
                
                # Người dùng
                k1.markdown("<div class='card-label'>👤 NGƯỜI MƯỢN</div>", unsafe_allow_html=True)
                k1.markdown(f"""
                <div class='card-value-bold'>{s.user_name}</div>
                <div class='card-value'>ID: <code>{s.user_uid}</code></div>
                <div class='card-value'>📞 {s.user_phone} | 📧 {s.user_email}</div>
                """, unsafe_allow_html=True)
                
                # Sách
                k2.markdown("<div class='card-label'>📘 SÁCH ĐÃ TRẢ</div>", unsafe_allow_html=True)
                bk_list = "".join([f"<div>• {i['title']} <span style='color:#666'>(Mã: {i['book_id']})</span></div>" for i in s.items])
                k2.markdown(f"<div class='card-value'>{bk_list}</div>", unsafe_allow_html=True)
                k2.markdown(f"<div class='card-value' style='margin-top:5px'>📅 Ngày mượn: {s.borrow_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
                k2.markdown(f"<div class='card-value'>📅 Ngày trả: <b>{s.return_date.strftime('%d/%m/%Y')}</b></div>", unsafe_allow_html=True)
                
                # Tài chính / Phạt
                k3.markdown("<div class='card-label'>KẾT QUẢ / PHẠT</div>", unsafe_allow_html=True)
                if s.total_fine > 0:
                    k3.markdown(f"<div style='color:#dc2626; font-size:1.1rem; font-weight:bold'>{s.total_fine:,}đ</div>", unsafe_allow_html=True)
                    with k3.popover("Xem lỗi phạt"):
                        for r in s.fine_details: st.write(f"- {r}")
                else:
                    k3.success("Không có lỗi")

def page_admin_system():
    st.title("🛠️ Quản Trị Hệ Thống")
    t1, t2 = st.tabs(["👥 Quản Lý Thành Viên", "📚 Quản Lý Kho Sách"])
    
    with t1:
        with st.form("search_user"):
            c1, c2 = st.columns([4,1])
            search = c1.text_input("Tìm thành viên...", placeholder="Tên, SĐT, Email...", label_visibility="collapsed")
            c2.form_submit_button("Tìm kiếm", use_container_width=True)
        users = list(lib.users.values())
        if search: users = [u for u in users if search.lower() in u.name.lower() or search in u.phone]
        
        for u in users:
            with st.container(border=True): # THẺ RIÊNG BIỆT CHO USER
                c1, c2, c3, c4 = st.columns([1, 2, 2, 1.5])
                c1.markdown(f"<div class='card-label'>UID</div><span class='id-badge'>{u.uid}</span>", unsafe_allow_html=True)
                c2.markdown(f"<div class='card-label'>THÔNG TIN</div><div class='card-value-bold'>{u.name}</div><div class='card-value'>@{u.username} | Role: {u.role}</div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='card-label'>LIÊN HỆ</div><div class='card-value'>📞 {u.phone}</div><div class='card-value'>📧 {u.email}</div>", unsafe_allow_html=True)
                
                c4.markdown("<div class='card-label'>THAO TÁC</div>", unsafe_allow_html=True)
                if u.role != 'librarian':
                    col_b1, col_b2 = c4.columns(2)
                    if col_b1.button("✏️", key=f"eu_{u.uid}", use_container_width=True): modal_edit_user(u)
                    if col_b2.button("🗑️", key=f"du_{u.uid}", type="primary", use_container_width=True): modal_confirm_delete('user', u.username, u.name)
                else:
                    c4.markdown("<span class='status-badge st-active'>ADMIN</span>", unsafe_allow_html=True)

    with t2:
        if st.button("➕ Thêm sách mới", type="primary"): modal_edit_book(Book(0, "", "", "Công nghệ", "", "", 1, 100000, 2024))
        
        for b in lib.books:
            with st.container(border=True): # THẺ RIÊNG BIỆT CHO SÁCH
                c1, c2, c3, c4, c5 = st.columns([0.8, 2, 1.5, 1, 1.5])
                c1.markdown(f'<img src="{b.image}" style="width:50px; height:70px; object-fit:cover; border-radius:4px;">', unsafe_allow_html=True)
                c2.markdown(f"<div class='card-label'>THÔNG TIN</div><div class='card-value-bold'>{b.title}</div><div class='card-value'>{b.author}</div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='card-label'>KHO & ID</div><div class='card-value'>ID: <span class='id-badge'>{b.id}</span></div><div class='card-value'>Kho: <b>{b.available()}/{b.qty}</b></div>", unsafe_allow_html=True)
                c4.markdown(f"<div class='card-label'>GIÁ</div><div class='card-value-bold'>{b.price:,}đ</div>", unsafe_allow_html=True)
                
                c5.markdown("<div class='card-label'>THAO TÁC</div>", unsafe_allow_html=True)
                col_b1, col_b2 = c5.columns(2)
                if col_b1.button("✏️", key=f"eb_{b.id}", use_container_width=True): modal_edit_book(b)
                if col_b2.button("🗑️", key=f"db_{b.id}", type="primary", use_container_width=True): modal_confirm_delete('book', b.id, b.title)

# --- AUTH & MAIN ---
def get_captcha_code(): return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
def page_login_register():
    st.markdown("<br>", unsafe_allow_html=True)
    if 'auth_mode' not in st.session_state: st.session_state.auth_mode = 'login'
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.container(border=True):
            if st.session_state.auth_mode == 'login':
                st.subheader("👋 Đăng Nhập")
                with st.form("login_form"):
                    u = st.text_input("Username")
                    p = st.text_input("Password", type="password")
                    if st.form_submit_button("Đăng nhập", type="primary", use_container_width=True):
                        user = lib.login(u, p)
                        if user: 
                            st.toast(f"Chào mừng {user.name} quay lại!", icon="🎉"); time.sleep(1)
                            st.session_state.user = user; st.session_state.page = "home"; st.rerun()
                        else: st.error("Sai thông tin!")
                st.markdown("---")
                c_a, c_b = st.columns(2)
                if c_a.button("Tạo tài khoản", use_container_width=True): st.session_state.auth_mode='register'; st.rerun()
                if c_b.button("Quên mật khẩu?", use_container_width=True): st.session_state.auth_mode='forgot'; st.rerun()
            elif st.session_state.auth_mode == 'register':
                st.subheader("✨ Đăng Ký")
                with st.form("reg_form"):
                    u=st.text_input("Username*"); p=st.text_input("Password*", type="password")
                    n=st.text_input("Họ tên*"); ph=st.text_input("SĐT"); e=st.text_input("Email")
                    if st.form_submit_button("Đăng ký ngay", type="primary", use_container_width=True):
                        ok, msg = lib.register({'username':u, 'password':p, 'name':n, 'phone':ph, 'email':e})
                        if ok: st.toast(msg, icon="✨"); time.sleep(1); st.session_state.auth_mode='login'; st.rerun()
                        else: st.error(msg)
                if st.button("Quay lại", use_container_width=True): st.session_state.auth_mode='login'; st.rerun()
            elif st.session_state.auth_mode == 'forgot':
                st.subheader("🔐 Cấp lại Mật khẩu")
                if 'captcha' not in st.session_state: st.session_state.captcha = get_captcha_code()
                u_reset = st.text_input("Username")
                st.markdown(f"<div style='background:#f3f4f6; padding:10px; text-align:center; font-family:monospace; font-size:24px; letter-spacing:8px;'>{st.session_state.captcha}</div>", unsafe_allow_html=True)
                c_cap1, c_cap2 = st.columns([2, 1])
                cap_in = c_cap1.text_input("Mã xác thực", label_visibility="collapsed")
                if c_cap2.button("🔄"): st.session_state.captcha = get_captcha_code(); st.rerun()
                new_p = st.text_input("Mật khẩu mới", type="password")
                if st.button("Xác nhận đổi", type="primary", use_container_width=True):
                    if cap_in != st.session_state.captcha: st.error("Sai mã Captcha"); st.session_state.captcha = get_captcha_code()
                    else:
                        ok, msg = lib.reset_password(u_reset, new_p)
                        if ok: st.toast(msg, icon="🔐"); time.sleep(1); st.session_state.auth_mode='login'; st.rerun()
                        else: st.error(msg)
                if st.button("Hủy bỏ", use_container_width=True): st.session_state.auth_mode='login'; st.rerun()

def main():
    if 'page' not in st.session_state: st.session_state.page = "home"
    render_sidebar()
    page = st.session_state.page
    user = st.session_state.get('user')
    if page == "home": page_home()
    elif page == "login": page_login_register()
    elif page == "history":
        if user and user.role == 'reader': page_reader_history()
        else: st.session_state.page = "home"; st.rerun()
    elif page == "loans":
        if user and user.role == 'librarian': page_admin_loans()
        else: st.error("Access Denied")
    elif page == "system":
        if user and user.role == 'librarian': page_admin_system()
        else: st.error("Access Denied")
    else: page_home()

if __name__ == "__main__":
    main()