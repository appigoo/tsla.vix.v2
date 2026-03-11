import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime

# --- 1. 配置与 Secrets ---
st.set_page_config(page_title="TSLA-VIX 领先指标分析", layout="wide")

# 安全获取 Secrets
try:
    TG_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TG_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("请在 .streamlit/secrets.toml 中配置 TELEGRAM_TOKEN 和 TELEGRAM_CHAT_ID")
    st.stop()

# --- 2. 核心功能函数 ---
def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        st.error(f"Telegram 发送失败: {e}")

@st.cache_data(ttl=60)
def fetch_market_data():
    # 获取最近 5 天的 1 分钟数据 (最适合观察领先关系)
    # 使用 ^VIX (CBOE Volatility Index) 和 TSLA
    tickers = ["TSLA", "^VIX"]
    raw_data = yf.download(tickers, period="5d", interval="1m", group_by='column')
    
    if raw_data.empty:
        return pd.DataFrame()

    # 处理 yfinance 可能返回的 MultiIndex (Close, TSLA)
    df = pd.DataFrame()
    df['TSLA'] = raw_data['Close']['TSLA']
    df['VIX'] = raw_data['Close']['^VIX']
    
    return df.dropna()

# --- 3. 页面布局 ---
st.title("📊 TSLA 与 VIX 指数实时同步分析")
st.info("原理：VIX 通常领先于高 Beta 股票（如 TSLA）的急跌。本工具通过监控两者‘不同步’的瞬间发出预警。")

df = fetch_market_data()

if df.empty:
    st.warning("暂未获取到实时数据，请检查市场是否开盘或 API 限制。")
else:
    # --- 4. 实时统计 ---
    col1, col2, col3 = st.columns(3)
    
    current_tsla = df['TSLA'].iloc[-1]
    current_vix = df['VIX'].iloc[-1]
    # 计算整体相关性
    total_corr = df['TSLA'].corr(df['VIX'])
    
    col1.metric("TSLA 现价", f"${current_tsla:.2f}")
    col2.metric("VIX 指数", f"{current_vix:.2f}")
    col3.metric("实时相关系数", f"{total_corr:.2f}", delta="高度负相关" if total_corr < -0.7 else "相关性减弱")

    # --- 5. 领先性证明逻辑 ---
    st.subheader("🧪 领先性证明：滞后相关性分析")
    
    # 计算 VIX 领先 TSLA 不同分钟数时的相关性
    lags = [0, 1, 3, 5, 10]
    lag_corrs = {}
    for lag in lags:
        # 将 VIX 序列向前移动 (shift)，看它与现在的 TSLA 相关性是否更高
        c = df['TSLA'].corr(df['VIX'].shift(lag))
        lag_corrs[f"{lag} min"] = c
    
    st.write("当 VIX 移动 N 分钟后的相关性（越负表示领先性越强）：")
    st.bar_chart(pd.Series(lag_corrs))

    # --- 6. 异常检测与报警 ---
    # 逻辑：过去 3 分钟 VIX 涨幅 > 1.5% 且 TSLA 跌幅 < 0.2% (说明 TSLA 还没反应过来)
    if len(df) > 5:
        vix_move = (df['VIX'].iloc[-1] / df['VIX'].iloc[-3]) - 1
        tsla_move = (df['TSLA'].iloc[-1] / df['TSLA'].iloc[-3]) - 1
        
        if vix_move > 0.015 and tsla_move > -0.002:
            alert_text = f"🚨 【VIX 领先预警】\nVIX 突增: {vix_move:.2%}\nTSLA 尚未大幅波动: {tsla_move:.2%}\n预测 TSLA 即将面临下行压力！"
            st.warning(alert_text)
            
            # 自动发送 Telegram (这里加个简单的 Session State 防止重复刷屏)
            if 'last_alert' not in st.session_state or (datetime.now() - st.session_state.last_alert).seconds > 300:
                send_telegram_msg(alert_text)
                st.session_state.last_alert = datetime.now()
                st.success("✅ 预警已发送至 Telegram")

    # --- 7. 可视化图表 ---
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df.index, y=df['TSLA'], name="TSLA", line=dict(color="#FF4B4B")), secondary_y=False)
    fig.add_trace(go.Scatter(x=df.index, y=df['VIX'], name="VIX", line=dict(color="#00CC96")), secondary_y=True)
    
    fig.update_layout(title_text="TSLA vs VIX 分钟级走势对比", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # 滚动相关性
    st.subheader("🕒 滚动相关性 (30分钟窗口)")
    rolling = df['TSLA'].rolling(30).corr(df['VIX'])
    st.line_chart(rolling)

st.divider()
st.caption(f"最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
