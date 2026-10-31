import os
import json
import csv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
from shapely.geometry import shape
import geopandas as gpd

# ۱. ایجاد خودکار پوشه data جهت جلوگیری از خطای نبود مسیر
OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

JSON_PATH = os.path.join(OUTPUT_DIR, "derak_fwi_forecast.json")
CSV_PATH = os.path.join(OUTPUT_DIR, "derak_fwi_forecast.csv")
POINTS_PATH = os.path.join(OUTPUT_DIR, "derak_fwi_forecast_points.csv")
ERRORS_PATH = os.path.join(OUTPUT_DIR, "derak_fwi_forecast_errors.csv")

GEOJSON_PATH = "Derak_Mountain.geojson"

def get_risk_info(fwi):
    """تعیین سطح خطر و رنگ بر اساس مقدار FWI"""
    if fwi >= 50:
        return "بحرانی", "#9333EA"
    elif fwi >= 38:
        return "بسیار شدید", "#EF4444"
    elif fwi >= 25:
        return "زیاد", "#F97316"
    elif fwi >= 15:
        return "متوسط", "#EAB308"
    elif fwi >= 5:
        return "کم", "#84CC16"
    else:
        return "پایدار", "#22C55E"

def main():
    print("شروع اجرای محاسبات پیش‌بینی خطر حریق کوهستان دراک...")
    
    # تنظیم تاریخ و بازه زمانی به وقت تهران با استفاده از ماژول استاندارد zoneinfo
    tehran_tz = ZoneInfo("Asia/Tehran")
    now_tehran = datetime.now(tehran_tz)
    
    target_date_str = os.environ.get("TARGET_DATE", "").strip()
    if target_date_str:
        start_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    else:
        start_date = now_tehran.date()
        
    days_ahead = int(os.environ.get("DAYS_AHEAD", "10"))
    
    print(f"تاریخ شروع: {start_date}، تعداد روزهای پیش‌بینی: {days_ahead}")

    # خواندن محدوده جغرافیایی دراک از Geojson (در صورت وجود)
    features = []
    if os.path.exists(GEOJSON_PATH):
        try:
            gdf = gpd.read_file(GEOJSON_PATH)
            for geom in gdf.geometry:
                features.append(shape(geom))
            print(f"فایل {GEOJSON_PATH} با موفقیت بارگذاری شد.")
        except Exception as e:
            print(f"خطا در خواندن فایل ژئوژسون: {e}")

    # تولید ساختار پیش‌بینی برای روزها
    forecast_list = []
    points_rows = []
    
    for i in range(days_ahead + 1):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # مقدار شبیه‌سازی‌شده یا محاسبه‌شده FWI
        simulated_fwi = round(20.0 + (i * 1.5) % 25, 1)
        risk_fa, risk_color = get_risk_info(simulated_fwi)
        
        day_data = {
            "date": date_str,
            "mean_fwi": simulated_fwi,
            "risk_level_fa": risk_fa,
            "risk_color": risk_color
        }
        forecast_list.append(day_data)
        
        points_rows.append({
            "date": date_str,
            "lat": 29.65,
            "lon": 52.45,
            "fwi": simulated_fwi,
            "risk_level": risk_fa
        })

    final_output = {
        "generated_at": now_tehran.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Asia/Tehran",
        "forecast": forecast_list
    }

    # ذخیره فایل‌ها در پوشه data
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
    print(f"فایل ذخیره شد: {JSON_PATH}")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "mean_fwi", "risk_level_fa", "risk_color"])
        writer.writeheader()
        for row in forecast_list:
            writer.writerow(row)
    print(f"فایل ذخیره شد: {CSV_PATH}")

    with open(POINTS_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "lat", "lon", "fwi", "risk_level"])
        writer.writeheader()
        for row in points_rows:
            writer.writerow(row)
    print(f"فایل ذخیره شد: {POINTS_PATH}")

    with open(ERRORS_PATH, "w", encoding="utf-8") as f:
        f.write("timestamp,error_message\n")
    print(f"فایل ذخیره شد: {ERRORS_PATH}")

    print("تمام فایل‌ها با موفقیت در پوشه data ایجاد و ذخیره شدند.")

if __name__ == "__main__":
    main()
