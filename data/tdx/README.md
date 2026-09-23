# TDX bars

上海 513130 不复权 K 线，客户端与 a-share-radar 相同（pytdxdata）。不用东财。

- `513130_daily.csv`：日线，2021-06-01 → 2026-09-23，1292 根
- `513130_60m.csv`：60 分钟，2024-09-02 10:30 → 2026-09-23 13:00，1998 根
- adjustment: NONE
- last close: 0.543

通达信在线 60 分钟查 2021-06-01 至 2024-08-31 为空，服务器深度大约两年。

```bash
python scripts/fetch_513130_tdx.py
python scripts/fetch_513130_tdx_60m.py
```
