import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY", "")
    TIANQIAPI_APPID = os.getenv("TIANQIAPI_APPID", "")
    TIANQIAPI_APPSECRET = os.getenv("TIANQIAPI_APPSECRET", "")
    TIANQIAPI_URL = os.getenv("TIANQIAPI_URL", "https://gfeljm.tianqiapi.com/api")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "weather.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-production")
