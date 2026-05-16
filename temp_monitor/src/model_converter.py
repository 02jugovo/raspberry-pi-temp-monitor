import os
import logging
import tensorflow as tf
import numpy as np

# 配置日志
logging.basicConfig(
    filename='logs/model_converter.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ModelConverter:
    def __init__(self, model_dir='models'):
        """初始化模型转换器
        Args:
            model_dir (str): 模型保存目录
        """
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
    
    def convert_to_tflite(self, input_model_path, output_model_path=None, quantize=True):
        """将Keras模型转换为TensorFlow Lite格式
        Args:
            input_model_path (str): 输入Keras模型路径
            output_model_path (str, optional): 输出TFLite模型路径，默认为input_model_path后缀改为.tflite
            quantize (bool): 是否进行量化
        Returns:
            str: TFLite模型路径
        """
        try:
            # 设置默认输出路径
            if output_model_path is None:
                output_model_path = os.path.splitext(input_model_path)[0] + '.tflite'
            
            # 加载Keras模型
            model = tf.keras.models.load_model(input_model_path)
            logging.info(f"成功加载模型: {input_model_path}")
            
            # 创建转换器
            converter = tf.lite.TFLiteConverter.from_keras_model(model)
            
            # 设置转换选项
            if quantize:
                # 启用量化 - 减小模型大小，可能轻微影响精度
                converter.optimizations = [tf.lite.Optimize.DEFAULT]
                logging.info("启用量化优化")
            
            # 执行转换
            tflite_model = converter.convert()
            logging.info("模型转换完成")
            
            # 保存TFLite模型
            with open(output_model_path, 'wb') as f:
                f.write(tflite_model)
            
            logging.info(f"TFLite模型已保存: {output_model_path}")
            
            # 检查模型大小
            original_size = os.path.getsize(input_model_path) / (1024 * 1024)
            tflite_size = os.path.getsize(output_model_path) / (1024 * 1024)
            logging.info(f"原始模型大小: {original_size:.2f} MB")
            logging.info(f"TFLite模型大小: {tflite_size:.2f} MB")
            logging.info(f"压缩比: {original_size / tflite_size:.2f}x")
            
            return output_model_path
        
        except Exception as e:
            logging.error(f"模型转换出错: {e}")
            return None
    
    def create_tflite_interpreter(self, tflite_model_path):
        """创建TFLite解释器
        Args:
            tflite_model_path (str): TFLite模型路径
        Returns:
            tf.lite.Interpreter: TFLite解释器
        """
        try:
            # 加载TFLite模型
            interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
            interpreter.allocate_tensors()
            
            logging.info(f"成功创建TFLite解释器: {tflite_model_path}")
            return interpreter
        
        except Exception as e:
            logging.error(f"创建TFLite解释器出错: {e}")
            return None
    
    def run_tflite_inference(self, interpreter, input_data):
        """使用TFLite解释器进行推理
        Args:
            interpreter (tf.lite.Interpreter): TFLite解释器
            input_data (ndarray): 输入数据
        Returns:
            ndarray: 推理结果
        """
        try:
            # 获取输入和输出张量详情
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            # 设置输入张量
            interpreter.set_tensor(input_details[0]['index'], input_data)
            
            # 运行推理
            interpreter.invoke()
            
            # 获取输出张量
            output_data = interpreter.get_tensor(output_details[0]['index'])
            
            return output_data
        
        except Exception as e:
            logging.error(f"TFLite推理出错: {e}")
            return None
    
    def compare_predictions(self, keras_model_path, tflite_model_path, test_data):
        """比较Keras模型和TFLite模型的预测结果
        Args:
            keras_model_path (str): Keras模型路径
            tflite_model_path (str): TFLite模型路径
            test_data (ndarray): 测试数据
        Returns:
            dict: 比较结果
        """
        try:
            # 加载Keras模型
            keras_model = tf.keras.models.load_model(keras_model_path)
            
            # 运行Keras模型预测
            keras_predictions = keras_model.predict(test_data)
            
            # 创建TFLite解释器
            interpreter = self.create_tflite_interpreter(tflite_model_path)
            
            # 运行TFLite推理
            tflite_predictions = []
            for i in range(len(test_data)):
                result = self.run_tflite_inference(interpreter, np.expand_dims(test_data[i], axis=0))
                tflite_predictions.append(result[0])
            
            tflite_predictions = np.array(tflite_predictions)
            
            # 计算预测差异
            mae = np.mean(np.abs(keras_predictions - tflite_predictions))
            mse = np.mean((keras_predictions - tflite_predictions) ** 2)
            rmse = np.sqrt(mse)
            
            # 计算相对误差
            relative_error = mae / np.mean(np.abs(keras_predictions)) * 100
            
            comparison = {
                'mae': mae,
                'mse': mse,
                'rmse': rmse,
                'relative_error_percent': relative_error
            }
            
            logging.info(f"模型比较结果: {comparison}")
            return comparison
        
        except Exception as e:
            logging.error(f"比较预测结果出错: {e}")
            return None

# 主函数（用于直接运行转换）
if __name__ == "__main__":
    converter = ModelConverter()
    
    # 将模型转换为TFLite格式
    keras_model_path = 'models/lstm_model.h5'
    tflite_model_path = 'models/lstm_model.tflite'
    
    if os.path.exists(keras_model_path):
        tflite_path = converter.convert_to_tflite(keras_model_path, tflite_model_path)
        
        if tflite_path:
            print(f"模型成功转换为TFLite格式: {tflite_path}")
        else:
            print("模型转换失败")
    else:
        print(f"模型文件不存在: {keras_model_path}")
