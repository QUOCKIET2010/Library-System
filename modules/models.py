import json
import os
import time
import random
import string
from datetime import datetime, timedelta
from .utils import safe_parse_date, make_hash

# --- GIỮ NGUYÊN CLASS BOOK VÀ USER ---
class Book:
    def __init__(self, id, title, author, category, image, desc, qty, price=100000, year=2020, borrowed=0, **kwargs):
        self.id = id; self.title = title; self.author = author; self.category = category; self.year = year
        self.image = image; self.desc = desc; self.qty = int(qty); self.price = int(price); self.borrowed = int(borrowed)
    def available(self): return self.qty - self.borrowed
    def to_dict(self): return self.__dict__

class User:
    def __init__(self, uid, username, password, name, role="reader", phone="", email="", created_at=None, **kwargs):
        self.uid = uid; self.username = username; self.password = password; self.name = name
        self.role = role; self.phone = phone; self.email = email
        self.created_at = safe_parse_date(created_at) if created_at else datetime.now()
    def to_dict(self): 
        d = self.__dict__.copy()
        d['created_at'] = str(self.created_at)
        return d

# --- GIỮ NGUYÊN CLASS BORROW SLIP ---
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
        if self.status == 'processing': return "CHỜ DUYỆT TRẢ", "st-process"
        if datetime.now().date() > self.due_date.date(): return "QUÁ HẠN", "st-overdue"
        return "ĐANG MƯỢN", "st-active"

    def get_estimated_fine(self):
        if self.status == 'completed': return self.total_fine
        now_date = datetime.now().date()
        due_date_date = self.due_date.date()
        if now_date > due_date_date:
            days_over = (now_date - due_date_date).days
            return days_over * 5000 * len(self.items)
        return 0

    def to_dict(self):
        d = self.__dict__.copy()
        d['borrow_date'] = str(self.borrow_date); d['due_date'] = str(self.due_date)
        d['return_date'] = str(self.return_date) if self.return_date else None
        return d

