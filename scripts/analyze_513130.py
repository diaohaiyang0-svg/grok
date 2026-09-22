#!/usr/bin/env python3
"""Analyze 513130 with the workspace Chanlun engine.

Only Tongdaxin unadjusted bars. No East Money / akshare fallback.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from chanlun.engine import analyze_ohlc

CODE = "513130"
NAME = "恒生科技ETF华泰柏瑞"
TDX_CSV = ROOT / "data" / "tdx" / "513130_daily.csv"
YEAR_DIR = ROOT / "data" / "tdx" / "by_year"


def _to_ohlc(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.rename(columns={"trade_date": "time"})[["time", "open", "high", "low", "close"]].copy()
    df["time"] = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d")
    return df.drop_duplicates("time").sort_values("time").reset_index(drop=True)


def load_daily() -> tuple[pd.DataFrame, str]:
    if TDX_CSV.exists():
        return _to_ohlc(pd.read_csv(TDX_CSV)), f"TDX {TDX_CSV}"
    parts = sorted(YEAR_DIR.glob("513130_*.csv"))
    if parts:
        raw = pd.concat((pd.read_csv(p) for p in parts), ignore_index=True)
        return _to_ohlc(raw), f"TDX year shards {YEAR_DIR}"
    raise SystemExit(
        "missing TDX daily bars; run scripts/fetch_513130_tdx.py "
        "(East Money / akshare is not used)"
    )


def main() -> None:
    print(f"=== {CODE} {NAME} 日线缠论结构 ===")
    df, source = load_daily()
    print(f"数据源 {source}")
    print(f"K线 {len(df)} 根  {df['time'].iloc[0]} -> {df['time'].iloc[-1]}  最新收盘 {df['close'].iloc[-1]:.3f}")

    result = analyze_ohlc(df)
    print(f"合并后K线 {result['merged_bars']}  分型 {len(result['fenxing'])}  笔 {len(result['bis'])}  中枢 {len(result['zhongshu'])}")
    print()
    print("--- 历史笔 ---")
    for i, bi in enumerate(result["bis"]):
        print(
            f"{i:02d} {bi.direction:4s} {bi.start.time} {bi.start.price:.3f} -> {bi.end.time} {bi.end.price:.3f}"
        )
    print()
    print("--- 历史中枢 ---")
    if not result["zhongshu"]:
        print("（无）")
    for i, zs in enumerate(result["zhongshu"]):
        print(
            f"{i:02d} ZD {zs.zd:.3f} ZG {zs.zg:.3f}  {zs.start_time} -> {zs.end_time}  bi[{zs.start_bi}:{zs.end_bi}]"
        )
    print()
    print("--- 现阶段 ---")
    print(result["now"])


if __name__ == "__main__":
    main()
