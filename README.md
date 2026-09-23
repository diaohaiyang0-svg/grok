# grok

Grok 专用仓库。513130（华泰柏瑞恒生科技 ETF）通达信不复权行情。

当前回测：backtesting.py + 海龟 20/10 只做多 + 12 个月绝对动量。缠论与 Weinstein/Dow v1 已删。

```bash
pip install -r requirements.txt
python scripts/fetch_513130_tdx.py
python scripts/run_513130_bt.py
```

规则与结果：`results/513130_rules_backtest.md`
