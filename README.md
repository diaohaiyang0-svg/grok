# grok

Grok 专用仓库。缠论框架已删除，只保留 513130（恒生科技ETF华泰柏瑞）的通达信不复权行情。

数据客户端与 a-share-radar 相同（pytdxdata），不用东财 / akshare。

## 数据

- `data/tdx/513130_daily.csv`：日线，2021-06-01 → 2026-09-23，1292 根，最新收盘 0.543
- `data/tdx/513130_60m.csv`：60 分钟，2024-09-02 10:30 → 2026-09-23 13:00，1998 根
- `data/tdx/513130_meta.json` / `513130_60m_meta.json`：抓取说明
- 通达信在线 60 分钟从 2024-09-02 起，更早分钟线服务器上没有

刷新：

```bash
pip install -r requirements.txt
python scripts/fetch_513130_tdx.py
python scripts/fetch_513130_tdx_60m.py
```
