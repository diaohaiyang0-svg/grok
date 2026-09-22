"""Minimal Chanlun structure engine.

Rules (locked):
- Merge overlapping K-lines in the current trend direction.
- Fenxing needs 3 independent merged bars.
- A bi connects opposite fenxings with at least 4 merged bars from start to end
  (classic 5-bar style: two fenxings share no bars and there are >=1 bars between).
- Zhongshu: three consecutive bis whose price ranges have a common overlap.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Bar:
    time: Any
    high: float
    low: float
    open: float
    close: float
    raw_index: int


@dataclass
class Fenxing:
    kind: str  # "top" | "bottom"
    index: int
    time: Any
    price: float


@dataclass
class Bi:
    direction: str  # "up" | "down"
    start: Fenxing
    end: Fenxing
    high: float
    low: float

    @property
    def range(self) -> tuple[float, float]:
        return self.low, self.high


@dataclass
class Zhongshu:
    start_bi: int
    end_bi: int
    zg: float
    zd: float
    start_time: Any
    end_time: Any


def _as_bars(df) -> list[Bar]:
    rows = []
    for i, row in enumerate(df.itertuples(index=False)):
        rows.append(
            Bar(
                time=getattr(row, "time"),
                high=float(getattr(row, "high")),
                low=float(getattr(row, "low")),
                open=float(getattr(row, "open")),
                close=float(getattr(row, "close")),
                raw_index=i,
            )
        )
    return rows


def merge_klines(bars: list[Bar]) -> list[Bar]:
    if not bars:
        return []
    merged: list[Bar] = [bars[0]]
    direction = 0  # 1 up, -1 down, 0 unknown

    for bar in bars[1:]:
        last = merged[-1]
        contained = bar.high <= last.high and bar.low >= last.low
        contains = bar.high >= last.high and bar.low <= last.low
        if not (contained or contains):
            if bar.high > last.high and bar.low > last.low:
                direction = 1
            elif bar.high < last.high and bar.low < last.low:
                direction = -1
            merged.append(bar)
            continue

        if direction >= 0:
            high = max(last.high, bar.high)
            low = max(last.low, bar.low)
        else:
            high = min(last.high, bar.high)
            low = min(last.low, bar.low)
        merged[-1] = Bar(
            time=bar.time,
            high=high,
            low=low,
            open=last.open,
            close=bar.close,
            raw_index=bar.raw_index,
        )
    return merged


def find_fenxing(merged: list[Bar]) -> list[Fenxing]:
    out: list[Fenxing] = []
    for i in range(1, len(merged) - 1):
        a, b, c = merged[i - 1], merged[i], merged[i + 1]
        if b.high > a.high and b.high > c.high and b.low > a.low and b.low > c.low:
            out.append(Fenxing("top", i, b.time, b.high))
        elif b.low < a.low and b.low < c.low and b.high < a.high and b.high < c.high:
            out.append(Fenxing("bottom", i, b.time, b.low))
    return out


def build_bis(fxs: list[Fenxing]) -> list[Bi]:
    cleaned: list[Fenxing] = []
    for fx in fxs:
        if not cleaned:
            cleaned.append(fx)
            continue
        last = cleaned[-1]
        if fx.kind == last.kind:
            if fx.kind == "top" and fx.price >= last.price:
                cleaned[-1] = fx
            elif fx.kind == "bottom" and fx.price <= last.price:
                cleaned[-1] = fx
            continue
        if fx.index - last.index < 4:
            if fx.kind == "top" and fx.price >= last.price:
                cleaned[-1] = fx
            elif fx.kind == "bottom" and fx.price <= last.price:
                cleaned[-1] = fx
            continue
        cleaned.append(fx)

    bis: list[Bi] = []
    for i in range(len(cleaned) - 1):
        a, b = cleaned[i], cleaned[i + 1]
        if a.kind == b.kind:
            continue
        if b.index - a.index < 4:
            continue
        direction = "up" if a.kind == "bottom" and b.kind == "top" else "down"
        if direction == "up" and b.price <= a.price:
            continue
        if direction == "down" and b.price >= a.price:
            continue
        bis.append(
            Bi(
                direction=direction,
                start=a,
                end=b,
                high=max(a.price, b.price),
                low=min(a.price, b.price),
            )
        )
    return bis


def overlap(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float] | None:
    lo = max(a[0], b[0])
    hi = min(a[1], b[1])
    if lo < hi:
        return lo, hi
    return None


def build_zhongshu(bis: list[Bi]) -> list[Zhongshu]:
    zs: list[Zhongshu] = []
    i = 0
    while i + 2 < len(bis):
        o12 = overlap(bis[i].range, bis[i + 1].range)
        if not o12:
            i += 1
            continue
        o123 = overlap(o12, bis[i + 2].range)
        if not o123:
            i += 1
            continue
        zd, zg = o123
        end = i + 2
        while end + 1 < len(bis):
            nxt = overlap((zd, zg), bis[end + 1].range)
            if not nxt:
                break
            zd, zg = nxt
            end += 1
        zs.append(
            Zhongshu(
                start_bi=i,
                end_bi=end,
                zg=zg,
                zd=zd,
                start_time=bis[i].start.time,
                end_time=bis[end].end.time,
            )
        )
        i = end + 1
    return zs


def describe_now(bis: list[Bi], zss: list[Zhongshu], last_close: float) -> str:
    if not bis:
        return "笔尚未形成，结构不足以定位。"
    last = bis[-1]
    lines = [
        f"最近一笔：{last.direction} {last.start.time} {last.start.price:.3f} -> {last.end.time} {last.end.price:.3f}"
    ]
    if not zss:
        lines.append("尚无确认中枢。当前更像单边趋势段或段未完成。")
        return "\n".join(lines)
    zs = zss[-1]
    lines.append(
        f"最近中枢：ZD {zs.zd:.3f} / ZG {zs.zg:.3f}，起止 {zs.start_time} ~ {zs.end_time}"
    )
    if zs.zd <= last_close <= zs.zg:
        lines.append(f"收盘 {last_close:.3f} 在中枢内，当前是震荡/盘整位置，不是追趋势段的位置。")
    elif last_close > zs.zg:
        lines.append(f"收盘 {last_close:.3f} 在中枢上方，看做离开中枢后的上方评估。")
    else:
        lines.append(f"收盘 {last_close:.3f} 在中枢下方，看做离开中枢后的下方评估。")
    return "\n".join(lines)


def analyze_ohlc(df) -> dict:
    bars = _as_bars(df)
    merged = merge_klines(bars)
    fxs = find_fenxing(merged)
    bis = build_bis(fxs)
    zss = build_zhongshu(bis)
    last_close = float(df["close"].iloc[-1])
    return {
        "merged_bars": len(merged),
        "fenxing": fxs,
        "bis": bis,
        "zhongshu": zss,
        "last_close": last_close,
        "now": describe_now(bis, zss, last_close),
    }
