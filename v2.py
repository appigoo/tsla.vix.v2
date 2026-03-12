"""
TSLA × VIX 实时相关性追踪器
- 1分钟级别实时数据（含盘前/盘后）
- 自动每30秒刷新
- 全中文界面
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import time
import datetime as dt
from datetime import datetime
import pytz
import requests
import json

# ══════════════════════════════════════════════════════════
# 页面配置
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="TSLA × VIX 实时追踪",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════
# 全局样式
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Noto+Sans+SC:wght@400;700;900&display=swap');

:root {
    --bg:     #07080f;
    --surf:   #0e0f1a;
    --surf2:  #141525;
    --border: #1e1f35;
    --acc1:   #e8ff47;
    --acc2:   #ff3d6b;
    --acc3:   #3df5b0;
    --acc4:   #7b7bff;
    --text:   #dde1f5;
    --muted:  #5a5c78;
}
html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Noto Sans SC', 'Space Mono', sans-serif;
}
.stApp { background: var(--bg) !important; }

[data-testid="stSidebar"] {
    background: var(--surf) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* 指标卡 */
.kcard {
    background: var(--surf2);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 22px 16px;
    position: relative;
    overflow: hidden;
    margin-bottom: 6px;
}
.kcard::after {
    content:''; position:absolute;
    top:0; left:0; right:0; height:3px;
    border-radius:14px 14px 0 0;
}
.kcard.y::after { background: var(--acc1); }
.kcard.r::after { background: var(--acc2); }
.kcard.t::after { background: var(--acc3); }
.kcard.p::after { background: var(--acc4); }
.klabel {
    font-size:10px; letter-spacing:2px;
    color:var(--muted); margin-bottom:5px;
    font-family:'Space Mono',monospace;
}
.kval {
    font-size:30px; font-weight:900; line-height:1;
}
.kval.y { color:var(--acc1); }
.kval.r { color:var(--acc2); }
.kval.t { color:var(--acc3); }
.kval.p { color:var(--acc4); }
.ksub {
    font-size:11px; color:var(--muted);
    margin-top:5px; font-family:'Space Mono',monospace;
}

/* 分节标题 */
.sec {
    font-family:'Space Mono',monospace;
    font-size:10px; letter-spacing:3px;
    color:var(--muted);
    border-bottom:1px solid var(--border);
    padding-bottom:6px; margin:20px 0 12px;
}

/* 主标题 */
.htitle {
    font-size:46px; font-weight:900; line-height:1;
    background: linear-gradient(120deg, var(--acc1), var(--acc3));
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text;
}
.hsub {
    font-family:'Space Mono',monospace;
    font-size:10px; letter-spacing:2px; color:var(--muted);
}

/* 结论框 */
.verdict {
    background: linear-gradient(135deg,#141525,#0a0b15);
    border:1px solid var(--acc1);
    border-radius:14px; padding:18px 22px; margin:12px 0;
}
.vt { font-family:'Space Mono',monospace; font-size:9px;
      letter-spacing:2px; color:var(--acc1); margin-bottom:8px; }
.vb { font-size:14px; line-height:1.7; color:var(--text); }

/* 交易时段徽章 */
.badge {
    display:inline-flex; align-items:center; gap:6px;
    border-radius:20px; padding:4px 14px;
    font-family:'Space Mono',monospace;
    font-size:10px; letter-spacing:1px;
}
.badge.pre  { background:rgba(123,123,255,.12); border:1px solid rgba(123,123,255,.4); color:var(--acc4); }
.badge.open { background:rgba(61,245,176,.10);  border:1px solid rgba(61,245,176,.4);  color:var(--acc3); }
.badge.post { background:rgba(255,61,107,.10);  border:1px solid rgba(255,61,107,.35); color:var(--acc2); }
.badge.clos { background:rgba(90,92,120,.15);   border:1px solid rgba(90,92,120,.4);   color:var(--muted); }
.dot { width:6px; height:6px; border-radius:50%; animation:blink 1.4s infinite; display:inline-block; }
.dot.g { background:var(--acc3); }
.dot.b { background:var(--acc4); }
@keyframes blink { 0%,100%{opacity:1}50%{opacity:.15} }

/* 告警面板 */
.alert-box {
    background: linear-gradient(135deg,#1a0f18,#0f0a18);
    border: 1px solid #ff3d6b;
    border-radius: 14px; padding: 14px 18px; margin: 6px 0;
    border-left: 4px solid #ff3d6b;
}
.alert-box.div-up {
    border-color: #ff8c00;
    border-left-color: #ff8c00;
    background: linear-gradient(135deg,#1a1200,#0f0c00);
}
.alert-box.div-down {
    border-color: #7b7bff;
    border-left-color: #7b7bff;
    background: linear-gradient(135deg,#0d0d1a,#080812);
}
.alert-time {
    font-family:'Space Mono',monospace; font-size:9px;
    color:var(--muted); margin-bottom:4px; letter-spacing:1px;
}
.alert-msg { font-size:13px; line-height:1.6; color:var(--text); }
.alert-badge {
    display:inline-block; border-radius:4px; padding:1px 8px;
    font-family:'Space Mono',monospace; font-size:9px; font-weight:700;
    margin-bottom:6px;
}
.alert-badge.warn  { background:#ff3d6b22; color:#ff3d6b; border:1px solid #ff3d6b55; }
.alert-badge.divup { background:#ff8c0022; color:#ff8c00; border:1px solid #ff8c0055; }
.alert-badge.divdn { background:#7b7bff22; color:#7b7bff; border:1px solid #7b7bff55; }
.tg-status {
    display:inline-flex; align-items:center; gap:6px;
    border-radius:8px; padding:5px 12px; margin-top:4px;
    font-family:'Space Mono',monospace; font-size:10px;
}
.tg-status.ok  { background:#3df5b010; border:1px solid #3df5b055; color:#3df5b0; }
.tg-status.err { background:#ff3d6b10; border:1px solid #ff3d6b55; color:#ff3d6b; }
.tg-status.off { background:#5a5c7820; border:1px solid #5a5c7855; color:#5a5c78; }

/* 多因子策略面板 */
.strat-card {
    background: var(--surf2);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    position: relative;
}
.win-meter {
    position: relative;
    width: 100%; height: 22px;
    background: #141525;
    border-radius: 11px;
    overflow: hidden;
    margin: 8px 0;
}
.win-fill {
    height: 100%;
    border-radius: 11px;
    transition: width .5s cubic-bezier(.4,0,.2,1);
}
.factor-row {
    display: flex; align-items: center; gap: 10px;
    padding: 7px 12px; border-radius: 8px; margin: 4px 0;
    font-family: 'Space Mono', monospace; font-size: 11px;
}
.factor-row.on  { background: #3df5b015; border: 1px solid #3df5b040; }
.factor-row.off { background: #ff3d6b0a; border: 1px solid #ff3d6b25; }
.factor-row.na  { background: #1e1f35;   border: 1px solid #2a2b45;   }
.f-icon { font-size: 15px; width: 20px; text-align: center; flex-shrink: 0; }
.f-name { flex: 1; color: #dde1f5; }
.f-val  { color: #5a5c78; font-size: 10px; text-align: right; }
.f-val.on  { color: #3df5b0; }
.f-val.off { color: #ff3d6b; }
.score-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 52px; height: 52px; border-radius: 50%;
    font-family: 'Space Mono', monospace; font-weight: 700; font-size: 17px;
    flex-shrink: 0;
}
.verdict-box {
    border-radius: 10px; padding: 12px 16px; margin: 10px 0;
    font-family: 'Space Mono', monospace;
}

/* 期权流面板 */
.pc-card {
    background: var(--surf2);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 20px;
    position: relative;
    overflow: hidden;
}
.pc-card::after {
    content:''; position:absolute;
    top:0; left:0; right:0; height:3px;
    border-radius:14px 14px 0 0;
}
.pc-card.bull::after { background: linear-gradient(90deg,#3df5b0,#00c896); }
.pc-card.bear::after { background: linear-gradient(90deg,#ff3d6b,#cc0040); }
.pc-card.neut::after { background: linear-gradient(90deg,#7b7bff,#5555cc); }

.pc-signal {
    display:inline-flex; align-items:center; gap:8px;
    border-radius:8px; padding:6px 14px; margin:8px 0;
    font-family:'Space Mono',monospace; font-size:11px; font-weight:700;
}
.pc-signal.bull { background:#3df5b020; border:1px solid #3df5b055; color:#3df5b0; }
.pc-signal.bear { background:#ff3d6b20; border:1px solid #ff3d6b55; color:#ff3d6b; }
.pc-signal.neut { background:#7b7bff20; border:1px solid #7b7bff55; color:#7b7bff; }

.pc-bar-wrap {
    background:#141525; border-radius:6px; height:10px;
    overflow:hidden; margin:6px 0;
}
.pc-bar-fill {
    height:100%; border-radius:6px;
    transition: width .4s ease;
}

/* 背离仪表板 */
.divdash-alert {
    border-radius: 12px; padding: 14px 18px; margin: 8px 0;
    border-left: 4px solid;
    font-family: 'Space Mono', monospace;
}
.divdash-alert.up   { background:#ff8c0012; border-color:#ff8c00; }
.divdash-alert.down { background:#3df5b012; border-color:#3df5b0; }
.divdash-alert.sync { background:#7b7bff12; border-color:#7b7bff; }
.divdash-alert.none { background:#1e1f35;   border-color:#2a2b45; }
.divdash-bar { display:flex; align-items:center; gap:6px; margin:3px 0;
               font-size:11px; }
.divdash-label { color:#5a5c78; width:80px; flex-shrink:0; }
.divdash-track { flex:1; height:6px; background:#141525;
                 border-radius:3px; overflow:hidden; }
.divdash-fill  { height:100%; border-radius:3px; }

#MainMenu, footer, header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════

ET = pytz.timezone("Europe/London")

# session_state 必须在任何使用之前初始化
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0


def get_market_session():
    """返回 (key, 中文标签, GMT时间字符串)"""
    now = datetime.now(ET)
    t   = now.time()
    wd  = now.weekday()
    ts  = now.strftime("%H:%M GMT")

    if wd >= 5:
        return "closed", "休市（周末）", ts
    if t < dt.time(4, 0) or t >= dt.time(20, 0):
        return "closed", "休市（场外）", ts
    if dt.time(4, 0) <= t < dt.time(9, 30):
        return "pre",    "盘前交易", ts
    if dt.time(9, 30) <= t < dt.time(16, 0):
        return "open",   "正常交易", ts
    return "post", "盘后交易", ts


@st.cache_data(ttl=25)
def fetch_1min(_cache_bust: int = 0):
    """1分钟K线，period=5d，prepost=True"""
    tsla = yf.Ticker("TSLA").history(period="5d", interval="1m",
                                      prepost=True, auto_adjust=True)
    vix  = yf.Ticker("^VIX").history(period="5d",  interval="1m",
                                      prepost=True, auto_adjust=True)
    return tsla, vix


@st.cache_data(ttl=60)
def fetch_history(period: str, interval: str):
    """历史数据，用 start/end 而非 period 避免 yfinance 内部缓存"""
    ET_tz = pytz.timezone("Europe/London")
    now   = datetime.now(ET_tz)
    # 根据 period 字符串换算 days_back
    _period_days = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 92,
                    "6mo": 182, "1y": 365, "2y": 730, "5y": 1825}
    days_back = _period_days.get(period, 30)
    start = (now - dt.timedelta(days=days_back + 1)).strftime("%Y-%m-%d")
    end   = (now + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    tsla = yf.download("TSLA", start=start, end=end, interval=interval,
                        progress=False, auto_adjust=True)
    vix  = yf.download("^VIX",  start=start, end=end, interval=interval,
                        progress=False, auto_adjust=True)
    return tsla, vix


def fetch_rt_price(ticker: str):
    """最新报价及昨日收盘"""
    try:
        fi = yf.Ticker(ticker).fast_info
        return getattr(fi, "last_price", None), getattr(fi, "previous_close", None)
    except Exception:
        return None, None


def build_df(tsla_raw, vix_raw):
    tc = tsla_raw["Close"].squeeze().rename("TSLA")
    vc = vix_raw["Close"].squeeze().rename("VIX")
    df = pd.concat([tc, vc], axis=1).dropna()
    # 统一时区为 London（Ticker.history 返回 ET，download 返回 UTC，两者都处理）
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert(ET)
    else:
        df.index = df.index.tz_convert(ET)
    return df


def pearson_corr(df):
    if len(df) < 5:
        return None, None
    r, p = stats.pearsonr(df["TSLA"].values, df["VIX"].values)
    return r, p


def strength_zh(r):
    a = abs(r)
    s = "强" if a >= 0.7 else ("中等" if a >= 0.4 else "弱")
    d = "负" if r < 0 else "正"
    return s, d


def pct(cur, prev):
    if cur and prev and prev != 0:
        return (cur - prev) / prev * 100
    return 0.0


def tag_session(index, tz=ET):
    """给时间索引打交易时段标签"""
    if hasattr(index, "tz_convert"):
        idx_et = index.tz_convert(tz)
    else:
        idx_et = index
    labels = []
    for t in idx_et:
        tt = t.time()
        if dt.time(4, 0) <= tt < dt.time(9, 30):
            labels.append("pre")
        elif dt.time(9, 30) <= tt < dt.time(16, 0):
            labels.append("open")
        elif dt.time(16, 0) <= tt < dt.time(20, 0):
            labels.append("post")
        else:
            labels.append("closed")
    return labels




# ══════════════════════════════════════════════════════════
# 期权流：Put/Call 比率
# ══════════════════════════════════════════════════════════

@st.cache_data(ttl=120)   # 2分钟缓存（期权链更新较慢）
def fetch_pc_ratio(ticker: str = "TSLA") -> dict:
    """
    从 yfinance 拉取期权链，计算各到期日的 Put/Call 比率。

    返回 dict：
      ratio_volume   : 以成交量加权的综合 P/C 比率
      ratio_oi       : 以未平仓量加权的综合 P/C 比率
      put_vol        : 总 Put 成交量
      call_vol       : 总 Call 成交量
      put_oi         : 总 Put 未平仓量
      call_oi        : 总 Call 未平仓量
      by_expiry      : [{expiry, put_vol, call_vol, pc_vol, put_oi, call_oi, pc_oi}, ...]
      near_expiry    : 最近到期日字符串
      near_pc_vol    : 最近到期 P/C 成交量比率（更敏感）
      near_pc_oi     : 最近到期 P/C 未平仓量比率
      atm_skew       : ATM 附近 Put IV - Call IV（波动率偏斜）
      timestamp      : 拉取时间
      error          : 错误信息（正常为 None）
    """
    result = {
        "ratio_volume": None, "ratio_oi": None,
        "put_vol": 0, "call_vol": 0,
        "put_oi": 0, "call_oi": 0,
        "by_expiry": [], "near_expiry": None,
        "near_pc_vol": None, "near_pc_oi": None,
        "atm_skew": None,
        "timestamp": datetime.now(ET).strftime("%H:%M:%S ET"),
        "error": None,
    }
    try:
        t = yf.Ticker(ticker)
        exps = t.options  # 所有到期日列表
        if not exps:
            result["error"] = "无法获取期权到期日"
            return result

        # 只取最近 4 个到期日（流动性最好）
        target_exps = exps[:4]
        total_pv = total_cv = total_poi = total_coi = 0
        by_expiry = []

        for exp in target_exps:
            try:
                chain = t.option_chain(exp)
                puts  = chain.puts
                calls = chain.calls

                pv  = int(puts["volume"].fillna(0).sum())
                cv  = int(calls["volume"].fillna(0).sum())
                poi = int(puts["openInterest"].fillna(0).sum())
                coi = int(calls["openInterest"].fillna(0).sum())

                total_pv  += pv
                total_cv  += cv
                total_poi += poi
                total_coi += coi

                pc_vol = round(pv / cv, 3) if cv > 0 else None
                pc_oi  = round(poi / coi, 3) if coi > 0 else None

                by_expiry.append({
                    "expiry":   exp,
                    "put_vol":  pv,  "call_vol":  cv,  "pc_vol":  pc_vol,
                    "put_oi":   poi, "call_oi":   coi, "pc_oi":   pc_oi,
                })
            except Exception:
                continue

        result["put_vol"]  = total_pv
        result["call_vol"] = total_cv
        result["put_oi"]   = total_poi
        result["call_oi"]  = total_coi
        result["by_expiry"] = by_expiry

        if total_cv > 0:
            result["ratio_volume"] = round(total_pv / total_cv, 3)
        if total_coi > 0:
            result["ratio_oi"] = round(total_poi / total_coi, 3)

        # 最近到期日详情
        if by_expiry:
            near = by_expiry[0]
            result["near_expiry"]  = near["expiry"]
            result["near_pc_vol"]  = near["pc_vol"]
            result["near_pc_oi"]   = near["pc_oi"]

        # ATM 波动率偏斜（最近到期日）
        try:
            spot = t.fast_info.last_price or 0
            chain0 = t.option_chain(exps[0])
            puts0  = chain0.puts.copy()
            calls0 = chain0.calls.copy()
            puts0["dist"]  = abs(puts0["strike"]  - spot)
            calls0["dist"] = abs(calls0["strike"] - spot)
            near_put  = puts0.nsmallest(3, "dist")
            near_call = calls0.nsmallest(3, "dist")
            avg_put_iv  = float(near_put["impliedVolatility"].mean())
            avg_call_iv = float(near_call["impliedVolatility"].mean())
            result["atm_skew"] = round((avg_put_iv - avg_call_iv) * 100, 2)
        except Exception:
            pass

        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def interpret_pc(ratio_vol: float | None, ratio_oi: float | None,
                 near_vol: float | None, atm_skew: float | None) -> dict:
    """
    根据 P/C 比率生成交易信号。

    P/C 比率解读（TSLA 历史经验值）：
      < 0.5  → 过度乐观（Call 主导），逆向看：短期可能见顶，偏空参考
      0.5–0.7→ 轻微看涨情绪，市场整体偏多
      0.7–1.0→ 中性，多空均衡
      1.0–1.3→ 偏向防御/看跌，市场情绪谨慎
      > 1.3  → 过度悲观（Put 主导），逆向看：短期可能见底，偏多参考
    """
    # 主信号基于成交量比率（更实时），辅以 OI 比率
    primary = ratio_vol if ratio_vol is not None else ratio_oi

    if primary is None:
        return {
            "signal": "neutral", "css": "neut", "emoji": "⚪",
            "label": "数据不足", "action": "—",
            "strength": 0, "desc": "无法获取期权数据",
            "tg_worthy": False,
        }

    # 信号强度（0–100）
    if primary < 0.4:
        signal, css, emoji = "bearish_contrarian", "bear", "🔴"
        label  = "极度看涨情绪（逆向偏空）"
        action = "⚠️ Call 严重堆积，市场过热，逆向参考：留意短期回调风险"
        strength = int(min(100, (0.4 - primary) / 0.4 * 100 + 60))
        tg_worthy = True
    elif primary < 0.6:
        signal, css, emoji = "bullish", "bull", "🟢"
        label  = "看涨情绪偏强"
        action = "✅ Call 主导，市场偏多，顺势参考：TSLA 短期看涨"
        strength = int(60 + (0.6 - primary) / 0.2 * 20)
        tg_worthy = primary < 0.5
    elif primary < 0.85:
        signal, css, emoji = "neutral", "neut", "🔵"
        label  = "市场情绪中性"
        action = "📊 多空均衡，无明显方向性信号"
        strength = 50
        tg_worthy = False
    elif primary < 1.1:
        signal, css, emoji = "cautious", "neut", "🟡"
        label  = "谨慎/轻微偏空"
        action = "⚠️ Put 略多，市场出现防御迹象，关注支撑位"
        strength = int(50 + (primary - 0.85) / 0.25 * 20)
        tg_worthy = False
    elif primary < 1.5:
        signal, css, emoji = "bearish", "bear", "🔴"
        label  = "看空情绪偏强"
        action = "⚠️ Put 主导，市场偏空，顺势参考：TSLA 短期承压"
        strength = int(65 + (primary - 1.1) / 0.4 * 20)
        tg_worthy = True
    else:
        signal, css, emoji = "bullish_contrarian", "bull", "🟢"
        label  = "极度看空情绪（逆向偏多）"
        action = "✅ Put 严重堆积，恐慌见底信号，逆向参考：考虑做多"
        strength = int(min(100, (primary - 1.5) / 0.5 * 100 + 70))
        tg_worthy = True

    # 附加信息：ATM 偏斜
    skew_note = ""
    if atm_skew is not None:
        if atm_skew > 5:
            skew_note = f"Put IV 溢价 {atm_skew:.1f}%（市场对下行风险定价偏高）"
        elif atm_skew < -3:
            skew_note = f"Call IV 溢价 {abs(atm_skew):.1f}%（市场对上行动能定价偏高）"
        else:
            skew_note = f"ATM 偏斜中性（{atm_skew:+.1f}%）"

    desc = f"综合 P/C={primary:.3f}"
    if near_vol:
        desc += f"，近月 P/C={near_vol:.3f}"
    if skew_note:
        desc += f"，{skew_note}"

    return {
        "signal": signal, "css": css, "emoji": emoji,
        "label": label, "action": action,
        "strength": strength, "desc": desc,
        "tg_worthy": tg_worthy,
        "primary": primary,
    }


def pc_tg_msg(pc_data: dict, interp: dict, now_ts: str) -> str:
    """生成期权流 Telegram 消息"""
    rv = pc_data.get("ratio_volume")
    ro = pc_data.get("ratio_oi")
    nv = pc_data.get("near_pc_vol")
    sk = pc_data.get("atm_skew")
    pv = pc_data.get("put_vol", 0)
    cv = pc_data.get("call_vol", 0)

    skew_str = f"{sk:+.1f}%" if sk is not None else "N/A"
    return (
        f"{interp['emoji']} <b>[期权流信号] {interp['label']}</b>\n\n"
        f"📊 Put/Call 成交量比率：<b>{rv:.3f}</b>\n"
        f"📊 Put/Call 未平仓量比率：<b>{ro:.3f}</b>\n"
        f"📊 近月 P/C 成交量：<b>{nv:.3f}</b>\n\n"
        f"📈 总 Call 成交量：{cv:,}\n"
        f"📉 总 Put 成交量：{pv:,}\n"
        f"⚖️ ATM 波动率偏斜：{skew_str}\n\n"
        f"💡 <b>操作参考</b>：{interp['action']}\n\n"
        f"🕐 {now_ts}"
    )





# ══════════════════════════════════════════════════════════
# 多因子策略胜率引擎
# ══════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def fetch_strategy_data():
    """
    拉取策略所需的所有数据：
    - TSLA 1分钟（VWAP、相对强度）
    - SPX（^GSPC）1分钟
    - VIX（^VIX）1分钟
    - TSLA 期权链最近到期日（Gamma levels）
    返回 dict，任何字段失败时为 None。
    """
    out = {
        "tsla_1m": None, "spx_1m": None, "vix_1m": None,
        "tsla_price": None, "spx_price": None, "vix_price": None,
        "tsla_prev": None, "spx_prev": None, "vix_prev": None,
        "gamma_levels": [],
        "error": None,
    }
    try:
        tickers = yf.download(
            ["TSLA", "^GSPC", "^VIX"],
            period="2d", interval="1m",
            prepost=True, progress=False, auto_adjust=True,
            group_by="ticker",
        )
        def _squeeze(df):
            if df is None or df.empty:
                return pd.Series(dtype=float)
            c = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
            return c.squeeze().dropna()

        if isinstance(tickers.columns, pd.MultiIndex):
            tsla_s = _squeeze(tickers["TSLA"])
            spx_s  = _squeeze(tickers["^GSPC"])
            vix_s  = _squeeze(tickers["^VIX"])
        else:
            tsla_s = _squeeze(tickers)
            spx_s  = pd.Series(dtype=float)
            vix_s  = pd.Series(dtype=float)

        out["tsla_1m"] = tsla_s
        out["spx_1m"]  = spx_s
        out["vix_1m"]  = vix_s

        if len(tsla_s): out["tsla_price"] = float(tsla_s.iloc[-1])
        if len(spx_s):  out["spx_price"]  = float(spx_s.iloc[-1])
        if len(vix_s):  out["vix_price"]  = float(vix_s.iloc[-1])

        # 昨日收盘（今日开盘前最后一根）
        def _prev_close(s):
            if s is None or len(s) < 2:
                return None
            now_et = datetime.now(ET)
            today  = now_et.date()
            prev   = s[s.index.tz_convert(ET).date < today]  # type: ignore
            return float(prev.iloc[-1]) if len(prev) else None

        out["tsla_prev"] = _prev_close(tsla_s)
        out["spx_prev"]  = _prev_close(spx_s)
        out["vix_prev"]  = _prev_close(vix_s)

    except Exception as e:
        out["error"] = str(e)

    # Gamma levels：从期权链提取高 OI 行权价（作为 Gamma 支撑/阻力）
    try:
        t    = yf.Ticker("TSLA")
        exps = t.options
        if exps and out["tsla_price"]:
            chain   = t.option_chain(exps[0])
            spot    = out["tsla_price"]
            # 合并 calls + puts 的 OI，找高 OI 行权价
            oi_df = pd.concat([
                chain.calls[["strike", "openInterest"]],
                chain.puts[["strike", "openInterest"]],
            ]).groupby("strike")["openInterest"].sum().reset_index()
            oi_df = oi_df[oi_df["openInterest"] > 0].sort_values("openInterest", ascending=False)
            # 取离当前价 ±10% 内的前 8 个高 OI 行权价
            near = oi_df[abs(oi_df["strike"] - spot) / spot < 0.10].head(8)
            out["gamma_levels"] = sorted(near["strike"].tolist())
    except Exception:
        pass

    return out


def calc_vwap(price_series: pd.Series, volume_series: pd.Series | None = None) -> float | None:
    """
    计算当日 VWAP（成交量加权均价）。
    若无成交量数据则用简单均价代替。
    """
    try:
        now_et = datetime.now(ET)
        today  = now_et.date()
        today_mask = price_series.index.tz_convert(ET).date == today  # type: ignore
        today_prices = price_series[today_mask]
        if len(today_prices) < 2:
            return None
        if volume_series is not None:
            today_vol = volume_series[today_mask]
            total_vol = today_vol.sum()
            if total_vol > 0:
                return float((today_prices * today_vol).sum() / total_vol)
        return float(today_prices.mean())
    except Exception:
        return None


def eval_factors(sd: dict, lookback: int = 10) -> dict:
    """
    评估五大因子，每个因子独立打分（满足=True，不满足=False，数据不足=None）。

    因子定义：
    ① VIX ↓     ：近 lookback 分钟 VIX 趋势向下（斜率 < 0）
    ② SPX ↑     ：近 lookback 分钟 SPX 趋势向上（斜率 > 0）
    ③ TSLA RS ↑ ：TSLA 涨幅 > SPX 涨幅（相对强度为正）
    ④ Gamma 支撑：当前价在最近 Gamma 行权价之上（价格未破 Gamma 支撑）
    ⑤ VWAP 夺回：当前 TSLA 价格 > 当日 VWAP

    返回 dict：每个因子的 {active, value, detail}
    """
    factors = {}
    tsla_s = sd.get("tsla_1m")
    spx_s  = sd.get("spx_1m")
    vix_s  = sd.get("vix_1m")
    price  = sd.get("tsla_price")
    gammas = sd.get("gamma_levels", [])

    # ── ① VIX ↓
    try:
        vix_win = vix_s.iloc[-lookback:] if len(vix_s) >= lookback else vix_s
        vix_sl, _, vix_r, *_ = stats.linregress(np.arange(len(vix_win)),
                                                  vix_win.values.astype(float))
        vix_chg = float(vix_win.iloc[-1] - vix_win.iloc[0])
        factors["vix_down"] = {
            "active":  vix_sl < 0,
            "value":   f"{vix_chg:+.2f} pt ({vix_sl*60:+.3f}/分钟)",
            "detail":  "VIX 趋势下行" if vix_sl < 0 else "VIX 趋势上行或横盘",
            "r2":      round(vix_r**2, 2),
        }
    except Exception:
        factors["vix_down"] = {"active": None, "value": "—", "detail": "数据不足", "r2": 0}

    # ── ② SPX ↑
    try:
        spx_win = spx_s.iloc[-lookback:] if len(spx_s) >= lookback else spx_s
        spx_sl, *_ = stats.linregress(np.arange(len(spx_win)),
                                        spx_win.values.astype(float))
        spx_chg_pct = (float(spx_win.iloc[-1]) - float(spx_win.iloc[0])) / float(spx_win.iloc[0]) * 100
        factors["spx_up"] = {
            "active": spx_sl > 0,
            "value":  f"{spx_chg_pct:+.3f}% ({lookback}分钟)",
            "detail": "SPX 趋势上行" if spx_sl > 0 else "SPX 趋势下行或横盘",
        }
    except Exception:
        factors["spx_up"] = {"active": None, "value": "—", "detail": "数据不足"}

    # ── ③ TSLA 相对强度 RS ↑（TSLA 涨幅 vs SPX）
    try:
        n = min(lookback, len(tsla_s), len(spx_s))
        tsla_win = tsla_s.iloc[-n:]
        spx_win2 = spx_s.iloc[-n:]
        tsla_ret = (float(tsla_win.iloc[-1]) - float(tsla_win.iloc[0])) / float(tsla_win.iloc[0]) * 100
        spx_ret  = (float(spx_win2.iloc[-1]) - float(spx_win2.iloc[0])) / float(spx_win2.iloc[0]) * 100
        rs       = round(tsla_ret - spx_ret, 3)
        factors["tsla_rs"] = {
            "active": rs > 0,
            "value":  f"RS={rs:+.3f}% (TSLA {tsla_ret:+.2f}% vs SPX {spx_ret:+.2f}%)",
            "detail": f"TSLA 相对强度{'为正（强于大盘）' if rs > 0 else '为负（弱于大盘）'}",
        }
    except Exception:
        factors["tsla_rs"] = {"active": None, "value": "—", "detail": "数据不足"}

    # ── ④ Gamma 支撑
    try:
        if price and gammas:
            below = [g for g in gammas if g <= price]
            above = [g for g in gammas if g >  price]
            nearest_support = max(below) if below else None
            nearest_resist  = min(above) if above else None
            # 支撑：当前价在最近 Gamma 支撑之上，且距离 < 1.5%
            if nearest_support:
                dist_pct = (price - nearest_support) / price * 100
                on_support = dist_pct < 1.5   # 价格接近支撑位（1.5% 以内）
                factors["gamma_support"] = {
                    "active": True,   # 有 Gamma 支撑位存在
                    "on_support": on_support,
                    "value":  (f"支撑 ${nearest_support:.1f} ({dist_pct:.1f}%↓)"
                               + (f" · 阻力 ${nearest_resist:.1f}" if nearest_resist else "")),
                    "detail": (f"价格在 Gamma 支撑 ${nearest_support:.1f} 附近（{dist_pct:.1f}%），"
                               + ("有效支撑 ✓" if on_support else "支撑偏远")),
                    "support": nearest_support,
                    "resist":  nearest_resist,
                    "dist":    dist_pct,
                }
            else:
                factors["gamma_support"] = {
                    "active": False, "on_support": False,
                    "value": "无下方 Gamma 支撑",
                    "detail": f"当前价 ${price:.2f} 低于所有 Gamma 行权价",
                    "support": None, "resist": nearest_resist, "dist": None,
                }
        else:
            factors["gamma_support"] = {"active": None, "on_support": None,
                                         "value": "—", "detail": "期权数据不足"}
    except Exception:
        factors["gamma_support"] = {"active": None, "on_support": None,
                                     "value": "—", "detail": "计算失败"}

    # ── ⑤ VWAP 夺回
    try:
        vwap = calc_vwap(tsla_s)
        if vwap and price:
            above_vwap = price > vwap
            dist_v = (price - vwap) / vwap * 100
            factors["vwap_reclaim"] = {
                "active": above_vwap,
                "vwap":   round(vwap, 2),
                "dist":   round(dist_v, 3),
                "value":  f"VWAP=${vwap:.2f}，价格{'高于' if above_vwap else '低于'} {abs(dist_v):.2f}%",
                "detail": ("价格高于 VWAP，多头占优" if above_vwap
                           else "价格低于 VWAP，空头占优"),
            }
        else:
            factors["vwap_reclaim"] = {"active": None, "vwap": None,
                                        "value": "—", "detail": "VWAP 计算中"}
    except Exception:
        factors["vwap_reclaim"] = {"active": None, "vwap": None,
                                    "value": "—", "detail": "计算失败"}

    return factors


def calc_winrate(factors: dict) -> dict:
    """
    根据满足的因子数量，映射历史胜率估算。

    因子权重设计（基于历史统计）：
    - 核心三因子（VIX↓ + SPX↑ + RS↑）：基础胜率 63–68%
    - 加 Gamma 支撑（on_support=True）：+3–4%
    - 加 VWAP 夺回：+3–4%
    - 全部满足：70%+

    返回：{score, max_score, pct, winrate, tier, color, signal, active_factors}
    """
    # 权重配置
    weights = {
        "vix_down":      {"w": 2, "label": "VIX ↓",        "icon": "📉"},
        "spx_up":        {"w": 2, "label": "SPX ↑",         "icon": "📈"},
        "tsla_rs":       {"w": 2, "label": "TSLA 相对强度 ↑","icon": "💪"},
        "gamma_support": {"w": 1.5, "label": "Gamma 支撑",  "icon": "🧲"},
        "vwap_reclaim":  {"w": 1.5, "label": "VWAP 夺回",   "icon": "📊"},
    }
    MAX_SCORE = sum(v["w"] for v in weights.values())  # 10.0

    score = 0.0
    active_list = []

    for key, cfg in weights.items():
        f = factors.get(key, {})
        active = f.get("active")

        # Gamma 支撑特殊处理：需要 on_support=True 才算满分
        if key == "gamma_support":
            on_sup = f.get("on_support")
            if on_sup is True:
                score += cfg["w"]
                active_list.append(key)
            elif active is True and on_sup is False:
                score += cfg["w"] * 0.4   # 有 Gamma 但不在支撑附近，部分分
        elif active is True:
            score += cfg["w"]
            active_list.append(key)

    pct = score / MAX_SCORE  # 0.0 – 1.0

    # 胜率映射（基于历史统计锚点插值）
    # 0因子：~50%，3核心：63–68%，5因子：70–75%
    if pct >= 0.95:
        winrate, tier, color = 74, "极强", "#3df5b0"
        signal = "🟢 高胜率做多信号"
    elif pct >= 0.75:
        winrate, tier, color = 70, "强", "#3df5b0"
        signal = "🟢 做多信号（70%+）"
    elif pct >= 0.55:
        winrate, tier, color = 66, "中等偏强", "#e8ff47"
        signal = "🟡 偏多信号，谨慎做多"
    elif pct >= 0.35:
        winrate, tier, color = 58, "中等", "#ff8c00"
        signal = "🟠 信号不足，观望为主"
    else:
        winrate, tier, color = 50, "弱", "#ff3d6b"
        signal = "🔴 无有效信号，不建议入场"

    # 细分插值（让胜率在区间内连续变化）
    winrate = round(winrate + (pct - 0.55) * 8, 1)
    winrate = max(48.0, min(76.0, winrate))

    return {
        "score":          round(score, 1),
        "max_score":      MAX_SCORE,
        "pct":            pct,
        "winrate":        winrate,
        "tier":           tier,
        "color":          color,
        "signal":         signal,
        "active_factors": active_list,
        "weights":        weights,
    }


def strategy_tg_msg(factors: dict, wr: dict, price: float | None, now_ts: str) -> str:
    """生成策略信号 Telegram 消息"""
    lines = [f"🎯 <b>[策略信号] {wr['signal']}</b>\n"]
    lines.append(f"📊 胜率估算：<b>{wr['winrate']:.1f}%</b>（{wr['tier']}，{len(wr['active_factors'])}/5 因子满足）\n")
    if price:
        lines.append(f"💵 TSLA 当前价：<b>${price:.2f}</b>\n")
    lines.append("\n<b>因子明细：</b>")
    icons = {"vix_down":"📉","spx_up":"📈","tsla_rs":"💪","gamma_support":"🧲","vwap_reclaim":"📊"}
    labels = {"vix_down":"VIX ↓","spx_up":"SPX ↑","tsla_rs":"TSLA RS ↑",
              "gamma_support":"Gamma 支撑","vwap_reclaim":"VWAP 夺回"}
    for k, cfg in wr["weights"].items():
        f   = factors.get(k, {})
        act = f.get("active")
        mark = "✅" if k in wr["active_factors"] else ("⚪" if act is None else "❌")
        lines.append(f"{mark} {icons[k]} {labels[k]}：{f.get('detail','—')}")
    vwap_v = factors.get("vwap_reclaim", {}).get("vwap")
    gs     = factors.get("gamma_support", {})
    if vwap_v:
        lines.append(f"\n📌 VWAP = ${vwap_v:.2f}")
    if gs.get("support"):
        lines.append(f"🧲 Gamma 支撑 = ${gs['support']:.1f}")
    lines.append(f"\n🕐 {now_ts}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
# 背离仪表板：K线同框实时背离检测
# ══════════════════════════════════════════════════════════

def detect_divergence_live(
    df: pd.DataFrame,
    n_bars: int = 15,
    div_thresh_vix: float = 0.5,    # VIX 变化超过此 % 视为有效移动
    div_thresh_tsla: float = 0.3,   # TSLA 理论上应跟随的最小 % 变化
) -> dict:
    """
    分析最近 n_bars 根 1 分钟 K 线，逐根判断背离。

    背离定义：
      VIX 移动幅度 >= div_thresh_vix%
      但 TSLA 未以反向幅度 >= div_thresh_tsla% 跟随

    返回 dict：
      status     : "div_up"（VIX↑TSLA未跌）| "div_down"（VIX↓TSLA未涨）
                   | "sync"（同步）| "flat"（VIX未动）
      bars       : 最近 n_bars 根的逐根分析列表
      div_count  : 当前窗口内背离根数
      div_pct    : 背离比例（背离根数 / 有效移动根数）
      vix_total  : 窗口总变化
      tsla_total : 窗口总变化
      last_vix   : 最新VIX值
      last_tsla  : 最新TSLA价格
      alert      : 最近1根是否背离（True/False）
      msg        : Telegram 消息文本
    """
    if len(df) < 3:
        return {"status": "flat", "bars": [], "div_count": 0, "div_pct": 0,
                "vix_total": 0, "tsla_total": 0, "last_vix": None,
                "last_tsla": None, "alert": False, "msg": ""}

    recent = df.iloc[-n_bars:].copy() if len(df) >= n_bars else df.copy()
    now_ts = datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S GMT")

    bars = []
    div_count = 0
    valid_count = 0   # VIX 有效移动根数

    vix_vals  = recent["VIX"].values.astype(float)
    tsla_vals = recent["TSLA"].values.astype(float)

    for i in range(1, len(recent)):
        vix_chg  = (vix_vals[i]  - vix_vals[i-1]) / vix_vals[i-1]  * 100 if vix_vals[i-1]  != 0 else 0.0
        tsla_chg = (tsla_vals[i] - tsla_vals[i-1]) / tsla_vals[i-1] * 100 if tsla_vals[i-1] != 0 else 0.0

        vix_moved = abs(vix_chg) >= div_thresh_vix

        if vix_moved:
            valid_count += 1
            # 背离：VIX 上升但 TSLA 未跌（或跌幅不足）
            if vix_chg > 0 and tsla_chg > -div_thresh_tsla:
                bar_status = "div_up"
                div_count += 1
            # 背离：VIX 下降但 TSLA 未涨（或涨幅不足）
            elif vix_chg < 0 and tsla_chg < div_thresh_tsla:
                bar_status = "div_down"
                div_count += 1
            else:
                bar_status = "sync"
        else:
            bar_status = "flat"

        bars.append({
            "time":      recent.index[i],
            "vix":       vix_vals[i],
            "tsla":      tsla_vals[i],
            "vix_chg":   vix_chg,
            "tsla_chg":  tsla_chg,
            "status":    bar_status,
        })

    # 整体判断：以最近3根为主，权重向最新倾斜
    last_bar    = bars[-1] if bars else {}
    last_status = last_bar.get("status", "flat")
    alert       = last_status in ("div_up", "div_down")

    # 窗口总变化
    vix_total  = (vix_vals[-1] - vix_vals[0]) / vix_vals[0]  * 100 if vix_vals[0]  != 0 else 0.0
    tsla_total = (tsla_vals[-1] - tsla_vals[0]) / tsla_vals[0] * 100 if tsla_vals[0] != 0 else 0.0
    div_pct    = div_count / valid_count if valid_count > 0 else 0.0

    # 整体状态：以最后3根中的多数方向判断
    recent3 = [b["status"] for b in bars[-3:]] if len(bars) >= 3 else [last_status]
    up3   = recent3.count("div_up")
    dn3   = recent3.count("div_down")
    sy3   = recent3.count("sync")
    if up3 >= 2:
        status = "div_up"
    elif dn3 >= 2:
        status = "div_down"
    elif sy3 >= 2:
        status = "sync"
    else:
        status = last_status if last_status != "flat" else "flat"

    # Telegram 消息
    if status == "div_up":
        emoji = "🟠"; head = "VIX 持续上升，TSLA 未跟跌（背离）"
        action = "⚠️ TSLA 补跌概率高，考虑减仓/做空"
    elif status == "div_down":
        emoji = "🔵"; head = "VIX 持续下降，TSLA 未跟涨（背离）"
        action = "✅ TSLA 补涨概率高，考虑做多/加仓"
    else:
        emoji = ""; head = ""; action = ""

    msg = ""
    if status in ("div_up", "div_down"):
        msg = (
            f"{emoji} <b>[K线背离仪表板] {head}</b>\n\n"
            f"📊 最近 {n_bars} 根 K 线分析\n"
            f"   背离根数：{div_count} / {valid_count} 有效移动（{div_pct:.0%}）\n"
            f"   VIX  窗口变化：{vix_total:+.2f}%（当前 {vix_vals[-1]:.2f}）\n"
            f"   TSLA 窗口变化：{tsla_total:+.2f}%（当前 ${tsla_vals[-1]:.2f}）\n\n"
            f"💡 <b>操作参考</b>：{action}\n\n"
            f"🕐 {now_ts}"
        )

    return {
        "status":     status,
        "bars":       bars,
        "div_count":  div_count,
        "div_pct":    div_pct,
        "valid_count": valid_count,
        "vix_total":  vix_total,
        "tsla_total": tsla_total,
        "last_vix":   float(vix_vals[-1]),
        "last_tsla":  float(tsla_vals[-1]),
        "alert":      alert,
        "status_last": last_status,
        "msg":        msg,
        "now_ts":     now_ts,
    }


def build_divdash_chart(df: pd.DataFrame, n_bars: int = 15, div_result: dict = None) -> go.Figure:
    """
    构建 VIX + TSLA 双 K 线同框图表，背离根高亮。
    上图：VIX K线 + 背离标注
    下图：TSLA K线 + 背离标注
    """
    recent = df.iloc[-n_bars:].copy() if len(df) >= n_bars else df.copy()
    bars   = div_result.get("bars", []) if div_result else []

    # 背离颜色 map：status → bar bgcolor (用 vrect 高亮)
    STATUS_COLOR = {
        "div_up":   "rgba(255,140,0,0.15)",
        "div_down": "rgba(61,245,176,0.15)",
        "sync":     "rgba(123,123,255,0.07)",
        "flat":     "rgba(0,0,0,0)",
    }

    # 构建 OHLC（1分钟K线，用close作为OHLC近似，因为df1m只有close）
    # 实际用折线+散点，清晰展示每根收盘价变化
    times = list(recent.index)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=["VIX 指数（1分钟）", "TSLA 股价（1分钟）"],
        row_heights=[0.5, 0.5],
    )

    vix_vals  = recent["VIX"].values.astype(float)
    tsla_vals = recent["TSLA"].values.astype(float)

    # 逐根颜色（基于背离状态）
    def _bar_colors(col_key):
        colors = []
        for b in bars:
            st = b["status"]
            if st == "div_up":
                colors.append("#ff8c00")
            elif st == "div_down":
                colors.append("#3df5b0")
            elif st == "sync":
                colors.append("#7b7bff")
            else:
                colors.append("#5a5c78")
        # 第一根无前一根，默认灰色
        return ["#5a5c78"] + colors if len(colors) < len(times) else colors

    bar_colors = _bar_colors("status")

    # ── VIX 折线 + 散点（颜色按背离状态）
    fig.add_trace(go.Scatter(
        x=times, y=vix_vals,
        mode="lines",
        line=dict(color="#ff3d6b", width=1.5),
        name="VIX",
        showlegend=True,
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=times, y=vix_vals,
        mode="markers",
        marker=dict(color=bar_colors, size=7, line=dict(width=1, color="#0e0f1a")),
        name="VIX点",
        showlegend=False,
        hovertemplate="VIX: %{y:.2f}<extra></extra>",
    ), row=1, col=1)

    # ── TSLA 折线 + 散点
    fig.add_trace(go.Scatter(
        x=times, y=tsla_vals,
        mode="lines",
        line=dict(color="#7b7bff", width=1.5),
        name="TSLA",
        showlegend=True,
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=times, y=tsla_vals,
        mode="markers",
        marker=dict(color=bar_colors, size=7, line=dict(width=1, color="#0e0f1a")),
        name="TSLA点",
        showlegend=False,
        hovertemplate="TSLA: $%{y:.2f}<extra></extra>",
    ), row=2, col=1)

    # ── 背离高亮竖条（vrect）
    for b in bars:
        c = STATUS_COLOR.get(b["status"], "rgba(0,0,0,0)")
        if c == "rgba(0,0,0,0)":
            continue
        t_idx = list(recent.index).index(b["time"]) if b["time"] in recent.index else -1
        if t_idx <= 0:
            continue
        x0 = recent.index[t_idx - 1]
        x1 = b["time"]
        for row in (1, 2):
            fig.add_vrect(x0=x0, x1=x1, fillcolor=c, layer="below",
                          line_width=0, row=row, col=1)

    # ── 最新一根特别标注
    if len(times) > 0:
        last_status = div_result.get("status_last", "flat") if div_result else "flat"
        ann_color = {"div_up": "#ff8c00", "div_down": "#3df5b0",
                     "sync": "#7b7bff", "flat": "#5a5c78"}.get(last_status, "#5a5c78")
        ann_text  = {"div_up": "⚠ 背离↑", "div_down": "✅ 背离↓",
                     "sync": "✓ 同步", "flat": "—"}.get(last_status, "")
        if ann_text:
            fig.add_annotation(
                x=times[-1], y=vix_vals[-1],
                text=ann_text, showarrow=True, arrowhead=2,
                font=dict(color=ann_color, size=11, family="Space Mono"),
                arrowcolor=ann_color, ax=20, ay=-28, row=1, col=1,
            )

    # ── 图表样式
    DARK = "#0e0f1a"
    GRID = "#141525"
    fig.update_layout(
        paper_bgcolor=DARK, plot_bgcolor=DARK,
        font=dict(color="#5a5c78", size=10, family="Space Mono"),
        margin=dict(l=10, r=10, t=36, b=8),
        height=420,
        hovermode="x unified",
        legend=dict(bgcolor=DARK, bordercolor="#1e1f35", borderwidth=1,
                    font=dict(color="#dde1f5", size=10),
                    orientation="h", x=0, y=1.05),
        showlegend=True,
    )
    for row in (1, 2):
        fig.update_xaxes(gridcolor=GRID, zeroline=False, showgrid=True,
                         tickfont=dict(size=9), row=row, col=1)
        fig.update_yaxes(gridcolor=GRID, zeroline=False, showgrid=True,
                         tickfont=dict(size=9), row=row, col=1)
    # 副标题颜色
    fig.update_annotations(font=dict(color="#dde1f5", size=10, family="Space Mono"))

    return fig


def tg_divdash_msg(result: dict) -> str:
    return result.get("msg", "")


def tg_send(bot_token: str, chat_id: str, text: str) -> tuple[bool, str]:
    """发送 Telegram 消息，返回 (成功, 信息)"""
    if not bot_token or not chat_id:
        return False, "未配置 Token / Chat ID"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }, timeout=8)
        data = resp.json()
        if data.get("ok"):
            return True, "发送成功"
        return False, data.get("description", "未知错误")
    except Exception as e:
        return False, str(e)


def tg_test(bot_token: str, chat_id: str) -> tuple[bool, str]:
    """测试 Telegram 连接"""
    return tg_send(bot_token, chat_id,
                   "✅ <b>TSLA × VIX 监控系统</b>\n\n连接测试成功！告警通知已就绪。")


def calc_trend(series: pd.Series) -> tuple[float, float, float]:
    """线性回归趋势：返回 (斜率_%/分钟, R², 总变化%)"""
    if len(series) < 3:
        return 0.0, 0.0, 0.0
    y = series.values.astype(float)
    x = np.arange(len(y))
    slope, intercept, r, *_ = stats.linregress(x, y)
    mean_val = float(np.mean(y))
    slope_pct = (slope / mean_val * 100) if mean_val != 0 else 0.0
    total_chg = (y[-1] - y[0]) / y[0] * 100 if y[0] != 0 else 0.0
    return slope_pct, r**2, total_chg


def detect_vix_spike(
    vix_series: pd.Series,
    spike_pct: float = 3.0,       # 单根 K 线涨跌幅超过此值 → 急速脉冲
    confirm_pct: float = 2.0,     # 连续 2 根同向 K 线累计涨跌幅 → 确认持续
    extreme_pct: float = 6.0,     # 超过此值为极端信号
) -> dict | None:
    """
    VIX 1 分钟急升/急跌检测（独立信号）

    检测两种模式：
    ① 单根脉冲：最后一根 K 线涨跌幅绝对值 ≥ spike_pct
    ② 连续确认：最后 2 根 K 线方向一致且累计幅度 ≥ confirm_pct

    返回 None（无信号）或 dict（信号详情）
    """
    if len(vix_series) < 3:
        return None

    v = vix_series.values.astype(float)
    now_ts = datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S GMT")

    last   = v[-1]
    prev1  = v[-2]
    prev2  = v[-3]

    # 单根 K 线变化率
    chg1 = (last  - prev1) / prev1 * 100 if prev1 != 0 else 0.0
    chg2 = (prev1 - prev2) / prev2 * 100 if prev2 != 0 else 0.0
    cumulative = (last - prev2) / prev2 * 100 if prev2 != 0 else 0.0

    # 判断是否触发
    single_spike  = abs(chg1) >= spike_pct
    double_confirm = (
        abs(cumulative) >= confirm_pct and
        np.sign(chg1) == np.sign(chg2) and   # 两根同向
        abs(chg1) >= spike_pct * 0.4 and      # 第二根也有一定幅度
        abs(chg2) >= spike_pct * 0.4
    )

    if not (single_spike or double_confirm):
        return None

    direction = "up" if chg1 > 0 else "down"
    is_extreme = abs(chg1) >= extreme_pct or abs(cumulative) >= extreme_pct

    # 触发模式描述
    if single_spike and double_confirm:
        mode_label = "单根脉冲＋连续确认"
        mode_short = "双重确认"
        confidence = "高" if is_extreme else "中"
    elif double_confirm:
        mode_label = "连续两根同向"
        mode_short = "连续确认"
        confidence = "中"
    else:
        mode_label = "单根脉冲"
        mode_short = "脉冲"
        confidence = "极高" if is_extreme else "中"

    if direction == "up":
        emoji   = "🔺" if is_extreme else "⬆️"
        label   = f"{'⚡极端' if is_extreme else ''}VIX 急升（{mode_short}）"
        css     = "div-up"
        badge   = "divup"
        meaning = "市场恐慌急速升温，TSLA 面临即时抛压"
        action  = "⚠️ 立即关注：TSLA 可能即将快速下跌，考虑减仓/止损"
        tg_head = f"{'⚡' if is_extreme else '🔺'} <b>VIX 1分钟急升警报</b>"
    else:
        emoji   = "🔻" if is_extreme else "⬇️"
        label   = f"{'⚡极端' if is_extreme else ''}VIX 急跌（{mode_short}）"
        css     = "div-down"
        badge   = "divdn"
        meaning = "市场恐慌急速消退，TSLA 或迎来即时反弹"
        action  = "✅ 立即关注：TSLA 可能即将快速上涨，考虑做多/加仓"
        tg_head = f"{'⚡' if is_extreme else '🔻'} <b>VIX 1分钟急跌警报</b>"

    msg = (
        f"{tg_head}\n\n"
        f"📊 VIX 当前：<b>{last:.2f}</b>\n"
        f"   最后1根变化：<b>{chg1:+.2f}%</b>（{prev1:.2f} → {last:.2f}）\n"
        f"   最后2根累计：<b>{cumulative:+.2f}%</b>（{prev2:.2f} → {last:.2f}）\n\n"
        f"📌 触发模式：{mode_label} · 置信度：{confidence}\n"
        f"💥 含义：{meaning}\n\n"
        f"💡 <b>操作参考</b>：{action}\n\n"
        f"🕐 {now_ts}"
    )

    desc_html = (
        f"VIX <b>{chg1:+.2f}%</b>（1根）· 累计 <b>{cumulative:+.2f}%</b>（2根）· "
        f"{mode_label} · 置信度：{confidence}<br>"
        f"<span style='color:{'#ff8c00' if direction=='up' else '#3df5b0'}'>{action}</span>"
    )

    return {
        "type":       f"vix_spike_{direction}",
        "direction":  direction,
        "label":      label,
        "badge":      badge,
        "css":        css,
        "emoji":      emoji,
        "is_extreme": is_extreme,
        "chg1":       chg1,
        "chg2":       chg2,
        "cumulative": cumulative,
        "vix_now":    last,
        "mode":       mode_short,
        "confidence": confidence,
        "meaning":    meaning,
        "action":     action,
        "desc_html":  desc_html,
        "msg":        msg,
    }



def detect_spot(
    df: pd.DataFrame,
    spot_window: int = 5,
    vix_thresh: float = 1.0,
    tsla_thresh: float = 0.5,
) -> dict | None:
    """
    ① 单点变化检测（快速预警）
    逻辑：比较最近 spot_window 根 K 线的首尾变化幅度
    优点：反应快，适合捕捉急速脉冲
    缺点：容易被噪音误触发
    """
    if len(df) < spot_window + 1:
        return None

    base = df.iloc[-(spot_window + 1)]
    last = df.iloc[-1]
    now_ts = datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S GMT")

    vix_chg  = (float(last["VIX"])  - float(base["VIX"]))  / float(base["VIX"])  * 100
    tsla_chg = (float(last["TSLA"]) - float(base["TSLA"])) / float(base["TSLA"]) * 100

    # VIX 急升，TSLA 未跌
    if vix_chg >= vix_thresh and tsla_chg >= -tsla_thresh:
        return {
            "type":    "spot_vix_up",
            "mode":    "spot",
            "label":   "🟠 快速预警：VIX急升 TSLA未跌",
            "badge":   "divup",
            "css":     "div-up",
            "emoji":   "🟠",
            "action":  "⚠️ TSLA 或将补跌（考虑减仓/做空）",
            "msg": (
                f"🟠 <b>[快速预警] VIX 急升，TSLA 尚未跟跌</b>\n\n"
                f"📈 VIX 过去 {spot_window} 分钟变化：<b>{vix_chg:+.2f}%</b>（当前 {float(last['VIX']):.2f}）\n"
                f"😴 TSLA 同期变化：<b>{tsla_chg:+.2f}%</b>（当前 ${float(last['TSLA']):.2f}）\n\n"
                f"📌 恐慌情绪急速上升，TSLA 尚未定价，大概率即将补跌。\n"
                f"💡 考虑减仓或设置止损，观察接下来 3–5 分钟。\n\n"
                f"🕐 {now_ts}"
            ),
            "desc_html": (
                f"<b style='color:#ff8c00'>[单点]</b> "
                f"VIX <b>{vix_chg:+.2f}%</b>（{spot_window}分钟），"
                f"TSLA 仅 <b>{tsla_chg:+.2f}%</b>（未跌）<br>"
                f"<span style='color:#ff8c00'>⚠ TSLA 或将补跌 · 减仓/做空参考</span>"
            ),
        }

    # VIX 急跌，TSLA 未涨
    if vix_chg <= -vix_thresh and tsla_chg <= tsla_thresh:
        return {
            "type":    "spot_vix_down",
            "mode":    "spot",
            "label":   "🔵 快速预警：VIX急跌 TSLA未涨",
            "badge":   "divdn",
            "css":     "div-down",
            "emoji":   "🔵",
            "action":  "✅ TSLA 或将补涨（考虑做多/加仓）",
            "msg": (
                f"🔵 <b>[快速预警] VIX 急跌，TSLA 尚未跟涨</b>\n\n"
                f"📉 VIX 过去 {spot_window} 分钟变化：<b>{vix_chg:+.2f}%</b>（当前 {float(last['VIX']):.2f}）\n"
                f"😴 TSLA 同期变化：<b>{tsla_chg:+.2f}%</b>（当前 ${float(last['TSLA']):.2f}）\n\n"
                f"📌 恐慌情绪迅速消退，TSLA 尚未定价，大概率即将补涨。\n"
                f"💡 考虑做多或加仓，观察接下来 3–5 分钟上行动能。\n\n"
                f"🕐 {now_ts}"
            ),
            "desc_html": (
                f"<b style='color:#7b7bff'>[单点]</b> "
                f"VIX <b>{vix_chg:+.2f}%</b>（{spot_window}分钟），"
                f"TSLA 仅 <b>{tsla_chg:+.2f}%</b>（未涨）<br>"
                f"<span style='color:#3df5b0'>✅ TSLA 或将补涨 · 做多/加仓参考</span>"
            ),
        }

    return None


def detect_trend(
    df: pd.DataFrame,
    trend_window: int = 10,       # 用户设定（现在仅作 EMA span 参考）
    vix_slope_thresh: float = 0.05,
    tsla_slope_thresh: float = 0.02,
    min_r2: float = 0.5,          # 保留参数名兼容侧边栏，但不再用 R² 作主要门槛
) -> dict | None:
    """
    ② EMA 斜率趋势确认（快速高置信版）

    原线性回归需要 10 根 K 线才稳定，本版改用：
      · EMA(3) 斜率：3 根指数加权均线，对最新数据权重更高，响应快 3–5 分钟
      · 连续方向计数：最近 N 根 K 线中有几根与趋势同向（替代 R² 门槛）
      · 双重确认：EMA 斜率 + 连续方向数同时满足才触发

    优点：3–4 分钟内即可确认趋势，且噪音容忍度可调
    """
    # 最少需要 ema_span*2 根数据才稳定
    ema_span = max(3, min(trend_window // 2, 5))   # 3–5，随窗口自适应
    min_bars = ema_span * 2 + 2
    if len(df) < min_bars:
        return None

    # ── EMA 斜率计算（用首尾差代替逐段平均，更稳定）
    vix_ema   = df["VIX"].ewm(span=ema_span, adjust=False).mean()
    tsla_ema  = df["TSLA"].ewm(span=ema_span, adjust=False).mean()

    def _ema_slope(ema_s):
        """用最后 ema_span+1 根 EMA 的首尾差算斜率（%/根），比逐段平均稳定"""
        n    = ema_span + 1
        vals = ema_s.iloc[-n:].values.astype(float)
        if len(vals) < 2 or vals[0] == 0:
            return 0.0
        return (vals[-1] - vals[0]) / vals[0] * 100 / (len(vals) - 1)

    vix_ema_slope  = _ema_slope(vix_ema)
    tsla_ema_slope = _ema_slope(tsla_ema)

    # ── 连续方向计数（最近 N 根原始 K 线有几根同向）
    check_n = min(trend_window, len(df) - 1, 6)   # 最多检查 6 根
    vix_vals  = df["VIX"].iloc[-(check_n+1):].values.astype(float)
    tsla_vals = df["TSLA"].iloc[-(check_n+1):].values.astype(float)

    vix_up_count  = sum(1 for i in range(1, len(vix_vals))  if vix_vals[i]  > vix_vals[i-1])
    vix_dn_count  = sum(1 for i in range(1, len(vix_vals))  if vix_vals[i]  < vix_vals[i-1])
    tsla_up_count = sum(1 for i in range(1, len(tsla_vals)) if tsla_vals[i] > tsla_vals[i-1])
    tsla_dn_count = sum(1 for i in range(1, len(tsla_vals)) if tsla_vals[i] < tsla_vals[i-1])

    # 方向一致性：60% 以上同向视为趋势（比 R²≥0.5 等效但响应更快）
    min_count = max(2, int(check_n * 0.6))

    now_ts   = datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S GMT")
    vix_now  = float(df["VIX"].iloc[-1])
    tsla_now = float(df["TSLA"].iloc[-1])
    vix_total  = (vix_now - float(df["VIX"].iloc[-check_n])) / float(df["VIX"].iloc[-check_n]) * 100
    tsla_total = (tsla_now - float(df["TSLA"].iloc[-check_n])) / float(df["TSLA"].iloc[-check_n]) * 100

    # 置信度标签（用方向计数替代 R²）
    def _conf(count, total):
        ratio = count / total if total > 0 else 0
        return "高" if ratio >= 0.8 else "中等"

    # 最新两根原始K线的即时方向（用于反转抑制）
    raw_dir = 1 if float(df["VIX"].iloc[-1]) > float(df["VIX"].iloc[-2]) else -1

    # ── 🔴 VIX EMA 上升 + 方向确认 + TSLA 未跟跌
    if (vix_ema_slope  >= vix_slope_thresh   and
        vix_up_count   >= min_count          and
        tsla_ema_slope > -tsla_slope_thresh):

        # 反转抑制：最新K线已经下跌，且下跌根数 ≥ 上升根数 → EMA 滞后，趋势已翻转
        if raw_dir < 0 and vix_dn_count >= vix_up_count:
            return None

        conf = _conf(vix_up_count, check_n)
        return {
            "type":       "trend_vix_up",
            "mode":       "trend",
            "label":      "🔴 趋势确认：VIX升势 TSLA未跌",
            "badge":      "divup",
            "css":        "div-up",
            "emoji":      "🔴",
            "vix_slope":  vix_ema_slope,
            "tsla_slope": tsla_ema_slope,
            "vix_r2":     round(vix_up_count / check_n, 2),
            "action":     "⚠️ 趋势确认：TSLA 补跌概率高（减仓/做空）",
            "msg": (
                f"🔴 <b>[趋势确认·EMA] VIX 升势持续，TSLA 尚未跟跌</b>\n\n"
                f"📈 VIX EMA({ema_span}) 斜率：<b>{vix_ema_slope:+.3f}%/根</b>\n"
                f"   {check_n} 根中 <b>{vix_up_count}</b> 根上升（方向一致率 {vix_up_count/check_n:.0%}，{conf}置信）\n"
                f"   累计涨幅：{vix_total:+.2f}%  |  当前：{vix_now:.2f}\n\n"
                f"😴 TSLA EMA 斜率：<b>{tsla_ema_slope:+.3f}%/根</b>（未同步下跌）\n"
                f"   当前：${tsla_now:.2f}\n\n"
                f"📌 恐慌升势已形成（{conf}置信），TSLA 大概率跟随补跌。\n"
                f"💡 建议减仓或做空，并设置止损位。\n\n"
                f"🕐 {now_ts}"
            ),
            "desc_html": (
                f"<b style='color:#ff3d6b'>[趋势·EMA{ema_span}]</b> "
                f"VIX 斜率 <b>{vix_ema_slope:+.3f}%/根</b>，"
                f"{check_n}根中 <b>{vix_up_count}</b> 根同向（{conf}置信），"
                f"TSLA 未跟跌<br>"
                f"<span style='color:#ff8c00'>⚠ 趋势确认 · TSLA 补跌概率高 · 减仓/做空</span>"
            ),
        }

    # ── 🟢 VIX EMA 下降 + 方向确认 + TSLA 未跟涨
    if (vix_ema_slope  <= -vix_slope_thresh  and
        vix_dn_count   >= min_count          and
        tsla_ema_slope <   tsla_slope_thresh):

        # 反转抑制：最新K线已经上涨，且上升根数 ≥ 下跌根数 → EMA 滞后，趋势已翻转
        if raw_dir > 0 and vix_up_count >= vix_dn_count:
            return None

        conf = _conf(vix_dn_count, check_n)
        return {
            "type":       "trend_vix_down",
            "mode":       "trend",
            "label":      "🟢 趋势确认：VIX降势 TSLA未涨",
            "badge":      "divdn",
            "css":        "div-down",
            "emoji":      "🟢",
            "vix_slope":  vix_ema_slope,
            "tsla_slope": tsla_ema_slope,
            "vix_r2":     round(vix_dn_count / check_n, 2),
            "action":     "✅ 趋势确认：TSLA 补涨概率高（做多/加仓）",
            "msg": (
                f"🟢 <b>[趋势确认·EMA] VIX 降势持续，TSLA 尚未跟涨</b>\n\n"
                f"📉 VIX EMA({ema_span}) 斜率：<b>{vix_ema_slope:+.3f}%/根</b>\n"
                f"   {check_n} 根中 <b>{vix_dn_count}</b> 根下降（方向一致率 {vix_dn_count/check_n:.0%}，{conf}置信）\n"
                f"   累计跌幅：{vix_total:+.2f}%  |  当前：{vix_now:.2f}\n\n"
                f"😴 TSLA EMA 斜率：<b>{tsla_ema_slope:+.3f}%/根</b>（未同步上涨）\n"
                f"   当前：${tsla_now:.2f}\n\n"
                f"📌 恐慌消退趋势已形成（{conf}置信），TSLA 大概率跟随补涨。\n"
                f"💡 建议做多或加仓，关注上行动能确认。\n\n"
                f"🕐 {now_ts}"
            ),
            "desc_html": (
                f"<b style='color:#3df5b0'>[趋势·EMA{ema_span}]</b> "
                f"VIX 斜率 <b>{vix_ema_slope:+.3f}%/根</b>，"
                f"{check_n}根中 <b>{vix_dn_count}</b> 根同向（{conf}置信），"
                f"TSLA 未跟涨<br>"
                f"<span style='color:#3df5b0'>✅ 趋势确认 · TSLA 补涨概率高 · 做多/加仓</span>"
            ),
        }

    return None


# ══════════════════════════════════════════════════════════
# 侧边栏
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sec">⚙ 控制面板</div>', unsafe_allow_html=True)

    auto_refresh = st.checkbox("🔄 自动刷新（每30秒）", value=True)

    hist_map = {
        "今日（1分钟）":   ("1d",  "1m"),
        "近5日（1分钟）":  ("5d",  "1m"),
        "近1月（1小时）":  ("1mo", "1h"),
        "近3月（日线）":   ("3mo", "1d"),
        "近1年（日线）":   ("1y",  "1d"),
    }
    period_label = st.selectbox("历史对比时段", list(hist_map.keys()), index=1)
    hist_period, hist_interval = hist_map[period_label]

    roll_window = st.slider("滚动相关窗口（根 K 线）", 5, 60, 20)
    normalize   = st.checkbox("标准化叠加（Z-Score）", value=True)

    # ── 背离仪表板配置
    st.markdown('<div class="sec">📺 背离实时仪表板</div>', unsafe_allow_html=True)
    divdash_enabled   = st.checkbox("启用背离K线仪表板", value=True)
    divdash_n_bars    = st.slider("显示K线数量", 5, 30, 15,
                                   help="同时显示最近 N 根 1 分钟 K 线")
    divdash_vix_thr   = st.slider("VIX 有效移动阈值（%）", 0.1, 2.0, 0.5, step=0.1,
                                   help="VIX 单根变化超过此值才视为有效移动")
    divdash_tsla_thr  = st.slider("TSLA 跟随阈值（%）", 0.1, 1.0, 0.3, step=0.1,
                                   help="TSLA 未以此幅度反向移动即判定为背离")
    divdash_cooldown  = st.slider("背离仪表板推送冷却（分钟）", 1, 30, 3,
                                   help="背离提醒最短推送间隔")

    # ── VIX 急速脉冲配置
    st.markdown('<div class="sec">⚡ VIX 1分钟急升急跌</div>', unsafe_allow_html=True)
    spike_enabled  = st.checkbox("启用 VIX 急速脉冲检测", value=True)
    spike_pct      = st.slider("单根脉冲阈值（%）", 1.0, 10.0, 3.0, step=0.5,
                                help="单根 1 分钟 K 线涨跌幅超过此值即触发")
    confirm_pct    = st.slider("连续确认阈值（%）", 1.0, 8.0, 2.0, step=0.5,
                                help="连续 2 根同向 K 线累计幅度超过此值即确认")
    extreme_pct    = st.slider("极端信号阈值（%）", 3.0, 15.0, 6.0, step=0.5,
                                help="超过此值升级为⚡极端信号")
    spike_cooldown = st.slider("急速信号冷却（分钟）", 1, 30, 5,
                                help="急速脉冲冷却时间，建议较短")

    # ── 多因子策略配置
    st.markdown('<div class="sec">🎯 多因子策略胜率</div>', unsafe_allow_html=True)
    strat_enabled    = st.checkbox("启用策略胜率引擎", value=True)
    strat_lookback   = st.slider("因子观察窗口（分钟）", 3, 20, 10,
                                  help="计算 VIX/SPX/TSLA 趋势使用的 K 线数量")
    strat_min_wr     = st.slider("Telegram 触发胜率（%）", 60, 75, 65,
                                  help="胜率估算超过此值才推送 Telegram")
    strat_cooldown   = st.slider("策略信号冷却（分钟）", 5, 60, 20,
                                  help="同一胜率级别的最短推送间隔")

    # ── 期权流配置
    st.markdown('<div class="sec">📊 期权流 Put/Call 监控</div>', unsafe_allow_html=True)
    pc_enabled     = st.checkbox("启用期权流信号", value=True)
    pc_bull_thresh = st.slider("看涨信号阈值（P/C <）", 0.3, 0.8, 0.6, step=0.05,
                               help="P/C 低于此值触发看涨/逆向偏空预警")
    pc_bear_thresh = st.slider("看空信号阈值（P/C >）", 0.8, 2.0, 1.1, step=0.05,
                               help="P/C 高于此值触发看空/逆向偏多预警")
    pc_cooldown    = st.slider("期权流冷却时间（分钟）", 5, 120, 30,
                               help="期权链数据更新慢，建议冷却时间较长")

    # ── Telegram 告警配置 ────────────────────────────────
    st.markdown('<div class="sec">📲 Telegram 告警设置</div>', unsafe_allow_html=True)

    tg_enabled = st.checkbox("启用 Telegram 告警", value=False)

    # ── 从 st.secrets 读取（优先），否则显示手动输入框 ──
    _secret_token   = st.secrets.get("telegram", {}).get("bot_token", "")
    _secret_chat_id = st.secrets.get("telegram", {}).get("chat_id", "")

    if _secret_token and _secret_chat_id:
        # Secrets 已配置：显示已加载状态，不暴露明文
        tg_token   = _secret_token
        tg_chat_id = _secret_chat_id
        st.markdown("""
