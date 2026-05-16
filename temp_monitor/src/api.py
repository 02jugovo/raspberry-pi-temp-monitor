from flask import Flask, jsonify, request
import logging
from database import Database
from sensor import TemperatureSensor
from datetime import datetime

# 配置日志
logging.basicConfig(
    filename='logs/api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
db = Database()
sensor = TemperatureSensor()

@app.route('/api/temperature/current', methods=['GET'])
def get_current_temperature():
    """获取当前温度"""
    temp = sensor.get_temperature()
    if temp is not None:
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
    """获取历史温度数据"""
    # 获取查询参数
    start_time = request.args.get('start')
    end_time = request.args.get('end')
    limit = request.args.get('limit', default=100, type=int)
    
    # 查询数据
    data = db.get_temperature_data(start_time, end_time, limit)
    
    # 格式化返回结果
    result = [{
        'timestamp': row[0],
        'temperature': row[1]
    } for row in data]
    
    return jsonify({
        'success': True,
        'data': result,
        'count': len(result)
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取系统配置"""
    configs = {
        'sampling_interval': db.get_config('sampling_interval', '600'),
        'alert_threshold': db.get_config('alert_threshold', '35.0')
    }
    
    return jsonify({
        'success': True,
        'config': configs
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新系统配置"""
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
        
    # 更新配置
    for key, value in data.items():
        db.set_config(key, str(value))
        
    return jsonify({
        'success': True,
        'message': 'Configuration updated'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
