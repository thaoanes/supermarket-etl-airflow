# Supermarket ETL Pipeline (Airflow + Docker + PostgreSQL)

## 1. Tổng quan dự án
- Mô tả ngắn gọn luồng xử lý dữ liệu từ file `Supermarket_sales.xlsx` qua Apache Airflow DAG và script `etl_pipeline.py` vào PostgreSQL (`staging_sales` -> làm sạch/khử trùng lặp -> `warehouse_sales`, kèm ghi log vào `etl_log`).
- Đảm bảo tính idempotent / chạy lại nhiều lần an toàn nhờ `TRUNCATE TABLE staging_sales` và `ON CONFLICT (invoice_id) DO UPDATE`.

## 2. Kiến trúc & Cấu trúc thư mục
Liệt kê cây thư mục gọn gàng của dự án (ví dụ: `dags/`, `scripts/etl_pipeline.py`, `data/Supermarket_sales.xlsx`, `docker-compose.yaml`, `.env.example`, `.gitignore`, `README.md`).

## 3. Yêu cầu môi trường & Biến môi trường
- Docker & Docker Compose.
- Tạo file `.env` từ `.env.example` và cấu hình các biến kết nối DB (`DB_HOST=postgres`, `DB_PORT=5432`, `DB_NAME=etl_db`, `DB_USER=...`, `DB_PASSWORD=...`).

## 4. Hướng dẫn khởi chạy
1. Khởi động các dịch vụ bằng `docker compose up -d`.
2. Khởi tạo bảng (`etl_log`, `staging_sales`, `warehouse_sales`) trong database `etl_db` nếu chưa có.
3. Mở Airflow UI, bật DAG `supermarket_etl_pipeline` và bấm **Trigger** (có thể trigger lặp lại để kiểm chứng chạy nhiều lần không lỗi).

## 5. Kiểm tra kết quả & Logging
- Mô tả cách kiểm tra log trong bảng `etl_log` (`START`, `EXTRACT_INGEST`, `TRANSFORM_LOAD`, `VALIDATION`, `SUCCESS`/`FAILED`).
- Mô tả các câu truy vấn kiểm tra số lượng bản ghi và tổng hợp dữ liệu trên `warehouse_sales`.
- Đính kèm ảnh chụp màn hình: Airflow DAG chạy thành công, log trong `etl_log`, và kết quả query dữ liệu.

## 6. Ghi chú xử lý sự cố thường gặp (Troubleshooting)
- Cài gói Python trong container Airflow đúng user (`python -m pip install ...`).
- Khớp thông tin role/database/mật khẩu trong `.env` với dịch vụ PostgreSQL của Docker Compose.
