from flask import Flask, render_template, redirect, url_for
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Đảm bảo chúng ta import đầy đủ các hàm cần thiết
from database import get_all_rooms, get_bookings_for_room, get_bookings_for_month, calculate_monthly_revenue, calculate_yearly_revenue, calculate_grand_total_revenue

app = Flask(__name__)

# Route cho trang Bảng điều khiển (homepage)
@app.route('/')
def trang_chu():
    # Lấy dữ liệu đặt phòng cho từng phòng như cũ
    rooms_list = get_all_rooms()
    full_rooms_data = []
    for room in rooms_list:
        room_dict = dict(room)
        bookings = get_bookings_for_room(room['id'])
        room_dict['bookings'] = bookings
        full_rooms_data.append(room_dict)

    # --- PHẦN MỚI: LẤY DỮ LIỆU THỐNG KÊ ---
    current_year = datetime.now().year
    yearly_revenue = calculate_yearly_revenue(current_year)
    grand_total = calculate_grand_total_revenue()

    # Gửi tất cả dữ liệu tới template
    return render_template(
        'index.html', 
        rooms=full_rooms_data,
        current_year=current_year,
        yearly_revenue=yearly_revenue,
        grand_total=grand_total
    )

# Route mặc định cho lịch, sẽ chuyển hướng đến tháng hiện tại
@app.route('/calendar/')
def calendar_redirect():
    now = datetime.now()
    return redirect(url_for('calendar_view', year=now.year, month=now.month))

# Route chính cho lịch, có thể nhận năm và tháng
@app.route('/calendar/<int:year>/<int:month>')
def calendar_view(year, month):
    calendar_weeks = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    bookings = get_bookings_for_month(year, month)
    total_revenue = calculate_monthly_revenue(year, month)

    bookings_by_day = {}
    for booking in bookings:
        day = datetime.strptime(booking['start_date'], '%Y-%m-%d').day
        if day not in bookings_by_day:
            bookings_by_day[day] = []
        bookings_by_day[day].append(dict(booking))
    
    current_date = datetime(year, month, 1)
    prev_date = current_date - relativedelta(months=1)
    next_date = current_date + relativedelta(months=1)

    return render_template(
        'calendar.html',
        year=year,
        month_name=month_name,
        calendar_weeks=calendar_weeks,
        bookings_by_day=bookings_by_day,
        total_revenue=total_revenue,
        prev_year=prev_date.year,
        prev_month=prev_date.month,
        next_year=next_date.year,
        next_month=next_date.month
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)