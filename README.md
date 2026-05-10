# 雾霾定位探测系统

基于 Flask 的实时天气与空气质量监测 Web 应用，支持 GPS / IP 双模定位，提供雾霾等级评估与健康建议。

## 项目架构

```
bce/
├── app.py                  # Flask 应用入口，路由 + API 定义
├── config.py               # 环境变量加载与配置类
├── models.py               # SQLite 数据库初始化与 CRUD 操作
├── utils.py                # 业务逻辑：定位、天气、空气、雾霾分类、健康建议
├── requirements.txt        # Python 依赖
├── .env                    # 敏感配置（API Key，不提交到 git）
├── weather.db              # SQLite 数据库文件
├── templates/
│   └── index.html          # 前端页面（Jinja2 模板）
└── static/
    ├── css/
    │   └── style.css       # Glassmorphism 暗色主题样式
    ├── js/
    │   ├── main.js         # 前端核心逻辑（定位、数据获取、渲染）
    │   ├── echart.js       # ECharts 图表库（本地副本）
    │   ├── skycons.js      # 天气图标动画库（本地副本）
    │   └── jquery-2.2.3.min.js
    ├── images/             # 背景图片素材（历史遗留）
    └── fonts/              # 中文字体文件（历史遗留）
```

### 后端（Python / Flask）

| 文件 | 职责 |
|------|------|
| `app.py` | Flask 应用定义。`/` 返回前端页面；3 个 JSON API 端点（见下方） |
| `utils.py` | 调用和风天气、天行天气、ip-api.com 三个外部服务；雾/霾等级判定；健康建议生成 |
| `models.py` | SQLite 四张表（`city`、`weather_snapshot`、`air_snapshot`、`forecast`）的建表与读写 |
| `config.py` | 通过 `python-dotenv` 从 `.env` 文件加载 API Key，提供 `Config` 类 |

### 前端（HTML5 + jQuery + ECharts）

| 文件 | 职责 |
|------|------|
| `index.html` | CSS Grid 2×2 卡片布局：实时天气、雾霾评估、空气质量、七天预报图表 |
| `style.css` | Glassmorphism 毛玻璃暗色主题，含浮动光晕背景动画，响应式适配 |
| `main.js` | 浏览器 GPS 定位 → 后端 IP 回退 → 拉取天气/空气/预报 → 渲染图表和 UI |

## API 端点

### `GET /` — 前端页面

返回 `templates/index.html`。

### `GET /api/location` — 定位

| 参数 | 类型 | 说明 |
|------|------|------|
| `lat` | float | 可选，浏览器 GPS 纬度 |
| `lon` | float | 可选，浏览器 GPS 经度 |
| `city` | string | 可选，与 GPS 坐标配合使用 |

**定位策略：** 如果传入了 `lat` / `lon`（浏览器 GPS），直接使用该坐标（`"source": "browser"`）。否则调用 ip-api.com 做 IP 定位（`"source": "ip"`）。两次都失败则返回 `"source": "fallback"`，lat/lon 为 null。

```json
{
  "city": "上海",
  "lat": 31.23,
  "lon": 121.47,
  "country": "中国",
  "region": "上海",
  "ip": "127.0.0.1",
  "source": "browser"
}
```

### `GET /api/weather` — 实时天气 + 空气 + 雾霾评估

| 参数 | 类型 | 说明 |
|------|------|------|
| `lat` | float | **必填**，纬度 |
| `lon` | float | **必填**，经度 |
| `city` | string | 可选，城市名（用于数据库记录） |

返回示例：

```json
{
  "weather": {
    "temp": "22",
    "feelsLike": "20",
    "text": "晴",
    "humidity": "46",
    "windSpeed": "15",
    "vis": "30000",
    "cloud": "3"
  },
  "air": {
    "aqi": "33",
    "category": "优",
    "pm2p5": "16",
    "pm10": "29",
    "so2": "8",
    "no2": "17",
    "co": "0.4",
    "o3": "104"
  },
  "fog_haze": {
    "fog_level": 0,
    "fog_label": "无雾",
    "haze_level": 1,
    "haze_label": "优",
    "advice": "当前天气状况良好（无雾、优），适合户外活动。"
  }
}
```

### `GET /api/forecast` — 七天预报

| 参数 | 类型 | 说明 |
|------|------|------|
| `city` | string | 用于查询数据库缓存 |

返回 `{"forecast": [...]}`，每个元素包含 `date`、`temp_max`、`temp_min`、`humidity`、`weather_text`、`wind_dir`、`wind_speed`。

## 雾/霾分级标准

### 雾等级（基于能见度，单位：米）

| 等级 | 标签 | 能见度范围 |
|------|------|-----------|
| 0 | 无雾 | ≥ 10000 |
| 1 | 轻雾 | 1000 – 2000 |
| 2 | 雾 | 500 – 1000 |
| 3 | 大雾 | 200 – 500 |
| 4 | 浓雾 | 50 – 200 |
| 5 | 严重浓雾 | < 50 |

### 霾等级（基于 AQI）

| 等级 | 标签 | AQI 范围 |
|------|------|---------|
| 1 | 优 | 0 – 50 |
| 2 | 良 | 51 – 100 |
| 3 | 轻度污染 | 101 – 150 |
| 4 | 中度污染 | 151 – 200 |
| 5 | 重度污染 | 201 – 300 |
| 6 | 严重污染 | > 300 |

## 外部 API 依赖

| 服务 | 用途 | 注册地址 |
|------|------|---------|
| 和风天气 (QWeather) | 实时天气 + 空气质量 | https://dev.qweather.com |
| 天行天气 (Tianqiapi) | 七天天气预报 | https://www.tianqiapi.com |
| ip-api.com | IP 地理定位（免费版） | http://ip-api.com |

## 快速开始

### 1. 环境准备

```bash
# Python 3.8+
python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

### 2. 配置 API Key

编辑 `.env` 文件，填入你在和风天气和天行天气注册获取的 Key：

```env
QWEATHER_API_KEY=你的和风天气key
TIANQIAPI_APPID=你的天行天气appid
TIANQIAPI_APPSECRET=你的天行天气appsecret
TIANQIAPI_URL=https://gfeljm.tianqiapi.com/api
SECRET_KEY=任意随机字符串
```

### 3. 启动

```bash
python app.py
```

浏览器打开 `http://localhost:5000`。

**首次访问时浏览器会弹出位置权限请求，点击"允许"以获取准确的 GPS 定位。** 如果拒绝，系统会回退到 IP 定位；如果 IP 定位也失败，页面将提示定位失败。

### 4. 数据库

首次启动时自动创建 `weather.db`（SQLite），包含 4 张表用于记录查询历史。无需手动初始化。
