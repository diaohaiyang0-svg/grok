# grok

Grok 专用仓库。513130（华泰柏瑞恒生科技 ETF）通达信不复权行情。

缠论、Weinstein/Dow v1.0 价格框架已删。数据客户端与 a-share-radar 相同（pytdxdata）。

```bash
pip install -r requirements.txt
python scripts/fetch_513130_tdx.py
python scripts/fetch_513130_tdx_60m.py
```

## 数据

- `data/tdx/513130_daily.csv`：日线 2021-06-01 → 2026-09-23
- `data/tdx/513130_60m.csv`：60 分钟（TDX 深度约 2024-09 起）
