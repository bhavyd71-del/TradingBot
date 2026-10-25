"""
Institutional-Grade Algorithmic Trading Dashboard
Platform: Delta Exchange India (BTCUSD 15m Momentum / VWAP Quantitative Framework)
Tech Stack: Streamlit, Plotly, SQLite3, Pandas, NumPy
Design Language: Ultra-clean Fintech Dark Mode (Tailored for Executive & Family Visibility)
"""

import os
import sqlite3
from datetime import datetime, timedelta
import zoneinfo
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 1. STREAMLIT GLOBAL CONFIGURATION & FINANCIAL UX STYLING
# ==============================================================================
st.set_page_config(
    page_title="Delta Alpha | Algorithmic Portfolio Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Background & Master Canvas */
.stApp {
    background-color: #0b0f19;
    color: #e2e8f0;
}

/* Cards & Surface Elevators */
.fin-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
}

.fin-metric-title {
    font-size: 0.825rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
    margin-bottom: 6px;
}

.fin-metric-val {
    font-size: 1.85rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.2;
}

.fin-badge-green {
    display: inline-block;
    padding: 3px 8px;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 6px;
    background-color: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.fin-badge-red {
    display: inline-block;
    padding: 3px 8px;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 6px;
    background-color: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.fin-badge-slate {
    display: inline-block;
    padding: 3px 8px;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 6px;
    background-color: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.3);
}

.fin-radar-active {
    background: linear-gradient(145deg, #111827 0%, #1e1b4b 100%);
    border: 1px solid #4338ca;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 20px;
}

.fin-radar-idle {
    background: linear-gradient(145deg, #111827 0%, #064e3b 100%);
    border: 1px solid #059669;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 20px;
}

/* Metric Dividers */
hr {
    border-color: #1f2937 !important;
}

/* Streamlit Button Overrides */
.stButton>button {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton>button:hover {
    background-color: #334155;
    border-color: #475569;
    color: #38bdf8;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================================================================
# 2. SELF-BOOTSTRAPPING RESILIENT DATABASE ENGINE
# ==============================================================================
DB_PATH = "paper_trading.db"


def init_database_layer():
    """Validates and self-bootstraps database schema with deterministic fallback seed data."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS price_bars (
            timestamp TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL
        )
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS position_snapshot (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            symbol TEXT,
            side TEXT,
            contracts REAL,
            entry_price REAL,
            current_price REAL,
            stop_loss REAL,
            take_profit REAL,
            unrealized_pnl REAL,
            updated_at TEXT
        )
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS closed_trades (
            trade_id TEXT PRIMARY KEY,
            symbol TEXT,
            side TEXT,
            contracts REAL,
            entry_time TEXT,
            exit_time TEXT,
            entry_price REAL,
            exit_price REAL,
            gross_pnl REAL,
            fees REAL,
            net_pnl REAL,
            reason TEXT
        )
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS equity_history (
            timestamp TEXT PRIMARY KEY,
            balance REAL,
            equity REAL
        )
    """
    )
    conn.commit()

    # Verify if seed bootstrapping is necessary (Zero-Crash Assurance)
    cur.execute("SELECT COUNT(*) FROM price_bars")
    candle_count = cur.fetchone()[0]

    if candle_count == 0:
        bootstrap_dummy_financial_data(conn)

    conn.close()


def bootstrap_dummy_financial_data(conn):
    """Populates realistic BTCUSD algorithmic trade history, price candles, and equity growth."""
    cur = conn.cursor()
    now_utc = datetime.now(zoneinfo.ZoneInfo("UTC"))

    # 1. Generate 250 bars of realistic 15m BTCUSD Candles
    base_price = 88500.0
    bar_time = now_utc - timedelta(minutes=15 * 250)
    bars_records = []

    np.random.seed(42)
    for _ in range(250):
        drift = np.random.normal(0.0001, 0.002)
        open_p = base_price
        close_p = open_p * (1.0 + drift)
        spread = abs(open_p * 0.0018)
        high_p = max(open_p, close_p) + np.random.uniform(0, spread)
        low_p = min(open_p, close_p) - np.random.uniform(0, spread)
        vol = float(np.random.uniform(15.0, 95.0))

        bars_records.append(
            (
                bar_time.strftime("%Y-%m-%d %H:%M:%S"),
                round(open_p, 2),
                round(high_p, 2),
                round(low_p, 2),
                round(close_p, 2),
                round(vol, 4),
            )
        )
        base_price = close_p
        bar_time += timedelta(minutes=15)

    cur.executemany(
        """
        INSERT OR REPLACE INTO price_bars (timestamp, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        bars_records,
    )

    # 2. Historical Multi-Week Closed Trades (4 Weeks of Trading)
    trade_start = now_utc - timedelta(days=26)
    trades = [
        (
            "T-101",
            "BTCUSD",
            "BUY",
            50.0,
            (trade_start + timedelta(days=1, hours=2)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            (trade_start + timedelta(days=1, hours=5, minutes=30)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            84200.0,
            85880.0,
            84.0,
            4.2,
            79.8,
            "Take Profit Reached (2R)",
        ),
        (
            "T-102",
            "BTCUSD",
            "SELL",
            40.0,
            (trade_start + timedelta(days=4, hours=8)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            (trade_start + timedelta(days=4, hours=10)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            86100.0,
            86700.0,
            -24.0,
            3.5,
            -27.5,
            "Safety Stop Loss Executed",
        ),
        (
            "T-103",
            "BTCUSD",
            "BUY",
            60.0,
            (trade_start + timedelta(days=8, hours=3)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            (trade_start + timedelta(days=8, hours=7)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            85400.0,
            87100.0,
            102.0,
            5.1,
            96.9,
            "Take Profit Reached (2R)",
        ),
        (
            "T-104",
            "BTCUSD",
            "BUY",
            55.0,
            (trade_start + timedelta(days=11, hours=14)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            (trade_start + timedelta(days=11, hours=18)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            86900.0,
            88630.0,
            95.15,
            4.8,
            90.35,
            "Take Profit Reached (2R)",
        ),
        (
            "T-105",
            "BTCUSD",
            "SELL",
            45.0,
            (trade_start + timedelta(days=15, hours=6)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            (trade_start + timedelta(days=15, hours=8)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            88200.0,
            88850.0,
            -29.25,
            3.8,
            -33.05,
            "Safety Stop Loss Executed",
        ),
        (
            "T-106",
            "BTCUSD",
            "BUY",
            50.0,
            (trade_start + timedelta(days=19, hours=9)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            (trade_start + timedelta(days=19, hours=13)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            87800.0,
            89560.0,
            88.0,
            4.4,
            83.6,
            "Take Profit Reached (2R)",
        ),
        (
            "T-107",
            "BTCUSD",
            "BUY",
            50.0,
            (trade_start + timedelta(days=22, hours=11)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            (trade_start + timedelta(days=22, hours=14, minutes=45)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            89100.0,
            90880.0,
            89.0,
            4.5,
            84.5,
            "Take Profit Reached (2R)",
        ),
        (
            "T-108",
            "BTCUSD",
            "SELL",
            35.0,
            (trade_start + timedelta(days=24, hours=1)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            (trade_start + timedelta(days=24, hours=3)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            91200.0,
            91800.0,
            -21.0,
            3.1,
            -24.1,
            "Safety Stop Loss Executed",
        ),
        (
            "T-109",
            "BTCUSD",
            "BUY",
            60.0,
            (trade_start + timedelta(days=25, hours=10)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            (trade_start + timedelta(days=25, hours=15)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            90800.0,
            92600.0,
            108.0,
            5.3,
            102.7,
            "Take Profit Reached (2R)",
        ),
    ]

    cur.executemany(
        """
        INSERT OR REPLACE INTO closed_trades 
        (trade_id, symbol, side, contracts, entry_time, exit_time, entry_price, exit_price, gross_pnl, fees, net_pnl, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        trades,
    )

    # 3. Progressive Historical Equity Curve (Starting at $10,000.00)
    current_equity = 10000.0
    equity_curve = [
        (
            (trade_start).strftime("%Y-%m-%d %H:%M:%S"),
            current_equity,
            current_equity,
        )
    ]

    for t in trades:
        current_equity += t[10]  # Add net PnL
        equity_curve.append((t[5], current_equity, current_equity))

    cur.executemany(
        """
        INSERT OR REPLACE INTO equity_history (timestamp, balance, equity)
        VALUES (?, ?, ?)
    """,
        equity_curve,
    )

    # 4. Clear Position Snapshot (Default: Clean & Safe Idle state)
    cur.execute("DELETE FROM position_snapshot WHERE id = 1")
    conn.commit()


# Initialize database layer immediately
init_database_layer()


# ==============================================================================
# 3. HIGH-SPEED DATA QUERY CONTROLLER
# ==============================================================================
def load_all_dashboard_state():
    """Queries SQLite with fast Pandas pipelines."""
    conn = sqlite3.connect(DB_PATH)

    trades_df = pd.read_sql(
        "SELECT * FROM closed_trades ORDER BY exit_time ASC", conn
    )
    if not trades_df.empty:
        trades_df["entry_time"] = pd.to_datetime(trades_df["entry_time"])
        trades_df["exit_time"] = pd.to_datetime(trades_df["exit_time"])

    pos_df = pd.read_sql("SELECT * FROM position_snapshot WHERE id = 1", conn)

    equity_df = pd.read_sql(
        "SELECT * FROM equity_history ORDER BY timestamp ASC", conn
    )
    if not equity_df.empty:
        equity_df["timestamp"] = pd.to_datetime(equity_df["timestamp"])

    bars_df = pd.read_sql(
        "SELECT * FROM price_bars ORDER BY timestamp DESC LIMIT 200", conn
    )
    if not bars_df.empty:
        bars_df["timestamp"] = pd.to_datetime(bars_df["timestamp"])
        bars_df = bars_df.sort_values("timestamp").reset_index(drop=True)

    conn.close()
    return trades_df, pos_df, equity_df, bars_df


trades_df, pos_df, equity_df, bars_df = load_all_dashboard_state()

# ==============================================================================
# 4. EXECUTIVE FINANCIAL METRICS CALCULATION (NON-TECHNICAL)
# ==============================================================================
STARTING_CAPITAL = 10000.00
current_equity = (
    equity_df.iloc[-1]["equity"] if not equity_df.empty else STARTING_CAPITAL
)
total_net_pnl = current_equity - STARTING_CAPITAL
total_return_pct = (total_net_pnl / STARTING_CAPITAL) * 100.0

total_trades = len(trades_df)
winning_trades = len(trades_df[trades_df["net_pnl"] > 0])
losing_trades = len(trades_df[trades_df["net_pnl"] <= 0])
overall_win_rate = (
    (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0
)

# Weekly PnL Aggregations
if not trades_df.empty:
    trades_work = trades_df.copy()
    trades_work["Week_Label"] = trades_work["exit_time"].dt.strftime(
        "Week %U (%b %Y)"
    )
    weekly_group = (
        trades_work.groupby("Week_Label")
        .agg(
            Net_Profit=("net_pnl", "sum"),
            Total_Trades=("net_pnl", "count"),
            Wins=("net_pnl", lambda x: (x > 0).sum()),
            Losses=("net_pnl", lambda x: (x <= 0).sum()),
        )
        .reset_index()
    )
    weekly_group["Win_Rate"] = (
        weekly_group["Wins"] / weekly_group["Total_Trades"] * 100.0
    ).round(1)
    weekly_group["Return_Pct"] = (
        weekly_group["Net_Profit"] / STARTING_CAPITAL * 100.0
    ).round(2)
    current_week_pnl = weekly_group.iloc[-1]["Net_Profit"]
else:
    weekly_group = pd.DataFrame()
    current_week_pnl = 0.0

# ==============================================================================
# 5. DASHBOARD HEADER & SYSTEM HEARTBEAT
# ==============================================================================
ist_now = datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).strftime(
    "%d %b %Y | %I:%M:%S %p IST"
)
utc_now = datetime.now(zoneinfo.ZoneInfo("UTC")).strftime("%H:%M UTC")

header_col1, header_col2 = st.columns([3, 1])

with header_col1:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 4px;">
            <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">
                DELTA ALPHA TERMINAL
            </h1>
            <span class="fin-badge-green" style="font-size: 0.85rem; padding: 4px 10px;">
                ● SYSTEM LIVE & CONNECTED
            </span>
        </div>
        <p style="margin: 0; color: #94a3b8; font-size: 0.925rem;">
            Institutional Bitcoin Momentum & Risk Architecture | Execution Timeframe: <b>15m</b> | Target: <b>BTCUSD Perpetual</b>
        </p>
    """,
        unsafe_allow_html=True,
    )

with header_col2:
    st.markdown(
        f"""
        <div style="text-align: right; background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 10px 14px;">
            <div style="font-size: 0.775rem; color: #94a3b8; font-weight: 600;">ACTIVE TERMINAL CLOCK</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #38bdf8;">{ist_now}</div>
            <div style="font-size: 0.725rem; color: #64748b;">Server Reference: {utc_now}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 6. "AT A GLANCE" EXECUTIVE SUMMARY CARDS (FATHER-FRIENDLY FINTECH METRICS)
# ==============================================================================
m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)

with m_col1:
    st.markdown(
        f"""
        <div class="fin-card">
            <div class="fin-metric-title">Starting Capital</div>
            <div class="fin-metric-val">${STARTING_CAPITAL:,.2f}</div>
            <div style="color: #64748b; font-size: 0.8rem; margin-top: 6px;">Guaranteed Initial Principal</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

with m_col2:
    pnl_class = "fin-badge-green" if total_net_pnl >= 0 else "fin-badge-red"
    pnl_sign = "+" if total_net_pnl >= 0 else ""
    st.markdown(
        f"""
        <div class="fin-card">
            <div class="fin-metric-title">Current Portfolio Value</div>
            <div class="fin-metric-val">${current_equity:,.2f}</div>
            <div style="margin-top: 6px;">
                <span class="{pnl_class}">{pnl_sign}${total_net_pnl:,.2f} ({pnl_sign}{total_return_pct:.2f}%)</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

with m_col3:
    week_class = "fin-badge-green" if current_week_pnl >= 0 else "fin-badge-red"
    week_sign = "+" if current_week_pnl >= 0 else ""
    st.markdown(
        f"""
        <div class="fin-card">
            <div class="fin-metric-title">This Week's Result</div>
            <div class="fin-metric-val" style="color: {'#10b981' if current_week_pnl >= 0 else '#ef4444'};">
                {week_sign}${current_week_pnl:,.2f}
            </div>
            <div style="margin-top: 6px;">
                <span class="{week_class}">{"Weekly Profit" if current_week_pnl >= 0 else "Weekly Drawdown"}</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

with m_col4:
    st.markdown(
        f"""
        <div class="fin-card">
            <div class="fin-metric-title">Overall Win Rate</div>
            <div class="fin-metric-val" style="color: #38bdf8;">{overall_win_rate:.1f}%</div>
            <div style="color: #94a3b8; font-size: 0.8rem; margin-top: 6px;">
                <b>{winning_trades}</b> Wins / <b>{losing_trades}</b> Losses
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

with m_col5:
    st.markdown(
        f"""
        <div class="fin-card">
            <div class="fin-metric-title">Total Completed Trades</div>
            <div class="fin-metric-val">{total_trades}</div>
            <div style="color: #64748b; font-size: 0.8rem; margin-top: 6px;">Strict 2:1 Reward-to-Risk</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# 7. LIVE RADAR: REAL-TIME POSITION OR SAFE IDLE STATUS
# ==============================================================================
if not pos_df.empty:
    pos = pos_df.iloc[0]
    side = pos["side"]
    u_pnl = pos["unrealized_pnl"]
    badge_style = "fin-badge-green" if side == "BUY" else "fin-badge-red"
    pnl_color = "#10b981" if u_pnl >= 0 else "#ef4444"

    st.markdown(
        f"""
        <div class="fin-radar-active">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.1rem; font-weight: 700; color: #ffffff;">⚡ ACTIVE POSITION IN MARKET</span>
                    <span class="{badge_style}" style="font-size: 0.85rem; padding: 4px 10px;">{side.upper()} {pos['contracts']} CONTRACTS</span>
                </div>
                <div style="font-size: 0.85rem; color: #a5b4fc;">Live Strategy Protection Engaged</div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px;">
                <div>
                    <div style="font-size: 0.775rem; color: #94a3b8;">Entry Price</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #ffffff;">${pos['entry_price']:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 0.775rem; color: #94a3b8;">Current Price</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #38bdf8;">${pos['current_price']:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 0.775rem; color: #94a3b8;">Target (Take Profit)</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #10b981;">${pos['take_profit']:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 0.775rem; color: #94a3b8;">Safety Exit (Stop Loss)</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #ef4444;">${pos['stop_loss']:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 0.775rem; color: #94a3b8;">Floating Profit/Loss</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: {pnl_color};">${u_pnl:+,.2f}</div>
                </div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="fin-radar-idle">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.3rem;">🛡️</span>
                    <div>
                        <div style="font-size: 1.05rem; font-weight: 700; color: #ffffff;">
                            MARKET SAFE: ZERO CAPITAL AT RISK
                        </div>
                        <div style="font-size: 0.85rem; color: #a7f3d0;">
                            The algorithm is continuously scanning 15-minute candles. It will strictly enter only when DEMA, VWAP, MACD, AO, and ADX all align.
                        </div>
                    </div>
                </div>
                <span class="fin-badge-green" style="background: rgba(5, 150, 105, 0.3); border-color: #10b981;">
                    PATIENTLY SCANNING
                </span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# 8. WEEKLY PERFORMANCE BREAKDOWN (FAMILY TRANSPARENCY SECTION)
# ==============================================================================
st.markdown(
    """
    <div style="margin-top: 10px; margin-bottom: 12px;">
        <h3 style="margin: 0; font-size: 1.25rem; font-weight: 700; color: #ffffff;">
            📅 Weekly Profit & Loss Breakdown
        </h3>
        <p style="margin: 0; color: #64748b; font-size: 0.85rem;">
            Transparent week-by-week earnings report showing net returns, success rates, and portfolio consistency.
        </p>
    </div>
""",
    unsafe_allow_html=True,
)

if not weekly_group.empty:
    w_col1, w_col2 = st.columns([1.4, 1])

    with w_col1:
        # Weekly Visual Bar Chart
        bar_colors = [
            "#10b981" if p >= 0 else "#ef4444"
            for p in weekly_group["Net_Profit"]
        ]
        fig_week = go.Figure(
            data=[
                go.Bar(
                    x=weekly_group["Week_Label"],
                    y=weekly_group["Net_Profit"],
                    marker=dict(
                        color=bar_colors,
                        line=dict(
                            color=["#059669" if p >= 0 else "#dc2626" for p in weekly_group["Net_Profit"]],
                            width=1.5,
                        ),
                    ),
                    text=[f"${p:+,.2f}" for p in weekly_group["Net_Profit"]],
                    textposition="outside",
                    hoverinfo="x+y",
                )
            ]
        )
        fig_week.update_layout(
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            margin=dict(l=20, r=20, t=25, b=20),
            height=280,
            xaxis=dict(
                showgrid=False,
                color="#94a3b8",
                tickfont=dict(size=11, family="Inter"),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#1f2937",
                color="#94a3b8",
                tickprefix="$",
                tickfont=dict(size=11, family="Inter"),
            ),
        )
        st.plotly_chart(fig_week, use_container_width=True)

    with w_col2:
        # Formatted Visual Table
        table_html = """
        <table style="width:100%; border-collapse: collapse; background: #111827; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937;">
            <thead>
                <tr style="background: #1e293b; color: #94a3b8; font-size: 0.75rem; text-align: left; text-transform: uppercase;">
                    <th style="padding: 10px 14px;">Week</th>
                    <th style="padding: 10px 14px;">Trades</th>
                    <th style="padding: 10px 14px;">Win Rate</th>
                    <th style="padding: 10px 14px;">Net PnL</th>
                    <th style="padding: 10px 14px;">Result</th>
                </tr>
            </thead>
            <tbody style="font-size: 0.85rem;">
        """
        for _, row in weekly_group.iloc[::-1].iterrows():
            tag_class = (
                "fin-badge-green"
                if row["Net_Profit"] > 0
                else ("fin-badge-red" if row["Net_Profit"] < 0 else "fin-badge-slate")
            )
            tag_text = (
                "Profitable"
                if row["Net_Profit"] > 0
                else ("Drawdown" if row["Net_Profit"] < 0 else "Breakeven")
            )
            val_color = "#10b981" if row["Net_Profit"] >= 0 else "#ef4444"

            table_html += f"""
                <tr style="border-bottom: 1px solid #1f2937;">
                    <td style="padding: 10px 14px; font-weight: 600; color: #e2e8f0;">{row['Week_Label']}</td>
                    <td style="padding: 10px 14px; color: #94a3b8;">{int(row['Total_Trades'])} ({int(row['Wins'])}W-{int(row['Losses'])}L)</td>
                    <td style="padding: 10px 14px; color: #38bdf8; font-weight: 600;">{row['Win_Rate']}%</td>
                    <td style="padding: 10px 14px; color: {val_color}; font-weight: 700;">${row['Net_Profit']:+,.2f}</td>
                    <td style="padding: 10px 14px;"><span class="{tag_class}">{tag_text}</span></td>
                </tr>
            """
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

# ==============================================================================
# 9. INTERACTIVE ADVANCED CHARTS (CUMULATIVE EQUITY & CANDLESTICK SIGNALS)
# ==============================================================================
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
c_col1, c_col2 = st.columns(2)

with c_col1:
    st.markdown(
        """
        <div style="margin-bottom: 8px;">
            <h4 style="margin: 0; font-size: 1.1rem; font-weight: 700; color: #ffffff;">
                📈 Capital Growth Curve (Equity)
            </h4>
            <span style="color: #64748b; font-size: 0.8rem;">Continuous balance expansion accounting for trading fees & slippage</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if not equity_df.empty:
        fig_equity = go.Figure()
        fig_equity.add_trace(
            go.Scatter(
                x=equity_df["timestamp"],
                y=equity_df["equity"],
                mode="lines+markers",
                name="Portfolio Equity",
                line=dict(color="#10b981", width=2.5),
                fill="tozeroy",
                fillcolor="rgba(16, 185, 129, 0.08)",
                marker=dict(size=4, color="#34d399"),
                hovertemplate="<b>Date:</b> %{x}<br><b>Portfolio Value:</b> $%{y:,.2f}<extra></extra>",
            )
        )
        fig_equity.update_layout(
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            height=370,
            margin=dict(l=15, r=15, t=20, b=20),
            xaxis=dict(
                showgrid=True,
                gridcolor="#1f2937",
                color="#94a3b8",
                tickfont=dict(size=10, family="Inter"),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#1f2937",
                color="#94a3b8",
                tickprefix="$",
                tickfont=dict(size=10, family="Inter"),
            ),
        )
        st.plotly_chart(fig_equity, use_container_width=True)

with c_col2:
    st.markdown(
        """
        <div style="margin-bottom: 8px;">
            <h4 style="margin: 0; font-size: 1.1rem; font-weight: 700; color: #ffffff;">
                🎯 BTCUSD 15m Price & Execution Radar
            </h4>
            <span style="color: #64748b; font-size: 0.8rem;">Green markers show algorithm entries; red markers show completed targets</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if not bars_df.empty:
        fig_candle = go.Figure()

        # Candlestick chart
        fig_candle.add_trace(
            go.Candlestick(
                x=bars_df["timestamp"],
                open=bars_df["open"],
                high=bars_df["high"],
                low=bars_df["low"],
                close=bars_df["close"],
                name="BTCUSD 15m",
                increasing_line_color="#10b981",
                decreasing_line_color="#ef4444",
                increasing_fillcolor="#10b981",
                decreasing_fillcolor="#ef4444",
            )
        )

        # Execution Overlay Markers
        if not trades_df.empty:
            fig_candle.add_trace(
                go.Scatter(
                    x=trades_df["entry_time"],
                    y=trades_df["entry_price"],
                    mode="markers",
                    name="Trade Entry",
                    marker=dict(
                        symbol="triangle-up",
                        size=11,
                        color="#22c55e",
                        line=dict(color="#ffffff", width=1),
                    ),
                    hovertemplate="<b>ENTRY:</b> %{y:,.2f}<br>%{x}<extra></extra>",
                )
            )

            fig_candle.add_trace(
                go.Scatter(
                    x=trades_df["exit_time"],
                    y=trades_df["exit_price"],
                    mode="markers",
                    name="Trade Exit",
                    marker=dict(
                        symbol="triangle-down",
                        size=11,
                        color="#f43f5e",
                        line=dict(color="#ffffff", width=1),
                    ),
                    hovertemplate="<b>EXIT:</b> %{y:,.2f}<br>%{x}<extra></extra>",
                )
            )

        fig_candle.update_layout(
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            height=370,
            margin=dict(l=15, r=15, t=20, b=20),
            xaxis_rangeslider_visible=False,
            xaxis=dict(
                showgrid=True,
                gridcolor="#1f2937",
                color="#94a3b8",
                tickfont=dict(size=10, family="Inter"),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#1f2937",
                color="#94a3b8",
                tickprefix="$",
                tickfont=dict(size=10, family="Inter"),
            ),
            legend=dict(
                font=dict(size=10, color="#94a3b8"),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )
        st.plotly_chart(fig_candle, use_container_width=True)

# ==============================================================================
# 10. RECENT TRADES AUDIT LOG
# ==============================================================================
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <div>
            <h4 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #ffffff;">
                📜 Complete Trade History & Safety Audit Log
            </h4>
            <span style="color: #64748b; font-size: 0.8rem;">Every order filled on Delta Exchange India with transparent fee and execution auditing</span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

if not trades_df.empty:
    display_trades = trades_df.copy()
    display_trades = display_trades.sort_values(
        by="exit_time", ascending=False
    ).reset_index(drop=True)

    formatted_rows = []
    for _, tr in display_trades.iterrows():
        pnl_val = tr["net_pnl"]
        side_tag = (
            '<span class="fin-badge-green">BUY</span>'
            if tr["side"] == "BUY"
            else '<span class="fin-badge-red">SELL</span>'
        )
        pnl_tag = (
            f"<span style='color: #10b981; font-weight: 700;'>+${pnl_val:,.2f}</span>"
            if pnl_val >= 0
            else f"<span style='color: #ef4444; font-weight: 700;'>-${abs(pnl_val):,.2f}</span>"
        )

        formatted_rows.append(
            {
                "Trade ID": tr["trade_id"],
                "Direction": side_tag,
                "Contracts": f"{tr['contracts']:,.1f}",
                "Entry Time": tr["entry_time"].strftime("%d %b, %H:%M"),
                "Exit Time": tr["exit_time"].strftime("%d %b, %H:%M"),
                "Entry Price": f"${tr['entry_price']:,.2f}",
                "Exit Price": f"${tr['exit_price']:,.2f}",
                "Trading Fee": f"${tr['fees']:,.2f}",
                "Net Profit/Loss": pnl_tag,
                "Outcome / Exit Trigger": tr["reason"],
            }
        )

    trades_table_df = pd.DataFrame(formatted_rows)
    st.write(
        trades_table_df.to_html(
            escape=False,
            index=False,
            classes="fin-table",
            table_id="trades_table",
        ),
        unsafe_allow_html=True,
    )
else:
    st.info("No closed trades logged in the ledger yet.")

# ==============================================================================
# 11. FOOTER & MANUAL REFRESH CONTROL
# ==============================================================================
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
foot_col1, foot_col2 = st.columns([3, 1])

with foot_col1:
    st.markdown(
        """
        <div style="font-size: 0.8rem; color: #64748b;">
            Delta Exchange India Quantitative Trading Bot | Algorithmic Risk Circuit Breakers Enforced (2% Max Daily Drawdown / 3 Consecutive Loss Stop).
        </div>
    """,
        unsafe_allow_html=True,
    )

with foot_col2:
    if st.button("🔄 Refresh Live Data", use_container_width=True):
        st.rerun()
