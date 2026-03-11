import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta

# --- 配置与 Secrets ---
st.set_page_config(page_title="TSLA vs VIX 实时监控", layout="wide")
TG_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TG_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    params = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        requests.get(url, params=params)
    except Exception as e:
        st.error(f"Telegram 发送失败: {e}")

# --- 数据获取 ---
@st.cache_data(ttl=60)  # 每分钟缓存一次
def get_data():
    # 获取最近 5 天的 1 分钟线数据以模拟实时感
    tsla = yf.download("TSLA", period="5d", interval="1m")
    vix = yf.download("^VIX", period="5d", interval="1m")
    
    # 清理数据并对齐
    data = pd.DataFrame({
        'TSLA': tsla['Close'],
        'VIX': vix['Close']
    }).dropna()
    return data

st.title("📈 TSLA vs VIX 领先指标实时分析")
st.markdown("证明原理：当 VIX 快速飙升且 TSLA 尚未反应时，发出潜在暴跌预警。")

data = get_data()

# --- 计算相关性 ---
# 负相关通常意味着 corr 接近 -1
correlation = data['TSLA'].corr(data['VIX'])
st.metric("实时皮尔逊相关系数", f"{correlation:.2f}", delta="负相关性" if correlation < 0 else "异常正相关")

# --- 异常检测逻辑 ---
# 示例逻辑：如果 VIX 在过去 5 分钟上涨超过 2% 且 TSLA 还没跌超过 0.5%
last_5 = data.tail(5)
vix_change = (last_5['VIX'].iloc[-1] / last_5['VIX'].iloc[0]) - 1
tsla_change = (last_5['TSLA'].iloc[-1] / last_5['TSLA'].iloc[0]) - 1

if vix_change > 0.02 and tsla_change > -0.005:
    msg = f"⚠️ 预警: VIX 短期拉升 {vix_change:.2%}, TSLA 尚未跟随下跌。可能存在领先信号！"
    st.warning(msg)
    if st.button("立即同步至 Telegram"):
        send_telegram_msg(msg)
        st.success("提醒已发送")

# --- 可视化 ---
fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(
    go.Scatter(x=data.index, y=data['TSLA'], name="TSLA 价格", line=dict(color="red")),
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=data.index, y=data['VIX'], name="VIX 指数", line=dict(color="cyan")),
    secondary_y=True,
)

fig.update_layout(title_text="TSLA 与 VIX 走势对比 (1分钟频率)", hovermode="x unified")
fig.update_yaxes(title_text="<b>TSLA</b> USD", secondary_y=False)
fig.update_yaxes(title_text="<b>VIX</b> Index", secondary_y=True)

st.plotly_chart(fig, use_container_width=True)

# --- 统计分析 ---
st.subheader("滚动相关性分析")
rolling_corr = data['TSLA'].rolling(window=30).corr(data['VIX'])
st.line_chart(rolling_corr)
