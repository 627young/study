from models.device_model import DeviceModel
from utils.logger import Logger

class DeviceController:
    def __init__(self):
        self.device_model = DeviceModel()
        
    def check_connection(self):
        """检查设备连接"""
        try:
            if not self.device_model.check_connection():
                return False
            return True
        except Exception as e:
            # self.logger.log(f"设备连接检查失败: {str(e)}")
            return False
            
    def show_version(self):
        """显示版本信息"""
        if not self.device_model.check_connection():
            return
            
        try:
            version_info = self.device_model.get_version_info()
            self.view.show_version_info(version_info)
        except Exception as e:
            # self.view.show_error(f"获取版本信息失败: {str(e)}")
            return
    
    def clean_upgrade_path(self):
        """清空升级路径"""
        self.device_model.check_connection()
        try:
            self.device_model.clean_upgrade_path()
            # self.logger.log("升级路径已清空。")
        except Exception as e:
            # self.logger.log(f"清空升级路径失败: {str(e)}")
            return
    
    def export_logs(self):
        """导出日志"""
        if not self.device_model.check_connection():
            return
        try:
            log_path = self.device_model.export_logs()
            self.view.show_log_path(log_path)
        except Exception as e:
            # self.view.show_error(f"导出日志失败: {str(e)}")
            return