# grok

Grok 专用仓库。当前任务：用缠论梳理 513130（恒生科技ETF华泰柏瑞）的历史走势，再定位现阶段。

数据已进仓库，回放不依赖本机通达信。

## 数据

- `data/tdx/513130_daily.csv`：通达信不复权日线（pytdxdata，与 a-share-radar 同一客户端）
- `data/tdx/by_year/`：按年拆分，方便 git
- 区间：2021-06-01 → 2026-09-22，1291 根，最新收盘 0.549

刷新（有网时）：

```bash
pip install -r requirements.txt
python scripts/fetch_513130_tdx.py
```

## 回放

```bash
python scripts/analyze_513130.py
python scripts/backtest_513130.py
```

结果在 `results/513130_replay.md` 和 `results/513130_structure.json`。

锁定规则：K 线包含 → 分型 → 笔 → 中枢。历史和现在用同一套，不另做预测模型。

## 为什么没有把 chanlun-pro 整仓拷进来

选定的上游是 [yijixiuxin/chanlun-pro](https://github.com/yijixiuxin/chanlun-pro)。不能整包搬进 `grok`：仓库大、`src/` 有 PyArmor 加固、作者要求本地部署授权。本仓库只放明文结构口径。
