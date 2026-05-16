import time
import csv
import os
import logging
from datetime import datetime
from .sensor import TemperatureSensor
from .database import Database

log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_dir, 'collector.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DataCollector:
    def __init__(self, interval=600,db_path='data/temperature.db'):
        """初始化数据采集器
        
        Args:
            interval (int): 采集间隔，单位为秒，默认600秒(10分钟)
            db_path(str): 输出文件路径
        """
        self.sensor = TemperatureSensor()
        self.interval = interval
        self.db = Database(db_path=db_path)
        
        # 从配置中读取采集间隔（如果存在）
        stored_interval = self.db.get_config('sampling_interval')
        if stored_interval:
            try:
                self.interval = int(stored_interval)
                logging.info(f"Using configured sampling interval: {self.interval}s")
            except ValueError:
                logging.warning(f"Invalid sampling_interval in config: {stored_interval}")
        else:
            # 保存当前采集间隔到配置
            self.db.set_config('sampling_interval', str(self.interval))

                
    def collect_data(self):
        """采集一次数据并保存"""
        temp = self.sensor.get_temperature()
        if temp is not None:
            self.db.insert_temperature(temp)
            print(f"Temperature reading: {temp}°C")  # 添加终端输出
            return temp
        else:
            error_msg = "Failed to collect data"
            logging.error(error_msg)
            print(f"ERROR: {error_msg}")  # 添加错误输出到终端
            return None
            
    def run(self, duration=None):
        """运行数据采集循环"""
        start_time = time.time()
        interval_msg = f"Starting data collection, interval: {self.interval}s"
        logging.info(interval_msg)
        print(interval_msg)  # 添加终端输出
    
        try:
            while True:
                self.collect_data()
            
                # 检查是否达到运行时间
                if duration and (time.time() - start_time >= duration):
                    stop_msg = f"Reached specified duration of {duration}s, stopping"
                    logging.info(stop_msg)
                    print(stop_msg)  # 添加终端输出
                    break
                    
                # 获取最新的采集间隔
                stored_interval = self.db.get_config('sampling_interval')
                if stored_interval:
                    try:
                        self.interval = int(stored_interval)
                    except ValueError:
                        pass


                # 计算下次采集时间
                next_time = time.time() + self.interval
                sleep_time = max(0, next_time - time.time())
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            stop_msg = "Data collection stopped by user"
            logging.info(stop_msg)
            print(stop_msg)  # 添加终端输出
        except Exception as e:
            error_msg = f"Error in data collection: {e}"
            logging.error(error_msg)
            print(f"ERROR: {error_msg}")  # 添加终端输出

# 简单测试
if __name__ == "__main__":
    # 测试模式：每10秒采集一次，运行60秒
    collector = DataCollector(interval=10, db_path='data/test.db')
    collector.run(duration=60)
