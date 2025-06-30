from pytrends.request import TrendReq
import pandas as pd

def analyze_meo_vac_trends():
    """
    Hàm này được chuyên biệt hóa để chỉ phân tích xu hướng cho Mèo Vạc, Hà Giang.
    Nó không cần tham số đầu vào nữa.
    """
    LOCATION = "Hà Nội"
    
    try:
        pytrends = TrendReq(hl='vi-VN', tz=420)
        
        kw_list = [f"khách sạn {LOCATION}", f"homestay {LOCATION}", f"nhà nghỉ {LOCATION}"]

        pytrends.build_payload(kw_list, cat=0, timeframe='today 1-m', geo='VN', gprop='')

        interest_df = pytrends.interest_over_time()
        top_keyword = None
        if not interest_df.empty:
            mean_interest = interest_df.drop(columns='isPartial').mean()
            top_keyword = mean_interest.idxmax()

        related_queries_data = pytrends.related_queries()
        main_keyword_data = related_queries_data.get(kw_list[0], {})
        
        rising_queries = main_keyword_data.get('rising')
        top_queries = main_keyword_data.get('top')
        
        return {
            "top_keyword": top_keyword,
            "rising_queries": rising_queries,
            "top_queries": top_queries,
            "error": None
        }

    except Exception as e:
        print(f"Lỗi khi phân tích trends: {e}")
        return {
            "top_keyword": None,
            "rising_queries": None,
            "top_queries": None,
            "error": "Không thể lấy dữ liệu từ Google Trends. Có thể bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau."
        }
    