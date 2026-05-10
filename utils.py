import requests
from config import Config

# Bypass system proxy settings (Windows registry proxy)
_session = requests.Session()
_session.trust_env = False


def get_location_by_ip(ip=None):
    url = "http://ip-api.com/json/"
    if ip and ip != "127.0.0.1":
        url += ip
    resp = _session.get(url, timeout=10)
    data = resp.json()
    if data.get("status") == "fail":
        # Don't hardcode Beijing — return a sentinel so the caller knows IP lookup failed
        return None
    return {
        "city": data.get("city", "未知"),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "country": data.get("country", ""),
        "region": data.get("regionName", ""),
        "ip": data.get("query", ip or "")
    }


def reverse_geocode(lat, lon):
    """Get city name from coordinates using QWeather City Lookup API."""
    key = Config.QWEATHER_API_KEY
    url = f"https://geoapi.qweather.com/v2/city/lookup?location={lon},{lat}&key={key}&number=1"
    try:
        resp = _session.get(url, timeout=10)
        data = resp.json()
        if data.get("code") == "200" and data.get("location"):
            loc = data["location"][0]
            name = loc.get("name", "")
            adm1 = loc.get("adm1", "")
            adm2 = loc.get("adm2", "")
            # Prefer city-level (adm2) over district-level (name)
            city = adm2 or name or "未知"
            region = adm1 or ""
            return {
                "city": city,
                "region": region,
                "country": loc.get("country", "中国")
            }
    except Exception as e:
        print(f"[REVERSE GEOCODE ERROR] {e}")
    return {"city": "未知位置", "region": "", "country": ""}


def get_weather_now(lon, lat):
    key = Config.QWEATHER_API_KEY
    url = f"https://devapi.qweather.com/v7/weather/now?location={lon},{lat}&key={key}"
    resp = _session.get(url, timeout=10)
    data = resp.json()
    if data.get("code") != "200":
        return None
    now = data["now"]
    # QWeather returns visibility in km; convert to meters for fog classification
    if "vis" in now:
        try:
            now["vis"] = str(float(now["vis"]) * 1000)
        except (TypeError, ValueError):
            pass
    return now


def get_air_now(lon, lat):
    key = Config.QWEATHER_API_KEY
    url = f"https://devapi.qweather.com/v7/air/now?location={lon},{lat}&key={key}"
    resp = _session.get(url, timeout=10)
    data = resp.json()
    if data.get("code") != "200":
        return None
    return data["now"]


def get_forecast_7d():
    appid = Config.TIANQIAPI_APPID
    appsecret = Config.TIANQIAPI_APPSECRET
    base_url = Config.TIANQIAPI_URL
    url = f"{base_url}?unescape=1&version=v91&appid={appid}&appsecret={appsecret}&ext=&cityid="
    resp = _session.get(url, timeout=10)
    data = resp.json()
    if not data.get("data"):
        return []
    forecast = []
    for day in data["data"]:
        forecast.append({
            "date": day.get("date", ""),
            "temp_max": day.get("tem1", day.get("tem", "")),
            "temp_min": day.get("tem2", ""),
            "humidity": day.get("humidity", ""),
            "weather_text": day.get("wea", ""),
            "wind_dir": day.get("win", [""])[0] if isinstance(day.get("win"), list) else day.get("win", ""),
            "wind_speed": day.get("win_speed", "")
        })
    return forecast


def classify_fog(visibility):
    if visibility is None:
        return {"level": -1, "label": "未知"}
    try:
        v = float(visibility)
    except (TypeError, ValueError):
        return {"level": -1, "label": "未知"}
    if v < 50:
        return {"level": 5, "label": "严重浓雾"}
    elif v < 200:
        return {"level": 4, "label": "浓雾"}
    elif v < 500:
        return {"level": 3, "label": "大雾"}
    elif v < 1000:
        return {"level": 2, "label": "雾"}
    elif v < 2000:
        return {"level": 1, "label": "轻雾"}
    elif v < 10000:
        return {"level": 0, "label": "薄雾"}
    else:
        return {"level": 0, "label": "无雾"}


def classify_haze(aqi):
    if aqi is None:
        return {"level": -1, "label": "未知"}
    try:
        a = int(aqi)
    except (TypeError, ValueError):
        return {"level": -1, "label": "未知"}
    if a <= 50:
        return {"level": 1, "label": "优"}
    elif a <= 100:
        return {"level": 2, "label": "良"}
    elif a <= 150:
        return {"level": 3, "label": "轻度污染"}
    elif a <= 200:
        return {"level": 4, "label": "中度污染"}
    elif a <= 300:
        return {"level": 5, "label": "重度污染"}
    else:
        return {"level": 6, "label": "严重污染"}


def get_health_advice(fog_result, haze_result):
    fog_level = fog_result["level"]
    haze_level = haze_result["level"]
    fog_label = fog_result["label"]
    haze_label = haze_result["label"]

    if fog_level >= 3 and haze_level >= 4:
        return f"当前{fog_label}、{haze_label}，建议取消户外活动并紧闭门窗。外出务必佩戴N95口罩，行车开启雾灯并减速慢行。"
    elif fog_level >= 3:
        return f"当前{fog_label}，能见度极低。驾车出行请开启雾灯、保持车距。行人请穿戴反光衣物，减少户外停留。"
    elif haze_level >= 4:
        return f"当前{haze_label}，空气质量较差。建议减少户外运动，外出佩戴N95口罩，关闭门窗并使用空气净化器。"
    elif fog_level >= 1 or haze_level >= 3:
        return f"当前{fog_label}、{haze_label}，敏感人群应减少户外活动。建议佩戴口罩，注意交通安全。"
    elif fog_level >= 0 and haze_level >= 2:
        return f"当前{fog_label}、{haze_label}，空气质量尚可但需注意防护。"
    else:
        return f"当前天气状况良好（{fog_label}、{haze_label}），适合户外活动。"
