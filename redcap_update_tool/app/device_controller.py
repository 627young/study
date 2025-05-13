from PyQt5.QtCore import QObject, pyqtSignal
from model import DeviceModel

class DeviceController(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.device_model = DeviceModel()

    def check_connection(self):
        try:
            connected = self.device_model.check_connection()
            self.log_signal.emit("设备连接状态检查完成")
            return connected
        except Exception as e:
            self.log_signal.emit(f"连接检查错误: {str(e)}")
            return False

    def get_device_info(self):
        try:
            info = self.device_model.get_device_info()
            self.log_signal.emit("成功获取设备信息")
            return info
        except Exception as e:
            self.log_signal.emit(f"获取设备信息失败: {str(e)}")
            return None

    def clean_upgrade_path(self):
        pass

    def export_logs(self):
        pass

    def show_version(self):
        pass