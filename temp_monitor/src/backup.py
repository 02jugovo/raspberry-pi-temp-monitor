import os
import shutil
import sqlite3
import logging
import time
from datetime import datetime
import glob
import zipfile

# 配置日志
logging.basicConfig(
    filename='logs/backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BackupManager:
    def __init__(self, db_path='data/temperature.db', backup_dir='backups'):
        """初始化备份管理器
        Args:
            db_path (str): 数据库文件路径
            backup_dir (str): 备份目录
        """
        self.db_path = os.path.abspath(db_path)
        self.backup_dir = os.path.abspath(backup_dir)
        
        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self):
        """创建数据库备份"""
        try:
            if not os.path.exists(self.db_path):
                logging.error(f"数据库文件不存在: {self.db_path}")
                return False
            
            # 创建备份文件名（使用时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f"temperature_db_backup_{timestamp}.db")
            
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_file)
            
            # 验证备份是否成功
            if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
                logging.info(f"数据库备份成功: {backup_file}")
                
                # 创建压缩备份
                zip_file = f"{backup_file}.zip"
                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_file, os.path.basename(backup_file))
                
                # 删除未压缩的备份
                os.remove(backup_file)
                
                logging.info(f"创建压缩备份: {zip_file}")
                
                # 清理旧备份
                self._cleanup_old_backups()
                
                return True
            else:
                logging.error(f"备份验证失败: {backup_file}")
                return False
        
        except Exception as e:
            logging.error(f"创建备份时出错: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count=10):
        """清理旧备份文件，只保留最新的几个
        Args:
            keep_count (int): 保留的备份数量
        """
        try:
            # 获取所有备份文件
            backup_files = glob.glob(os.path.join(self.backup_dir, "temperature_db_backup_*.zip"))
            
            # 按修改时间排序
            backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # 删除多余的旧备份
            if len(backup_files) > keep_count:
                for old_file in backup_files[keep_count:]:
                    os.remove(old_file)
                    logging.info(f"已删除旧备份: {old_file}")
        
        except Exception as e:
            logging.error(f"清理旧备份时出错: {e}")
    
    def restore_from_backup(self, backup_file=None):
        """从备份恢复数据库
        Args:
            backup_file (str, optional): 指定备份文件路径，默认使用最新备份
        Returns:
            bool: 恢复是否成功
        """
        try:
            # 如果未指定备份文件，使用最新的备份
            if backup_file is None:
                backup_files = glob.glob(os.path.join(self.backup_dir, "temperature_db_backup_*.zip"))
                
                if not backup_files:
                    logging.error("没有可用的备份文件")
                    return False
                
                # 按修改时间排序，选择最新的备份
                backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                backup_file = backup_files[0]
            
            # 检查备份文件是否存在
            if not os.path.exists(backup_file):
                logging.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 提取备份文件
            temp_dir = os.path.join(self.backup_dir, "temp_restore")
            os.makedirs(temp_dir, exist_ok=True)
            
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 获取解压后的DB文件
            extracted_files = glob.glob(os.path.join(temp_dir, "temperature_db_backup_*.db"))
            
            if not extracted_files:
                logging.error(f"从压缩文件中未找到数据库备份: {backup_file}")
                shutil.rmtree(temp_dir)
                return False
            
            restored_db = extracted_files[0]
            
            # 确保原数据库没有连接
            time.sleep(1)  # 等待可能的连接关闭
            
            # 创建原数据库的备份（以防恢复失败）
            if os.path.exists(self.db_path):
                safety_backup = f"{self.db_path}.before_restore"
                shutil.copy2(self.db_path, safety_backup)
            
            # 恢复数据库
            shutil.copy2(restored_db, self.db_path)
            
            # 清理临时文件
            shutil.rmtree(temp_dir)
            
            logging.info(f"成功从备份恢复: {backup_file}")
            return True
        
        except Exception as e:
            logging.error(f"从备份恢复时出错: {e}")
            return False
    
    def verify_database(self):
        """验证数据库完整性"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 执行简单查询来验证数据库
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            conn.close()
            
            if result and result[0] == "ok":
                logging.info("数据库完整性检查通过")
                return True
            else:
                logging.error(f"数据库完整性检查失败: {result}")
                return False
        
        except Exception as e:
            logging.error(f"验证数据库时出错: {e}")
            return False

# 主函数（用于直接运行备份）
if __name__ == "__main__":
    backup_manager = BackupManager()
    
    # 验证数据库
    if backup_manager.verify_database():
        # 创建备份
        if backup_manager.create_backup():
            print("数据库备份成功")
        else:
            print("数据库备份失败")
    else:
        print("数据库验证失败，尝试从备份恢复")
        if backup_manager.restore_from_backup():
            print("从备份恢复成功")
        else:
            print("从备份恢复失败")
