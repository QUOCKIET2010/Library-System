# Sử dụng Python 3.9 (bản nhẹ slim)
FROM python:3.9-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy file requirements và cài đặt thư viện trước (để tận dụng cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Mở cổng 8501 (Cổng mặc định của Streamlit)
EXPOSE 8501

# Lệnh chạy ứng dụng
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]