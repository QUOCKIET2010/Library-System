import json
import os
from datetime import datetime

# Đường dẫn đến các file trong thư mục data
DIR = 'data'
FILES = {
    'users': os.path.join(DIR, 'users.json'),
    'books': os.path.join(DIR, 'books.json'),
    'slips': os.path.join(DIR, 'slips.json')
}

def fix_users():
    """Thêm trường created_at còn thiếu cho user cũ"""
    if not os.path.exists(FILES['users']): return
    
    print("⏳ Đang sửa file Users...")
    with open(FILES['users'], 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    count = 0
    for uname, info in users.items():
        # Thêm created_at nếu chưa có (mặc định lấy ngày giờ hiện tại)
        if 'created_at' not in info:
            info['created_at'] = str(datetime.now())
            count += 1
        
        # Đảm bảo có role, phone, email (tránh lỗi key error)
        if 'role' not in info: info['role'] = 'reader'
        if 'phone' not in info: info['phone'] = ''
        if 'email' not in info: info['email'] = ''

    with open(FILES['users'], 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)
    print(f"✅ Đã cập nhật {count} user cũ.")

def fix_slips():
    """Đảm bảo phiếu mượn tương thích"""
    if not os.path.exists(FILES['slips']): return
    
    print("⏳ Đang sửa file Slips...")
    with open(FILES['slips'], 'r', encoding='utf-8') as f:
        slips = json.load(f)
    
    fixed = 0
    for s in slips:
        # Nếu thiếu fine_details (chi tiết phạt), thêm list rỗng
        if 'fine_details' not in s:
            s['fine_details'] = []
            fixed += 1
        # Nếu thiếu total_fine
        if 'total_fine' not in s:
            s['total_fine'] = 0
    
    with open(FILES['slips'], 'w', encoding='utf-8') as f:
        json.dump(slips, f, indent=4, ensure_ascii=False)
    print(f"✅ Đã cập nhật {fixed} phiếu mượn.")

if __name__ == "__main__":
    if not os.path.exists(DIR):
        os.makedirs(DIR)
        print(f"⚠️ Đã tạo thư mục '{DIR}'. Hãy copy các file json cũ vào đây rồi chạy lại script này!")
    else:
        fix_users()
        fix_slips()
        print("\n🎉 Hoàn tất! Bây giờ bạn có thể chạy 'streamlit run app.py'")