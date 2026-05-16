import logging
import numpy as np
import os
from .database import Database
from datetime import datetime, timedelta

logging.basicConfig(
    filename='logs/data_processor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DataProcessor:
    def __init__(self, db_path='data/temperature.db'):
        # 获取脚本所在目录的上一级目录(项目根目录)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 构建数据库的绝对路径
        db_path = os.path.join(base_dir, db_path)
        self.db = Database(db_path=db_path)
        
    def get_recent_data(self, hours=24, use_relative_time=True):
        """获取最近n小时的数据
        
        Args:
            hours (int): 小时数，默认24
            use_relative_time (bool): 是否使用相对于当前时间的过滤，默认True
        
        Returns:
            list: [(timestamp, temperature)] 数据列表
        """
        if use_relative_time:
            #使用相对于当前时间的过滤
            end_time = datetime.now().isoformat()
            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            logging.info(f"查询时间范围: {start_time} 到 {end_time}")
            
            return self.db.get_temperature_data(start_time, end_time, limit=1000)
        else:
            return self.db.get_temperature_data(limit=1000)
    
        logging.info(f"从数据库获取到 {len(data) if data else 0} 条数据")
    
    def sample_data(self, data, max_points=100):
        """智能采样数据，避免图表显示过于密集"""
        if len(data) <= max_points:
            return data

        # 计算采样间隔
        interval = len(data) // max_points
    
        # 执行采样
        sampled_data = []
        for i in range(0, len(data), interval):
            sampled_data.append(data[i])
    
        # 确保包含最后一个数据点
        if sampled_data[-1] != data[-1]:
            sampled_data.append(data[-1])
    
        return sampled_data
    
        
    def detect_outliers(self, data, threshold=2.0):
        """检测异常值
        
        Args:
            data (list): [(timestamp, temperature)] 数据列表
            threshold (float): 标准差倍数，默认2.0
            
        Returns:
            list: [(timestamp, temperature, is_outlier)] 带异常标记的数据列表
        """
        if not data:
            return []
            
        # 提取温度值
        temperatures = [item[1] for item in data]
        
        # 计算均值和标准差
        mean = np.mean(temperatures)
        std = np.std(temperatures)
        
        # 标记异常值
        result = []
        for timestamp, temp in data:
            is_outlier = abs(temp - mean) > threshold * std
            result.append((timestamp, temp, is_outlier))
            
        return result
        
    def smooth_data(self, data, window_size=5):
        """使用滑动窗口平均法平滑数据
        
        Args:
            data (list): [(timestamp, temperature)] 数据列表
            window_size (int): 窗口大小，默认5
            
        Returns:
            list: [(timestamp, smoothed_temperature)] 平滑后的数据列表
        """
        if not data or len(data) < window_size:
            return data
            
        # 提取时间戳和温度值
        timestamps = [item[0] for item in data]
        temperatures = [item[1] for item in data]
        
        # 使用卷积计算滑动窗口平均值
        kernel = np.ones(window_size) / window_size
        smoothed_temps = np.convolve(temperatures, kernel, mode='valid')
        
        # 由于滑动窗口计算会减少数据点，需要调整时间戳
        offset = window_size // 2
        result = []
        for i in range(len(smoothed_temps)):
            result.append((timestamps[i + offset], smoothed_temps[i]))
            
        return result
        
    def calculate_statistics(self, data):
        """计算基本统计信息
        
        Args:
            data (list): [(timestamp, temperature)] 数据列表
            
        Returns:
            dict: 包含统计信息的字典
        """
        if not data:
            return {
                'count': 0,
                'min': None,
                'max': None,
                'mean': None,
                'std': None
            }
            
        # 提取温度值
        temperatures = [item[1] for item in data]
        
        return {
            'count': len(temperatures),
            'min': np.min(temperatures),
            'max': np.max(temperatures),
            'mean': np.mean(temperatures),
            'std': np.std(temperatures),
            'median': np.median(temperatures)
        }
        
    def get_hourly_data_for_day(self, day_start):
        """
        获取某天每小时的平均温度（24个点）
        :param day_start: datetime对象，表示当天0点
        :return: [(timestamp, avg_temp)]
        """
        day_end = day_start + timedelta(days=1)
        data = self.db.get_temperature_data(day_start.isoformat(), day_end.isoformat(), limit=2000)
        hourly = [[] for _ in range(24)]
        for ts, temp in data:
            try:
                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                hour = dt.hour
                hourly[hour].append(float(temp))
            except:
                continue
        result = []
        for h in range(24):
            ts = (day_start + timedelta(hours=h)).isoformat()
            if hourly[h]:
                avg = sum(hourly[h]) / len(hourly[h])
                result.append((ts, avg))
            else:
                result.append((ts, None))
        return result

    def get_daily_data_for_month(self, month_start):
        """
        获取某月每天的平均温度（本月天数）
        :param month_start: datetime对象，表示当月1号0点
        :return: [(timestamp, avg_temp)]
        """
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year+1, month=1, day=1)
        else:
            next_month = month_start.replace(month=month_start.month+1, day=1)
        data = self.db.get_temperature_data(month_start.isoformat(), next_month.isoformat(), limit=5000)
        days_in_month = (next_month - month_start).days
        daily = [[] for _ in range(days_in_month)]
        for ts, temp in data:
            try:
                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                day = (dt - month_start).days
                if 0 <= day < days_in_month:
                    daily[day].append(float(temp))
            except:
                continue
        result = []
        for d in range(days_in_month):
            ts = (month_start + timedelta(days=d)).isoformat()
            if daily[d]:
                avg = sum(daily[d]) / len(daily[d])
                result.append((ts, avg))
            else:
                result.append((ts, None))
        return result

    def get_monthly_data_for_year(self, year_start):
        """
        获取某年每月的平均温度（12个点）
        :param year_start: datetime对象，表示当年1月1日0点
        :return: [(timestamp, avg_temp)]
        """
        year = year_start.year
        result = []
        for m in range(1, 13):
            month_start = year_start.replace(month=m, day=1)
            if m == 12:
                next_month = month_start.replace(year=year+1, month=1, day=1)
            else:
                next_month = month_start.replace(month=m+1, day=1)
            data = self.db.get_temperature_data(month_start.isoformat(), next_month.isoformat(), limit=5000)
            temps = []
            for ts, temp in data:
                try:
                    temps.append(float(temp))
                except:
                    continue
            ts = month_start.isoformat()
            if temps:
                avg = sum(temps) / len(temps)
                result.append((ts, avg))
            else:
                result.append((ts, None))
        return result

# 简单测试
if __name__ == "__main__":
    processor = DataProcessor(db_path='data/temperature.db')
    
    # 获取最近数据
    recent_data = processor.get_recent_data(hours=6)
    print(f"Recent data count: {len(recent_data)}")
    
    # 检测异常值
    outliers = processor.detect_outliers(recent_data)
    outlier_count = sum(1 for _, _, is_outlier in outliers if is_outlier)
    print(f"Detected {outlier_count} outliers")
    
    # 计算统计信息
    stats = processor.calculate_statistics(recent_data)
    print(f"Statistics: {stats}")
    
    # 简单预测
    prediction = processor.predict_simple(recent_data, hours_ahead=1)
    print(f"Predicted temperature (1 hour ahead): {prediction}°C")