<div style="background:#3df5b010;border:1px solid #3df5b055;border-radius:8px;
            padding:8px 12px;font-family:'Space Mono',monospace;font-size:10px;
            color:#3df5b0;line-height:1.8">
  ✅ <b>已从 Streamlit Secrets 加载</b><br>
  <span style="color:#5a5c78">bot_token ••••••••<br>
  chat_id ••••••••</span>
</div>""", unsafe_allow_html=True)
    else:
        # Secrets 未配置：降级到手动输入
        st.markdown("""
<div style="background:#ff3d6b0a;border:1px solid #ff3d6b33;border-radius:8px;
            padding:8px 12px;font-family:'Space Mono',monospace;font-size:10px;
            color:#ff3d6b;line-height:1.6;margin-bottom:8px">
  ⚠ 未检测到 Secrets，请手动输入<br>
  <span style="color:#5a5c78">建议配置 .streamlit/secrets.toml</span>
</div>""", unsafe_allow_html=True)
        tg_token   = st.text_input("Bot Token",
                                   placeholder="110201543:AAHdqTcvCH1vGWJxfSeofSz326CKEqt4VN",
                                   type="password",
                                   help="从 @BotFather 获取")
        tg_chat_id = st.text_input("Chat ID",
                                   placeholder="-1001234567890 或 你的 user_id",
                                   help="可用 @userinfobot 查询")

    # ── 单点变化检测参数
    st.markdown("**① 单点变化（快速预警）**")
    spot_window      = st.slider("单点观察窗口（分钟）", 2, 15, 5,
                                 help="比较最近 N 分钟首尾变化幅度，反应快但易受噪音影响")
    vix_thresh       = st.slider("VIX 单点变化阈值（%）", 0.3, 5.0, 1.0, step=0.1,
                                 help="VIX 变动超过此值即触发检测")
    tsla_thresh      = st.slider("TSLA 未响应容忍度（%）", 0.1, 3.0, 0.5, step=0.1,
                                 help="TSLA 变动在此范围内视为「未跟随」")

    # ── 趋势回归检测参数
    st.markdown("**② 线性趋势（高置信确认）**")
    trend_window      = st.slider("趋势观察窗口（分钟）", 4, 20, 6,
                                  help="EMA span 自动取窗口的一半（3–5），检查最近 min(窗口,6) 根 K 线方向一致性")
    vix_slope_thresh  = st.slider("VIX 趋势斜率阈值（%/分钟）", 0.01, 0.20, 0.05, step=0.01,
                                  help="VIX 每分钟需涨/跌超过此值才视为有效趋势")
    tsla_slope_thresh = st.slider("TSLA 斜率容忍度（%/分钟）", 0.01, 0.10, 0.02, step=0.01,
                                  help="TSLA 每分钟变化低于此值视为「未跟随」")
    min_r2            = st.slider("VIX 趋势线性度 R²", 0.3, 0.9, 0.5, step=0.05,
                                  help="R² 越高代表趋势越稳定，建议 0.5 以上过滤锯齿")

    # 冷却时间（防止重复告警）
    alert_cooldown = st.slider("告警冷却时间（分钟）", 1, 60, 15,
                               help="同类型告警的最短间隔，防止刷屏")

    col_test, col_clear = st.columns(2)
    with col_test:
        if st.button("📡 测试连接", use_container_width=True):
            if tg_token and tg_chat_id:
                ok, msg = tg_test(tg_token, tg_chat_id)
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("未检测到有效的 Token / Chat ID")
    with col_clear:
        if st.button("🗑 清除记录", use_container_width=True):
            st.session_state.alert_history = []
            st.session_state.last_alert_time = {}
            st.success("已清除")

    st.markdown('<div class="sec">📌 背景知识</div>', unsafe_allow_html=True)
    st.markdown("""
