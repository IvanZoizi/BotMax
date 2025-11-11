# # Установите библиотеку: pip install timezonefinder
#
# from timezonefinder import TimezoneFinder
# import pytz
# from datetime import datetime
#
#
# def get_timezone_simple(latitude: float, longitude: float) -> Dict[str, Any]:
#     """
#     Простая функция для получения часового пояса с использованием timezonefinder
#     """
#     tf = TimezoneFinder()
#
#     timezone_name = tf.timezone_at(lat=latitude, lng=longitude)
#
#     if not timezone_name:
#         raise ValueError("Не удалось определить часовой пояс для данных координат")
#
#     tz = pytz.timezone(timezone_name)
#     now = datetime.now(tz)
#     utc_offset = now.utcoffset().total_seconds() / 3600
#
#     return {
#         'timezone_id': timezone_name,
#         'timezone_name': timezone_name,
#         'total_offset': utc_offset,
#         'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
#         'is_dst': now.dst().total_seconds() > 0
#     }
#
#
# # Пример использования
# if __name__ == "__main__":
#     moscow_tz = get_timezone_simple(55.7558, 37.6173)
#     print(f"Москва: {moscow_tz}")