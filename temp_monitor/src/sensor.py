from w1thermsensor import W1ThermSensor, SensorNotReadyError
import time
import logging
import os

# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志
logging.basicConfig(
    filename=os.path.join(log_dir, 'sensor.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TemperatureSensor:
    def __init__(self):
        self.sensor = None
        self.connect()
        
    def connect(self):
        """尝试连接到温度传感器"""
        try:
            self.sensor = W1ThermSensor()
            logging.info("Successfully connected to temperature sensor")
            return True
        except Exception as e:
            logging.error(f"Error connecting to sensor: {e}")
            return False
    
    def get_temperature(self, max_retries=3):
        """读取温度值，支持重试机制"""
        if not self.sensor and not self.connect():
            return None
            
        for attempt in range(max_retries):
            try:
                temp = self.sensor.get_temperature()
                logging.info(f"Temperature reading: {temp}°C")
                return temp
            except SensorNotReadyError:
                logging.warning(f"Sensor not ready, retrying ({attempt+1}/{max_retries})")
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error reading temperature: {e}")
                time.sleep(1)
                
        logging.error(f"Failed to read temperature after {max_retries} attempts")
        return None

# 简单测试
if __name__ == "__main__":
    sensor = TemperatureSensor()
    for i in range(5):
        temp = sensor.get_temperature()
        print(f"Temperature: {temp}°C")
        time.sleep(2)
