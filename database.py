import sqlite3

DATABASE_FILE = 'hotel.db'

def init_db():
    """
    Hàm này sẽ được chạy một lần duy nhất để khởi tạo cơ sở dữ liệu.
    Nó sẽ tạo ra file hotel.db và các bảng cần thiết.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    print("Bảng 'rooms' đã được tạo hoặc đã tồn tại.")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            source TEXT,
            price REAL,
            guest_country TEXT,
            notes TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')
    print("Bảng 'bookings' đã được tạo hoặc đã tồn tại.")

    cursor.execute("SELECT COUNT(*) FROM rooms")
    room_count = cursor.fetchone()[0]
    if room_count == 0:
        print("Thêm 15 phòng mặc định vào cơ sở dữ liệu...")
        for i in range(1, 16):
            cursor.execute("INSERT INTO rooms (name) VALUES (?)", (f'Phòng {i:03}',))
        print("Đã thêm 15 phòng.")
    else:
        print("Bảng 'rooms' đã có dữ liệu, không cần thêm mới.")

    cursor.execute("SELECT COUNT(*) FROM bookings")
    booking_count = cursor.fetchone()[0]
    if booking_count == 0:
        print("Thêm dữ liệu đặt phòng mẫu...")
        sample_bookings = [
            (1, '2025-07-05', '2025-07-08', 'Agoda', 2500000, 'Hàn Quốc', 'Khách yêu cầu phòng yên tĩnh.'),
            (1, '2025-07-12', '2025-07-13', 'Booking.com', 900000, 'Việt Nam', ''),
            (3, '2025-07-06', '2025-07-07', 'Khách vãng lai', 750000, 'Pháp', 'Check-in muộn sau 10h tối.')
        ]
        cursor.executemany('''
            INSERT INTO bookings (room_id, start_date, end_date, source, price, guest_country, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_bookings)
        print("Đã thêm dữ liệu đặt phòng mẫu.")
    
    conn.commit()
    conn.close()
    print("Cơ sở dữ liệu đã được khởi tạo thành công.")

def get_all_rooms():
    """Hàm này lấy tất cả các phòng từ cơ sở dữ liệu."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms ORDER BY name")
    rooms = cursor.fetchall()
    conn.close()
    return rooms

def get_bookings_for_room(room_id):
    """Lấy tất cả các lượt đặt phòng cho một phòng cụ thể."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # === ĐÃ SỬA LỖI Ở ĐÂY: Thêm dấu phẩy sau room_id ===
    cursor.execute("SELECT * FROM bookings WHERE room_id = ? ORDER BY start_date", (room_id,))
    bookings = cursor.fetchall()
    conn.close()
    return bookings
def get_bookings_for_month(year, month):
    """Lấy tất cả các lượt đặt phòng trong một tháng/năm cụ thể."""
    # Định dạng tháng để so sánh trong SQL, ví dụ: '2025-07'
    month_str = f"{year}-{month:02d}"
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # strftime('%Y-%m', start_date) sẽ trích xuất 'năm-tháng' từ ngày đầy đủ
    cursor.execute("""
        SELECT b.*, r.name as room_name FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE strftime('%Y-%m', b.start_date) = ?
        ORDER BY b.start_date
    """, (month_str,))
    bookings = cursor.fetchall()
    conn.close()
    return bookings
def calculate_monthly_revenue(year, month):
    """Tính tổng doanh thu của tất cả các booking trong một tháng/năm cụ thể."""
    month_str = f"{year}-{month:02d}"
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(price) FROM bookings
        WHERE strftime('%Y-%m', start_date) = ?
    """, (month_str,))
    # fetchone()[0] sẽ lấy giá trị của cột đầu tiên trong hàng đầu tiên
    total = cursor.fetchone()[0]
    conn.close()
    # Nếu không có booking nào, total sẽ là None. Ta trả về 0 trong trường hợp này.
    return total if total is not None else 0
def calculate_yearly_revenue(year):
    """Tính tổng doanh thu của một năm cụ thể."""
    year_str = str(year)
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(price) FROM bookings
        WHERE strftime('%Y', start_date) = ?
    """, (year_str,))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0

def calculate_grand_total_revenue():
    """Tính tổng doanh thu từ trước đến nay."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(price) FROM bookings")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0
if __name__ == '__main__':
    init_db()