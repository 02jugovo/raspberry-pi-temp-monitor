import sqlite3
import os
import logging
from datetime import datetime

# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志
logging.basicConfig(
    filename=os.path.join(log_dir, 'database.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Database:
    def __init__(self, db_path='data/temperature.db'):
        """初始化数据库连接
        
        Args:
            db_path (str): 数据库文件路径
        """
        self.db_path = db_path
        self.ensure_db_dir_exists()
        self.init_db()
        
    def ensure_db_dir_exists(self):
        """确保数据库目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def get_connection(self):
        """获取数据库连接
        
        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        return sqlite3.connect(self.db_path)
        
    def init_db(self):
        """初始化数据库表结构"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 创建温度数据表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS temperature_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                temperature REAL NOT NULL,
                is_abnormal INTEGER DEFAULT 0
            )
            ''')
            
            # 创建设备信息表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                location TEXT,
                created_at TEXT NOT NULL
            )
            ''')
            
            # 创建系统配置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT NOT NULL UNIQUE,
                config_value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            ''')
            
            # 创建预测结果表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                predicted_temperature REAL NOT NULL,
                prediction_time TEXT NOT NULL,
                model_version TEXT DEFAULT 'v1.0',
                confidence_score REAL DEFAULT 0.0
            )
            ''')
            
            # 添加索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_temperature_timestamp ON temperature_data (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_timestamp ON prediction_results (timestamp)')
            
            conn.commit()
            logging.info("Database initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            raise
        finally:
            conn.close()
            
    def insert_temperature(self, temperature, timestamp=None):
        """插入温度数据
        
        Args:
            temperature (float): 温度值
            timestamp (str, optional): 时间戳，默认为当前时间
            
        Returns:
            bool: 插入是否成功
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        else:
            # 确保时间戳是ISO格式
            if isinstance(timestamp, datetime): 
                timestamp = timestamp.isoformat()
            else:
                # 尝试解析并重新格式化时间戳
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.isoformat()
                except ValueError:
                    logging.warning(f"Invalid timestamp format: {timestamp}, using current time")
                    timestamp = datetime.now().isoformat()
                    
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 判断温度是否异常（可根据实际需求调整阈值）
            is_abnormal = 1 if temperature < -10 or temperature > 50 else 0
            
            cursor.execute(
                'INSERT INTO temperature_data (timestamp, temperature, is_abnormal) VALUES (?, ?, ?)',
                (timestamp, temperature, is_abnormal)
            )
            
            conn.commit()
            logging.info(f"Temperature data inserted: {timestamp}, {temperature}°C")
            return True
            
        except Exception as e:
            logging.error(f"Error inserting temperature data: {e}")
            return False
        finally:
            conn.close()
            
    def get_temperature_data(self, start_time=None, end_time=None, limit=100):
        """获取温度数据
        
        Args:
            start_time (str, optional): 开始时间
            end_time (str, optional): 结束时间
            limit (int, optional): 最大记录数，默认100
            
        Returns:
            list: 温度数据列表 [(timestamp, temperature), ...]
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = 'SELECT timestamp, temperature FROM temperature_data'
            params = []
            # 添加时间过滤条件
            if start_time and end_time:
                query += ' WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp ASC'
                params.extend([start_time, end_time])
                # 不加limit，查全部
            elif start_time:
                query += ' WHERE timestamp >= ? ORDER BY timestamp ASC'
                params.append(start_time)
            elif end_time:
                query += ' WHERE timestamp <= ? ORDER BY timestamp ASC'
                params.append(end_time)
            else:
                query += ' ORDER BY timestamp DESC'
                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)
            cursor.execute(query, params)
            data = cursor.fetchall()
            logging.info(f"Database query returned {len(data)} records")
            return data
        except Exception as e:
            logging.error(f"Error fetching temperature data: {e}")
            return []
        finally:
            conn.close()
            
    def insert_prediction(self, timestamp, predicted_temperature, model_version='v1.0', confidence_score=0.0):
        """插入预测结果
        
        Args:
            timestamp (str): 预测时间点
            predicted_temperature (float): 预测温度值
            model_version (str): 模型版本
            confidence_score (float): 置信度分数
            
        Returns:
            bool: 插入是否成功
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            prediction_time = datetime.now().isoformat()
            
            cursor.execute(
                '''INSERT INTO prediction_results 
                   (timestamp, predicted_temperature, prediction_time, model_version, confidence_score) 
                   VALUES (?, ?, ?, ?, ?)''',
                (timestamp, predicted_temperature, prediction_time, model_version, confidence_score)
            )
            
            conn.commit()
            logging.info(f"Prediction data inserted: {timestamp}, {predicted_temperature}°C")
            return True
            
        except Exception as e:
            logging.error(f"Error inserting prediction data: {e}")
            return False
        finally:
            conn.close()
            
    def get_predictions(self, start_time=None, end_time=None, limit=50):
        """获取预测数据
        
        Args:
            start_time (str, optional): 开始时间
            end_time (str, optional): 结束时间
            limit (int, optional): 最大记录数，默认50
            
        Returns:
            list: 预测数据列表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = '''SELECT timestamp, predicted_temperature, prediction_time, 
                      model_version, confidence_score FROM prediction_results'''
            params = []
            
            if start_time and end_time:
                query += ' WHERE timestamp BETWEEN ? AND ?'
                params.extend([start_time, end_time])
            elif start_time:
                query += ' WHERE timestamp >= ?'
                params.append(start_time)
            elif end_time:
                query += ' WHERE timestamp <= ?'
                params.append(end_time)
                
            query += ' ORDER BY prediction_time DESC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
                
            cursor.execute(query, params)
            return cursor.fetchall()
            
        except Exception as e:
            logging.error(f"Error fetching prediction data: {e}")
            return []
        finally:
            conn.close()
            
    def set_config(self, key, value):
        """设置系统配置
        
        Args:
            key (str): 配置键
            value (str): 配置值
            
        Returns:
            bool: 设置是否成功
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            updated_at = datetime.now().isoformat()
            
            cursor.execute(
                '''INSERT INTO system_config (config_key, config_value, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(config_key) DO UPDATE SET
                       config_value = excluded.config_value,
                       updated_at = excluded.updated_at''',
                (key, value, updated_at)
            )
            
            conn.commit()
            logging.info(f"Config set: {key}={value}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting config: {e}")
            return False
        finally:
            conn.close()
            
    def get_config(self, key, default=None):
        """获取系统配置
        
        Args:
            key (str): 配置键
            default: 默认值，如果配置不存在
            
        Returns:
            str: 配置值
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT config_value FROM system_config WHERE config_key = ?', (key,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            return default
            
        except Exception as e:
            logging.error(f"Error getting config: {e}")
            return default
        finally:
            conn.close()
            
    def get_statistics(self):
        """获取数据库统计信息
        
        Returns:
            dict: 包含统计信息的字典
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 获取温度数据统计
            cursor.execute('SELECT COUNT(*) FROM temperature_data')
            temp_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT MIN(temperature), MAX(temperature), AVG(temperature) FROM temperature_data')
            temp_stats = cursor.fetchone()
            
            # 获取预测数据统计
            cursor.execute('SELECT COUNT(*) FROM prediction_results')
            pred_count = cursor.fetchone()[0]
            
            # 获取异常数据统计
            cursor.execute('SELECT COUNT(*) FROM temperature_data WHERE is_abnormal = 1')
            abnormal_count = cursor.fetchone()[0]
            
            return {
                'temperature_records': temp_count,
                'prediction_records': pred_count,
                'abnormal_records': abnormal_count,
                'min_temperature': temp_stats[0] if temp_stats[0] else 0,
                'max_temperature': temp_stats[1] if temp_stats[1] else 0,
                'avg_temperature': round(temp_stats[2], 2) if temp_stats[2] else 0
            }
            
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return {}
        finally:
            conn.close()
            
    def cleanup_old_data(self, days_to_keep=30):
        """清理旧数据
        
        Args:
            days_to_keep (int): 保留天数，默认30天
            
        Returns:
            int: 删除的记录数
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            # 删除旧的温度数据
            cursor.execute('DELETE FROM temperature_data WHERE timestamp < ?', (cutoff_date,))
            temp_deleted = cursor.rowcount
            
            # 删除旧的预测数据
            cursor.execute('DELETE FROM prediction_results WHERE timestamp < ?', (cutoff_date,))
            pred_deleted = cursor.rowcount
            
            conn.commit()
            total_deleted = temp_deleted + pred_deleted
            
            logging.info(f"Cleanup completed: {total_deleted} records deleted (temp: {temp_deleted}, pred: {pred_deleted})")
            return total_deleted
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            return 0
        finally:
            conn.close()

# 简单测试代码
if __name__ == "__main__":
    # 创建数据库实例
    db = Database(db_path='data/test.db')
    
    # 测试插入温度数据
    print("Testing temperature data insertion...")
    db.insert_temperature(25.5)
    db.insert_temperature(26.2)
    db.insert_temperature(24.8)
    
    # 测试查询温度数据
    print("\nTesting temperature data retrieval...")
    data = db.get_temperature_data(limit=10)
    for row in data:
        print(f"Timestamp: {row[0]}, Temperature: {row[1]}°C")
        
    # 测试配置功能
    print("\nTesting configuration...")
    db.set_config('sampling_interval', '600')
    db.set_config('alert_threshold', '35.0')
    
    print(f"Sampling interval: {db.get_config('sampling_interval')} seconds")
    print(f"Alert threshold: {db.get_config('alert_threshold')}°C")
    
    # 测试预测数据插入
    print("\nTesting prediction data insertion...")
    from datetime import timedelta
    future_time = (datetime.now() + timedelta(hours=1)).isoformat()
    db.insert_prediction(future_time, 27.3, 'LSTM_v1.0', 0.85)
    
    # 测试统计信息
    print("\nTesting statistics...")
    stats = db.get_statistics()
    print(f"Database statistics: {stats}")
