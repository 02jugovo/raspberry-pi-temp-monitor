import os
import sys
import time
from src.collector import DataCollector

# 确保工作目录正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 创建并启动数据采集器
collector = DataCollector(interval=600)  # 默认10分钟采集一次
print(f"Starting temperature data collector...")
print(f"Press Ctrl+C to stop")

try:
    collector.run()  # 无限运行
except KeyboardInterrupt:
    print("Data collection stopped by user")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
