from src.predictorS import TemperaturePredictor

predictor = TemperaturePredictor()
data = predictor.get_training_data(days=1)
print(f"获取的数据数量: {len(data) if data else 0}")

if data and len(data) > 24:
    predictions = predictor.predict_next_hours(data, hours_ahead=3)
    print("预测结果:", predictions)
else:
    print("数据不足，无法进行预测")
