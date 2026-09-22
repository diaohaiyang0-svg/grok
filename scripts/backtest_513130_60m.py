#!/usr/bin/env python3
"""60-minute Chanlun backtest on 513130 with the locked engine.

Two layers, same rules as daily:
1. Full-sample structure path: each confirmed zhongshu and the first
   non-overlapping bi that leaves it.
2. Causal walk-forward: rebuild structure on bars[:i+1] and record the
   first time close leaves the then-latest zhongshu.

No extra thresholds. Leave = close (walk-forward) or next-bi range
(full-sample) no longer overlaps [ZD, ZG].
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from chanlun.engine import analyze_ohlc

CODE = "513130"
TDX_CSV = ROOT / "data" / "tdx" / "513130_60m.csv"
OUT_JSON = ROOT / "results" / "513130_60m_backtest.json"
OUT_MD = ROOT / "results" / "513130_60m_backtest.md"


def load_60m() -> pd.DataFrame:
    if not TDX_CSV.exists():
        raise SystemExit(f"missing {TDX_CSV}; run scripts/fetch_513130_tdx_60m.py")
    raw = pd.read_csv(TDX_CSV)
    df = raw.rename(columns={"trade_time": "time"})[
        ["time", "open", "high", "low", "close"]
    ].copy()
    df["time"] = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d %H:%M")
    return df.drop_duplicates("time").sort_values("time").reset_index(drop=True)


def pos_vs(close: float, zd: float, zg: float) -> str:
    if zd <= close <= zg:
        return "inside"
    if close > zg:
        return "above"
    return "below"


def fwd_stats(df: pd.DataFrame, start_i: int, zd: float, zg: float, direction: str) -> dict:
    if start_i >= len(df) - 1:
        return {
            "bars_fwd": 0,
            "returned": False,
            "return_bar": None,
            "return_time": None,
            "ext_px": None,
            "ext_time": None,
            "ext_pct": None,
            "ret_5": None,
            "ret_20": None,
            "ret_40": None,
            "mfe_pct": None,
            "mae_pct": None,
        }
    entry = float(df["close"].iloc[start_i])
    highs = df["high"].iloc[start_i + 1 :]
    lows = df["low"].iloc[start_i + 1 :]
    closes = df["close"].iloc[start_i + 1 :]
    times = df["time"].iloc[start_i + 1 :]
    returned = False
    return_bar = None
    return_time = None
    for k, px in enumerate(closes):
        if zd <= float(px) <= zg:
            returned = True
            return_bar = k + 1
            return_time = str(times.iloc[k])
            break
    window = slice(0, return_bar) if returned else slice(None)
    if direction == "below":
        ext_px = float(lows.iloc[window].min()) if len(lows.iloc[window]) else entry
        ext_i = int(lows.iloc[window].values.argmin()) if len(lows.iloc[window]) else 0
        ext_pct = (entry - ext_px) / entry * 100.0
        mfe = (entry - float(lows.iloc[window].min())) / entry * 100.0 if len(lows.iloc[window]) else 0.0
        mae = (float(highs.iloc[window].max()) - entry) / entry * 100.0 if len(highs.iloc[window]) else 0.0
    else:
        ext_px = float(highs.iloc[window].max()) if len(highs.iloc[window]) else entry
        ext_i = int(highs.iloc[window].values.argmax()) if len(highs.iloc[window]) else 0
        ext_pct = (ext_px - entry) / entry * 100.0
        mfe = (float(highs.iloc[window].max()) - entry) / entry * 100.0 if len(highs.iloc[window]) else 0.0
        mae = (entry - float(lows.iloc[window].min())) / entry * 100.0 if len(lows.iloc[window]) else 0.0
    ext_time = str(times.iloc[ext_i]) if len(times.iloc[window]) else None

    def ret_n(n: int):
        j = start_i + n
        if j >= len(df):
            return None
        return (float(df["close"].iloc[j]) - entry) / entry * 100.0

    return {
        "bars_fwd": int(len(closes)),
        "returned": returned,
        "return_bar": return_bar,
        "return_time": return_time,
        "ext_px": round(ext_px, 4),
        "ext_time": ext_time,
        "ext_pct": round(ext_pct, 2),
        "ret_5": None if ret_n(5) is None else round(ret_n(5), 2),
        "ret_20": None if ret_n(20) is None else round(ret_n(20), 2),
        "ret_40": None if ret_n(40) is None else round(ret_n(40), 2),
        "mfe_pct": round(mfe, 2),
        "mae_pct": round(mae, 2),
        "entry_px": round(entry, 4),
    }


def full_sample_leaves(df: pd.DataFrame, result: dict) -> list[dict]:
    bis = result["bis"]
    zss = result["zhongshu"]
    time_to_i = {str(t): i for i, t in enumerate(df["time"])}
    rows = []
    for zi, zs in enumerate(zss):
        leave_i = zs.end_bi + 1
        row = {
            "zs": zi,
            "zd": round(float(zs.zd), 4),
            "zg": round(float(zs.zg), 4),
            "width": round(float(zs.zg) - float(zs.zd), 4),
            "zs_start": str(zs.start_time),
            "zs_end": str(zs.end_time),
            "bi_span": f"{zs.start_bi}:{zs.end_bi}",
            "leave": None,
        }
        if leave_i >= len(bis):
            row["leave"] = "none_yet"
            rows.append(row)
            continue
        bi = bis[leave_i]
        if bi.high <= zs.zd:
            direction = "below"
        elif bi.low >= zs.zg:
            direction = "above"
        else:
            direction = "unclear"
        end_i = time_to_i.get(str(bi.end.time))
        stats = fwd_stats(df, end_i, float(zs.zd), float(zs.zg), direction) if end_i is not None else {}
        row.update(
            {
                "leave": direction,
                "leave_bi": leave_i,
                "leave_dir_bi": bi.direction,
                "leave_start": str(bi.start.time),
                "leave_end": str(bi.end.time),
                "leave_start_px": round(float(bi.start.price), 4),
                "leave_end_px": round(float(bi.end.price), 4),
                **{f"path_{k}": v for k, v in stats.items()},
            }
        )
        rows.append(row)
    return rows


def walk_forward_leaves(df: pd.DataFrame, step: int = 1, warmup: int = 80) -> list[dict]:
    events = []
    prev = None
    n = len(df)
    for i in range(warmup, n, step):
        result = analyze_ohlc(df.iloc[: i + 1])
        zss = result["zhongshu"]
        if not zss:
            prev = None
            continue
        zs = zss[-1]
        close = float(df["close"].iloc[i])
        pos = pos_vs(close, float(zs.zd), float(zs.zg))
        key = (
            str(zs.start_time),
            round(float(zs.zd), 4),
            round(float(zs.zg), 4),
        )
        cur = {"key": key, "pos": pos, "i": i, "zs": zs, "close": close}
        if prev is not None and prev["key"] == key and prev["pos"] != pos:
            if prev["pos"] == "inside" and pos in ("above", "below"):
                stats = fwd_stats(df, i, float(zs.zd), float(zs.zg), pos)
                events.append(
                    {
                        "kind": "leave",
                        "time": str(df["time"].iloc[i]),
                        "bar": i,
                        "direction": pos,
                        "zd": round(float(zs.zd), 4),
                        "zg": round(float(zs.zg), 4),
                        "zs_start": str(zs.start_time),
                        "zs_end": str(zs.end_time),
                        "close": round(close, 4),
                        **stats,
                    }
                )
            elif prev["pos"] in ("above", "below") and pos == "inside":
                events.append(
                    {
                        "kind": "reenter",
                        "time": str(df["time"].iloc[i]),
                        "bar": i,
                        "from": prev["pos"],
                        "zd": round(float(zs.zd), 4),
                        "zg": round(float(zs.zg), 4),
                        "close": round(close, 4),
                    }
                )
        prev = cur
    return events


def summarize(leaves: list[dict], wf: list[dict]) -> dict:
    fs = [x for x in leaves if x.get("leave") in ("above", "below")]
    wf_leave = [x for x in wf if x.get("kind") == "leave"]
    def pack(items, ret_key="returned", dir_key="direction"):
        if not items:
            return {"n": 0}
        below = [x for x in items if x.get(dir_key) == "below" or x.get("leave") == "below"]
        above = [x for x in items if x.get(dir_key) == "above" or x.get("leave") == "above"]
        def avg(xs, k):
            vals = [x[k] for x in xs if x.get(k) is not None]
            return None if not vals else round(sum(vals) / len(vals), 2)
        return {
            "n": len(items),
            "below": len(below),
            "above": len(above),
            "returned": sum(1 for x in items if x.get(ret_key) or x.get("path_returned")),
            "avg_mfe_below": avg(below, "mfe_pct") or avg(below, "path_mfe_pct"),
            "avg_mae_below": avg(below, "mae_pct") or avg(below, "path_mae_pct"),
            "avg_mfe_above": avg(above, "mfe_pct") or avg(above, "path_mfe_pct"),
            "avg_mae_above": avg(above, "mae_pct") or avg(above, "path_mae_pct"),
            "avg_ret20_below": avg(below, "ret_20") or avg(below, "path_ret_20"),
            "avg_ret20_above": avg(above, "ret_20") or avg(above, "path_ret_20"),
        }
    return {
        "full_sample_leaves": pack(fs, ret_key="path_returned", dir_key="leave"),
        "walk_forward_leaves": pack(wf_leave, ret_key="returned", dir_key="direction"),
        "walk_forward_reenter": sum(1 for x in wf if x.get("kind") == "reenter"),
    }


def md_table(rows: list[dict], cols: list[tuple[str, str]]) -> list[str]:
    head = "| " + " | ".join(c[0] for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    lines = [head, sep]
    for r in rows:
        vals = []
        for _, k in cols:
            v = r.get(k, "")
            if v is None:
                v = ""
            vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def main() -> None:
    df = load_60m()
    result = analyze_ohlc(df)
    leaves = full_sample_leaves(df, result)
    print("walk-forward on every bar (warmup 80) ...")
    wf = walk_forward_leaves(df, step=1, warmup=80)
    summary = summarize(leaves, wf)
    last_close = float(df["close"].iloc[-1])
    last_zs = result["zhongshu"][-1] if result["zhongshu"] else None
    last_bi = result["bis"][-1] if result["bis"] else None

    payload = {
        "symbol": CODE,
        "period": "60m",
        "source": "TDX pytdxdata NONE",
        "bars": int(len(df)),
        "first": str(df["time"].iloc[0]),
        "last": str(df["time"].iloc[-1]),
        "last_close": last_close,
        "bi_count": len(result["bis"]),
        "zhongshu_count": len(result["zhongshu"]),
        "rules": {
            "merge": "inclusion in trend direction",
            "fenxing": "3 independent merged bars",
            "bi": "opposite fenxing, gap >= 4 merged bars",
            "zhongshu": "3 consecutive bis with common overlap",
            "leave_full_sample": "first bi after zs.end_bi whose range does not overlap [ZD,ZG]",
            "leave_walk_forward": "first close that exits the then-latest [ZD,ZG]",
        },
        "full_sample_leaves": leaves,
        "walk_forward_events": wf,
        "summary": summary,
        "now": {
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
            },
            "vs_last_zhongshu": pos_vs(last_close, last_zs.zd, last_zs.zg) if last_zs else None,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    fs_sum = summary["full_sample_leaves"]
    wf_sum = summary["walk_forward_leaves"]
    lines = [
        "# 513130 60分钟缠论回测（锁定规则）",
        "",
        f"- 数据：TDX 不复权 60 分钟 {df['time'].iloc[0]} → {df['time'].iloc[-1]}，{len(df)} 根",
        f"- 全样本结构：笔 {len(result['bis'])}，中枢 {len(result['zhongshu'])}",
        "- 规则与日线同一套：包含合并 → 分型 → 间隔≥4 的笔 → 三笔重叠中枢",
        "- 回测只量中枢离开后的路径，不加均线、不加阈值、不做预测模型",
        "",
        "## 1. 全样本：每个中枢的第一笔离开",
        "",
        "离开定义：中枢延伸结束后的下一笔，价格区间与 [ZD, ZG] 不再重叠。",
        "随后路径看到价格重新回到该中枢区间为止（或走到样本末）。",
        "",
    ]
    cols = [
        ("中枢", "zs"),
        ("ZD", "zd"),
        ("ZG", "zg"),
        ("宽度", "width"),
        ("离开", "leave"),
        ("离开笔结束", "leave_end"),
        ("离开价", "leave_end_px"),
        ("是否回抽进中枢", "path_returned"),
        ("回抽根数", "path_return_bar"),
        ("同向极值%", "path_ext_pct"),
        ("MFE%", "path_mfe_pct"),
        ("MAE%", "path_mae_pct"),
        ("+20根收益%", "path_ret_20"),
    ]
    lines += md_table(leaves, cols)
    lines += [
        "",
        f"- 已完成离开：{fs_sum.get('n', 0)}（下 {fs_sum.get('below', 0)} / 上 {fs_sum.get('above', 0)}）",
        f"- 离开后重新走进原中枢：{fs_sum.get('returned', 0)} / {fs_sum.get('n', 0)}",
        f"- 向下离开后平均有利波动 MFE {fs_sum.get('avg_mfe_below')}%，平均回吐 MAE {fs_sum.get('avg_mae_below')}%，20 根收益 {fs_sum.get('avg_ret20_below')}%",
        f"- 向上离开后平均有利波动 MFE {fs_sum.get('avg_mfe_above')}%，平均回吐 MAE {fs_sum.get('avg_mae_above')}%，20 根收益 {fs_sum.get('avg_ret20_above')}%",
        "",
        "## 2. 走步：当时能看到的最新中枢",
        "",
        "每根 60 分钟 K 只用当时及之前的数据重建结构。",
        "信号：收盘第一次离开当时最新中枢的 [ZD, ZG]。",
        "这比全样本更严，因为当时中枢区间可能还没被后来的笔收窄。",
        "",
        f"- 走步离开次数：{wf_sum.get('n', 0)}（下 {wf_sum.get('below', 0)} / 上 {wf_sum.get('above', 0)}）",
        f"- 其中重新进入同一中枢：{summary.get('walk_forward_reenter', 0)} 次",
        f"- 向下离开后平均 MFE {wf_sum.get('avg_mfe_below')}%，MAE {wf_sum.get('avg_mae_below')}%，20 根收益 {wf_sum.get('avg_ret20_below')}%",
        f"- 向上离开后平均 MFE {wf_sum.get('avg_mfe_above')}%，MAE {wf_sum.get('avg_mae_above')}%，20 根收益 {wf_sum.get('avg_ret20_above')}%",
        "",
    ]
    wf_rows = []
    for e in wf:
        if e.get("kind") != "leave":
            continue
        wf_rows.append(
            {
                "time": e["time"],
                "direction": e["direction"],
                "zd": e["zd"],
                "zg": e["zg"],
                "close": e["close"],
                "returned": e["returned"],
                "return_bar": e["return_bar"],
                "mfe_pct": e["mfe_pct"],
                "mae_pct": e["mae_pct"],
                "ret_20": e["ret_20"],
                "ext_px": e["ext_px"],
            }
        )
    lines += md_table(
        wf_rows,
        [
            ("时间", "time"),
            ("方向", "direction"),
            ("ZD", "zd"),
            ("ZG", "zg"),
            ("当时收盘", "close"),
            ("回抽", "returned"),
            ("回抽根数", "return_bar"),
            ("MFE%", "mfe_pct"),
            ("MAE%", "mae_pct"),
            ("+20根%", "ret_20"),
            ("同向极值", "ext_px"),
        ],
    )
    lines += [
        "",
        "## 3. 现阶段套进回测口径",
        "",
    ]
    if last_zs and last_bi:
        lines += [
            f"- 最近确认中枢：{last_zs.zd:.3f}–{last_zs.zg:.3f}（{last_zs.start_time} ~ {last_zs.end_time}）",
            f"- 全样本第一笔不再重叠：bi[{last_zs.end_bi + 1}]，真正打离中枢的是后续向下笔",
            f"- 最近一笔：{last_bi.direction} {last_bi.start.time} {last_bi.start.price:.3f} → {last_bi.end.time} {last_bi.end.price:.3f}",
            f"- 现价 {last_close:.3f} 相对该中枢：{pos_vs(last_close, last_zs.zd, last_zs.zg)}",
            "- 现价还没回到 0.572。按回测口径，这仍是最近一次向下离开后的反抽，不是新的向上离开。",
        ]
    lines += [
        "",
        "## 4. 怎么读这些数字",
        "",
        "- 60 分钟中枢比日线密，离开次数也更多。宽度经常很窄（有的只有 0.001），离开几乎必然发生，这种中枢不能当大级别仓位锚。",
        "- 回测问的是：离开之后，同向极值是否先出现、要不要很快走回中枢。不是问「下根会涨还是跌」。",
        "- 走步离开如果大量回抽进原中枢，说明这个周期上「离开」噪声大，不宜当开仓扳机。",
        "- 「下手」仍然只看结构位置：现价在最近确认中枢下方的反抽段。回测没有给出一个已经验证有效的买入公式。",
        "",
        f"结果文件：`{OUT_JSON.relative_to(ROOT)}`、`{OUT_MD.relative_to(ROOT)}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"walk-forward leave events: {len([e for e in wf if e.get('kind')=='leave'])}")


if __name__ == "__main__":
    main()
