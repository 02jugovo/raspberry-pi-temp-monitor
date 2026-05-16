import tensorflow as tf
from flask import Flask, jsonify, request, render_template
import logging
import os
from datetime import datetime, timedelta
from dateutil import parser
from .database import Database
from .sensor import TemperatureSensor
from .data_processor import DataProcessor
from .predictorS import TemperaturePredictor
from flask_socketio import SocketIO
import threading
import time
import psutil
import traceback

# 配置日志
logging.basicConfig(
    filename='logs/web_server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__,
    template_folder='../templates',
    static_folder='../static')

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

db = Database()
sensor = TemperatureSensor()
processor = DataProcessor()
predictor = TemperaturePredictor()

# 添加系统状态监控线程
def system_monitor():
    while True:
        try:
            # 获取系统信息
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            # 获取当前温度
            temp = sensor.get_temperature()
            
            # 构建状态数据
            status_data = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_info.percent,
                    'disk_usage': disk_info.percent
                }
            }
            
            if temp is not None:
                status_data['temperature'] = temp
            
            # 通过WebSocket发送状态数据
            socketio.emit('system_status', status_data)
            
            # 每分钟发送一次
            time.sleep(60)
        except Exception as e:
            logging.error(f"系统监控线程出错: {e}")
            time.sleep(60)  # 出错时等待一分钟再试

# 初始化模型训练线程
def model_training_job():
    while True:
        try:
            # 每6小时重新训练一次模型
            logging.info("开始定期模型训练...")
            predictor.train_model(training_days=7)
            time.sleep(6 * 60 * 60)  # 6小时
        except Exception as e:
            logging.error(f"模型训练线程出错: {e}")
            time.sleep(60 * 60)  # 出错时等待一小时再试

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/api/temperature/current', methods=['GET'])
def get_current_temperature():
    """获取当前温度"""
    temp = sensor.get_temperature()
    if temp is not None:
        # 记录新的温度数据
        db.insert_temperature(temp)
        
        # 通过WebSocket推送新数据
        socketio.emit('new_temperature', {
            'temperature': temp,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'temperature': temp,
            'unit': 'celsius',
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to read temperature'
        }), 500

@app.route('/api/temperature/history', methods=['GET'])
def get_temperature_history():
    """获取历史温度数据，支持多时间范围，mode=raw时返回原始数据"""
    start_time = request.args.get('start')
    end_time = request.args.get('end')
    range_type = request.args.get('range', default='hour')
    mode = request.args.get('mode', default=None)
    data = []
    try:
        # 自动去除+08:00或Z等时区部分，保证与数据库一致
        def strip_tz(s):
            if s:
                s = s.split('+')[0]
                if s.endswith('Z'):
                    s = s[:-1]
                return s
            return s
        start_time = strip_tz(start_time)
        end_time = strip_tz(end_time)
        if mode == 'raw':
            # 返回原始数据
            limit = request.args.get('limit', type=int)
            if (not limit or limit < 0) and start_time and end_time:
                limit = 30000
            elif not limit:
                limit = 1000
            data = db.get_temperature_data(start_time, end_time, limit)
            result = []
            for row in data:
                timestamp_str = row[0]
                temperature = row[1]
                try:
                    dt = parser.parse(str(timestamp_str))
                    timestamp_str = dt.isoformat()
                except:
                    pass
                result.append({'timestamp': timestamp_str, 'temperature': float(temperature) if temperature is not None else None})
            result.sort(key=lambda x: x['timestamp'])
            return jsonify({'success': True, 'data': result, 'count': len(result)})
        # 聚合逻辑
        now = datetime.now()
        if range_type == 'hour':
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            hourly_data = processor.get_hourly_data_for_day(day_start)
            current_hour = now.hour
            data = hourly_data[max(0, current_hour-11):current_hour+1]
        elif range_type == 'day':
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            data = processor.get_hourly_data_for_day(day_start)
            if len(data) > 24:
                data = data[-24:]
        elif range_type == 'month':
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            data = processor.get_daily_data_for_month(month_start)
        elif range_type == 'year':
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            data = processor.get_monthly_data_for_year(year_start)
        else:
            return jsonify({'success': False, 'error': '无效的range参数'}), 400
    except Exception as e:
        logging.error(f"history接口异常: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'后端异常: {str(e)}'}), 500
    result = []
    for row in data:
        timestamp_str = row[0]
        temperature = row[1]
        try:
            dt = parser.parse(str(timestamp_str))
            timestamp_str = dt.isoformat()
        except:
            pass
        result.append({'timestamp': timestamp_str, 'temperature': float(temperature) if temperature is not None else None})
    result.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify({'success': True, 'data': result, 'count': len(result)})

@app.route('/api/temperature/stats', methods=['GET'])
def get_temperature_stats():
    """获取温度统计信息"""
    hours = request.args.get('hours', default=24, type=int)
    
    data = processor.get_recent_data(hours=hours)
    
    if not data:
        return jsonify({
            'success': False,
            'error': '无数据可用'
        }), 404
    
    stats = processor.calculate_statistics(data)
    outliers = processor.detect_outliers(data)
    outlier_count = sum(1 for _, _, is_outlier in outliers if is_outlier)
    
    return jsonify({
        'success': True,
        'period': f'最近{hours}小时',
        'stats': stats,
        'outlier_count': outlier_count
    })

@app.route('/api/temperature/predict', methods=['GET'])
def predict_temperature():
    """预测未来温度"""
    hours_ahead = request.args.get('hours', default=3, type=int)
    
    data = db.get_temperature_data(
        start_time=(datetime.now() - timedelta(hours=24)).isoformat(),
        end_time=datetime.now().isoformat(),
        limit=1000
    )
    
    if len(data) < 24:
        return jsonify({
            'success': False,
            'error': '数据不足，无法预测'
        }), 400
    
    # 使用当前时间作为预测基准
    current_time = datetime.now()
    
    # 删除数据中的重复时间戳，保证是30分钟一个数据点
    unique_times = {}
    for timestamp, temp in data:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        time_key = dt.strftime('%Y-%m-%d %H:%M')
        unique_times[time_key] = (timestamp, temp)
    
    # 按时间升序排序，这是预测器需要的顺序
    sorted_data = sorted(unique_times.values(), key=lambda x: x[0])
    
    # 添加当前时间的数据点作为最新数据
    last_temp = sorted_data[-1][1] if sorted_data else 20.0  # 如果没有数据，设置为默认值
    sorted_data.append((current_time.isoformat(), last_temp))
    
    predictions = predictor.predict_next_hours(sorted_data, hours_ahead=hours_ahead)
    
    if not predictions:
        return jsonify({
            'success': False,
            'error': '预测失败'
        }), 500
    
    result = [{
        'timestamp': timestamp,
        'predicted_temperature': temp
    } for timestamp, temp in predictions]
    
    return jsonify({
        'success': True,
        'predictions': result,
        'hours_ahead': hours_ahead
    })

@app.route('/api/temperature/chart-data', methods=['GET'])
def get_chart_data():
    """获取图表数据，支持多时间范围"""
    range_type = request.args.get('range', default='hour')
    now = datetime.now()
    data = []
    if range_type == 'hour':
        # 近12小时，1小时1点（用当天的小时聚合，取最后12个点）
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hourly_data = processor.get_hourly_data_for_day(start_time)
        current_hour = now.hour
        # 只取当前时间前的12个点
        data = hourly_data[max(0, current_hour-11):current_hour+1]
    elif range_type == 'day':
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        data = processor.get_hourly_data_for_day(start_time)
        if len(data) > 24:
            data = data[-24:]
    elif range_type == 'month':
        start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        data = processor.get_daily_data_for_month(start_time)
        max_days = (now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)).day
        if len(data) > max_days:
            data = data[-max_days:]
    elif range_type == 'year':
        start_time = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        data = processor.get_monthly_data_for_year(start_time)
        if len(data) > 12:
            data = data[-12:]
    else:
        return jsonify({'success': False, 'error': '无效的range参数'}), 400
    # 格式化
    result = []
    for timestamp, temp in data:
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.isoformat()
            result.append({'timestamp': timestamp, 'temperature': float(temp) if temp is not None else None})
        except Exception as e:
            continue
    result.sort(key=lambda x: x['timestamp'])
    return jsonify({'success': True, 'data': result, 'count': len(result)})

