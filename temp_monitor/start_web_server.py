#!/usr/bin/env python3
import os
import sys
import threading
import time
import schedule
import logging
from datetime import datetime
from src.web_server import app
from src.predictorS import TemperaturePredictor


# 设置工作目录
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# 配置Python路径
sys.path.insert(0, script_dir)

# 创建日志目录（新增代码）
os.makedirs('logs', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_server_startup.log'),
        logging.StreamHandler()
    ]
)

predictor = None

def run_server():
    try:
        logging.info("正在启动Web服务器...")
        from src.web_server import app, socketio  # 确保web_server中定义了socketio
        
        logging.info("开始监听端口5000...")
        socketio.run(app, host='0.0.0.0', port=8080, debug=True)
        
    except Exception as e:
        logging.error(f"启动失败: {e}")
        sys.exit(1)

def train_model():
    """定期训练模型"""
    global predictor
    print(f"Starting model training at {datetime.now()}")
    try:
        # 创建新的预测器实例或使用现有的
        if predictor is None:
            predictor = TemperaturePredictor()
        
        # 获取最近的训练数据
        training_data = predictor.get_training_data(days=7)
        
        if len(training_data) > 100:  # 确保有足够的数据
            # 准备训练数据
            X_train, y_train, mean, std = predictor.prepare_data(training_data)
            
            if X_train is not None and len(X_train) > 10:
                # 训练模型
                slope, intercept = predictor.train_linear_regression(X_train, y_train)
                print(f"Model trained successfully: slope={slope}, intercept={intercept}")
                
                # 评估模型
                evaluation = predictor.evaluate_model()
                print(f"Model evaluation: {evaluation}")
            else:
                print("Insufficient training data")
        else:
            print("Not enough historical data for training")
            
    except Exception as e:
        print(f"Error during model training: {e}")
    
    print(f"Model training completed at {datetime.now()}")


def schedule_training():
    """设置定时训练任务"""
    # 每6小时训练一次
    schedule.every(6).hours.do(train_model)
    
 
    # 在独立线程中运行调度器
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

# 确保工作目录正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 启动Web服务器
if __name__ == '__main__':
    print("Starting temperature monitoring web server...")
    print("Access the web interface at http://[raspberry_pi_ip]:8080")
    
    # 初始化训练模型
    train_model()
    
    # 启动定时训练
    schedule_training()
    
    # 运行Flask应用
    app.run(host='0.0.0.0', port=8082, debug=True)
