#!/usr/bin/env python3
"""Fetch 513130 daily bars via Tongdaxin, same client as a-share-radar (pytdxdata)."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pytdxdata import TdxData
from pytdxdata.models import Adjust, KlinePeriod

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tdx" / "513130_daily.csv"
META = ROOT / "data" / "tdx" / "513130_meta.json"


def bars_to_frame(bars) -> pd.DataFrame:
    rows = []
    for b in bars or []:
        year = int(getattr(b, "year", 0) or 0)
        month = int(getattr(b, "month", 0) or 0)
        day = int(getattr(b, "day", 0) or 0)
        if not year or not month or not day:
            continue
        rows.append(
            {
                "trade_date": f"{year:04d}-{month:02d}-{day:02d}",
                "open": float(b.open),
                "high": float(b.high),
                "low": float(b.low),
                "close": float(b.close),
                "volume": float(b.vol),
                "amount": float(b.amount),
                "symbol": "513130",
                "exchange": "SH",
                "provider": "TDX",
                "client": "pytdxdata",
                "adjustment": "NONE",
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return (
        frame.sort_values("trade_date")
        .drop_duplicates("trade_date", keep="last")
        .reset_index(drop=True)
    )


async def fetch() -> pd.DataFrame:
    # Do not pass end_date: local timezone can drop the latest Shanghai session.
    async with TdxData() as td:
        bars = await td.get_bars(
            "sh513130",
            KlinePeriod.DAY,
            start=0,
            count=2500,
            adjust=Adjust.NONE,
            start_date=datetime(2021, 5, 1),
        )
    return bars_to_frame(bars)


def write_meta(df: pd.DataFrame) -> None:
    meta = {
        "symbol": "513130",
        "name": "恒生科技ETF华泰柏瑞",
        "exchange": "SH",
        "provider": "TDX",
        "client": "pytdxdata",
        "adjustment": "NONE",
        "period": "day",
        "bars": int(len(df)),
        "first_date": str(df["trade_date"].iloc[0]),
        "last_date": str(df["trade_date"].iloc[-1]),
        "first_close": float(df["close"].iloc[0]),
        "last_close": float(df["close"].iloc[-1]),
        "high": float(df["high"].max()),
        "low": float(df["low"].min()),
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "Unadjusted Shanghai ETF daily bars from Tongdaxin via pytdxdata.get_bars(sh513130, DAY, Adjust.NONE)",
    }
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    out = Path(args.out)
    df = asyncio.run(fetch())
    if df.empty:
        raise SystemExit("TDX returned no 513130 bars")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    if out.resolve() == OUT.resolve():
        write_meta(df)
    print(
        f"wrote {out} rows={len(df)} {df['trade_date'].iloc[0]} -> {df['trade_date'].iloc[-1]} last_close={df['close'].iloc[-1]:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