@app.route('/api/model/evaluate', methods=['GET'])
def evaluate_model():
    """评估预测模型性能"""
    test_size = request.args.get('test_size', default=48, type=int)
    
    evaluation = predictor.evaluate_model(test_size=test_size)
    
    if 'error' in evaluation:
        return jsonify({
            'success': False,
            'error': evaluation['error']
        }), 400
    
    return jsonify({
        'success': True,
        'evaluation': evaluation
    })

# 系统状态API
@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        # 获取数据库大小
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/temperature.db')
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        return jsonify({
            'success': True,
            'status': {
                'cpu_usage': cpu_usage,
                'memory': {
                    'total': memory_info.total,
                    'available': memory_info.available,
                    'used_percent': memory_info.percent
                },
                'disk': {
                    'total': disk_info.total,
                    'free': disk_info.free,
                    'used_percent': disk_info.percent
                },
                'database': {
                    'size_bytes': db_size,
                    'size_mb': db_size / (1024 * 1024)
                },
                'uptime': {
                    'seconds': int(time.time() - psutil.boot_time()),
                    'formatted': str(timedelta(seconds=int(time.time() - psutil.boot_time())))
                }
            }
        })
    except Exception as e:
        logging.error(f"获取系统状态出错: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 启动模型转换为TensorFlow Lite格式
@app.route('/api/model/convert-to-tflite', methods=['POST'])
def convert_to_tflite():
    """将模型转换为TFLite格式"""
    try:
        # 确保模型存在
        if not os.path.exists('models/lstm_model.h5'):
            return jsonify({
                'success': False,
                'error': '模型文件不存在'
            }), 404
        
        # 加载Keras模型
        model = tf.keras.models.load_model('models/lstm_model.h5')
        
        # 转换为TFLite模型
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        tflite_model = converter.convert()
        
        # 保存TFLite模型
        with open('models/model.tflite', 'wb') as f:
            f.write(tflite_model)
        
        return jsonify({
            'success': True,
            'message': '模型成功转换为TFLite格式',
            'model_path': 'models/model.tflite'
        })
    except Exception as e:
        logging.error(f"模型转换出错: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 启动后台线程
@socketio.on('connect')
def handle_connect():
    logging.info(f"客户端已连接: {request.sid}")
    
    # 发送初始系统状态
    cpu_usage = psutil.cpu_percent(interval=1)
    socketio.emit('system_status', {
        'timestamp': datetime.now().isoformat(),
        'system': {
            'cpu_usage': cpu_usage,
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
    }, room=request.sid)

# 主函数
def main():
    # 启动系统监控线程
    monitor_thread = threading.Thread(target=system_monitor, daemon=True)
    monitor_thread.start()
    
    # 启动模型训练线程
    training_thread = threading.Thread(target=model_training_job, daemon=True)
    training_thread.start()
    
    # 启动Web服务器（使用SocketIO）
    socketio.run(app, host='0.0.0.0', port=8081, debug=True, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()