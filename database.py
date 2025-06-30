import os
from sqlalchemy import create_engine, text

# --- PHẦN CẤU HÌNH KẾT NỐI ---

# Lấy Connection String từ Biến Môi Trường (khi chạy trên Render)
DATABASE_URL = os.environ.get('DATABASE_URL')

# Nếu không tìm thấy URL (ví dụ: khi chạy trên máy tính của bạn để kiểm tra),
# thì tự động dùng file sqlite cũ. Điều này giúp bạn vẫn có thể chạy code trên máy tính!
if not DATABASE_URL:
    print("!!! DANG DUNG CO SO DU LIEU SQLITE TREN MAY TINH (LOCAL) !!!")
    DATABASE_URL = "sqlite:///hotel.db" # 3 dấu gạch chéo cho đường dẫn tương đối

# Tạo ra "Cổng kết nối" duy nhất. Toàn bộ file sẽ dùng chung engine này.
engine = create_engine(DATABASE_URL)

# --- KẾT THÚC PHẦN CẤU HÌNH ---

def init_db():
    """
    Hàm này sẽ được chạy một lần duy nhất để khởi tạo cơ sở dữ liệu.
    Nó sẽ tạo ra file hotel.db và các bảng cần thiết.
    """
    with engine.connect() as connection:
        # Dùng transaction để đảm bảo tất cả các lệnh được thực hiện thành công
        with connection.begin() as transaction:
            try:
                # Sửa lại CREATE TABLE để tương thích tốt hơn với PostgreSQL
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS rooms (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE
                    )
                """))
                print("Bang 'rooms' da duoc tao hoac da ton tai.")

                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY,
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

                # Kiểm tra và thêm dữ liệu mẫu
                room_count = connection.execute(text("SELECT COUNT(*) FROM rooms")).scalar_one()
                if room_count == 0:
                    print("Them 15 phong mac dinh vao co so du lieu...")
                    # Chú ý: Đã đổi '?' thành '%s' cho PostgreSQL
                    for i in range(1, 16):
                        connection.execute(text("INSERT INTO rooms (name) VALUES (%s)"), (f'Phòng {i:03}',))
                    print("Da them 15 phong.")
                else:
                    print("Bang 'rooms' da co du lieu, khong can them moi.")

                booking_count = connection.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()
                if booking_count == 0:
                    print("Them du lieu dat phong mau...")
                    sample_bookings = [
                        (1, '2025-07-05', '2025-07-08', 'Agoda', 2500000, 'Hàn Quốc', 'Khách yêu cầu phòng yên tĩnh.'),
                        (1, '2025-07-12', '2025-07-13', 'Booking.com', 900000, 'Việt Nam', ''),
                        (3, '2025-07-06', '2025-07-07', 'Khách vãng lai', 750000, 'Pháp', 'Check-in muộn sau 10h tối.')
                    ]
                    # Chú ý: Đã đổi các dấu '?' thành '%s'
                    insert_query = text("""
                        INSERT INTO bookings (room_id, start_date, end_date, source, price, guest_country, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """)
                    for booking in sample_bookings:
                        connection.execute(insert_query, booking)
                    print("Da them du lieu dat phong mau.")
                
                transaction.commit() # Lưu lại tất cả các thay đổi
                print("Co so du lieu da duoc khoi tao thanh cong.")
            except Exception as e:
                print(f"Loi khi khoi tao CSDL: {e}")
                transaction.rollback() # Hoàn tác nếu có lỗi

def get_all_rooms():
    """Hàm này bây giờ sẽ dùng 'engine' đã được tạo sẵn."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM rooms ORDER BY name"))
        
        # Chuyển đổi kết quả thành list of dicts để giống với row_factory cũ
        rooms = [dict(row._mapping) for row in result]
        
    return rooms

def get_bookings_for_room(room_id):
    """Lấy tất cả các lượt đặt phòng cho một phòng cụ thể."""
    with engine.connect() as connection:
        # Dùng :id làm placeholder an toàn cho tham số
        query = text("SELECT * FROM bookings WHERE room_id = :id ORDER BY start_date")
        result = connection.execute(query, {"id": room_id})
        bookings = [dict(row._mapping) for row in result]
    return bookings
def get_bookings_for_month(year, month):
    """Lấy tất cả các lượt đặt phòng trong một tháng/năm cụ thể."""
    # Định dạng tháng để so sánh trong SQL, ví dụ: '2025-07'
    month_str = f"{year}-{month:02d}"
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()def get_bookings_for_month(year, month):
    """Lấy tất cả các lượt đặt phòng trong một tháng/năm cụ thể."""
    month_str = f"{year}-{month:02d}"
    with engine.connect() as connection:
        # Chú ý: Đã đổi hàm strftime của SQLite thành to_char của PostgreSQL
        # dialect.name sẽ giúp code tự nhận biết đang chạy trên môi trường nào
        if connection.dialect.name == 'sqlite':
            query = text("""
                SELECT b.*, r.name as room_name FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE strftime('%Y-%m', b.start_date) = :month_str
                ORDER BY b.start_date
            """)
        else: # Mặc định là PostgreSQL
            query = text("""
                SELECT b.*, r.name as room_name FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE to_char(b.start_date::date, 'YYYY-MM') = :month_str
                ORDER BY b.start_date
            """)
        
        result = connection.execute(query, {"month_str": month_str})
        bookings = [dict(row._mapping) for row in result]
    return bookings
def calculate_monthly_revenue(year, month):
    """Tính tổng doanh thu của tất cả các booking trong một tháng/năm cụ thể."""
    month_str = f"{year}-{month:02d}"
    with engine.connect() as connection:
        # Tương tự, đổi strftime thành to_char
        if connection.dialect.name == 'sqlite':
            query = text("SELECT SUM(price) FROM bookings WHERE strftime('%Y-%m', start_date) = :month_str")
        else: # Mặc định là PostgreSQL
            query = text("SELECT SUM(price) FROM bookings WHERE to_char(start_date::date, 'YYYY-MM') = :month_str")
        
        result = connection.execute(query, {"month_str": month_str})
        total = result.scalar_one_or_none()
    return total if total is not None else 0
def calculate_yearly_revenue(year):
    """Tính tổng doanh thu của một năm cụ thể."""
    year_str = str(year)
    with engine.connect() as connection:
        # Tương tự, đổi strftime thành to_char
        if connection.dialect.name == 'sqlite':
            query = text("SELECT SUM(price) FROM bookings WHERE strftime('%Y', start_date) = :year_str")
        else: # Mặc định là PostgreSQL
            query = text("SELECT SUM(price) FROM bookings WHERE to_char(start_date::date, 'YYYY') = :year_str")
            
        result = connection.execute(query, {"year_str": year_str})
        total = result.scalar_one_or_none()
    return total if total is not None else 0

def calculate_grand_total_revenue():
    """Tính tổng doanh thu từ trước đến nay."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT SUM(price) FROM bookings"))
        total = result.scalar_one_or_none() # .scalar_one_or_none() là cách an toàn để lấy giá trị đơn
    return total if total is not None else 0
# if __name__ == '__main__':
#     init_db()