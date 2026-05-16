#!/usr/bin/env python3
import os
import sys
import time
import logging
import requests
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Web服务器地址
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8082")

def test_api_endpoint(url, method="get", data=None):
    """测试API端点
    
    Args:
        url (str): API端点URL
        method (str): 请求方法，默认为get
        data (dict, optional): POST请求数据
        
    Returns:
        tuple: (success, response_data)
    """
    try:
        if method.lower() == "get":
            response = requests.get(url, timeout=5)
        elif method.lower() == "post":
            response = requests.post(url, json=data, timeout=5)
            
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Error: Status code {response.status_code}"
    except Exception as e:
        return False, f"Exception: {e}"

def run_tests():
    """运行所有测试"""
    tests_passed = 0
    tests_failed = 0
    
    # 测试1：获取当前温度
    logging.info("Test 1: Get current temperature")
    success, data = test_api_endpoint(f"{SERVER_URL}/api/temperature/current")
    if success and data.get('success'):
        logging.info("✓ Current temperature: %s°C", data.get('temperature'))
        tests_passed += 1
    else:
        logging.error("✗ Failed to get current temperature: %s", data)
        tests_failed += 1
    
    # 测试2：获取历史数据
    logging.info("Test 2: Get temperature history")
    success, data = test_api_endpoint(f"{SERVER_URL}/api/temperature/history")
    if success and data.get('success'):
        logging.info("✓ Retrieved %d history records", data.get('count'))
        tests_passed += 1
    else:
        logging.error("✗ Failed to get temperature history: %s", data)
        tests_failed += 1
    
    # 测试3：获取统计数据
    logging.info("Test 3: Get temperature statistics")
    success, data = test_api_endpoint(f"{SERVER_URL}/api/temperature/stats")
    if success and data.get('success'):
        logging.info("✓ Statistics: Mean=%s°C, Min=%s°C, Max=%s°C", 
                  data.get('stats').get('mean'),
                  data.get('stats').get('min'),
                  data.get('stats').get('max'))
        tests_passed += 1
    else:
        logging.error("✗ Failed to get temperature statistics: %s", data)
        tests_failed += 1
    
    # 测试4：获取预测数据
    logging.info("Test 4: Get temperature prediction")
    success, data = test_api_endpoint(f"{SERVER_URL}/api/temperature/predict")
    if success and data.get('success'):
        logging.info("✓ Predictions retrieved for next %d hours", data.get('hours_ahead'))
        tests_passed += 1
    else:
        logging.error("✗ Failed to get temperature prediction: %s", data)
        tests_failed += 1
    
    # 测试5：更新配置
    logging.info("Test 5: Update configuration")
    config_data = {
        "sampling_interval": "300"  # 5分钟
    }
    success, data = test_api_endpoint(f"{SERVER_URL}/api/config", method="post", data=config_data)
    if success and data.get('success'):
        logging.info("✓ Configuration updated successfully")
        tests_passed += 1
    else:
        logging.error("✗ Failed to update configuration: %s", data)
        tests_failed += 1
    
    # 测试6：获取图表数据
    logging.info("Test 6: Get chart data")
    success, data = test_api_endpoint(f"{SERVER_URL}/api/temperature/chart-data")
    if success and data.get('success'):
        logging.info("✓ Retrieved %d chart data points", data.get('count'))
        tests_passed += 1
    else:
        logging.error("✗ Failed to get chart data: %s", data)
        tests_failed += 1
    
    # 测试7：获取模型评估结果
    logging.info("Test 7: Get model evaluation")
    success, data = test_api_endpoint(f"{SERVER_URL}/api/model/evaluate")
    if success and data.get('success'):
        logging.info("✓ Model evaluation: MAE=%s°C, RMSE=%s°C", 
                  data.get('evaluation').get('mae'),
                  data.get('evaluation').get('rmse'))
        tests_passed += 1
    else:
        logging.error("✗ Failed to get model evaluation: %s", data)
        tests_failed += 1
    
    # 打印测试结果摘要
    logging.info("Test Summary: %d passed, %d failed", tests_passed, tests_failed)
    if tests_failed == 0:
        logging.info("All tests passed!")
    
if __name__ == "__main__":
    run_tests()
