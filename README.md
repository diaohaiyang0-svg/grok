# grok

Grok 专用仓库。当前任务：用缠论梳理 513130（恒生科技ETF华泰柏瑞）的历史走势，再定位现阶段。

## 为什么没有把 chanlun-pro 整仓拷进来

选定的上游是 [yijixiuxin/chanlun-pro](https://github.com/yijixiuxin/chanlun-pro)（Apache-2.0 声明 + 本地部署付费/试用）。

不能整包搬进 `grok` 的原因：

- 仓库约 200MB，含 web、回测、多市场接口
- `src/` 里有 PyArmor 加固运行时（`pyarmor_runtime_*`），不是可维护的明文算法
- 作者要求本地部署授权，拷进公开仓库不合适

本仓库放的是同一套结构口径的**明文实现**：K 线包含 → 分型 → 笔 → 中枢 → 当前位置。用于 513130 的历史校验与现阶段判断。

若以后要完整 Web 看盘，在本机单独 clone 上游，不要合并进这个仓库。

## 目录

```
chanlun/          #缠论核心
scripts/          #513130 分析入口
third_party/      #上游说明
```

## 跑 513130

```bash
pip install -r requirements.txt
python scripts/analyze_513130.py
```

默认拉日线（成交价，不是净值），打印：

1. 历史笔/中枢是否能对上主要高低点
2. 当前一笔、最近中枢、是否在中枢内
