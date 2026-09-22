#!/usr/bin/env python3
"""Analyze 513130 60-minute bars with the locked Chanlun engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from chanlun.engine import analyze_ohlc

CODE = "513130"
NAME = "恒生科技ETF华泰柏瑞"
TDX_CSV = ROOT / "data" / "tdx" / "513130_60m.csv"
OUT_JSON = ROOT / "results" / "513130_60m_now.json"
OUT_MD = ROOT / "results" / "513130_60m_replay.md"


def load_60m() -> pd.DataFrame:
    if not TDX_CSV.exists():
        raise SystemExit(f"missing {TDX_CSV}; run scripts/fetch_513130_tdx_60m.py")
    raw = pd.read_csv(TDX_CSV)
    df = raw.rename(columns={"trade_time": "time"})[["time", "open", "high", "low", "close"]].copy()
    df["time"] = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d %H:%M")
    return df.drop_duplicates("time").sort_values("time").reset_index(drop=True)


def same_dir_pairs(bis):
    pairs = []
    for i in range(len(bis) - 1):
        if bis[i].direction == bis[i + 1].direction:
            pairs.append(
                {
                    "a": i,
                    "b": i + 1,
                    "direction": bis[i].direction,
                    "a_end": str(bis[i].end.time),
                    "b_start": str(bis[i + 1].start.time),
                }
            )
    return pairs


def swing_points(df: pd.DataFrame, window: int = 40):
    highs, lows = [], []
    h = df["high"].values
    l = df["low"].values
    t = df["time"].values
    n = len(df)
    for i in range(window, n - window):
        sl = slice(i - window, i + window + 1)
        if h[i] == h[sl].max() and list(h[sl]).count(h[i]) == 1:
            highs.append((str(t[i]), float(h[i])))
        if l[i] == l[sl].min() and list(l[sl]).count(l[i]) == 1:
            lows.append((str(t[i]), float(l[i])))
    return highs, lows


def match_point(pt_time, pt_px, ends, tol_px=0.008, tol_bars_time=None):
    for et, ep in ends:
        if abs(ep - pt_px) <= tol_px:
            return True
    return False


def main() -> None:
    print(f"=== {CODE} {NAME} 60分钟缠论结构 ===")
    df = load_60m()
    print(f"数据源 TDX {TDX_CSV}")
    print(f"K线 {len(df)} 根  {df['time'].iloc[0]} -> {df['time'].iloc[-1]}  最新收盘 {df['close'].iloc[-1]:.3f}")

    result = analyze_ohlc(df)
    bis = result["bis"]
    zss = result["zhongshu"]
    pairs = same_dir_pairs(bis)
    print(f"合并后K线 {result['merged_bars']}  分型 {len(result['fenxing'])}  笔 {len(bis)}  中枢 {len(zss)}")
    print()
    print("--- 历史笔（最近 20）---")
    start_i = max(0, len(bis) - 20)
    for i, bi in enumerate(bis):
        if i < start_i:
            continue
        print(f"{i:03d} {bi.direction:4s} {bi.start.time} {bi.start.price:.3f} -> {bi.end.time} {bi.end.price:.3f}")
    print()
    print("--- 历史中枢 ---")
    if not zss:
        print("（无）")
    for i, zs in enumerate(zss):
        print(
            f"{i:02d} ZD {zs.zd:.3f} ZG {zs.zg:.3f}  {zs.start_time} -> {zs.end_time}  bi[{zs.start_bi}:{zs.end_bi}]"
        )
    print()
    print("--- 现阶段 ---")
    print(result["now"])
    print()
    print("--- 同向笔 ---")
    print(pairs if pairs else "无")

    ends = []
    for bi in bis:
        ends.append((str(bi.start.time), float(bi.start.price)))
        ends.append((str(bi.end.time), float(bi.end.price)))
    highs, lows = swing_points(df, window=40)
    hit_h = sum(1 for t, p in highs if match_point(t, p, ends))
    hit_l = sum(1 for t, p in lows if match_point(t, p, ends))

    last_bi = bis[-1] if bis else None
    last_zs = zss[-1] if zss else None
    last_close = float(df["close"].iloc[-1])
    vs = None
    if last_zs:
        if last_zs.zd <= last_close <= last_zs.zg:
            vs = "inside"
        elif last_close > last_zs.zg:
            vs = "above"
        else:
            vs = "below"

    payload = {
        "symbol": CODE,
        "source": "TDX pytdxdata NONE 60m",
        "bars": int(len(df)),
        "first": str(df["time"].iloc[0]),
        "last": str(df["time"].iloc[-1]),
        "last_close": last_close,
        "merged_bars": result["merged_bars"],
        "fenxing": len(result["fenxing"]),
        "bi_count": len(bis),
        "zhongshu_count": len(zss),
        "swing_window_bars": 40,
        "swing_high_hit": f"{hit_h}/{len(highs)}",
        "swing_low_hit": f"{hit_l}/{len(lows)}",
        "same_direction_bi_pairs": pairs,
        "last_bi": None
        if last_bi is None
        else {
            "direction": last_bi.direction,
            "start": str(last_bi.start.time),
            "start_px": float(last_bi.start.price),
            "end": str(last_bi.end.time),
            "end_px": float(last_bi.end.price),
        },
        "last_zhongshu": None
        if last_zs is None
        else {
            "zd": float(last_zs.zd),
            "zg": float(last_zs.zg),
            "start": str(last_zs.start_time),
            "end": str(last_zs.end_time),
            "start_bi": last_zs.start_bi,
            "end_bi": last_zs.end_bi,
        },
        "vs_last_zhongshu": vs,
        "daily_reference": {
            "last_bi": "down 2026-09-04 0.572 -> 2026-09-17 0.528",
            "last_zhongshu": "ZD 0.603 / ZG 0.617, 2024-10-08 ~ 2025-03-19",
            "vs_last_zhongshu": "below",
            "last_close": 0.549,
        },
        "coverage_note": "TDX online 60m starts 2024-09-02; earlier listing history is not on the server.",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# 513130 60分钟缠论回放（锁定规则）",
        "",
        f"- 数据：TDX / pytdxdata / 不复权 60 分钟 {df['time'].iloc[0]} → {df['time'].iloc[-1]}，{len(df)} 根",
        "- 覆盖说明：通达信在线 60 分钟从 2024-09-02 起；2021-06 上市至 2024-08 的 60 分钟在服务器上查不到",
        f"- 最新收盘：{last_close:.3f}",
        f"- 合并K线 {result['merged_bars']}，分型 {len(result['fenxing'])}，笔 {len(bis)}，中枢 {len(zss)}",
        f"- 40 根摆动高点被笔端覆盖：{hit_h}/{len(highs)}",
        f"- 40 根摆动低点被笔端覆盖：{hit_l}/{len(lows)}",
        "",
        "## 规则（与日线同一套）",
        "",
        "- K 线包含合并",
        "- 分型：三根独立合并 K",
        "- 笔：反向分型，间隔至少 4 根合并 K",
        "- 中枢：连续三笔价格区间有公共重叠",
        "",
        "## 现阶段（60分钟）",
        "",
        result["now"],
        "",
        "## 对照日线位置",
        "",
        "- 日线最近确认中枢：0.603–0.617（2024-10-08 ~ 2025-03-19），收盘 0.549 在其下方",
        "- 日线最近一笔：down 2026-09-04 0.572 -> 2026-09-17 0.528，9-18 至 9-22 反弹尚未确认向上笔",
    ]
    if last_zs:
        lines.append(
            f"- 60分钟最近中枢：{last_zs.zd:.3f}–{last_zs.zg:.3f}（{last_zs.start_time} ~ {last_zs.end_time}），相对该中枢：{vs}"
        )
    if last_bi:
        lines.append(
            f"- 60分钟最近一笔：{last_bi.direction} {last_bi.start.time} {last_bi.start.price:.3f} -> {last_bi.end.time} {last_bi.end.price:.3f}"
        )
    lines += [
        "",
        "## 结论口径",
        "",
        "- 这是结构定位，不是预测涨跌。",
        "- 60 分钟比日线更快确认局部笔和中枢，但不能替代日线那个更旧、更宽的中枢。",
        "- 日线仍在 0.603–0.617 中枢下方评估；60 分钟用来看这个下方段内部走到哪一笔。",
        "- 引擎若出现同向笔相连，说明中间有一笔被间隔规则丢掉，解读局部结构可用，不能当精确买卖点时钟。",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
