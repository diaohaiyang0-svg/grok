# TDX daily bars

`513130` 恒生科技ETF华泰柏瑞, Shanghai unadjusted daily bars.

- Client: `pytdxdata` (same as `a-share-radar`)
- Symbol: `sh513130`
- Period: day
- Adjust: `NONE`
- Latest live pull: 1291 bars, 2021-06-01 -> 2026-09-22, last close 0.549

Refresh locally (writes `513130_daily.csv` + updates `513130_meta.json`):

```bash
pip install -r requirements.txt
python scripts/fetch_513130_tdx.py
```
