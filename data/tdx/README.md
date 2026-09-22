# TDX daily bars

`513130_daily.csv` 与 `by_year/513130_YYYY.csv` 是上海 513130 不复权日线。

- provider: Tongdaxin
- client: pytdxdata（与 a-share-radar 相同）
- adjustment: NONE
- 1291 bars, 2021-06-01 → 2026-09-22, last close 0.549

```bash
python scripts/fetch_513130_tdx.py
```
