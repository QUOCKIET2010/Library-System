import streamlit as st
import time
import random
from datetime import datetime
from .models import Book
from .utils import get_captcha_code
from .ui import get_paginated_items, render_pagination_footer

QUOTES = [
    "Việc đọc rất quan trọng. Nếu bạn biết cách đọc, cả thế giới sẽ mở ra cho bạn.",
    "Một cuốn sách thực sự hay nên đọc trong tuổi trẻ, rồi đọc lại khi đã trưởng thành.",
    "Sách là giấc mơ bạn cầm trên tay.",
    "Không có người bạn nào trung thành như một cuốn sách.",
    "Thư viện là kho tàng chứa đựng cả thế giới."
]

# ==========================================
# 1. DIALOGS (HỘP THOẠI)
# ==========================================

@st.dialog("📘 Chi tiết tác phẩm", width="large")
def modal_book_detail(book, lib):
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
            if not st.session_state.get('user'): 
                st.error("Bạn cần đăng nhập!"); time.sleep(1)
            elif st.session_state.user.role == 'librarian': 
                st.warning("Thủ thư vui lòng dùng quyền Admin.")
            else:
                ok, msg = lib.borrow_book(book.id, st.session_state.user)
                if ok: 
                    st.toast(msg, icon="📚"); time.sleep(1.5); st.rerun()
                else: 
                    st.error(msg)
    else: 
        cols[1].button("🚫 Hết hàng", disabled=True, use_container_width=True)

@st.dialog("⚠️ Xác nhận")
def modal_confirm_delete(type, id, name, lib):
    st.write(f"Bạn có chắc chắn muốn xóa **{name}**?")
    c1, c2 = st.columns(2)
    if c1.button("Hủy", use_container_width=True): st.rerun()
    if c2.button("Xóa ngay", type="primary", use_container_width=True):
        if type == 'book': ok, msg = lib.delete_book(id)
        else: ok, msg = lib.delete_user_logic(id, st.session_state.user.uid)
        
        if ok: st.toast(msg, icon="🗑️"); time.sleep(1); st.rerun()
        else: st.error(msg)

@st.dialog("✏️ Cập nhật Sách")
def modal_edit_book(book, lib):
    with st.form("edit_book_form"):
        st.caption(f"Đang sửa ID: {book.id}")
        t = st.text_input("Tên sách", value=book.title)
        a = st.text_input("Tác giả", value=book.author)
        c1, c2 = st.columns(2)
        cat = c1.text_input("Thể loại", value=book.category, placeholder="VD: Công nghệ, Văn học...")
        y = c2.number_input("Năm XB", value=book.year)
        c3, c4 = st.columns(2)
        q = c3.number_input("Tổng nhập kho", value=book.qty, min_value=1)
        b_count = c4.number_input("Đang được mượn (Thực tế)", value=book.borrowed, min_value=0)
        p = st.number_input("Giá bìa (VNĐ)", value=book.price)
        d = st.text_area("Mô tả", value=book.desc)
        img = st.text_input("Link ảnh", value=book.image)
        
        if st.form_submit_button("Lưu thay đổi", type="primary"):
            final_cat = cat.strip().title() if cat else "Chưa phân loại"
            data = {'title':t, 'author':a, 'category':final_cat, 'year':y, 'qty':q, 'borrowed':b_count, 'price':p, 'desc':d, 'image':img}
            ok, msg = lib.add_or_update_book(data, book_id=book.id)
            st.toast(msg, icon="💾"); time.sleep(1); st.rerun()

@st.dialog("✏️ Cập nhật User")
def modal_edit_user(u_obj, lib):
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

# --- DIALOG QUAN TRỌNG: CHỌN SÁCH ĐỂ TRẢ (TÁCH PHIẾU) ---
@st.dialog("📚 Chọn sách muốn trả")
def modal_return_selection(slip, lib):
    st.write("Vui lòng chọn những cuốn sách bạn muốn trả trong phiếu này:")
    
    # Tạo danh sách options từ slip.items
    book_map = {item['book_id']: f"{item['title']} (ID: {item['book_id']})" for item in slip.items}
    
    # Mặc định tick chọn tất cả
    selected_ids = st.multiselect(
        "Danh sách sách:",
        options=list(book_map.keys()),
        format_func=lambda x: book_map[x],
        default=list(book_map.keys())
    )
    
    st.info(f"Bạn đang chọn trả: **{len(selected_ids)}** cuốn.")
    
    # Cảnh báo nếu trả thiếu
    if len(selected_ids) < len(slip.items) and len(selected_ids) > 0:
        st.warning("⚠️ **Lưu ý:** Hệ thống sẽ tách phiếu. Các sách KHÔNG được chọn vẫn sẽ tiếp tục tính thời gian mượn.")
    
    col1, col2 = st.columns(2)
    if col1.button("Hủy bỏ", use_container_width=True):
        st.rerun()
        
    if col2.button("Xác nhận gửi yêu cầu", type="primary", use_container_width=True, disabled=len(selected_ids)==0):
        ok, msg = lib.request_return_logic(slip.id, selected_ids)
        if ok:
            st.toast(msg, icon="✅"); time.sleep(1.5); st.rerun()
        else:
            st.error(msg)

