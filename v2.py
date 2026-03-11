import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
# 需先安裝: pip install streamlit-autorefresh
from streamlit_autorefresh import st_autorefresh

# --- 1. 配置與 Secrets ---
st.set_page_config(page_title="TSLA-VIX 實時自動監控", layout="wide")

# 安全獲取 Secrets
try:
    TG_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TG_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("❌ 錯誤：請在 .streamlit/secrets.toml 中配置 TELEGRAM_TOKEN 和 TELEGRAM_CHAT_ID")
    st.stop()

# --- 2. 自動刷新設置 (放在側邊欄) ---
st.sidebar.header("⚙️ 系統設置")
refresh_interval = st.sidebar.selectbox(
    "選擇自動刷新頻率",
    options=["1m", "5m", "15m"],
    index=0,
    help="系統將根據此時間間隔自動重新加載數據"
)

# 轉換為毫秒 (1m = 60000ms)
interval_map = {"1m": 60 * 1000, "5m": 5 * 60 * 1000, "15m": 15 * 60 * 1000}
st_autorefresh(interval=interval_map[refresh_interval], key="datarefresh")

# --- 3. 核心功能函數 ---
def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        st.error(f"Telegram 發送失敗: {e}")

@st.cache_data(ttl=30) # 緩存失效時間略低於刷新頻率
def fetch_market_data(interval):
    # 根據選定的頻率調整獲取數據的範圍
    period_map = {"1m": "1d", "5m": "5d", "15m": "1mo"}
    tickers = ["TSLA", "^VIX"]
    
    raw_data = yf.download(tickers, period=period_map[interval], interval=interval, group_by='column')
    
    if raw_data.empty:
        return pd.DataFrame()

    df = pd.DataFrame()
    # 處理 yfinance 的 MultiIndex 結構
    try:
        df['TSLA'] = raw_data['Close']['TSLA']
        df['VIX'] = raw_data['Close']['^VIX']
    except KeyError:
        # 有時 yfinance 返回格式不同，做個保險
        df['TSLA'] = raw_data[('Close', 'TSLA')]
        df['VIX'] = raw_data[('Close', '^VIX')]
    
    return df.dropna()

# --- 4. 頁面主體 ---
st.title("📈 TSLA vs VIX 領先指標實時分析")
st.write(f"⏱️ 當前自動刷新頻率: **{refresh_interval}** | 最後更新: {datetime.now().strftime('%H:%M:%S')}")

df = fetch_market_data(refresh_interval)

if df.empty:
    st.warning("⚠️ 數據獲取失敗。請確認美股是否在交易時段（美東 9:30 - 16:00），或更換刷新頻率。")
else:
    # --- 數據儀錶盤 ---
    col1, col2, col3 = st.columns(3)
    curr_tsla = df['TSLA'].iloc[-1]
    curr_vix = df['VIX'].iloc[-1]
    corr = df['TSLA'].corr(df['VIX'])
    
    col1.metric("TSLA 價格", f"${curr_tsla:.2f}")
    col2.metric("VIX 指數", f"{curr_vix:.2f}")
    col3.metric("相關性", f"{corr:.2f}", delta="負相關" if corr < -0.5 else "警告: 相關性異常")

    # --- 異常監控邏輯 ---
    # 設定波動閾值
    vix_change = (df['VIX'].iloc[-1] / df['VIX'].iloc[-2]) - 1
    tsla_change = (df['TSLA'].iloc[-1] / df['TSLA'].iloc[-2]) - 1

    # 預警觸發：VIX 漲超過 1% 而 TSLA 沒跌
    if vix_change > 0.01 and tsla_change > -0.001:
        alert_msg = f"🔔 【{refresh_interval} 預警】\nVIX 突增 {vix_change:.2%}\nTSLA 尚未跟隨: {tsla_change:.2%}\n數據點: {df.index[-1]}"
        st.warning(alert_msg)
        
        # 使用 session_state 防止同一時間點重複發送
        if 'last_alert_time' not in st.session_state or st.session_state.last_alert_time != df.index[-1]:
            send_telegram_msg(alert_msg)
            st.session_state.last_alert_time = df.index[-1]
            st.success("Telegram 提醒已送出")

    # --- 可視化 ---
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df.index, y=df['TSLA'], name="TSLA", line=dict(color="#FF4B4B")), secondary_y=False)
    fig.add_trace(go.Scatter(x=df.index, y=df['VIX'], name="VIX", line=dict(color="#00CC96")), secondary_y=True)
    
    fig.update_layout(title_text=f"TSLA & VIX ({refresh_interval}) 走勢圖", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # --- 滯後相關性分析 ---
    with st.expander("🔬 點擊查看滯後相關性證明"):
        lags = [0, 1, 2, 3, 5]
        lag_results = {f"Lag {l}": df['TSLA'].corr(df['VIX'].shift(l)) for l in lags}
        st.bar_chart(pd.Series(lag_results))
        st.write("💡 如果 Lag 1-3 的負相關性比 Lag 0 更強，則證明 VIX 具有領先性。")
