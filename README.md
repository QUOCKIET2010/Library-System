# Library-System
 Library-app
│
├── app.py                  # 🟢 FILE CHẠY CHÍNH (Entry Point)
├── data/                   # 💾 KHO DỮ LIỆU (Tự động tạo nếu chưa có)
│   ├── books.json
│   ├── users.json
│   └── slips.json
└── modules/                # 📦 GÓI MÃ NGUỒN (Package)
    ├── __init__.py         # ⚠️ Quan trọng: File rỗng để Python hiểu đây là package
    ├── models.py           # 🧠 Logic dữ liệu (Class Book, User, System) - Code ở bước 1
    ├── views.py            # 🎨 Giao diện (Màn hình, Dialogs) - Code ở bước 2
    ├── utils.py            # 🛠️ Các hàm tiện ích (Hash, Date, Captcha)
    └── ui.py               # 🧩 Các thành phần UI chung (Phân trang, CSS)

