#!/usr/bin/env python3
"""Analyze 513130 with the workspace Chanlun engine.

Step 1: print historical bi / zhongshu so you can check whether major swings match.
Step 2: print current location from the same rules.
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


def load_daily(code: str) -> pd.DataFrame:
    import akshare as ak

    raw = ak.fund_etf_hist_em(symbol=code, period="daily", adjust="qfq")
    raw = raw.rename(
        columns={
            "日期": "time",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
        }
    )
    df = raw[["time", "open", "high", "low", "close"]].copy()
    df["time"] = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d")
    return df


def main() -> None:
    print(f"=== {CODE} {NAME} 日线缠论结构 ===")
    df = load_daily(CODE)
    print(f"K线 {len(df)} 根  {df['time'].iloc[0]} -> {df['time'].iloc[-1]}  最新收盘 {df['close'].iloc[-1]:.3f}")

    result = analyze_ohlc(df)
    print(f"合并后K线 {result['merged_bars']}  分型 {len(result['fenxing'])}  笔 {len(result['bis'])}  中枢 {len(result['zhongshu'])}")
    print()
    print("--- 历史笔（用于核对主要高低点）---")
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
    print()
    print("说明：历史有效性看笔的端点是否落在明显大波段高低点附近。")
    print("若对得上，再相信上面的现阶段描述；对不上就换规则或换级别，不要直接下手。")


if __name__ == "__main__":
    main()