@st.dialog("💸 Xử lý Trả sách (Admin)", width="large")
def modal_process_return(slip, lib):
    st.subheader(f"Phiếu: {slip.id}")
    st.caption(f"Người mượn: {slip.user_name} | Hạn trả: {slip.due_date.strftime('%d/%m/%Y')}")
    
    est_fine = slip.get_estimated_fine()
    # Check quá hạn theo ngày
    check_date = slip.due_date.date() if slip.due_date else datetime.now().date()
    now_date = datetime.now().date()
    
    if now_date > check_date:
        days = (now_date - check_date).days
        st.error(f"⚠️ Đã quá hạn {days} ngày.")
        st.markdown(f"💰 **Tiền phạt trễ hạn dự kiến:** `{est_fine:,}đ` (5.000đ x {len(slip.items)} cuốn x {days} ngày)")
    else:
        st.success("✅ Trả đúng hạn. Không có phạt trễ.")
        
    with st.form(f"ret_{slip.id}"):
        conds = {}
        # Duyệt qua từng sách trong phiếu để đánh giá tình trạng
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
# 2. PAGES (CÁC TRANG CHỨC NĂNG)
# ==========================================

def page_home(lib):
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

    paginated_books, current_page, total_pages = get_paginated_items(filtered, 12, "home")
    
    cols = st.columns(4)
    for i, book in enumerate(paginated_books):
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
                if b1.button("Chi tiết", key=f"d_{book.id}", use_container_width=True): modal_book_detail(book, lib)
                dis = book.available() <= 0
                if b2.button("Mượn", key=f"b_{book.id}", disabled=dis, type="primary" if not dis else "secondary", use_container_width=True):
                    if not st.session_state.get('user'): st.toast("Vui lòng đăng nhập!", icon="🔒")
                    else: 
                        ok, msg = lib.borrow_book(book.id, st.session_state.user)
                        if ok: st.toast(msg, icon="📚"); time.sleep(1); st.rerun()
                        else: st.error(msg)
    
    render_pagination_footer(current_page, total_pages, "home")

