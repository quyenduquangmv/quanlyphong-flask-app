import os
from sqlalchemy import create_engine, text
import sys

# --- PHẦN CẤU HÌNH KẾT NỐI ---
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("!!! DANG DUNG CO SO DU LIEU SQLITE TREN MAY TINH (LOCAL) !!!")
    DATABASE_URL = "sqlite:///hotel.db"

engine = create_engine(DATABASE_URL)
# --- KẾT THÚC PHẦN CẤU HÌNH ---


def init_db():
    """Khởi tạo cơ sở dữ liệu, tạo bảng và chèn dữ liệu mẫu nếu cần."""
    with engine.connect() as connection:
        with connection.begin() as transaction:
            try:
                # Dùng SERIAL PRIMARY KEY cho PostgreSQL để tự động tăng ID
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS rooms (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE
                    )
                """))
                print("Bang 'rooms' da duoc tao hoac da ton tai.")

                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS bookings (
                        id SERIAL PRIMARY KEY,
                        room_id INTEGER NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        source TEXT,
                        price REAL,
                        guest_country TEXT,
                        notes TEXT,
                        FOREIGN KEY (room_id) REFERENCES rooms (id)
                    )
                """))
                print("Bang 'bookings' da duoc tao hoac da ton tai.")

                room_count = connection.execute(text("SELECT COUNT(*) FROM rooms")).scalar_one()
                if room_count == 0:
                    print("Them 15 phong mac dinh...")
                    # Dùng named parameters để nhất quán và an toàn
                    for i in range(1, 16):
                        connection.execute(text("INSERT INTO rooms (name) VALUES (:name)"), {"name": f'Phòng {i:03}'})
                    print("Da them 15 phong.")

                booking_count = connection.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()
                if booking_count == 0:
                    print("Them du lieu dat phong mau...")
                    sample_bookings = [
                        {"room_id": 1, "start_date": '2025-07-05', "end_date": '2025-07-08', "source": 'Agoda', "price": 2500000, "guest_country": 'Hàn Quốc', "notes": 'Khách yêu cầu phòng yên tĩnh.'},
                        {"room_id": 1, "start_date": '2025-07-12', "end_date": '2025-07-13', "source": 'Booking.com', "price": 900000, "guest_country": 'Việt Nam', "notes": ''},
                        {"room_id": 3, "start_date": '2025-07-06', "end_date": '2025-07-07', "source": 'Khách vãng lai', "price": 750000, "guest_country": 'Pháp', "notes": 'Check-in muộn sau 10h tối.'}
                    ]
                    insert_query = text("""
                        INSERT INTO bookings (room_id, start_date, end_date, source, price, guest_country, notes)
                        VALUES (:room_id, :start_date, :end_date, :source, :price, :guest_country, :notes)
                    """)
                    # SQLAlchemy có thể thực thi một danh sách các dict với executemany
                    connection.execute(insert_query, sample_bookings)
                    print("Da them du lieu dat phong mau.")
                
                transaction.commit()
                print("Co so du lieu da duoc khoi tao thanh cong.")
            except Exception as e:
                print(f"Loi khi khoi tao CSDL: {e}")
                transaction.rollback()

def get_all_rooms():
    """Lấy tất cả các phòng từ cơ sở dữ liệu."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM rooms ORDER BY name"))
        rooms = [dict(row._mapping) for row in result]
    return rooms

def get_bookings_for_room(room_id):
    """Lấy tất cả các lượt đặt phòng cho một phòng cụ thể."""
    with engine.connect() as connection:
        query = text("SELECT * FROM bookings WHERE room_id = :id ORDER BY start_date")
        result = connection.execute(query, {"id": room_id})
        bookings = [dict(row._mapping) for row in result]
    return bookings

def get_bookings_for_month(year, month):
    """Lấy tất cả các lượt đặt phòng trong một tháng/năm cụ thể."""
    month_str = f"{year}-{month:02d}"
    with engine.connect() as connection:
        # Tự động chọn hàm ngày tháng phù hợp cho SQLite hoặc PostgreSQL
        if connection.dialect.name == 'sqlite':
            date_format_sql = "strftime('%Y-%m', b.start_date)"
        else: # Mặc định là PostgreSQL
            date_format_sql = "to_char(b.start_date::date, 'YYYY-MM')"
        
        # Dùng f-string để chèn tên hàm, nhưng dùng named parameter cho giá trị để an toàn
        query = text(f"""
            SELECT b.*, r.name as room_name FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            WHERE {date_format_sql} = :month_str
            ORDER BY b.start_date
        """)
        
        result = connection.execute(query, {"month_str": month_str})
        bookings = [dict(row._mapping) for row in result]
    return bookings

def calculate_monthly_revenue(year, month):
    """Tính tổng doanh thu trong một tháng/năm cụ thể."""
    month_str = f"{year}-{month:02d}"
    with engine.connect() as connection:
        if connection.dialect.name == 'sqlite':
            date_format_sql = "strftime('%Y-%m', start_date)"
        else:
            date_format_sql = "to_char(start_date::date, 'YYYY-MM')"
        
        query = text(f"SELECT SUM(price) FROM bookings WHERE {date_format_sql} = :month_str")
        total = connection.execute(query, {"month_str": month_str}).scalar_one_or_none()
    return total if total is not None else 0

def calculate_yearly_revenue(year):
    """Tính tổng doanh thu của một năm cụ thể."""
    year_str = str(year)
    with engine.connect() as connection:
        if connection.dialect.name == 'sqlite':
            date_format_sql = "strftime('%Y', start_date)"
        else:
            date_format_sql = "to_char(start_date::date, 'YYYY')"

        query = text(f"SELECT SUM(price) FROM bookings WHERE {date_format_sql} = :year_str")
        total = connection.execute(query, {"year_str": year_str}).scalar_one_or_none()
    return total if total is not None else 0

def calculate_grand_total_revenue():
    """Tính tổng doanh thu từ trước đến nay."""
    with engine.connect() as connection:
        total = connection.execute(text("SELECT SUM(price) FROM bookings")).scalar_one_or_none()
    return total if total is not None else 0

# Đảm bảo khối lệnh này được vô hiệu hóa trên server
# if __name__ == '__main__':
#     init_db()