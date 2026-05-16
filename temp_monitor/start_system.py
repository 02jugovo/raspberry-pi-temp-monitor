#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temperature monitoring system main startup script
"""
import os
import sys
import time
import logging
import signal
import subprocess
import threading
from datetime import datetime

# 添加源码目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import Database
from src.sensor import TemperatureSensor
from src.collector import DataCollector
from src.predictorS import TemperaturePredictor
from src.web_server import main as start_web_server

# 配置日志
logging.basicConfig(
    filename='logs/system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class SystemManager:
    """System Manager"""
    
    def __init__(self):
        self.running = True
        self.processes = []
        
    def signal_handler(self, signum, frame):
        """Handling system signal"""
        logging.info(f"接收到信号 {signum}，正在关闭系统...")
        self.shutdown()
        
    def initialize_system(self):
        """Initializing system"""
        logging.info("正在初始化系统...")
        
        # 创建必要的目录
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('models', exist_ok=True)
        os.makedirs('static/js', exist_ok=True)
        os.makedirs('static/css', exist_ok=True)
        os.makedirs('templates', exist_ok=True)
        
        # 初始化数据库
        db = Database()
        logging.info("数据库初始化完成")
        
        # 测试传感器连接
        sensor = TemperatureSensor()
        if sensor.read_temperature() is not None:
            logging.info("传感器连接正常")
        else:
            logging.warning("传感器连接失败，系统将使用模拟数据")
        
        # 初始化预测器
        predictor = AdvancedPredictor()
        logging.info(f"预测器初始化完成，使用模型类型: {predictor.model_type}")
        
    def start_services(self):
        """启动所有服务"""
        logging.info("Starting services...")
        
        # 启动数据采集服务
        collector_process = subprocess.Popen(
            [sys.executable, '-m', 'src.collector'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes.append(collector_process)
        logging.info(f"数据采集服务已启动 (PID: {collector_process.pid})")
        
        # 短暂等待，确保数据采集服务正常启动
        time.sleep(2)
        
        # 启动Web服务（包含实时监控）
        try:
            start_web_server()
        except Exception as e:
            logging.error(f"Web服务启动失败: {e}")
            self.shutdown()
            sys.exit(1)
    
    def monitor_services(self):
        """监控服务状态"""
        while self.running:
            try:
                # 检查所有子进程
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        logging.warning(f"进程 {process.pid} 已停止，正在重启...")
                        # 重启进程
                        if i == 0:  # 数据采集进程
                            new_process = subprocess.Popen(
                                [sys.executable, '-m', 'src.collector'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                            self.processes[i] = new_process
                            logging.info(f"数据采集服务已重启 (PID: {new_process.pid})")
                
                time.sleep(30)  # 每30秒检查一次
                
            except KeyboardInterrupt:
                self.shutdown()
                break
            except Exception as e:
                logging.error(f"监控服务出错: {e}")
                time.sleep(60)
    
    def shutdown(self):
        """关闭系统"""
        logging.info("正在关闭系统...")
        self.running = False
        
        # 终止所有子进程
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        logging.info("系统已关闭")
    
    def run(self):
        """运行系统"""
        # 注册信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # 初始化系统
            self.initialize_system()
            
            # 启动服务
            self.start_services()
            
        except Exception as e:
            logging.error(f"系统启动失败: {e}")
            self.shutdown()
            sys.exit(1)

# 将backup_job移到类外部作为独立函数
def backup_job():
    """定期备份数据库"""
    from src.backup import BackupManager
    
    backup_manager = BackupManager()
    
    while True:
        try:
            logging.info("开始数据库备份...")
            
            # 验证数据库
            if backup_manager.verify_database():
                # 创建备份
                if backup_manager.create_backup():
                    logging.info("数据库备份成功")
                else:
                    logging.error("数据库备份失败")
            else:
                logging.error("数据库验证失败，尝试从备份恢复")
                if backup_manager.restore_from_backup():
                    logging.info("从备份恢复成功")
                else:
                    logging.error("从备份恢复失败")
            
            # 每天备份一次
            time.sleep(24 * 60 * 60)
            
        except Exception as e:
            logging.error(f"备份任务出错: {e}")
            time.sleep(60 * 60)  # 出错时等待一小时再试

def main():
    """main enter"""
    print("=== Temperature Monitoring System ===")
    print(f"Start time: {datetime.now()}")
    print("Starting system...")
    
    print("Creating SystemManager...")
    manager = SystemManager()
    print("SystemManager created.")
    
    
    # 启动备份线程
    print("Starting backup thread...")
    backup_thread = threading.Thread(target=backup_job, daemon=True)
    backup_thread.start()
    print("Backup thread started.")
    
    # 运行系统
    print("Running manager...")
    manager.run()
    print("Manager run completed.")
    
    print("Entering main loop...")
    try:
        while True:
            time.sleep(60)  # 每60秒检查一次
    except KeyboardInterrupt:
        logging.info("Received interrupt signal, shutting down...")
        manager.shutdown()

if __name__ == '__main__':
    main()
