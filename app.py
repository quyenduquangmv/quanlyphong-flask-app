from flask import Flask, render_template, redirect, url_for
from datetime import datetime
from database import (
    get_all_rooms, 
    get_bookings_for_room, 
    get_bookings_for_month, 
    calculate_monthly_revenue, 
    calculate_yearly_revenue, 
    calculate_grand_total_revenue
)

# Khởi tạo ứng dụng web Flask
app = Flask(__name__)

@app.route('/')
def trang_chu():
    """
    Đây là route cho trang chủ. 
    Nó sẽ lấy dữ liệu và hiển thị ra trang index.html.
    """
    try:
        # Lấy ngày tháng hiện tại để tính toán doanh thu
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Gọi các hàm từ database.py để lấy dữ liệu
        grand_total = calculate_grand_total_revenue()
        yearly_revenue = calculate_yearly_revenue(current_year)
        monthly_revenue = calculate_monthly_revenue(current_year, current_month)
        all_rooms = get_all_rooms()

        # Trả về trang HTML và "nhồi" dữ liệu vào
        return render_template(
            'index.html',
            rooms=all_rooms,
            grand_total=grand_total,
            yearly_revenue=yearly_revenue,
            monthly_revenue=monthly_revenue,
            current_year=current_year
        )
    except Exception as e:
        # In ra lỗi nếu có vấn đề xảy ra để dễ dàng gỡ rối
        print(f"Da co loi xay ra tai trang chu: {e}")
        # Trả về một trang lỗi đơn giản
        return "Da co loi xay ra, vui long kiem tra log tren server.", 500

# Các route khác cho các chức năng khác có thể được thêm vào đây
# Ví dụ: một route để xem chi tiết một phòng
@app.route('/room/<int:room_id>')
def chi_tiet_phong(room_id):
    try:
        bookings = get_bookings_for_room(room_id)
        # Giả sử bạn có một template tên là 'room_details.html'
        # Nếu không có, bạn có thể tạo nó hoặc xóa route này đi
        return render_template('room_details.html', bookings=bookings, room_id=room_id)
    except Exception as e:
        print(f"Da co loi khi xem chi tiet phong {room_id}: {e}")
        return "Khong the tim thay chi tiet cho phong nay.", 404

# Khối lệnh này để bạn có thể chạy app trên máy tính của mình để kiểm tra
if __name__ == '__main__':
    app.run(debug=True)