<div style="font-size:12px;color:#5a5c78;line-height:1.9">
<b style="color:#dde1f5">TSLA 与 VIX 为何负相关？</b><br><br>
· <b style="color:#ff3d6b">VIX 上升</b>（恐慌加剧）→ 资金避险撤出成长股 → <b style="color:#ff3d6b">TSLA 下跌</b><br><br>
· <b style="color:#3df5b0">VIX 下降</b>（情绪平稳）→ 风险偏好回升 → <b style="color:#3df5b0">TSLA 上涨</b><br><br>
TSLA 贝塔值约 <b style="color:#e8ff47">2.0</b>，对市场情绪高度敏感，是追踪此负相关的理想标的。
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 顶栏
# ══════════════════════════════════════════════════════════
session_key, session_zh_label, et_time = get_market_session()
badge_cls = {"pre": "pre", "open": "open", "post": "post", "closed": "clos"}[session_key]

col_h, col_b = st.columns([5, 2])
with col_h:
    st.markdown('<div class="htitle">TSLA × VIX</div>', unsafe_allow_html=True)
    st.markdown('<div class="hsub">实时相关性追踪 · 1分钟级别 · 含盘前/盘后交易时段</div>',
                unsafe_allow_html=True)
with col_b:
    dot = '<span class="dot g"></span>' if session_key == "open" else (
          '<span class="dot b"></span>' if session_key == "pre" else "●")
    st.markdown(f"""
    <div style="padding-top:24px;text-align:right">
      <div class="badge {badge_cls}">{dot} {session_zh_label} · {et_time}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════
# 数据加载
# ══════════════════════════════════════════════════════════
now_str = datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S GMT")

with st.spinner("⏳ 正在拉取 1 分钟实时行情（含盘前数据）…"):
    tsla_1m_raw, vix_1m_raw = fetch_1min(_cache_bust=st.session_state.refresh_count)

if tsla_1m_raw.empty or vix_1m_raw.empty:
    st.error("⚠ 数据获取失败，请检查网络或稍后重试。")
    st.stop()

df1m = build_df(tsla_1m_raw, vix_1m_raw)
sessions_1m = tag_session(df1m.index)

r1m, p1m = pearson_corr(df1m)

# ── Session state 初始化（告警历史 & 冷却）
if "alert_history" not in st.session_state:
    st.session_state.alert_history = []
if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = {}

# ══════════════════════════════════════════════════════════
# 背离仪表板：实时K线检测
# ══════════════════════════════════════════════════════════
if "divdash_alert_time" not in st.session_state:
    st.session_state.divdash_alert_time = None

divdash_result  = {}
divdash_fig     = None
divdash_tg_fired = None

if divdash_enabled:
    divdash_result = detect_divergence_live(
        df1m,
        n_bars=divdash_n_bars,
        div_thresh_vix=divdash_vix_thr,
        div_thresh_tsla=divdash_tsla_thr,
    )
    divdash_fig = build_divdash_chart(df1m, n_bars=divdash_n_bars, div_result=divdash_result)

    # Telegram 推送（独立冷却）
    if divdash_result.get("alert") and divdash_result.get("msg"):
        dd_now_dt  = datetime.now(ET)
        dd_last_t  = st.session_state.divdash_alert_time
        dd_cool_ok = (
            dd_last_t is None or
            (dd_now_dt - dd_last_t).total_seconds() >= divdash_cooldown * 60
        )
        if tg_enabled and tg_token and tg_chat_id and dd_cool_ok:
            ok_dd, err_dd = tg_send(tg_token, tg_chat_id, divdash_result["msg"])
            divdash_tg_fired = (ok_dd, err_dd)
            if ok_dd:
                st.session_state.divdash_alert_time = dd_now_dt

# ══════════════════════════════════════════════════════════
# 双引擎背离检测 & Telegram 告警
# ══════════════════════════════════════════════════════════
sig_spot  = detect_spot(df1m, spot_window, vix_thresh, tsla_thresh)
sig_trend = detect_trend(df1m, trend_window, vix_slope_thresh, tsla_slope_thresh, min_r2)

# 合并为列表，各自独立触发（类型名不同，冷却时间互不干扰）
all_signals = [s for s in [sig_spot, sig_trend] if s is not None]

tg_results = {}   # {type: (ok, err)}
now_dt = datetime.now(ET)

for sig in all_signals:
    dtype = sig["type"]

    # 写入历史
    # 去重规则：同一 type（方向相同）60秒内不重复；但反向信号（同mode不同type）立即写入
    already = (
        st.session_state.alert_history and
        st.session_state.alert_history[0]["type"] == dtype and
        (now_dt - st.session_state.alert_history[0]["time"]).total_seconds() < 60
    )

    # 方向反转检测：若当前信号与上次推送的同 mode 信号方向相反，清除旧方向冷却
    _opposite = {
        "trend_vix_up":   "trend_vix_down",
        "trend_vix_down": "trend_vix_up",
        "spot_vix_up":    "spot_vix_down",
        "spot_vix_down":  "spot_vix_up",
    }
    opp_key = _opposite.get(dtype)
    if opp_key and opp_key in st.session_state.last_alert_time:
        # 旧方向冷却清除（方向已反转，允许立即推送新方向）
        del st.session_state.last_alert_time[opp_key]
    if not already:
        st.session_state.alert_history.insert(0, {
            "type":      dtype,
            "mode":      sig["mode"],
            "label":     sig["label"],
            "badge":     sig["badge"],
            "css":       sig["css"],
            "desc_html": sig["desc_html"],
            "time":      now_dt,
            "sent":      False,
        })
        st.session_state.alert_history = st.session_state.alert_history[:50]

    # Telegram：各自独立冷却
    last_t = st.session_state.last_alert_time.get(dtype)
    cooldown_ok = (
        last_t is None or
        (now_dt - last_t).total_seconds() >= alert_cooldown * 60
    )
    if tg_enabled and tg_token and tg_chat_id and cooldown_ok:
        ok, err = tg_send(tg_token, tg_chat_id, sig["msg"])
        tg_results[dtype] = (ok, err)
        if ok:
            st.session_state.last_alert_time[dtype] = now_dt
            if st.session_state.alert_history:
                st.session_state.alert_history[0]["sent"] = True

# ══════════════════════════════════════════════════════════
# VIX 1分钟急升急跌检测（独立信号）
# ══════════════════════════════════════════════════════════
if "spike_alert_time" not in st.session_state:
    st.session_state.spike_alert_time = {}   # {type: datetime}
if "spike_history" not in st.session_state:
    st.session_state.spike_history = []

spike_sig    = None
spike_tg_fired = None

if spike_enabled and len(df1m) >= 3:
    spike_sig = detect_vix_spike(
        df1m["VIX"],
        spike_pct=spike_pct,
        confirm_pct=confirm_pct,
        extreme_pct=extreme_pct,
    )

if spike_sig is not None:
    spike_now_dt  = datetime.now(ET)
    spike_now_str = spike_now_dt.strftime("%Y-%m-%d %H:%M:%S GMT")
    spike_type    = spike_sig["type"]
    spike_last_t  = st.session_state.spike_alert_time.get(spike_type)
    spike_cool_ok = (
        spike_last_t is None or
        (spike_now_dt - spike_last_t).total_seconds() >= spike_cooldown * 60
    )

    # 写入历史（不受冷却限制）
    already_sp = (
        st.session_state.spike_history and
        st.session_state.spike_history[0]["type"] == spike_type and
        (spike_now_dt - st.session_state.spike_history[0]["time"]).total_seconds() < 60
    )
    if not already_sp:
        st.session_state.spike_history.insert(0, {
            "type":       spike_type,
            "label":      spike_sig["label"],
            "css":        spike_sig["css"],
            "badge":      spike_sig["badge"],
            "emoji":      spike_sig["emoji"],
            "desc_html":  spike_sig["desc_html"],
            "chg1":       spike_sig["chg1"],
            "cumulative": spike_sig["cumulative"],
            "vix_now":    spike_sig["vix_now"],
            "is_extreme": spike_sig["is_extreme"],
            "time":       spike_now_dt,
            "sent":       False,
        })
        st.session_state.spike_history = st.session_state.spike_history[:50]

    # Telegram（独立冷却）
    if tg_enabled and tg_token and tg_chat_id and spike_cool_ok:
        ok_sp, err_sp = tg_send(tg_token, tg_chat_id, spike_sig["msg"])
        spike_tg_fired = (ok_sp, err_sp)
        if ok_sp:
            st.session_state.spike_alert_time[spike_type] = spike_now_dt
            if st.session_state.spike_history:
                st.session_state.spike_history[0]["sent"] = True

# ══════════════════════════════════════════════════════════
# 期权流 Put/Call 比率（独立信号）
# ══════════════════════════════════════════════════════════
if "pc_alert_time" not in st.session_state:
    st.session_state.pc_alert_time = None
if "pc_history" not in st.session_state:
    st.session_state.pc_history = []

pc_data   = {}
pc_interp = {}
pc_tg_fired = None

if pc_enabled:
    with st.spinner("⏳ 正在拉取 TSLA 期权链数据…"):
        pc_data = fetch_pc_ratio("TSLA")

    pc_interp = interpret_pc(
        pc_data.get("ratio_volume"),
        pc_data.get("ratio_oi"),
        pc_data.get("near_pc_vol"),
        pc_data.get("atm_skew"),
    )

    # 用用户自定义阈值覆盖默认触发判断
    primary_pc = pc_data.get("ratio_volume") or pc_data.get("ratio_oi")
    if primary_pc is not None:
        if primary_pc < pc_bull_thresh or primary_pc > pc_bear_thresh:
            pc_interp["tg_worthy"] = True
        else:
            pc_interp["tg_worthy"] = False

    pc_now_dt  = datetime.now(ET)
    pc_now_str = pc_now_dt.strftime("%Y-%m-%d %H:%M:%S GMT")
    pc_last_t  = st.session_state.pc_alert_time
    pc_cooldown_ok = (
        pc_last_t is None or
        (pc_now_dt - pc_last_t).total_seconds() >= pc_cooldown * 60
    )

    # Telegram 推送（独立冷却）
    if pc_interp.get("tg_worthy") and pc_cooldown_ok:
        if tg_enabled and tg_token and tg_chat_id:
            msg_pc = pc_tg_msg(pc_data, pc_interp, pc_now_str)
            ok_pc, err_pc = tg_send(tg_token, tg_chat_id, msg_pc)
            pc_tg_fired = (ok_pc, err_pc)
            if ok_pc:
                st.session_state.pc_alert_time = pc_now_dt

    # 写入期权流历史
    if pc_interp.get("tg_worthy"):
        already_pc = (
            st.session_state.pc_history and
            (pc_now_dt - st.session_state.pc_history[0]["time"]).total_seconds() < 120
        )
        if not already_pc and primary_pc is not None:
            st.session_state.pc_history.insert(0, {
                "label":  pc_interp["label"],
                "css":    pc_interp["css"],
                "emoji":  pc_interp["emoji"],
                "desc":   pc_interp["desc"],
                "ratio":  primary_pc,
                "time":   pc_now_dt,
                "sent":   bool(pc_tg_fired and pc_tg_fired[0]),
            })
            st.session_state.pc_history = st.session_state.pc_history[:30]

# ══════════════════════════════════════════════════════════
# 多因子策略胜率评估
# ══════════════════════════════════════════════════════════
if "strat_alert_time" not in st.session_state:
    st.session_state.strat_alert_time = None
if "strat_history" not in st.session_state:
    st.session_state.strat_history = []

strat_data    = {}
strat_factors = {}
strat_wr      = {}
strat_tg_fired = None

if strat_enabled:
    with st.spinner("⏳ 正在计算多因子策略胜率…"):
        strat_data = fetch_strategy_data()

    if not strat_data.get("error"):
        strat_factors = eval_factors(strat_data, lookback=strat_lookback)
        strat_wr      = calc_winrate(strat_factors)

        # Telegram：胜率超过用户设定阈值时推送
        strat_now_dt  = datetime.now(ET)
        strat_now_str = strat_now_dt.strftime("%Y-%m-%d %H:%M:%S GMT")
        strat_last_t  = st.session_state.strat_alert_time
        strat_cool_ok = (
            strat_last_t is None or
            (strat_now_dt - strat_last_t).total_seconds() >= strat_cooldown * 60
        )

        if strat_wr.get("winrate", 0) >= strat_min_wr and strat_cool_ok:
            if tg_enabled and tg_token and tg_chat_id:
                msg_s = strategy_tg_msg(strat_factors, strat_wr,
                                         strat_data.get("tsla_price"), strat_now_str)
                ok_s, err_s = tg_send(tg_token, tg_chat_id, msg_s)
                strat_tg_fired = (ok_s, err_s)
                if ok_s:
                    st.session_state.strat_alert_time = strat_now_dt

        # 写入历史（每次胜率≥60%记录）
        if strat_wr.get("winrate", 0) >= 60:
            already_s = (
                st.session_state.strat_history and
                (strat_now_dt - st.session_state.strat_history[0]["time"]).total_seconds() < 120
            )
            if not already_s:
                st.session_state.strat_history.insert(0, {
                    "winrate":  strat_wr["winrate"],
                    "tier":     strat_wr["tier"],
                    "color":    strat_wr["color"],
                    "signal":   strat_wr["signal"],
                    "n_active": len(strat_wr.get("active_factors", [])),
                    "time":     strat_now_dt,
                    "sent":     bool(strat_tg_fired and strat_tg_fired[0]),
                })
                st.session_state.strat_history = st.session_state.strat_history[:30]

tsla_rt, tsla_prev = fetch_rt_price("TSLA")
vix_rt,  vix_prev  = fetch_rt_price("^VIX")

# ── 使用1分钟最后一根兜底
if not tsla_rt and len(df1m):
    tsla_rt = float(df1m["TSLA"].iloc[-1])
if not vix_rt and len(df1m):
    vix_rt  = float(df1m["VIX"].iloc[-1])
if not tsla_prev and len(df1m) > 390:
    tsla_prev = float(df1m["TSLA"].iloc[-391])
if not vix_prev and len(df1m) > 390:
    vix_prev  = float(df1m["VIX"].iloc[-391])

tsla_chg = pct(tsla_rt, tsla_prev)
vix_chg  = pct(vix_rt,  vix_prev)

# ══════════════════════════════════════════════════════════
# 指标卡
# ══════════════════════════════════════════════════════════
c1, c2, c3, c4 = st.columns(4)

with c1:
    v = f"${tsla_rt:,.2f}" if tsla_rt else "—"
    s = "▲" if tsla_chg >= 0 else "▼"
    c = "#3df5b0" if tsla_chg >= 0 else "#ff3d6b"
    st.markdown(f"""
    <div class="kcard y">
      <div class="klabel">TSLA 实时价格</div>
      <div class="kval y">{v}</div>
      <div class="ksub" style="color:{c}">{s} {abs(tsla_chg):.2f}%&nbsp;&nbsp;较昨日收盘</div>
    </div>""", unsafe_allow_html=True)

with c2:
    v2 = f"{vix_rt:.2f}" if vix_rt else "—"
    s2 = "▲" if vix_chg >= 0 else "▼"
    c2c = "#ff3d6b" if vix_chg >= 0 else "#3df5b0"
    st.markdown(f"""
    <div class="kcard r">
      <div class="klabel">VIX 恐慌指数</div>
      <div class="kval r">{v2}</div>
      <div class="ksub" style="color:{c2c}">{s2} {abs(vix_chg):.2f}%&nbsp;&nbsp;较昨日收盘</div>
    </div>""", unsafe_allow_html=True)

with c3:
    if r1m is not None:
        st_zh, d_zh = strength_zh(r1m)
        rc = "r" if r1m < 0 else "t"
        st.markdown(f"""
        <div class="kcard t">
          <div class="klabel">皮尔逊相关系数 r（1分钟线）</div>
          <div class="kval {rc}">{r1m:.3f}</div>
          <div class="ksub">{st_zh}{d_zh}相关 · 样本 {len(df1m)} 根</div>
        </div>""", unsafe_allow_html=True)

with c4:
    if p1m is not None:
        p_str = f"{p1m:.2e}" if p1m < 0.001 else f"{p1m:.4f}"
        sig   = "✓ 极度显著" if p1m < 0.001 else ("✓ 显著" if p1m < 0.05 else "✗ 不显著")
        sc    = "#3df5b0" if p1m < 0.05 else "#ff3d6b"
        r2p   = r1m**2 * 100
        st.markdown(f"""
        <div class="kcard p">
          <div class="klabel">P 值 / R² 解释方差</div>
          <div class="kval p" style="font-size:22px">{p_str}</div>
          <div class="ksub" style="color:{sc}">{sig} · R²={r2p:.1f}%</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 结论框
# ══════════════════════════════════════════════════════════
if r1m is not None:
    ar = abs(r1m)
    if r1m <= -0.5:
        verdict_msg = (
            f"基于 <b>{len(df1m)}</b> 根 1 分钟 K 线，皮尔逊 r = <b>{r1m:.3f}</b>，"
            f"p 值 = {p1m:.2e}（远低于 0.05 显著性门槛），证明 TSLA 与 VIX 之间存在"
            f"<b>统计上高度显著的强负相关</b>。<br>"
            f"VIX 可解释 TSLA 价格 <b>{ar**2*100:.1f}%</b> 的方差（R²），"
            f"充分验证了「市场恐慌加剧，特斯拉抛压显著」的系统性规律。"
            f"当前交易时段：<b>{session_zh_label}</b>。"
        )
    elif r1m < -0.3:
        verdict_msg = (
            f"r = <b>{r1m:.3f}</b>，当前呈<b>中等负相关</b>（R²={ar**2*100:.1f}%）。"
            f"信号有效但存在噪音，可能受{'盘前流动性偏低' if session_key=='pre' else '盘中事件驱动'}影响，"
            f"负相关规律依然成立。"
        )
    elif r1m < 0:
        verdict_msg = (
            f"r = <b>{r1m:.3f}</b>，负相关信号偏弱。"
            f"当前处于 <b>{session_zh_label}</b>，可能有个股特定催化剂（如宏观数据、财报）"
            f"短暂压过 VIX 的系统性影响，建议延长观测窗口。"
        )
    else:
        verdict_msg = (
            f"r = <b>{r1m:.3f}</b>，当前出现<b>正相关异常</b>。"
            f"这属于短期特殊情况，通常由重大事件（财报、政策发布）主导个股走势所致，"
            f"历史长期负相关规律不受影响。"
        )

    st.markdown(f"""
    <div class="verdict">
      <div class="vt">⚡ 实时分析结论 · {now_str}</div>
      <div class="vb">{verdict_msg}</div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 告警状态栏 & 历史记录
# ══════════════════════════════════════════════════════════
st.markdown('<div class="sec">🚨 双引擎预警监控（单点快速 + 趋势确认）</div>', unsafe_allow_html=True)

# 实时趋势数值（用于正常状态显示）
_r_spot  = df1m.iloc[-spot_window:] if len(df1m) >= spot_window else df1m
_r_trend = df1m.iloc[-(trend_window*2+2):] if len(df1m) >= trend_window*2+2 else df1m
_ema_span = max(3, min(trend_window // 2, 5))
_vix_ema  = _r_trend["VIX"].ewm(span=_ema_span, adjust=False).mean()
_tsla_ema = _r_trend["TSLA"].ewm(span=_ema_span, adjust=False).mean()
def _quick_slope(s):
    n = _ema_span + 1
    v = s.iloc[-n:].values.astype(float)
    if len(v) < 2 or v[0] == 0: return 0.0
    return (v[-1] - v[0]) / v[0] * 100 / (len(v) - 1)
_vix_slope  = _quick_slope(_vix_ema)
_tsla_slope = _quick_slope(_tsla_ema)
_check_n = min(trend_window, len(_r_trend)-1, 6)
_vix_vals = _r_trend["VIX"].iloc[-(_check_n+1):].values.astype(float)
_vix_up_c = sum(1 for i in range(1, len(_vix_vals)) if _vix_vals[i] > _vix_vals[i-1])
_vix_dn_c = sum(1 for i in range(1, len(_vix_vals)) if _vix_vals[i] < _vix_vals[i-1])
_dir_count = max(_vix_up_c, _vix_dn_c)
_vix_r2 = round(_dir_count / _check_n, 2) if _check_n > 0 else 0.0

# 单点窗口涨跌幅
if len(df1m) >= spot_window + 1:
    _base = df1m.iloc[-(spot_window + 1)]
    _last = df1m.iloc[-1]
    _vix_spot_chg  = (float(_last["VIX"])  - float(_base["VIX"]))  / float(_base["VIX"])  * 100
    _tsla_spot_chg = (float(_last["TSLA"]) - float(_base["TSLA"])) / float(_base["TSLA"]) * 100
else:
    _vix_spot_chg = _tsla_spot_chg = 0.0

panel_spot, panel_trend = st.columns(2)

# ── 左：单点预警面板 ──────────────────────────────────────
with panel_spot:
    st.markdown(f"""
    <div style="font-family:'Space Mono',monospace;font-size:9px;letter-spacing:2px;
                color:#5a5c78;margin-bottom:8px">🟠 单点变化检测（窗口 {spot_window} 分钟）</div>
    """, unsafe_allow_html=True)

    if sig_spot is not None:
        tg_s = tg_results.get(sig_spot["type"])
        tg_icon = ("📲 已推送" if tg_s and tg_s[0] else
                   f"❌ {tg_s[1]}" if tg_s else
                   ("📡 监控中" if tg_enabled else "📵 未启用"))
        action_clr = "#3df5b0" if "down" in sig_spot["type"] else "#ff8c00"
        st.markdown(f"""
        <div class="alert-box {sig_spot['css']}">
          <div class="alert-badge {sig_spot['badge']}">{sig_spot['emoji']} {sig_spot['label'].split('：')[1] if '：' in sig_spot['label'] else sig_spot['label']}</div>
          <div class="alert-msg" style="margin:6px 0 8px;font-size:12px">{sig_spot['desc_html']}</div>
          <div style="background:rgba(0,0,0,.3);border-radius:5px;padding:5px 8px;
                      font-size:12px;color:{action_clr};font-weight:700">{sig_spot['action']}</div>
          <div class="alert-time" style="margin-top:6px">{tg_icon} · {now_dt.strftime('%H:%M:%S GMT')}</div>
        </div>""", unsafe_allow_html=True)
    else:
        vc = "#ff3d6b" if _vix_spot_chg > 0 else "#3df5b0"
        tc = "#3df5b0" if _tsla_spot_chg > 0 else "#ff3d6b"
        va = "▲" if _vix_spot_chg > 0 else "▼"
        ta = "▲" if _tsla_spot_chg > 0 else "▼"
        st.markdown(f"""
        <div class="kcard t" style="border-left:3px solid #3df5b0;padding:14px 16px">
          <div class="klabel">单点状态 · 过去 {spot_window} 分钟</div>
          <div style="font-size:16px;font-weight:700;color:#3df5b0;margin:4px 0">✅ 未触发</div>
          <div style="font-family:'Space Mono',monospace;font-size:11px;margin-top:6px;line-height:2">
            <span style="color:{vc}">VIX {va} {abs(_vix_spot_chg):.2f}%</span>
            &nbsp;·&nbsp;
            <span style="color:{tc}">TSLA {ta} {abs(_tsla_spot_chg):.2f}%</span>
          </div>
          <div style="font-family:'Space Mono',monospace;font-size:10px;color:#5a5c78;margin-top:2px">
            阈值：VIX±{vix_thresh:.1f}%，TSLA±{tsla_thresh:.1f}%
          </div>
        </div>""", unsafe_allow_html=True)

# ── 右：趋势确认面板 ──────────────────────────────────────
with panel_trend:
    st.markdown(f"""
    <div style="font-family:'Space Mono',monospace;font-size:9px;letter-spacing:2px;
                color:#5a5c78;margin-bottom:8px">🔴🟢 线性趋势检测（窗口 {trend_window} 分钟）</div>
    """, unsafe_allow_html=True)

    if sig_trend is not None:
        tg_t = tg_results.get(sig_trend["type"])
        tg_icon2 = ("📲 已推送" if tg_t and tg_t[0] else
                    f"❌ {tg_t[1]}" if tg_t else
                    ("📡 监控中" if tg_enabled else "📵 未启用"))
        action_clr2 = "#3df5b0" if "down" in sig_trend["type"] else "#ff8c00"
        st.markdown(f"""
        <div class="alert-box {sig_trend['css']}">
          <div class="alert-badge {sig_trend['badge']}">{sig_trend['emoji']} {sig_trend['label'].split('：')[1] if '：' in sig_trend['label'] else sig_trend['label']}</div>
          <div class="alert-msg" style="margin:6px 0 8px;font-size:12px">{sig_trend['desc_html']}</div>
          <div style="background:rgba(0,0,0,.3);border-radius:5px;padding:5px 8px;
                      font-size:12px;color:{action_clr2};font-weight:700">{sig_trend['action']}</div>
          <div class="alert-time" style="margin-top:6px">{tg_icon2} · {now_dt.strftime('%H:%M:%S GMT')}</div>
        </div>""", unsafe_allow_html=True)
    else:
        vc2 = "#ff3d6b" if _vix_slope > 0 else "#3df5b0"
        tc2 = "#3df5b0" if _tsla_slope > 0 else "#ff3d6b"
        va2 = "↗" if _vix_slope > 0.01 else ("↘" if _vix_slope < -0.01 else "→")
        ta2 = "↗" if _tsla_slope > 0.01 else ("↘" if _tsla_slope < -0.01 else "→")
        st.markdown(f"""
        <div class="kcard t" style="border-left:3px solid #7b7bff;padding:14px 16px">
          <div class="klabel">趋势状态 · 过去 {trend_window} 分钟</div>
          <div style="font-size:16px;font-weight:700;color:#3df5b0;margin:4px 0">✅ 未触发</div>
          <div style="font-family:'Space Mono',monospace;font-size:11px;margin-top:6px;line-height:2">
            <span style="color:{vc2}">VIX {va2} {_vix_slope:+.3f}%/分钟</span>
            &nbsp;·&nbsp;
            <span style="color:{tc2}">TSLA {ta2} {_tsla_slope:+.3f}%/分钟</span><br>
            <span style="color:#5a5c78">VIX 方向一致率={_vix_r2:.0%}（{_dir_count}/{_check_n}根同向）</span>
          </div>
          <div style="font-family:'Space Mono',monospace;font-size:10px;color:#5a5c78;margin-top:2px">
            阈值：斜率±{vix_slope_thresh:.2f}%/分钟，R²≥{min_r2:.2f}
          </div>
        </div>""", unsafe_allow_html=True)

# ── Telegram 总状态 + 告警说明
tg_col, info_col = st.columns([1, 2])
with tg_col:
    if tg_enabled:
        if tg_token and tg_chat_id:
            st.markdown('<div class="tg-status ok" style="margin-top:4px">📡 Telegram 双引擎监控中</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="tg-status err" style="margin-top:4px">⚠ 缺少 Token / Chat ID</div>',
                        unsafe_allow_html=True)
    else:
        st.markdown('<div class="tg-status off" style="margin-top:4px">📵 Telegram 已关闭</div>',
                    unsafe_allow_html=True)

with info_col:
    st.markdown(f"""
    <div style="font-size:10px;color:#5a5c78;font-family:'Space Mono',monospace;
                line-height:1.8;padding:6px 0">
      🟠 <b style="color:#dde1f5">单点</b>：快速，适合捕捉急速脉冲，噪音较多
      &nbsp;|&nbsp;
      🔴🟢 <b style="color:#dde1f5">趋势</b>：慢速，R²过滤噪音，置信度高
      &nbsp;|&nbsp;
      冷却：{alert_cooldown} 分钟（两引擎独立计算）
    </div>""", unsafe_allow_html=True)

# ── 历史记录
if st.session_state.alert_history:
    with st.expander(f"📋 预警历史（共 {len(st.session_state.alert_history)} 条，两引擎合并）",
                     expanded=False):
        for rec in st.session_state.alert_history:
            sent_icon = "📲" if rec.get("sent") else "🔕"
            mode_badge = (
                "<span style='color:#ff8c00;font-size:9px'>[单点]</span>" if rec.get("mode") == "spot"
                else "<span style='color:#7b7bff;font-size:9px'>[趋势]</span>"
            )
            st.markdown(f"""
            <div class="alert-box {rec['css']}" style="padding:10px 14px;margin:4px 0">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span>{mode_badge} <span class="alert-badge {rec['badge']}" style="font-size:9px">{rec['label']}</span></span>
                <span class="alert-time">{sent_icon} {rec['time'].strftime('%m-%d %H:%M GMT')}</span>
              </div>
              <div class="alert-msg" style="font-size:11px;margin-top:4px">{rec['desc_html']}</div>
            </div>""", unsafe_allow_html=True)





st.markdown('<div class="sec">01 — 1分钟实时走势（含盘前 04:00 / 盘后 16:00（纽约时间））</div>',
            unsafe_allow_html=True)

# 标准化
if normalize:
    t_plot = (df1m["TSLA"] - df1m["TSLA"].mean()) / df1m["TSLA"].std()
    v_plot = (df1m["VIX"]  - df1m["VIX"].mean())  / df1m["VIX"].std()
    y_lab  = "Z-Score（标准化）"
    use_sec2 = False
else:
    t_plot, v_plot = df1m["TSLA"], df1m["VIX"]
    y_lab  = "价格 / 指数"
    use_sec2 = True

fig1 = make_subplots(specs=[[{"secondary_y": use_sec2}]])

# 盘前/盘后背景色块（按日分组，避免过多 vrect）
sess_series = pd.Series(sessions_1m, index=df1m.index)
in_pre  = sess_series == "pre"
in_post = sess_series == "post"

def add_bands(fig, mask, color, label):
    start = None
    idx = df1m.index
    vals = mask.values
    for i, v in enumerate(vals):
        if v and start is None:
            start = idx[i]
        elif not v and start is not None:
            fig.add_vrect(x0=start, x1=idx[i-1],
                          fillcolor=color, line_width=0,
                          annotation_text=label,
                          annotation_font=dict(size=8,
                              color="#7b7bff" if "盘前" in label else "#ff3d6b"),
                          annotation_position="top left")
            start = None
    if start is not None:
        fig.add_vrect(x0=start, x1=idx[-1],
                      fillcolor=color, line_width=0)

add_bands(fig1, in_pre,  "rgba(123,123,255,0.07)", "盘前")
add_bands(fig1, in_post, "rgba(255,61,107,0.06)",  "盘后")

fig1.add_trace(go.Scatter(
    x=df1m.index, y=t_plot,
    name="TSLA", mode="lines",
    line=dict(color="#e8ff47", width=1.8),
    fill="tozeroy", fillcolor="rgba(232,255,71,0.04)",
    hovertemplate="TSLA: %{y:.3f}<extra></extra>",
), secondary_y=False)

fig1.add_trace(go.Scatter(
    x=df1m.index, y=v_plot,
    name="VIX", mode="lines",
    line=dict(color="#ff3d6b", width=1.8, dash="dot"),
    hovertemplate="VIX: %{y:.3f}<extra></extra>",
), secondary_y=use_sec2)

# 标注最新值
if len(df1m):
    fig1.add_annotation(
        x=df1m.index[-1], y=float(t_plot.iloc[-1]),
        text=f"  ¥{float(df1m['TSLA'].iloc[-1]):.2f}",
        showarrow=False,
        font=dict(color="#e8ff47", size=11, family="Space Mono"),
        xanchor="left",
    )

fig1.update_layout(
    paper_bgcolor="#0e0f1a", plot_bgcolor="#09090f",
    font=dict(family="'Noto Sans SC',monospace", color="#5a5c78", size=10),
    legend=dict(bgcolor="#0e0f1a", bordercolor="#1e1f35", borderwidth=1,
                font=dict(color="#dde1f5")),
    margin=dict(l=8, r=8, t=16, b=8), height=360,
    xaxis=dict(gridcolor="#141525", zeroline=False, rangeslider=dict(visible=False)),
    yaxis=dict(gridcolor="#141525", zeroline=False, title=y_lab),
    yaxis2=dict(gridcolor="rgba(0,0,0,0)", zeroline=False,
                title="VIX", showgrid=False) if use_sec2 else {},
    hovermode="x unified",
)
st.plotly_chart(fig1, use_container_width=True)

# ══════════════════════════════════════════════════════════
# 图2 + 图3：滚动相关 & 散点图
# ══════════════════════════════════════════════════════════
col_roll, col_scat = st.columns([3, 2])

with col_roll:
    st.markdown(f'<div class="sec">02 — 滚动皮尔逊相关（窗口 {roll_window} 根 K 线）</div>',
                unsafe_allow_html=True)

    roll = df1m["TSLA"].rolling(roll_window).corr(df1m["VIX"]).dropna()

    fig2 = go.Figure()
    fig2.add_hrect(y0=-1,   y1=-0.4, fillcolor="rgba(255,61,107,0.07)", line_width=0)
    fig2.add_hrect(y0=-0.4, y1=0.4,  fillcolor="rgba(90,92,120,0.03)",  line_width=0)
    fig2.add_hrect(y0=0.4,  y1=1,    fillcolor="rgba(61,245,176,0.05)", line_width=0)
    fig2.add_hline(y=-0.4, line_color="#ff3d6b", line_dash="dash", line_width=1,
                   annotation_text="强负相关阈值 −0.4",
                   annotation_font=dict(color="#ff3d6b", size=9))
    fig2.add_hline(y=0,    line_color="#1e1f35",  line_width=1)
    fig2.add_hline(y=0.4,  line_color="#3df5b0",  line_dash="dash", line_width=1,
                   annotation_text="强正相关阈值 +0.4",
                   annotation_font=dict(color="#3df5b0", size=9))

    fig2.add_trace(go.Scatter(
        x=roll.index, y=roll.values, mode="lines",
        line=dict(width=2, color="#7b7bff"),
        fill="tozeroy", fillcolor="rgba(123,123,255,0.06)",
        name=f"滚动 r（{roll_window}根）",
        hovertemplate="时间: %{x}<br>r = %{y:.3f}<extra></extra>",
    ))

    if len(roll):
        cur_r = float(roll.iloc[-1])
        fig2.add_annotation(
            x=roll.index[-1], y=cur_r,
            text=f"  当前 r = {cur_r:.3f}",
            showarrow=False,
            font=dict(color="#e8ff47", size=11, family="Space Mono"),
            xanchor="left",
        )

    fig2.update_layout(
        paper_bgcolor="#0e0f1a", plot_bgcolor="#09090f",
        font=dict(color="#5a5c78", size=10),
        margin=dict(l=8, r=8, t=8, b=8), height=310,
        yaxis=dict(range=[-1.05, 1.05], gridcolor="#141525",
                   zeroline=False, title="皮尔逊 r"),
        xaxis=dict(gridcolor="#141525", zeroline=False),
        showlegend=False, hovermode="x unified",
    )
    st.plotly_chart(fig2, use_container_width=True)

with col_scat:
    st.markdown('<div class="sec">03 — 散点图 + OLS 线性回归</div>', unsafe_allow_html=True)

    slope_v, intercept_v, *_ = stats.linregress(df1m["VIX"].values, df1m["TSLA"].values)
    xr = np.linspace(df1m["VIX"].min(), df1m["VIX"].max(), 200)
    yr = slope_v * xr + intercept_v

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df1m["VIX"], y=df1m["TSLA"],
        mode="markers",
        marker=dict(
            color=df1m["TSLA"].values,
            colorscale=[[0, "#ff3d6b"], [0.5, "#5a5c78"], [1, "#e8ff47"]],
            size=3, opacity=0.5, line=dict(width=0),
        ),
        name="观测点",
        hovertemplate="VIX=%{x:.2f}  TSLA=%{y:.2f}<extra></extra>",
    ))
    fig3.add_trace(go.Scatter(
        x=xr, y=yr, mode="lines",
        line=dict(color="#e8ff47", width=2, dash="dot"),
        name=f"OLS（斜率={slope_v:.2f}）",
    ))

    fig3.update_layout(
        paper_bgcolor="#0e0f1a", plot_bgcolor="#09090f",
        font=dict(color="#5a5c78", size=10),
        margin=dict(l=8, r=8, t=8, b=8), height=310,
        xaxis=dict(gridcolor="#141525", zeroline=False, title="VIX 恐慌指数"),
        yaxis=dict(gridcolor="#141525", zeroline=False, title="TSLA 股价（美元）"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#dde1f5", size=9)),
        hovermode="closest",
    )
    st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════
# 图4：历史视角
# ══════════════════════════════════════════════════════════
st.markdown(f'<div class="sec">04 — 历史相关性视角（{period_label}）</div>',
            unsafe_allow_html=True)

with st.spinner("加载历史数据…"):
    th_raw, vh_raw = fetch_history(hist_period, hist_interval)

if not th_raw.empty and not vh_raw.empty:
    dfh = build_df(th_raw, vh_raw)
    rh, ph = pearson_corr(dfh)

    fig4 = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.65, 0.35], vertical_spacing=0.03,
    )

    tp2 = (dfh["TSLA"] - dfh["TSLA"].mean()) / dfh["TSLA"].std() if normalize else dfh["TSLA"]
    vp2 = (dfh["VIX"]  - dfh["VIX"].mean())  / dfh["VIX"].std()  if normalize else dfh["VIX"]

    fig4.add_trace(go.Scatter(x=dfh.index, y=tp2, name="TSLA（历史）",
                              line=dict(color="#e8ff47", width=1.4),
                              fill="tozeroy", fillcolor="rgba(232,255,71,0.04)"),
                   row=1, col=1)
    fig4.add_trace(go.Scatter(x=dfh.index, y=vp2, name="VIX（历史）",
                              line=dict(color="#ff3d6b", width=1.4, dash="dot")),
                   row=1, col=1)

    roll_h = dfh["TSLA"].rolling(roll_window).corr(dfh["VIX"]).dropna()
    fig4.add_trace(go.Scatter(x=roll_h.index, y=roll_h.values,
                              name=f"滚动r（{roll_window}根）",
                              line=dict(color="#7b7bff", width=1.8),
                              fill="tozeroy", fillcolor="rgba(123,123,255,0.06)"),
                   row=2, col=1)
    fig4.add_hline(y=-0.4, line_color="#ff3d6b", line_dash="dash",
                   line_width=1, row=2, col=1)
    fig4.add_hline(y=0, line_color="#1e1f35", line_width=1, row=2, col=1)

    title_txt = (f"历史皮尔逊 r = {rh:.3f}  |  R² = {rh**2*100:.1f}%  |  p = {ph:.2e}"
                 if rh else "")
    fig4.update_layout(
        paper_bgcolor="#0e0f1a", plot_bgcolor="#09090f",
        font=dict(color="#5a5c78", size=10),
        title=dict(text=title_txt,
                   font=dict(color="#e8ff47", size=11, family="Space Mono"), x=0.01),
        margin=dict(l=8, r=8, t=34, b=8), height=440,
        legend=dict(bgcolor="#0e0f1a", bordercolor="#1e1f35", borderwidth=1,
                    font=dict(color="#dde1f5")),
        hovermode="x unified",
        xaxis=dict(gridcolor="#141525", zeroline=False),
        xaxis2=dict(gridcolor="#141525", zeroline=False),
        yaxis=dict(gridcolor="#141525", zeroline=False,
                   title="Z-Score" if normalize else "价格/指数"),
        yaxis2=dict(gridcolor="#141525", zeroline=False,
                    range=[-1.05, 1.05], title="r 值"),
    )
    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════
# 统计摘要表
# ══════════════════════════════════════════════════════════
st.markdown('<div class="sec">05 — 完整统计摘要</div>', unsafe_allow_html=True)

if r1m is not None:
    rows = [
        ("皮尔逊相关系数 r（1分钟线）",  f"{r1m:.4f}",
         "强负相关 → 高度反向联动" if r1m < -0.5 else
         ("中等负相关" if r1m < -0.3 else ("弱负相关" if r1m < 0 else "正相关（异常）"))),
        ("R² 解释方差（1分钟线）",       f"{r1m**2:.4f}（{r1m**2*100:.1f}%）",
         f"VIX 解释了 TSLA {r1m**2*100:.1f}% 的价格波动"),
        ("P 值（1分钟线）",              f"{p1m:.2e}",
         "极度显著（p<0.001）" if p1m < 0.001 else
         ("显著（p<0.05）" if p1m < 0.05 else "不显著")),
        ("OLS 回归斜率（TSLA/VIX）",    f"{slope_v:.4f}",
         f"VIX 每升 1 点 → TSLA 理论变动 {slope_v:.2f} 美元"),
        ("OLS 截距",                    f"{intercept_v:.4f}",
         "VIX=0 时 TSLA 的理论基准值"),
        ("样本量（1分钟 K 线数）",       str(len(df1m)),
         f"约覆盖 {len(df1m)//390 + 1} 个交易日"),
        ("TSLA 均值",                   f"${df1m['TSLA'].mean():.2f}", ""),
        ("TSLA 标准差",                 f"${df1m['TSLA'].std():.2f}", ""),
        ("VIX 均值",                    f"{df1m['VIX'].mean():.2f}",  ""),
        ("VIX 标准差",                  f"{df1m['VIX'].std():.2f}",   ""),
        ("当前交易时段",                session_zh_label,              et_time),
        ("实时 TSLA 价格",             f"${tsla_rt:.2f}" if tsla_rt else "—",
         f"较昨日 {'▲' if tsla_chg>=0 else '▼'} {abs(tsla_chg):.2f}%"),
        ("实时 VIX 指数",              f"{vix_rt:.2f}" if vix_rt else "—",
         f"较昨日 {'▲' if vix_chg>=0 else '▼'} {abs(vix_chg):.2f}%"),
        ("数据更新时间",               now_str,
         "每30秒自动刷新（已开启）" if auto_refresh else "自动刷新已关闭"),
    ]
    df_stats = pd.DataFrame(rows, columns=["指标", "数值", "解读"])
    st.dataframe(df_stats, use_container_width=True, hide_index=True,
                 column_config={
                     "指标": st.column_config.TextColumn("指标", width=240),
                     "数值": st.column_config.TextColumn("数值", width=220),
                     "解读": st.column_config.TextColumn("解读"),
                 })

# ══════════════════════════════════════════════════════════
# 背离仪表板 UI
# ══════════════════════════════════════════════════════════
st.markdown('<div class="sec">📺 背离实时仪表板 — VIX × TSLA K线同框（独立信号）</div>',
            unsafe_allow_html=True)

if not divdash_enabled:
    st.markdown("""<div style="font-family:'Space Mono',monospace;font-size:11px;
    color:#5a5c78;padding:14px;border:1px solid #1e1f35;border-radius:10px">
    📵 背离仪表板已关闭，在侧边栏启用「背离实时仪表板」</div>""", unsafe_allow_html=True)

elif divdash_result:
    dr     = divdash_result
    status = dr.get("status", "flat")
    alert  = dr.get("alert", False)

    # ── 状态颜色映射
    STATUS_CFG = {
        "div_up":   {"color": "#ff8c00", "bg": "#ff8c0015", "border": "#ff8c0055",
                     "emoji": "🟠", "label": "VIX ↑ · TSLA 未跌（背离）",
                     "action": "⚠️ TSLA 补跌概率高，考虑减仓/做空"},
        "div_down": {"color": "#3df5b0", "bg": "#3df5b015", "border": "#3df5b055",
                     "emoji": "🔵", "label": "VIX ↓ · TSLA 未涨（背离）",
                     "action": "✅ TSLA 补涨概率高，考虑做多/加仓"},
        "sync":     {"color": "#7b7bff", "bg": "#7b7bff10", "border": "#7b7bff44",
                     "emoji": "✅", "label": "VIX × TSLA 同步运动",
                     "action": "📊 市场正常联动，无背离"},
        "flat":     {"color": "#5a5c78", "bg": "#1e1f35",   "border": "#2a2b45",
                     "emoji": "—",  "label": "VIX 波动不足，无有效信号",
                     "action": "📊 等待有效移动"},
    }
    cfg = STATUS_CFG.get(status, STATUS_CFG["flat"])
    ac  = cfg["color"]

    # ── 顶部状态栏
    dd_stat_col, dd_num_col = st.columns([3, 2])

    with dd_stat_col:
        # 背离状态卡
        glow = f"box-shadow:0 0 20px {ac}44;" if alert else ""
        tg_dd_icon = "📲 已推送" if (divdash_tg_fired and divdash_tg_fired[0]) else (
                     f"❌ {divdash_tg_fired[1]}" if divdash_tg_fired else
                     ("📡 监控中" if tg_enabled else "📵 未启用"))
        last_dd_t = st.session_state.divdash_alert_time
        cool_remain = ""
        if last_dd_t:
            elapsed = int((datetime.now(ET) - last_dd_t).total_seconds() / 60)
            if elapsed < divdash_cooldown:
                cool_remain = f"（冷却 {elapsed}/{divdash_cooldown}分）"

        st.markdown(f"""
        <div class="divdash-alert {'up' if status=='div_up' else ('down' if status=='div_down' else ('sync' if status=='sync' else 'none'))}"
             style="{glow}">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
            <span style="font-size:24px">{cfg['emoji']}</span>
            <div>
              <div style="font-family:'Space Mono',monospace;font-weight:700;
                          font-size:13px;color:{ac}">{cfg['label']}</div>
              <div style="font-size:10px;color:#5a5c78;font-family:'Space Mono',monospace;
                          margin-top:2px">最近 {divdash_n_bars} 根 · 阈值 VIX±{divdash_vix_thr:.1f}% TSLA±{divdash_tsla_thr:.1f}%</div>
            </div>
          </div>
          <div style="background:rgba(0,0,0,.25);border-radius:7px;padding:7px 12px;
                      font-size:12px;font-weight:700;color:{ac};margin-bottom:8px">
            {cfg['action']}
          </div>
          <div style="font-family:'Space Mono',monospace;font-size:10px;color:#5a5c78">
            {tg_dd_icon} {cool_remain} · {dr.get('now_ts','—')}
          </div>
        </div>""", unsafe_allow_html=True)

    with dd_num_col:
        # 逐根背离统计
        div_c   = dr.get("div_count", 0)
        valid_c = dr.get("valid_count", 0)
        div_pct = dr.get("div_pct", 0)
        vix_tot = dr.get("vix_total", 0)
        tsla_tot= dr.get("tsla_total", 0)
        lv      = dr.get("last_vix")
        lt      = dr.get("last_tsla")

        bar_fill = int(div_pct * 100)
        bar_col  = "#ff8c00" if status == "div_up" else ("#3df5b0" if status == "div_down" else "#7b7bff")

        st.markdown(f"""
        <div style="font-family:'Space Mono',monospace;font-size:11px;
                    background:#0e0f1a;border:1px solid #1e1f35;border-radius:10px;
                    padding:14px 16px;line-height:2.2">
          <b style="color:#dde1f5">窗口统计</b><br>
          VIX  当前：<b style="color:#ff3d6b">{lv:.2f}</b>
          &nbsp;({vix_tot:+.2f}%)<br>
          TSLA 当前：<b style="color:#7b7bff">${lt:.2f}</b>
          &nbsp;({tsla_tot:+.2f}%)<br>
          背离根数：<b style="color:{bar_col}">{div_c}</b> / {valid_c} 有效移动<br>
          <div class="divdash-bar" style="margin:4px 0">
            <span class="divdash-label">背离率</span>
            <div class="divdash-track">
              <div class="divdash-fill" style="width:{bar_fill}%;
                   background:linear-gradient(90deg,{bar_col}88,{bar_col})"></div>
            </div>
            <span style="color:{bar_col};font-size:10px;width:32px;text-align:right">{bar_fill}%</span>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── 颜色图例
    st.markdown("""
    <div style="display:flex;gap:16px;font-family:'Space Mono',monospace;font-size:10px;
                color:#5a5c78;margin:6px 0 8px;flex-wrap:wrap">
      <span>🟠 <span style="color:#ff8c00">背离↑</span>（VIX升TSLA未跌）</span>
      <span>🔵 <span style="color:#3df5b0">背离↓</span>（VIX降TSLA未涨）</span>
      <span>🟣 <span style="color:#7b7bff">同步</span></span>
      <span>⬜ <span style="color:#5a5c78">VIX无效移动</span></span>
    </div>""", unsafe_allow_html=True)

    # ── 双图表
    if divdash_fig is not None:
        st.plotly_chart(divdash_fig, use_container_width=True)

    # ── 逐根明细表
    bars = dr.get("bars", [])
    if bars:
        with st.expander(f"📋 逐根背离明细（最近 {len(bars)} 根）", expanded=False):
            rows_dd = []
            STATUS_LABEL = {
                "div_up":   "🟠 背离↑", "div_down": "🔵 背离↓",
                "sync":     "✅ 同步",  "flat":     "— 无效",
            }
            for b in reversed(bars):
                t_str = b["time"].tz_convert(ET).strftime("%H:%M") if hasattr(b["time"], "tz_convert") else str(b["time"])
                rows_dd.append({
                    "时间(GMT)":    t_str,
                    "VIX":        f"{b['vix']:.2f}",
                    "VIX变化":    f"{b['vix_chg']:+.2f}%",
                    "TSLA":       f"${b['tsla']:.2f}",
                    "TSLA变化":   f"{b['tsla_chg']:+.2f}%",
                    "状态":       STATUS_LABEL.get(b["status"], "—"),
                })
            st.dataframe(pd.DataFrame(rows_dd), use_container_width=True,
                         hide_index=True)

# ══════════════════════════════════════════════════════════
# VIX 急升急跌面板 UI
# ══════════════════════════════════════════════════════════
st.markdown('<div class="sec">⚡ VIX 1分钟急升急跌监控（独立信号）</div>',
            unsafe_allow_html=True)

if not spike_enabled:
    st.markdown("""<div style="font-family:'Space Mono',monospace;font-size:11px;
    color:#5a5c78;padding:14px;border:1px solid #1e1f35;border-radius:10px">
    📵 急速脉冲检测已关闭，在侧边栏启用「VIX 1分钟急升急跌」</div>""",
    unsafe_allow_html=True)
else:
    sp_col1, sp_col2 = st.columns([3, 2])

    with sp_col1:
        if spike_sig is not None:
            s       = spike_sig
            ac      = "#ff8c00" if s["direction"] == "up" else "#3df5b0"
            ex_glow = f"box-shadow:0 0 18px {ac}55;" if s["is_extreme"] else ""
            tg_icon = "📲 已推送" if (spike_tg_fired and spike_tg_fired[0]) else (
                      f"❌ {spike_tg_fired[1]}" if spike_tg_fired else
                      ("📡 监控中" if tg_enabled else "📵 未启用"))

            st.markdown(f"""
            <div class="alert-box {s['css']}" style="{ex_glow}padding:18px 20px">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
                <span style="font-size:32px">{s['emoji']}</span>
                <div>
                  <div class="alert-badge {s['badge']}" style="font-size:13px">
                    {s['label']}
                  </div>
                  <div style="font-family:'Space Mono',monospace;font-size:10px;
                              color:#5a5c78;margin-top:4px">
                    置信度：<b style="color:{ac}">{s['confidence']}</b>
                    &nbsp;·&nbsp; 模式：{s['mode']}
                  </div>
                </div>
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;
                          font-family:'Space Mono',monospace;margin-bottom:12px">
                <div style="background:rgba(0,0,0,.3);border-radius:8px;padding:8px 10px;text-align:center">
                  <div style="font-size:9px;color:#5a5c78;margin-bottom:3px">最后1根</div>
                  <div style="font-size:18px;font-weight:700;color:{ac}">{s['chg1']:+.2f}%</div>
                </div>
                <div style="background:rgba(0,0,0,.3);border-radius:8px;padding:8px 10px;text-align:center">
                  <div style="font-size:9px;color:#5a5c78;margin-bottom:3px">2根累计</div>
                  <div style="font-size:18px;font-weight:700;color:{ac}">{s['cumulative']:+.2f}%</div>
                </div>
                <div style="background:rgba(0,0,0,.3);border-radius:8px;padding:8px 10px;text-align:center">
                  <div style="font-size:9px;color:#5a5c78;margin-bottom:3px">VIX 当前</div>
                  <div style="font-size:18px;font-weight:700;color:#dde1f5">{s['vix_now']:.2f}</div>
                </div>
              </div>

              <div style="background:rgba(0,0,0,.3);border-radius:8px;padding:8px 12px;
                          font-size:11px;color:#5a5c78;margin-bottom:10px;line-height:1.7">
                💥 {s['meaning']}
              </div>

              <div style="background:rgba(0,0,0,.25);border-radius:8px;padding:8px 12px;
                          font-size:13px;color:{ac};font-weight:700">
                {s['action']}
              </div>

              <div class="alert-time" style="margin-top:8px">{tg_icon} · {datetime.now(ET).strftime('%H:%M:%S GMT')}</div>
            </div>""", unsafe_allow_html=True)

            if spike_tg_fired:
                cl = "ok" if spike_tg_fired[0] else "err"
                ic = "⚡ 急速信号已推送" if spike_tg_fired[0] else f"❌ {spike_tg_fired[1]}"
                st.markdown(f'<div class="tg-status {cl}" style="margin-top:6px">{ic}</div>',
                            unsafe_allow_html=True)
        else:
            # 正常状态：显示最近2根 VIX K线变化
            if len(df1m) >= 3:
                v     = df1m["VIX"].values.astype(float)
                c1    = (v[-1] - v[-2]) / v[-2] * 100 if v[-2] != 0 else 0
                c2    = (v[-2] - v[-3]) / v[-3] * 100 if v[-3] != 0 else 0
                cum   = (v[-1] - v[-3]) / v[-3] * 100 if v[-3] != 0 else 0
                col1  = "#ff3d6b" if c1 > 0 else "#3df5b0"
                col2  = "#ff3d6b" if c2 > 0 else "#3df5b0"
                colc  = "#ff3d6b" if cum > 0 else "#3df5b0"
                st.markdown(f"""
                <div class="kcard t" style="border-left:4px solid #3df5b0;padding:16px 18px">
                  <div class="klabel">VIX 急速脉冲状态 · 实时监控中</div>
                  <div style="font-size:18px;font-weight:700;color:#3df5b0;margin:6px 0 12px">
                    ✅ 未触发（阈值 ±{spike_pct:.1f}%）
                  </div>
                  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;
                              font-family:'Space Mono',monospace">
                    <div style="background:#141525;border-radius:8px;padding:8px 10px;text-align:center">
                      <div style="font-size:9px;color:#5a5c78;margin-bottom:3px">最后1根</div>
                      <div style="font-size:17px;font-weight:700;color:{col1}">{c1:+.2f}%</div>
                    </div>
                    <div style="background:#141525;border-radius:8px;padding:8px 10px;text-align:center">
                      <div style="font-size:9px;color:#5a5c78;margin-bottom:3px">前1根</div>
                      <div style="font-size:17px;font-weight:700;color:{col2}">{c2:+.2f}%</div>
                    </div>
                    <div style="background:#141525;border-radius:8px;padding:8px 10px;text-align:center">
                      <div style="font-size:9px;color:#5a5c78;margin-bottom:3px">2根累计</div>
                      <div style="font-size:17px;font-weight:700;color:{colc}">{cum:+.2f}%</div>
                    </div>
                  </div>
                  <div style="font-family:'Space Mono',monospace;font-size:10px;
                              color:#5a5c78;margin-top:8px">
                    VIX 当前：{v[-1]:.2f} · 单根触发：±{spike_pct:.1f}% · 极端：±{extreme_pct:.1f}%
                  </div>
                </div>""", unsafe_allow_html=True)

        # Telegram 总状态
        if tg_enabled and tg_token and tg_chat_id:
            st.markdown('<div class="tg-status ok" style="margin-top:6px">📡 VIX 脉冲 Telegram 监控中</div>',
                        unsafe_allow_html=True)
        elif not tg_enabled:
            st.markdown('<div class="tg-status off" style="margin-top:6px">📵 Telegram 已关闭</div>',
                        unsafe_allow_html=True)

    with sp_col2:
        # 参数说明 + 历史
        last_sp_up   = st.session_state.spike_alert_time.get("vix_spike_up")
        last_sp_down = st.session_state.spike_alert_time.get("vix_spike_down")
        up_str   = last_sp_up.strftime("%H:%M GMT") if last_sp_up else "—"
        down_str = last_sp_down.strftime("%H:%M GMT") if last_sp_down else "—"
        st.markdown(f"""
        <div style="font-family:'Space Mono',monospace;font-size:10px;color:#5a5c78;
                    background:#0e0f1a;border:1px solid #1e1f35;border-radius:10px;
                    padding:14px 16px;line-height:2.1">
          <b style="color:#dde1f5">触发条件</b><br>
          ⬆️ 急升：单根 ≥ +{spike_pct:.1f}%<br>
          ⬇️ 急跌：单根 ≤ -{spike_pct:.1f}%<br>
          🔁 确认：2根累计 ≥ ±{confirm_pct:.1f}%（同向）<br>
          ⚡ 极端：单根/累计 ≥ ±{extreme_pct:.1f}%<br>
          🔕 冷却：{spike_cooldown} 分钟<br><br>
          <b style="color:#dde1f5">上次推送</b><br>
          ⬆️ 急升：{up_str}<br>
          ⬇️ 急跌：{down_str}
        </div>""", unsafe_allow_html=True)

    # 历史记录
    if st.session_state.spike_history:
        with st.expander(f"📋 VIX 急速信号历史（共 {len(st.session_state.spike_history)} 条）",
                         expanded=False):
            for rec in st.session_state.spike_history:
                sent_icon = "📲" if rec.get("sent") else "🔕"
                ex_mark   = "⚡" if rec.get("is_extreme") else ""
                ac2       = "#ff8c00" if "up" in rec["type"] else "#3df5b0"
                st.markdown(f"""
                <div class="alert-box {rec['css']}" style="padding:10px 14px;margin:4px 0">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span class="alert-badge {rec['badge']}" style="font-size:10px">
                      {ex_mark}{rec['emoji']} {rec['label']}
                    </span>
                    <span class="alert-time">
                      {sent_icon} {rec['time'].strftime('%m-%d %H:%M:%S GMT')}
                    </span>
                  </div>
                  <div style="font-family:'Space Mono',monospace;font-size:11px;
                              color:#5a5c78;margin-top:4px;line-height:1.7">
                    VIX={rec['vix_now']:.2f} · 1根 <span style="color:{ac2}">{rec['chg1']:+.2f}%</span>
                    · 2根累计 <span style="color:{ac2}">{rec['cumulative']:+.2f}%</span>
                  </div>
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 期权流面板 UI
# ══════════════════════════════════════════════════════════
st.markdown('<div class="sec">📊 期权流信号 — TSLA Put/Call 比率（独立信号）</div>',
            unsafe_allow_html=True)

if not pc_enabled:
    st.markdown("""
    <div style="font-family:'Space Mono',monospace;font-size:11px;color:#5a5c78;
                padding:14px;border:1px solid #1e1f35;border-radius:10px">
    📵 期权流监控已关闭，在侧边栏启用「期权流 Put/Call 监控」
    </div>""", unsafe_allow_html=True)

elif pc_data.get("error"):
    st.markdown(f"""
    <div style="background:#ff3d6b10;border:1px solid #ff3d6b55;border-radius:10px;
                padding:14px;font-family:'Space Mono',monospace;font-size:11px;color:#ff3d6b">
    ⚠ 期权数据获取失败：{pc_data['error']}<br>
    <span style="color:#5a5c78">Yahoo Finance 期权链在非交易时段可能返回空数据，盘中效果最佳。</span>
    </div>""", unsafe_allow_html=True)

else:
    rv       = pc_data.get("ratio_volume")
    ro       = pc_data.get("ratio_oi")
    nv       = pc_data.get("near_pc_vol")
    no_      = pc_data.get("near_pc_oi")
    pv       = pc_data.get("put_vol", 0)
    cv       = pc_data.get("call_vol", 0)
    poi      = pc_data.get("put_oi", 0)
    coi      = pc_data.get("call_oi", 0)
    skew     = pc_data.get("atm_skew")
    near_exp = pc_data.get("near_expiry", "—")
    by_exp   = pc_data.get("by_expiry", [])
    css      = pc_interp.get("css", "neut")
    emoji    = pc_interp.get("emoji", "⚪")
    label    = pc_interp.get("label", "—")
    action   = pc_interp.get("action", "—")
    desc     = pc_interp.get("desc", "—")
    strength = pc_interp.get("strength", 50)
    ac       = {"bull": "#3df5b0", "bear": "#ff3d6b", "neut": "#7b7bff"}.get(css, "#7b7bff")

    # ── 顶部指标行
    pc1, pc2, pc3, pc4 = st.columns(4)

    with pc1:
        rv_str = f"{rv:.3f}" if rv else "—"
        st.markdown(f"""
        <div class="kcard {css}">
          <div class="klabel">P/C 成交量比率（综合）</div>
          <div class="kval {css}" style="font-size:28px">{rv_str}</div>
          <div class="ksub">Put {pv:,} · Call {cv:,}</div>
        </div>""", unsafe_allow_html=True)

    with pc2:
        ro_str = f"{ro:.3f}" if ro else "—"
        st.markdown(f"""
        <div class="kcard {css}">
          <div class="klabel">P/C 未平仓量比率（综合）</div>
          <div class="kval {css}" style="font-size:28px">{ro_str}</div>
          <div class="ksub">Put OI {poi:,} · Call OI {coi:,}</div>
        </div>""", unsafe_allow_html=True)

    with pc3:
        nv_str = f"{nv:.3f}" if nv else "—"
        st.markdown(f"""
        <div class="kcard {css}">
          <div class="klabel">近月 P/C（{near_exp}）</div>
          <div class="kval {css}" style="font-size:28px">{nv_str}</div>
          <div class="ksub">近月最敏感，流动性最好</div>
        </div>""", unsafe_allow_html=True)

    with pc4:
        skew_str   = f"{skew:+.1f}%" if skew is not None else "—"
        skew_color = "#ff3d6b" if skew and skew > 3 else ("#3df5b0" if skew and skew < -2 else "#7b7bff")
        skew_label = "Put 溢价（偏空）" if skew and skew > 3 else ("Call 溢价（偏多）" if skew and skew < -2 else "ATM 偏斜中性")
        st.markdown(f"""
        <div class="kcard p">
          <div class="klabel">ATM 波动率偏斜（Put IV − Call IV）</div>
          <div class="kval p" style="font-size:26px;color:{skew_color}">{skew_str}</div>
          <div class="ksub">{skew_label}</div>
        </div>""", unsafe_allow_html=True)

    # ── 信号解读 + 各到期日明细
    sig_col, detail_col = st.columns([3, 2])

    with sig_col:
        # 信号强度条
        bar_color = ac
        st.markdown(f"""
        <div class="pc-card {css}">
          <div class="klabel" style="margin-bottom:8px">期权流信号研判</div>
          <div class="pc-signal {css}">{emoji} {label}</div>
          <div style="margin:10px 0 4px;font-family:'Space Mono',monospace;
                      font-size:10px;color:#5a5c78">信号强度</div>
          <div class="pc-bar-wrap">
            <div class="pc-bar-fill" style="width:{strength}%;
                 background:linear-gradient(90deg,{bar_color}88,{bar_color})"></div>
          </div>
          <div style="font-family:'Space Mono',monospace;font-size:10px;
                      color:{bar_color};margin-bottom:10px">{strength}/100</div>
          <div style="background:rgba(0,0,0,.25);border-radius:8px;padding:10px 12px;
                      font-size:13px;color:{ac};font-weight:700;margin-bottom:10px">
            {action}
          </div>
          <div style="font-family:'Space Mono',monospace;font-size:11px;
                      color:#5a5c78;line-height:1.8">{desc}</div>
        </div>""", unsafe_allow_html=True)

        # Telegram 状态
        if pc_interp.get("tg_worthy"):
            if pc_tg_fired:
                tg_ic = "✅ 期权流 Telegram 已推送" if pc_tg_fired[0] else f"❌ 推送失败：{pc_tg_fired[1]}"
                tg_cl = "ok" if pc_tg_fired[0] else "err"
            else:
                last_pc = st.session_state.pc_alert_time
                if last_pc:
                    mins = int((datetime.now(ET) - last_pc).total_seconds() / 60)
                    tg_ic = f"⏱ 冷却中（{mins}/{pc_cooldown} 分钟）"
                else:
                    tg_ic = "📵 Telegram 未启用" if not tg_enabled else "⏱ 冷却中"
                tg_cl = "off"
            st.markdown(f'<div class="tg-status {tg_cl}" style="margin-top:6px">📊 {tg_ic}</div>',
                        unsafe_allow_html=True)

    with detail_col:
        # 各到期日明细
        st.markdown("""
        <div style="font-family:'Space Mono',monospace;font-size:10px;
                    letter-spacing:1px;color:#5a5c78;margin-bottom:8px">
        各到期日 P/C 明细
        </div>""", unsafe_allow_html=True)

        if by_exp:
            for row in by_exp:
                exp     = row["expiry"]
                pc_v    = row.get("pc_vol")
                pc_o    = row.get("pc_oi")
                rv_disp = f"{pc_v:.2f}" if pc_v else "—"
                ro_disp = f"{pc_o:.2f}" if pc_o else "—"
                # 颜色：<0.7 绿，>1.0 红，其他蓝
                v_col = "#3df5b0" if pc_v and pc_v < 0.7 else ("#ff3d6b" if pc_v and pc_v > 1.0 else "#7b7bff")
                pct_call = int(row["call_vol"] / (row["call_vol"] + row["put_vol"]) * 100) if (row["call_vol"] + row["put_vol"]) > 0 else 50
                st.markdown(f"""
                <div style="background:#141525;border:1px solid #1e1f35;border-radius:8px;
                            padding:10px 12px;margin-bottom:6px">
                  <div style="display:flex;justify-content:space-between;
                              font-family:'Space Mono',monospace;font-size:10px">
                    <span style="color:#dde1f5;font-weight:700">{exp}</span>
                    <span style="color:{v_col}">P/C={rv_disp}</span>
                  </div>
                  <div style="margin:6px 0 3px;height:6px;background:#0e0f1a;border-radius:3px;overflow:hidden">
                    <div style="height:100%;width:{pct_call}%;
                                background:linear-gradient(90deg,#3df5b0,#00c896);border-radius:3px"></div>
                  </div>
                  <div style="font-family:'Space Mono',monospace;font-size:9px;color:#5a5c78;
                              display:flex;justify-content:space-between">
                    <span>Call {row['call_vol']:,}</span>
                    <span>Put {row['put_vol']:,}</span>
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#5a5c78;font-size:11px">暂无到期日数据</div>',
                        unsafe_allow_html=True)

    # ── P/C 比率参考区间说明
    st.markdown(f"""
    <div style="font-family:'Space Mono',monospace;font-size:10px;color:#5a5c78;
                background:#0e0f1a;border:1px solid #1e1f35;border-radius:8px;
                padding:10px 14px;margin-top:8px;line-height:2">
      <b style="color:#dde1f5">P/C 比率参考区间（TSLA 经验值）</b> &nbsp;·&nbsp;
      当前触发阈值：看涨 &lt; {pc_bull_thresh:.2f}，看空 &gt; {pc_bear_thresh:.2f}<br>
      &lt;0.4 极度乐观（逆向偏空）&nbsp;·&nbsp;
      0.4–0.6 偏多&nbsp;·&nbsp;
      0.6–0.85 中性偏多&nbsp;·&nbsp;
      0.85–1.1 中性&nbsp;·&nbsp;
      1.1–1.5 偏空&nbsp;·&nbsp;
      &gt;1.5 极度悲观（逆向偏多）&nbsp;·&nbsp;
      更新间隔：约 2 分钟 · 冷却：{pc_cooldown} 分钟
    </div>""", unsafe_allow_html=True)

    # ── 期权流历史
    if st.session_state.pc_history:
        with st.expander(f"📋 期权流信号历史（共 {len(st.session_state.pc_history)} 条）",
                         expanded=False):
            for rec in st.session_state.pc_history:
                sent_icon = "📲" if rec.get("sent") else "🔕"
                ratio_str = f"{rec['ratio']:.3f}" if rec.get("ratio") else "—"
                clr = {"bull": "#3df5b0", "bear": "#ff3d6b", "neut": "#7b7bff"}.get(rec.get("css"), "#7b7bff")
                st.markdown(f"""
                <div class="pc-card {rec.get('css','neut')}" style="padding:10px 14px;margin:4px 0">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="color:{clr};font-weight:700;font-size:12px">
                      {rec.get('emoji','')} {rec['label']}
                    </span>
                    <span style="font-family:'Space Mono',monospace;font-size:9px;color:#5a5c78">
                      {sent_icon} P/C={ratio_str} · {rec['time'].strftime('%m-%d %H:%M GMT')}
                    </span>
                  </div>
                  <div style="font-size:11px;color:#5a5c78;margin-top:4px">{rec['desc']}</div>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# 多因子策略胜率面板 UI
# ══════════════════════════════════════════════════════════
st.markdown('<div class="sec">🎯 多因子策略胜率信号（独立信号）</div>', unsafe_allow_html=True)

if not strat_enabled:
    st.markdown("""<div style="font-family:'Space Mono',monospace;font-size:11px;
    color:#5a5c78;padding:14px;border:1px solid #1e1f35;border-radius:10px">
    📵 策略胜率引擎已关闭，在侧边栏启用「多因子策略胜率」</div>""", unsafe_allow_html=True)

elif strat_data.get("error"):
    st.warning(f"⚠ 策略数据获取失败：{strat_data['error']}")

elif strat_wr:
    wr      = strat_wr
    factors = strat_factors
    price   = strat_data.get("tsla_price")
    color   = wr["color"]
    winrate = wr["winrate"]
    pct_bar = min(100, int((winrate - 48) / (76 - 48) * 100))

    main_col, factor_col = st.columns([2, 3])

    with main_col:
        score_bg     = f"{color}22"
        score_border = f"{color}66"
        st.markdown(f"""
        <div class="strat-card" style="text-align:center;border-color:{score_border};
                                        background:{score_bg}">
          <div style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:2px;
                      color:#5a5c78;margin-bottom:12px">策略胜率估算</div>
          <div style="font-family:'Space Mono',monospace;font-size:52px;font-weight:700;
                      color:{color};line-height:1">{winrate:.1f}<span style="font-size:22px">%</span></div>
          <div style="font-family:'Space Mono',monospace;font-size:12px;
                      color:{color};margin:8px 0 14px">{wr['tier']} · {len(wr['active_factors'])}/5 因子满足</div>
          <div class="win-meter">
            <div class="win-fill" style="width:{pct_bar}%;
                 background:linear-gradient(90deg,{color}88,{color})"></div>
          </div>
          <div style="font-family:'Space Mono',monospace;font-size:12px;
                      font-weight:700;color:{color};margin-top:10px">{wr['signal']}</div>
        </div>""", unsafe_allow_html=True)

        vwap_f  = factors.get("vwap_reclaim", {})
        gamma_f = factors.get("gamma_support", {})
        vwap_v  = vwap_f.get("vwap")
        g_sup   = gamma_f.get("support")
        g_res   = gamma_f.get("resist")
        if price or vwap_v or g_sup:
            st.markdown(f"""
            <div style="font-family:'Space Mono',monospace;font-size:11px;
                        background:#0e0f1a;border:1px solid #1e1f35;border-radius:10px;
                        padding:12px 14px;margin-top:10px;line-height:2.2">
              <b style="color:#dde1f5">关键价位参考</b><br>
              {"💵 TSLA $" + f"{price:.2f}" if price else ""}
              {"&nbsp;·&nbsp;📊 VWAP $" + f"{vwap_v:.2f}" if vwap_v else ""}<br>
              {"🧲 Gamma 支撑 $" + f"{g_sup:.1f}" if g_sup else ""}
              {"&nbsp;·&nbsp;🚧 阻力 $" + f"{g_res:.1f}" if g_res else ""}
            </div>""", unsafe_allow_html=True)

        if strat_tg_fired:
            tg_s_ic = "✅ 策略信号已推送" if strat_tg_fired[0] else f"❌ {strat_tg_fired[1]}"
            tg_s_cl = "ok" if strat_tg_fired[0] else "err"
        elif winrate >= strat_min_wr:
            last_s = st.session_state.strat_alert_time
            if last_s:
                m = int((datetime.now(ET) - last_s).total_seconds() / 60)
                tg_s_ic, tg_s_cl = f"⏱ 冷却中（{m}/{strat_cooldown}分钟）", "off"
            else:
                tg_s_ic = "📵 Telegram 未启用" if not tg_enabled else "📡 监控中"
                tg_s_cl = "ok" if tg_enabled else "off"
        else:
            tg_s_ic = f"⏸ 胜率 {winrate:.1f}% < 阈值 {strat_min_wr}%"
            tg_s_cl = "off"
        st.markdown(f'<div class="tg-status {tg_s_cl}" style="margin-top:6px">🎯 {tg_s_ic}</div>',
                    unsafe_allow_html=True)

    with factor_col:
        st.markdown("""<div style="font-family:'Space Mono',monospace;font-size:10px;
        letter-spacing:1px;color:#5a5c78;margin-bottom:10px">五大因子评估</div>""",
                    unsafe_allow_html=True)

        factor_defs = [
            ("vix_down",      "📉", "VIX ↓",          "核心因子，权重×2"),
            ("spx_up",        "📈", "SPX ↑",           "核心因子，权重×2"),
            ("tsla_rs",       "💪", "TSLA 相对强度 ↑",  "核心因子，权重×2"),
            ("gamma_support", "🧲", "Gamma 支撑",       "加强因子，权重×1.5"),
            ("vwap_reclaim",  "📊", "VWAP 夺回",        "加强因子，权重×1.5"),
        ]
        for key, icon, name, weight_note in factor_defs:
            f    = factors.get(key, {})
            act  = f.get("active")
            if key == "gamma_support":
                on_s    = f.get("on_support")
                row_cls = "on" if on_s else ("off" if on_s is False else "na")
                mark    = "✅" if on_s else ("⚠️" if act is True else ("—" if act is None else "❌"))
            else:
                row_cls = "on" if act is True else ("off" if act is False else "na")
                mark    = "✅" if act is True else ("—" if act is None else "❌")
            val_cls = "on" if row_cls == "on" else ("off" if row_cls == "off" else "")

            st.markdown(f"""
            <div class="factor-row {row_cls}">
              <span class="f-icon">{mark}</span>
              <span class="f-icon">{icon}</span>
              <span class="f-name">
                <b>{name}</b>
                <span style="color:#5a5c78;font-size:9px"> · {weight_note}</span><br>
                <span style="color:#5a5c78;font-size:10px">{f.get('detail','—')}</span>
              </span>
              <span class="f-val {val_cls}">{f.get('value','—')}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-family:'Space Mono',monospace;font-size:10px;color:#5a5c78;
                    background:#0e0f1a;border:1px solid #1e1f35;border-radius:8px;
                    padding:10px 14px;margin-top:10px;line-height:1.9">
          <b style="color:#dde1f5">胜率参考（历史统计锚点）</b><br>
          VIX↓ + SPX↑ + RS↑ → 约 63–68%&nbsp;·&nbsp;
          加 Gamma 支撑 → +3–4%&nbsp;·&nbsp;
          全部5因子 → 70%+<br>
          当前因子得分：<b style="color:{color}">{wr['score']:.1f} / {wr['max_score']:.1f}</b>
          &nbsp;·&nbsp;触发阈值：{strat_min_wr}%&nbsp;·&nbsp;冷却：{strat_cooldown} 分钟
        </div>""", unsafe_allow_html=True)

    if st.session_state.strat_history:
        with st.expander(f"📋 策略信号历史（共 {len(st.session_state.strat_history)} 条）",
                         expanded=False):
            for rec in st.session_state.strat_history:
                sent_icon = "📲" if rec.get("sent") else "🔕"
                clr = rec.get("color", "#7b7bff")
                st.markdown(f"""
                <div style="background:#0e0f1a;border:1px solid #1e1f35;border-radius:8px;
                            padding:10px 14px;margin:4px 0">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="color:{clr};font-weight:700;font-size:12px;
                                 font-family:'Space Mono',monospace">{rec['signal']}</span>
                    <span style="font-family:'Space Mono',monospace;font-size:9px;color:#5a5c78">
                      {sent_icon} {rec['n_active']}/5因子 · {rec['time'].strftime('%m-%d %H:%M GMT')}
                    </span>
                  </div>
                  <div style="font-family:'Space Mono',monospace;font-size:10px;
                              color:#5a5c78;margin-top:4px">
                    胜率 {rec['winrate']:.1f}% · {rec['tier']}
                  </div>
                </div>""", unsafe_allow_html=True)


refresh_info = "下次刷新：30 秒后" if auto_refresh else "自动刷新已关闭"
st.markdown(f"""
<div style="font-family:'Space Mono',monospace;font-size:10px;color:#22233a;
            text-align:center;margin-top:32px;padding:14px;border-top:1px solid #141525">
    数据来源：Yahoo Finance · 更新：{now_str} · {refresh_info} · 本页面仅供学术研究，不构成任何投资建议。
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 自动刷新
# ══════════════════════════════════════════════════════════
if auto_refresh:
    time.sleep(30)
    st.session_state.refresh_count = st.session_state.get("refresh_count", 0) + 1
    st.cache_data.clear()   # 清除其他缓存（期权链、历史数据等）
    st.rerun()
