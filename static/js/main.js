$(document).ready(function () {

  // ========== 1. Skycons ==========
  var skycons = new Skycons({ color: "#94a3b8" });

  function getSkyconType(text) {
    if (!text) return "cloudy";
    if (text.indexOf("晴") >= 0) return "clear-day";
    if (text.indexOf("多云") >= 0) return "partly-cloudy-day";
    if (text.indexOf("阴") >= 0) return "cloudy";
    if (text.indexOf("雨") >= 0) return "rain";
    if (text.indexOf("雪") >= 0) return "snow";
    if (text.indexOf("雾") >= 0 || text.indexOf("霾") >= 0) return "fog";
    if (text.indexOf("风") >= 0) return "wind";
    return "cloudy";
  }

  // ========== 2. ECharts ==========
  var chartDom = document.getElementById("forecastChart");
  var forecastChart = echarts.init(chartDom);
  var option = {
    tooltip: { trigger: "axis" },
    legend: {
      data: ["最高气温", "最低气温", "湿度"],
      textStyle: { color: "#94a3b8" },
      top: 0
    },
    grid: { left: "3%", right: "4%", bottom: "10%", top: "40px", containLabel: true },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: [],
      axisLabel: { color: "#888", fontSize: 11 },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.1)" } }
    },
    yAxis: [
      {
        type: "value", name: "°C",
        nameTextStyle: { color: "#888" },
        axisLabel: { color: "#888", formatter: "{value}°" },
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } }
      },
      {
        type: "value", name: "%",
        nameTextStyle: { color: "#888" },
        axisLabel: { color: "#888", formatter: "{value}%" },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: "最高气温", type: "line", yAxisIndex: 0, data: [],
        smooth: true, symbol: "circle", symbolSize: 6,
        itemStyle: { color: "#f59e0b" },
        lineStyle: { width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(245,158,11,0.25)" },
            { offset: 1, color: "rgba(245,158,11,0.02)" }
          ])
        }
      },
      {
        name: "最低气温", type: "line", yAxisIndex: 0, data: [],
        smooth: true, symbol: "circle", symbolSize: 6,
        itemStyle: { color: "#38bdf8" },
        lineStyle: { width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(56,189,248,0.25)" },
            { offset: 1, color: "rgba(56,189,248,0.02)" }
          ])
        }
      },
      {
        name: "湿度", type: "line", yAxisIndex: 1, data: [],
        smooth: true, symbol: "diamond", symbolSize: 6,
        itemStyle: { color: "#a78bfa" },
        lineStyle: { width: 2, type: "dashed" }
      }
    ]
  };
  forecastChart.setOption(option);

  // ========== 3. Update fog/haze bars ==========
  function setFogBar(level) {
    var pct = 0;
    if (level >= 5) pct = 100;
    else if (level >= 4) pct = 80;
    else if (level >= 3) pct = 60;
    else if (level >= 2) pct = 40;
    else if (level >= 1) pct = 20;
    else if (level >= 0) pct = 5;
    $("#fogBar").css("width", pct + "%");
  }

  function setHazeBar(level) {
    var pct = 0;
    if (level >= 6) pct = 100;
    else if (level >= 5) pct = 83;
    else if (level >= 4) pct = 67;
    else if (level >= 3) pct = 50;
    else if (level >= 2) pct = 33;
    else if (level >= 1) pct = 10;
    $("#hazeBar").css("width", pct + "%");
  }

  // ========== 4. Fetch data ==========

  // 4a. Location: HTML5 Geolocation first, then IP fallback
  function fetchLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        function (pos) {
          // Browser GPS success — send coords to backend
          var lat = pos.coords.latitude;
          var lon = pos.coords.longitude;
          $.get("/api/location", { lat: lat, lon: lon, city: "当前位置", source: "gps" })
            .done(function (loc) { applyLocation(loc); })
            .fail(function () { fetchIpLocation(); });
        },
        function () {
          // GPS denied or unavailable — fall back to IP
          fetchIpLocation();
        },
        { timeout: 5000, maximumAge: 600000 }
      );
    } else {
      fetchIpLocation();
    }
  }

  function fetchIpLocation() {
    $.get("/api/location")
      .done(function (loc) { applyLocation(loc); })
      .fail(function () {
        $("#locCity").text("定位失败").addClass("status-error");
        $("#locSource").text("无可用定位来源");
        showErrorMessage("无法获取位置信息，请检查网络连接");
      });
  }

  function applyLocation(loc) {
    var city = loc.city || "未知";
    if (loc.lat == null || loc.lon == null) {
      $("#locCity").text("定位失败").addClass("status-error");
      $("#locSource").text("无位置数据");
      showErrorMessage("位置数据无效，无法加载天气");
      return;
    }
    $("#locCity").text(city).removeClass("status-loading status-error");
    var srcLabel = "";
    if (loc.source === "browser" || loc.source === "gps") srcLabel = "GPS 定位";
    else if (loc.source === "ip") srcLabel = "IP 定位";
    else srcLabel = "默认位置";
    $("#locSource").text(srcLabel);

    fetchWeather(city, loc.lat, loc.lon);
    fetchForecast(city, loc.lat, loc.lon);
  }

  // 4b. Weather + Air
  function fetchWeather(city, lat, lon) {
    $.get("/api/weather", { lat: lat, lon: lon, city: city })
      .done(function (data) {
        if (data.weather) {
          var w = data.weather;
          $("#tempValue").text(w.temp || "--").removeClass("status-loading");
          $("#weatherDesc").text(w.text || "--").removeClass("status-loading");
          $("#humidity").text((w.humidity != null ? w.humidity : "--") + "%");
          $("#windSpeed").text(w.windSpeed || "--");
          $("#visibility").text(w.vis ? (parseFloat(w.vis) / 1000).toFixed(1) + " km" : "--");

          var skyType = getSkyconType(w.text);
          skycons.set("skycon", skyType);
          skycons.play();
        } else {
          showWeatherError();
        }

        if (data.air) {
          var a = data.air;
          $("#aqiValue").text(a.aqi || "--").removeClass("status-loading");
          $("#pm25Value").text(a.pm2p5 != null ? a.pm2p5 : "--").removeClass("status-loading");
          $("#pm10Value").text(a.pm10 != null ? a.pm10 : "--").removeClass("status-loading");
          $("#so2Value").text(a.so2 != null ? a.so2 : "--").removeClass("status-loading");
          $("#no2Value").text(a.no2 != null ? a.no2 : "--").removeClass("status-loading");
          $("#coValue").text(a.co != null ? a.co : "--").removeClass("status-loading");
          $("#o3Value").text(a.o3 != null ? a.o3 : "--").removeClass("status-loading");
          $("#airCategory").text("空气质量：" + (a.category || "--")).removeClass("status-loading");

          // Color AQI circle
          colorAqiCircle(parseInt(a.aqi) || 0);
        } else {
          showAirError();
        }

        if (data.fog_haze) {
          var fh = data.fog_haze;
          $("#fogLevel").text(fh.fog_label || "--").removeClass("status-loading");
          $("#hazeLevel").text(fh.haze_label || "--").removeClass("status-loading");
          $("#healthAdvice .advice-text").text(fh.advice || "");

          setFogBar(fh.fog_level);
          setHazeBar(fh.haze_level);

          // Color-code text
          if (fh.fog_level >= 3) $("#fogLevel").css("color", "#f59e0b");
          else if (fh.fog_level >= 1) $("#fogLevel").css("color", "#facc15");
          else $("#fogLevel").css("color", "#34d399");

          if (fh.haze_level >= 4) $("#hazeLevel").css("color", "#ef4444");
          else if (fh.haze_level >= 3) $("#hazeLevel").css("color", "#f59e0b");
          else if (fh.haze_level >= 2) $("#hazeLevel").css("color", "#facc15");
          else $("#hazeLevel").css("color", "#34d399");
        } else {
          $("#fogLevel, #hazeLevel").text("获取失败").addClass("status-error");
          $("#healthAdvice .advice-text").text("天气数据获取失败，请稍后重试");
        }
      })
      .fail(function () {
        showWeatherError();
        showAirError();
        $("#fogLevel, #hazeLevel").text("获取失败").addClass("status-error");
        $("#healthAdvice .advice-text").text("网络连接失败，请稍后重试");
      });
  }

  // 4c. Forecast
  function fetchForecast(city, lat, lon) {
    $.get("/api/forecast", { city: city, lat: lat, lon: lon })
      .done(function (data) {
        var forecast = data.forecast || [];
        if (forecast.length === 0) {
          chartDom.innerHTML = '<p style="text-align:center;color:#666;padding-top:120px">暂无预报数据</p>';
          return;
        }
        option.xAxis.data = [];
        option.series[0].data = [];
        option.series[1].data = [];
        option.series[2].data = [];

        for (var i = 0; i < forecast.length; i++) {
          var d = forecast[i].date || "";
          option.xAxis.data.push(d.length > 5 ? d.substring(5) : d);
          option.series[0].data.push(parseFloat(forecast[i].temp_max) || null);
          option.series[1].data.push(parseFloat(forecast[i].temp_min) || null);
          option.series[2].data.push(parseFloat(forecast[i].humidity) || null);
        }
        forecastChart.setOption(option);
      })
      .fail(function () {
        chartDom.innerHTML = '<p style="text-align:center;color:#666;padding-top:120px">预报获取失败</p>';
      });
  }

  // ========== 5. Helpers ==========
  function colorAqiCircle(aqi) {
    var el = $("#aqiCircle");
    var color, bg;
    if (aqi <= 50)       { color = "#34d399"; bg = "rgba(52,211,153,0.15)"; }
    else if (aqi <= 100) { color = "#facc15"; bg = "rgba(250,204,21,0.15)"; }
    else if (aqi <= 150) { color = "#f59e0b"; bg = "rgba(245,158,11,0.15)"; }
    else if (aqi <= 200) { color = "#f97316"; bg = "rgba(249,115,22,0.15)"; }
    else if (aqi <= 300) { color = "#ef4444"; bg = "rgba(239,68,68,0.15)"; }
    else                 { color = "#7c3aed"; bg = "rgba(124,58,237,0.15)"; }
    el.css({ "border-color": color, "background": bg });
    el.find(".air-number").css("color", color);
  }

  function showWeatherError() {
    $("#tempValue").text("--").addClass("status-error");
    $("#weatherDesc").text("获取失败").addClass("status-error");
    $("#humidity").text("--%");
    $("#windSpeed").text("--");
    $("#visibility").text("--");
  }

  function showAirError() {
    $("#aqiValue,#pm25Value,#pm10Value,#so2Value,#no2Value,#coValue,#o3Value")
      .text("--").addClass("status-error");
    $("#airCategory").text("数据获取失败").addClass("status-error");
  }

  function showErrorMessage(msg) {
    $("#healthAdvice .advice-text").text(msg);
    $("#fogLevel, #hazeLevel").text("--").addClass("status-error");
  }

  // ========== 6. Resize handler ==========
  $(window).on("resize", function () {
    forecastChart.resize();
  });

  // ========== 7. Start ==========
  fetchLocation();
});
