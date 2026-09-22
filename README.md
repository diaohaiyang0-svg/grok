# grok

Grok 专用仓库。当前任务：用缠论梳理 513130（恒生科技ETF华泰柏瑞）的历史走势，再定位现阶段。

数据已进仓库，回放不依赖本机通达信。

## 数据

- `data/tdx/513130_daily.csv`：通达信不复权日线（pytdxdata，与 a-share-radar 同一客户端）
- `data/tdx/by_year/`：按年拆分，方便 git
- `data/tdx/513130_60m.csv`：通达信不复权 60 分钟
- 日线区间：2021-06-01 → 2026-09-22，1291 根，最新收盘 0.549
- 60 分钟区间：2024-09-02 10:30 → 2026-09-22 15:00，1996 根  
  通达信在线 60 分钟只保留到 2024-09-02，更早的分钟线服务器上没有。

刷新（有网时）：

```bash
pip install -r requirements.txt
python scripts/fetch_513130_tdx.py
python scripts/fetch_513130_tdx_60m.py
```

## 回放

```bash
python scripts/analyze_513130.py
python scripts/analyze_513130_60m.py
python scripts/backtest_513130_60m.py
```

结果：

- 日线：`results/513130_replay.md`、`results/513130_now.json`
- 60 分钟结构：`results/513130_60m_replay.md`、`results/513130_60m_now.json`
- 60 分钟回测：`results/513130_60m_backtest.md`、`results/513130_60m_backtest.json`

锁定规则：K 线包含 → 分型 → 笔 → 中枢。日线和 60 分钟用同一套，不另做预测模型。

## 为什么没有把 chanlun-pro 整仓拷进来

选定的上游是 [yijixiuxin/chanlun-pro](https://github.com/yijixiuxin/chanlun-pro)。不能整包搬进 `grok`：仓库大、`src/` 有 PyArmor 加固、作者要求本地部署授权。本仓库只放明文结构口径。
