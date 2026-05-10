from flask import Flask, render_template, request, jsonify
from models import init_db, save_city, save_weather, save_air, save_forecast_batch, get_forecast
from utils import get_location_by_ip, reverse_geocode, get_weather_now, get_air_now, get_forecast_7d, classify_fog, classify_haze, get_health_advice

app = Flask(__name__)
app.secret_key = "dev-key-change-in-production"

# Initialize database on startup
init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/location")
def api_location():
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    # Accept browser-provided coordinates (HTML5 Geolocation) as the primary source
    browser_lat = request.args.get("lat", type=float)
    browser_lon = request.args.get("lon", type=float)

    if browser_lat is not None and browser_lon is not None:
        # Reverse geocode to get the actual city name
        geo = reverse_geocode(browser_lat, browser_lon)
        location = {
            "city": geo["city"],
            "lat": browser_lat,
            "lon": browser_lon,
            "country": geo.get("country", ""),
            "region": geo.get("region", ""),
            "ip": client_ip or "",
            "source": "browser"
        }
    else:
        try:
            location = get_location_by_ip(client_ip)
            if location is None:
                raise ValueError("IP lookup returned no result")
            location["source"] = "ip"
        except Exception as e:
            print(f"[LOCATION ERROR] {e}")
            location = {"city": "定位失败", "lat": None, "lon": None, "country": "", "region": "", "ip": client_ip or "", "source": "fallback"}

    try:
        save_city(
            ip=location["ip"] or client_ip or "",
            city=location["city"],
            lat=location["lat"],
            lon=location["lon"],
            country=location.get("country", ""),
            region=location.get("region", "")
        )
    except Exception as e:
        print(f"[DB SAVE ERROR] {e}")

    return jsonify(location)


@app.route("/api/weather")
def api_weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    city = request.args.get("city", "未知")

    if lat is None or lon is None:
        return jsonify({"error": "缺少经纬度参数"}), 400

    result = {"weather": None, "air": None, "fog_haze": None}
    weather = None
    air = None

    try:
        weather = get_weather_now(lon, lat)
        result["weather"] = weather
        if weather and city:
            try:
                save_weather(city, weather)
            except Exception as e:
                print(f"[DB SAVE WEATHER] {e}")
    except Exception as e:
        print(f"[WEATHER API ERROR] {e}")

    try:
        air = get_air_now(lon, lat)
        result["air"] = air
        if air and city:
            try:
                save_air(city, air)
            except Exception as e:
                print(f"[DB SAVE AIR] {e}")
    except Exception as e:
        print(f"[AIR API ERROR] {e}")

    if weather and air:
        fog = classify_fog(weather.get("vis"))
        haze = classify_haze(air.get("aqi"))
        advice = get_health_advice(fog, haze)
        result["fog_haze"] = {
            "fog_level": fog["level"],
            "fog_label": fog["label"],
            "haze_level": haze["level"],
            "haze_label": haze["label"],
            "advice": advice
        }

    return jsonify(result)


@app.route("/api/forecast")
def api_forecast():
    city = request.args.get("city", "")

    try:
        cached = get_forecast(city)
        if cached:
            return jsonify({"forecast": cached})
    except Exception as e:
        print(f"[FORECAST CACHE ERROR] {e}")

    try:
        forecast = get_forecast_7d()
        if forecast and city:
            try:
                save_forecast_batch(city, forecast)
            except Exception as e:
                print(f"[DB SAVE FORECAST] {e}")
        return jsonify({"forecast": forecast})
    except Exception as e:
        print(f"[FORECAST API ERROR] {e}")
        return jsonify({"forecast": []})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
