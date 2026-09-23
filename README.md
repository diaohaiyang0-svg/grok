# grok

Grok 专用仓库。513130（恒生科技ETF华泰柏瑞）通达信不复权行情 + v1.0 价格框架（周线温斯坦阶段 + 日线道氏结构 + ATR）。

缠论已删。数据客户端与 a-share-radar 相同（pytdxdata）。

## 规则

- `framework/SPEC.md`：v1.0 复盘与回测规格（锁定）
- `framework/engine.py`：指标 / 阶段 / 结构 / 交易
- `只做多`；收盘信号、次日开盘成交

```bash
pip install -r requirements.txt
python scripts/fetch_513130_tdx.py
python scripts/run_513130_v1.py
```

## 数据

- `data/tdx/513130_daily.csv`：日线 2021-06-01 → 2026-09-23
- 溢价过滤需净值，本轮 TDX 拉数没有 NAV，过滤未启用
