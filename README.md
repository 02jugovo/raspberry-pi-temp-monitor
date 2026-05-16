# 🌡️ 树莓派环境温度采集、分析与智能预测系统

基于树莓派的全栈物联网项目，实现环境温度数据的实时采集、存储、可视化展示与机器学习预测。

---

## 📌 项目简介

本系统以树莓派为核心硬件平台，通过温度传感器持续采集环境数据，结合 Python 后端与 Web 前端，实现：

- **实时采集**：持续读取传感器温度数据并存储
- **数据分析**：对历史数据进行统计分析与趋势判断
- **智能预测**：基于机器学习模型对未来温度走势进行预测
- **可视化展示**：通过 Web 界面直观展示数据与预测结果

---

## 🗂️ 项目结构

```
raspberry-pi-temp-monitor/
├── src/                # 核心源代码
├── scripts/            # 辅助脚本
├── models/             # 机器学习模型文件
├── data/               # 采集的温度数据
├── static/             # Web 前端静态资源（CSS、JS）
├── templates/          # HTML 页面模板
├── requirements.txt    # Python 依赖列表
├── start_system.py     # 一键启动全系统
├── start_collector.py  # 单独启动数据采集模块
├── start_web_server.py # 单独启动 Web 服务
└── test_system.py      # 系统测试脚本
```

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| 硬件平台 | Raspberry Pi |
| 后端语言 | Python 3 |
| Web 框架 | Flask |
| 数据分析 | pandas、NumPy |
| 机器学习 | scikit-learn |
| 前端 | HTML / JavaScript / CSS |
| 数据存储 | CSV / 本地文件 |

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/02jugovo/raspberry-pi-temp-monitor.git
cd raspberry-pi-temp-monitor
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动系统

```bash
# 一键启动（采集 + Web 服务）
python start_system.py

# 或分别启动
python start_collector.py    # 数据采集
python start_web_server.py   # Web 界面
```

### 4. 访问 Web 界面

启动后在浏览器打开：

```
http://localhost:5000
```

---

## 📊 功能展示

- 实时温度曲线图
- 历史数据查询与导出
- 温度异常告警
- 未来温度预测结果可视化

---

## 📝 开发环境

- Python 3.8+
- Raspberry Pi OS（或普通 PC 模拟运行）
- 温度传感器：DHT11 / DHT22（可选）

---

## 📄 License

MIT License — 可自由使用与修改。

---

> 本项目为本科毕业设计作品，完整记录了从硬件数据采集到机器学习预测的全流程实现。