# --- HỆ THỐNG CHÍNH ---
class LibrarySystem:
    def __init__(self):
        # Giữ nguyên cấu trúc thư mục data/
        if not os.path.exists('data'): os.makedirs('data')
        self.files = {'books': 'data/books.json', 'users': 'data/users.json', 'slips': 'data/slips.json'}
        self.books = []; self.users = {}; self.slips = []
        self.load_data()

    def load_data(self):
        if os.path.exists(self.files['books']):
            with open(self.files['books'], 'r', encoding='utf-8') as f: self.books = [Book(**b) for b in json.load(f)]
        else: self.save_data('books')

        if os.path.exists(self.files['users']):
            with open(self.files['users'], 'r', encoding='utf-8') as f: self.users = {k: User(**v) for k,v in json.load(f).items()}
        else:
            admin_pass = make_hash("123")
            self.users = {'admin': User("AD-001", "admin", admin_pass, "Quản Trị Viên", "librarian", "090999", "admin@lib.com")}
            self.save_data('users')

        if os.path.exists(self.files['slips']):
             with open(self.files['slips'], 'r', encoding='utf-8') as f: self.slips = [BorrowSlip(**s) for s in json.load(f)]

    def save_data(self, type):
        if type == 'books': f, d = self.files['books'], [b.to_dict() for b in self.books]
        elif type == 'users': f, d = self.files['users'], {k:v.to_dict() for k,v in self.users.items()}
        elif type == 'slips': f, d = self.files['slips'], [s.to_dict() for s in self.slips]
        with open(f, 'w', encoding='utf-8') as file: json.dump(d, file, ensure_ascii=False, indent=4)

    def login(self, u, p):
        user = self.users.get(u)
        return user if user and user.password == make_hash(p) else None

    # --- CẬP NHẬT: THÊM RÀNG BUỘC SĐT VÀ EMAIL ---
    def register(self, d):
        # Kiểm tra thông tin cơ bản
        if not d['username'] or not d['password'] or not d['name']: 
            return False, "Thiếu thông tin cơ bản!"
        
        # Kiểm tra SĐT và Email (BẮT BUỘC)
        if not d['phone'] or not d['email']: 
            return False, "Vui lòng nhập đầy đủ SĐT và Email!"
            
        if d['username'] in self.users: return False, "Username đã tồn tại!"
        
        uid = f"U{len(self.users)+1:03d}"
        hashed_pass = make_hash(d['password'])
        self.users[d['username']] = User(uid, d['username'], hashed_pass, d['name'], "reader", d['phone'], d['email'])
        self.save_data('users'); return True, "Đăng ký thành công!"

    def reset_password(self, username, new_pass):
        if username not in self.users: return False, "Username không tồn tại!"
        self.users[username].password = make_hash(new_pass)
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

    # --- GIỮ NGUYÊN LOGIC GỘP PHIẾU CŨ ---
    def borrow_book(self, bid, user):
        active_slips = [s for s in self.slips if s.user_uid == user.uid and s.status in ['active', 'processing']]
        total_holding = sum(len(s.items) for s in active_slips)
        
        if total_holding >= 5: 
            return False, f"Đạt giới hạn! Bạn đang giữ {total_holding}/5 cuốn. Vui lòng trả bớt."
        
        for s in active_slips:
            if s.status == 'active' and datetime.now().date() > s.due_date.date(): 
                return False, "BẠN CÓ SÁCH QUÁ HẠN! Không thể mượn tiếp."
        
        book = next((b for b in self.books if b.id == bid), None)
        if not book or book.available() <= 0: return False, "Sách không khả dụng."
        
        today_date = datetime.now().date()
        target_slip = None
        for s in active_slips:
            if s.status == 'active' and s.borrow_date.date() == today_date:
                target_slip = s
                break
        
        item_data = {'book_id': book.id, 'title': book.title, 'price': book.price}
        
        if target_slip:
            target_slip.items.append(item_data)
            msg = f"Đã thêm '{book.title}' vào phiếu mượn hôm nay!"
        else:
            slip_id = f"M{int(time.time())}" 
            new_slip = BorrowSlip(slip_id, user.uid, user.name, user.phone, user.email, 
                                  [item_data], datetime.now(), datetime.now() + timedelta(days=7))
            self.slips.append(new_slip)
            msg = f"Mượn '{book.title}' thành công (Tạo phiếu mới)!"

        book.borrowed += 1
        self.save_data('books'); self.save_data('slips'); return True, msg

    # --- GIỮ NGUYÊN LOGIC TÁCH PHIẾU CŨ ---
    def request_return_logic(self, slip_id, selected_book_ids):
        slip = next((s for s in self.slips if s.id == slip_id), None)
        if not slip or slip.status != 'active': return False, "Phiếu không hợp lệ"
        if not selected_book_ids: return False, "Chưa chọn sách để trả"

        items_to_return = []
        items_remaining = []
        
        for item in slip.items:
            if item['book_id'] in selected_book_ids: items_to_return.append(item)
            else: items_remaining.append(item)
        
        if not items_remaining:
            slip.status = 'processing'
            self.save_data('slips')
            return True, "Đã gửi yêu cầu trả toàn bộ!"
        else:
            slip.items = items_remaining
            suffix = ''.join(random.choices(string.ascii_uppercase, k=3))
            new_slip_id = f"{slip.id}_RET_{suffix}" 
            
            new_slip = BorrowSlip(
                id=new_slip_id,
                user_uid=slip.user_uid, user_name=slip.user_name, user_phone=slip.user_phone, user_email=slip.user_email,
                items=items_to_return,
                borrow_date=slip.borrow_date, due_date=slip.due_date, status='processing'
            )
            self.slips.append(new_slip)
            self.save_data('slips')
            return True, f"Đã tách yêu cầu trả {len(items_to_return)} cuốn sách!"

    def cancel_return_request(self, slip_id):
        slip = next((s for s in self.slips if s.id == slip_id), None)
        if slip and slip.status == 'processing':
            slip.status = 'active'; self.save_data('slips'); return True, "Đã hủy yêu cầu!"
        return False, "Không thể hủy."

    def confirm_return(self, slip_id, conditions):
        slip = next((s for s in self.slips if s.id == slip_id), None)
        if not slip: return False, "Lỗi."
        slip.return_date = datetime.now()
        total_fine = 0; details = []
        
        check_date = slip.due_date.date() if slip.due_date else datetime.now().date()
        return_date_val = slip.return_date.date()
        
        if return_date_val > check_date:
            days = (return_date_val - check_date).days
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