def page_reader_history(lib):
    st.title("📂 Phiếu mượn của tôi")
    u_uid = st.session_state.user.uid
    tab1, tab2 = st.tabs(["📘 Đang hoạt động", "📜 Lịch sử"])
    
    with tab1:
        # Lấy phiếu đang mượn (Active & Processing)
        active = [s for s in lib.slips if s.user_uid == u_uid and s.status in ['active', 'processing']]
        
        # Sắp xếp: Phiếu chờ xử lý lên đầu, sau đó theo ngày mượn
        active.sort(key=lambda x: (0 if x.status == 'processing' else 1, x.borrow_date), reverse=False)
        
        if not active: st.info("Bạn không có sách nào đang mượn.")
        
        for s in active:
            st_lbl, st_cls = s.get_status_info()
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 3, 2, 1.2])
                
                # Cột 1: Mã phiếu
                c1.markdown(f"<div class='card-label'>MÃ PHIẾU</div><span class='id-badge'>#{s.id}</span>", unsafe_allow_html=True)
                
                # Cột 2: Danh sách sách (Gộp phiếu)
                with c2:
                    st.markdown("<div class='card-label'>SÁCH MƯỢN</div>", unsafe_allow_html=True)
                    for item in s.items:
                        st.markdown(f"• **{item['title']}** <span style='color:#666; font-size:0.8em'>(ID: {item['book_id']})</span>", unsafe_allow_html=True)

                # Cột 3: Thời gian & Cảnh báo quá hạn
                is_late = datetime.now().date() > s.due_date.date()
                date_color = "#dc2626" if is_late else "#111"
                date_html = f"""
                <div class='card-label'>THỜI GIAN</div>
                <div class='card-value'>Ngày mượn: {s.borrow_date.strftime('%d/%m/%Y')}</div>
                <div class='card-value' style='color:{date_color}'>Hạn trả: <b>{s.due_date.strftime('%d/%m/%Y')}</b></div>
                """
                if is_late:
                    est_fine = s.get_estimated_fine()
                    date_html += f"<div style='color:#dc2626; font-size:0.85em; font-weight:bold; margin-top:4px;'>⚠️ Quá hạn! Phạt: {est_fine:,}đ</div>"
                c3.markdown(date_html, unsafe_allow_html=True)
                
                # Cột 4: Nút thao tác
                c4.markdown(f"<div style='margin-bottom:5px'><span class='status-badge {st_cls}'>{st_lbl}</span></div>", unsafe_allow_html=True)
                
                if s.status == 'active':
                    # Nút Trả Sách -> Mở Dialog chọn sách
                    if c4.button("Trả sách", key=f"btn_ret_{s.id}", type="primary", use_container_width=True):
                        modal_return_selection(s, lib)
                
                elif s.status == 'processing':
                    # Nút Hủy yêu cầu (New Feature)
                    if c4.button("❌ Hủy yêu cầu", key=f"btn_can_{s.id}", use_container_width=True): 
                        lib.cancel_return_request(s.id)
                        st.toast("Đã hủy yêu cầu, sách trở về trạng thái đang mượn.", icon="↩️"); time.sleep(1.5); st.rerun()

    with tab2:
        history = [s for s in lib.slips if s.user_uid == u_uid and s.status == 'completed']
        history.sort(key=lambda x: x.return_date, reverse=True)
        
        paginated_hist, curr, total = get_paginated_items(history, 5, "my_hist")
        if not paginated_hist: st.info("Chưa có lịch sử.")
        
        for s in paginated_hist:
            with st.container(border=True):
                k1, k2, k3, k4 = st.columns([1, 3, 2, 2])
                k1.markdown(f"<div class='card-label'>MÃ PHIẾU</div><span class='id-badge'>#{s.id}</span>", unsafe_allow_html=True)
                
                # Hiển thị list sách đã trả
                with k2:
                    st.markdown("<div class='card-label'>SÁCH ĐÃ TRẢ</div>", unsafe_allow_html=True)
                    for item in s.items:
                        st.write(f"• {item['title']}")
                        
                k3.markdown(f"<div class='card-label'>NGÀY TRẢ</div><div class='card-value'>{s.return_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
                
                if s.total_fine > 0:
                    k4.markdown(f"<div class='card-label'>PHẠT</div><div style='color:red; font-weight:bold'>{s.total_fine:,}đ</div>", unsafe_allow_html=True)
                    with k4.popover("Chi tiết lỗi"):
                        for r in s.fine_details: st.write(f"- {r}")
                else:
                    k4.markdown("<div class='card-label'>TRẠNG THÁI</div><div style='color:green; font-weight:bold'>Hoàn thành</div>", unsafe_allow_html=True)
        
        render_pagination_footer(curr, total, "my_hist")

def page_admin_loans(lib):
    st.title("📂 Quản lý Phiếu Mượn (Admin)")
    t1, t2 = st.tabs(["⚡ Cần xử lý & Đang mượn", "📜 Lịch sử trả"])
    
    with t1:
        slips = [s for s in lib.slips if s.status in ['active', 'processing']]
        slips.sort(key=lambda x: (0 if x.status == 'processing' else 1, x.due_date or datetime.now()))
        
        p_slips, curr, total = get_paginated_items(slips, 10, "adm_active")
        if not p_slips: st.success("Không có phiếu nào.")
        
        for s in p_slips:
            with st.container(border=True):
                st_lbl, st_cls = s.get_status_info()
                is_proc = s.status == 'processing'
                
                r1_c1, r1_c2 = st.columns([1, 1])
                r1_c1.markdown(f"🎫 **Phiếu #** <span class='id-badge'>{s.id}</span>", unsafe_allow_html=True)
                r1_c2.markdown(f"<div style='text-align:right'><span class='status-badge {st_cls}'>{st_lbl}</span></div>", unsafe_allow_html=True)
                st.divider()
                
                c1, c2, c3 = st.columns([1.2, 1.5, 1])
                c1.markdown("<div class='card-label'>👤 NGƯỜI MƯỢN</div>", unsafe_allow_html=True)
                c1.markdown(f"""<div class='card-value-bold'>{s.user_name}</div><div class='card-value'>ID: <code>{s.user_uid}</code></div><div class='card-value'>📞 {s.user_phone}</div><div class='card-value'>📧 {s.user_email}</div>""", unsafe_allow_html=True)
                
                # Cột Sách
                with c2:
                    st.markdown("<div class='card-label'>📘 SÁCH & THỜI GIAN</div>", unsafe_allow_html=True)
                    for item in s.items:
                        st.markdown(f"• {item['title']} <span style='color:#666; font-size:0.85em'>(Mã: {item['book_id']})</span>", unsafe_allow_html=True)
                    
                    # Logic hiển thị thời gian & quá hạn
                    is_late = datetime.now().date() > (s.due_date.date() or datetime.now().date())
                    date_color = "#dc2626" if is_late else "#111"
                    
                    st.markdown(f"<div class='card-value' style='margin-top:8px'>📅 Ngày mượn: {s.borrow_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='card-value' style='color:{date_color}'>⏳ Hạn trả: <b>{(s.due_date or datetime.now()).strftime('%d/%m/%Y')}</b></div>", unsafe_allow_html=True)
                    
                    if is_late and s.status == 'active':
                         est_fine = s.get_estimated_fine()
                         st.markdown(f"<div style='color:#dc2626; font-size:0.8em; font-weight:700'>⚠️ Quá hạn - Phạt dự kiến: {est_fine:,}đ</div>", unsafe_allow_html=True)
                
                c3.markdown("<div class='card-label'>THAO TÁC</div>", unsafe_allow_html=True)
                btn_txt = "⚡ Xử lý ngay" if is_proc else "Thu hồi / Trả sách"
                # Nút xử lý mở Dialog
                if c3.button(btn_txt, key=f"adm_btn_{s.id}", type="primary" if is_proc else "secondary", use_container_width=True):
                    modal_process_return(s, lib)
        
        render_pagination_footer(curr, total, "adm_active")

    with t2:
        done = [s for s in lib.slips if s.status == 'completed']
        done.sort(key=lambda x: x.return_date, reverse=True)
        
        p_done, curr, total = get_paginated_items(done, 10, "adm_hist")
        if not p_done: st.info("Chưa có dữ liệu.")
        for s in p_done:
            with st.container(border=True):
                d1, d2 = st.columns([1, 1])
                d1.markdown(f"✅ **Phiếu #** <span class='id-badge'>{s.id}</span>", unsafe_allow_html=True)
                d2.markdown("<div style='text-align:right'><span class='status-badge st-done'>ĐÃ HOÀN THÀNH</span></div>", unsafe_allow_html=True)
                st.divider()
                
                k1, k2, k3 = st.columns([1.2, 1.5, 1])
                k1.markdown("<div class='card-label'>👤 NGƯỜI MƯỢN</div>", unsafe_allow_html=True)
                k1.markdown(f"""<div class='card-value-bold'>{s.user_name}</div><div class='card-value'>ID: <code>{s.user_uid}</code></div><div class='card-value'>📞 {s.user_phone} | 📧 {s.user_email}</div>""", unsafe_allow_html=True)
                
                with k2:
                    st.markdown("<div class='card-label'>📘 SÁCH ĐÃ TRẢ</div>", unsafe_allow_html=True)
                    for item in s.items:
                        st.write(f"• {item['title']}")
                    st.markdown(f"<div class='card-value' style='margin-top:5px'>📅 Ngày mượn: {s.borrow_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='card-value'>📅 Ngày trả: <b>{s.return_date.strftime('%d/%m/%Y')}</b></div>", unsafe_allow_html=True)
                
                k3.markdown("<div class='card-label'>KẾT QUẢ / PHẠT</div>", unsafe_allow_html=True)
                if s.total_fine > 0:
                    k3.markdown(f"<div style='color:#dc2626; font-size:1.1rem; font-weight:bold'>{s.total_fine:,}đ</div>", unsafe_allow_html=True)
                    with k3.popover("Xem lỗi phạt"):
                        for r in s.fine_details: st.write(f"- {r}")
                else: k3.success("Không có lỗi")
        
        render_pagination_footer(curr, total, "adm_hist")

def page_admin_system(lib):
    st.title("🛠️ Quản Trị Hệ Thống")
    t1, t2, t3 = st.tabs(["📊 Thống kê & Biểu đồ", "👥 Quản Lý Thành Viên", "📚 Quản Lý Kho Sách"])
    
    with t1:
        total_books = sum(b.qty for b in lib.books)
        total_users = len(lib.users)
        active_loans = sum(1 for s in lib.slips if s.status in ['active', 'processing'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng Đầu Sách", total_books)
        m2.metric("Thành Viên", total_users)
        m3.metric("Đang Mượn (Phiếu)", active_loans)
        st.divider()
        
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.subheader("📈 Xu hướng mượn sách")
            borrow_stats = {}
            for s in lib.slips:
                d_key = s.borrow_date.strftime('%Y-%m-%d')
                borrow_stats[d_key] = borrow_stats.get(d_key, 0) + 1
            if borrow_stats: st.line_chart(borrow_stats)
            else: st.info("Chưa có dữ liệu mượn.")
            
        with c_chart2:
            st.subheader("💰 Doanh thu phạt")
            fine_stats = {}
            for s in lib.slips:
                if s.status == 'completed' and s.total_fine > 0:
                    d_key = s.return_date.strftime('%Y-%m-%d')
                    fine_stats[d_key] = fine_stats.get(d_key, 0) + s.total_fine
            if fine_stats: st.bar_chart(fine_stats)
            else: st.info("Chưa có dữ liệu phạt.")
            
        st.divider()
        st.subheader("🍩 Phân bổ thể loại sách đã mượn")
        cat_stats = {}
        for s in lib.slips:
            for item in s.items:
                bk = next((b for b in lib.books if b.id == item['book_id']), None)
                if bk:
                    cat_stats[bk.category] = cat_stats.get(bk.category, 0) + 1
        
        if cat_stats: st.bar_chart(cat_stats)
        else: st.info("Chưa có dữ liệu.")

    with t2:
        with st.form("search_user"):
            c1, c2 = st.columns([4,1])
            search = c1.text_input("Tìm thành viên...", placeholder="Tên, SĐT, Email...", label_visibility="collapsed")
            c2.form_submit_button("Tìm kiếm", use_container_width=True)
        users = list(lib.users.values())
        if search: users = [u for u in users if search.lower() in u.name.lower() or search in u.phone]
        
        p_users, curr, total = get_paginated_items(users, 10, "adm_usr")
        for u in p_users:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 2, 2, 1.5])
                c1.markdown(f"<div class='card-label'>UID</div><span class='id-badge'>{u.uid}</span>", unsafe_allow_html=True)
                c2.markdown(f"<div class='card-label'>THÔNG TIN</div><div class='card-value-bold'>{u.name}</div><div class='card-value'>@{u.username} | Role: {u.role}</div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='card-label'>LIÊN HỆ</div><div class='card-value'>📞 {u.phone}</div><div class='card-value'>📧 {u.email}</div>", unsafe_allow_html=True)
                c4.markdown("<div class='card-label'>THAO TÁC</div>", unsafe_allow_html=True)
                if u.role != 'librarian':
                    col_b1, col_b2 = c4.columns(2)
                    if col_b1.button("✏️", key=f"eu_{u.uid}", use_container_width=True): modal_edit_user(u, lib)
                    if col_b2.button("🗑️", key=f"du_{u.uid}", type="primary", use_container_width=True): modal_confirm_delete('user', u.username, u.name, lib)
                else:
                    c4.markdown("<span class='status-badge st-active'>ADMIN</span>", unsafe_allow_html=True)
        
        render_pagination_footer(curr, total, "adm_usr")

    with t3:
        if st.button("➕ Thêm sách mới", type="primary"): modal_edit_book(Book(0, "", "", "Công nghệ", "", "", 1, 100000, 2024), lib)
        p_books, curr, total = get_paginated_items(lib.books, 10, "adm_bk")
        for b in p_books:
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([0.8, 2, 1.5, 1, 1.5])
                c1.markdown(f'<img src="{b.image}" style="width:50px; height:70px; object-fit:cover; border-radius:4px;">', unsafe_allow_html=True)
                c2.markdown(f"<div class='card-label'>THÔNG TIN</div><div class='card-value-bold'>{b.title}</div><div class='card-value'>{b.author}</div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='card-label'>KHO & ID</div><div class='card-value'>ID: <span class='id-badge'>{b.id}</span></div><div class='card-value'>Kho: <b>{b.available()}/{b.qty}</b></div>", unsafe_allow_html=True)
                c4.markdown(f"<div class='card-label'>GIÁ</div><div class='card-value-bold'>{b.price:,}đ</div>", unsafe_allow_html=True)
                c5.markdown("<div class='card-label'>THAO TÁC</div>", unsafe_allow_html=True)
                col_b1, col_b2 = c5.columns(2)
                if col_b1.button("✏️", key=f"eb_{b.id}", use_container_width=True): modal_edit_book(b, lib)
                if col_b2.button("🗑️", key=f"db_{b.id}", type="primary", use_container_width=True): modal_confirm_delete('book', b.id, b.title, lib)
        
        render_pagination_footer(curr, total, "adm_bk")

def page_login_register(lib):
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
                    # Bắt buộc SĐT, Email (*)
                    n=st.text_input("Họ tên*"); ph=st.text_input("SĐT*"); e=st.text_input("Email*")
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