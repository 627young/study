from PyQt5.QtCore import QObject, pyqtSignal
from model import UpdateModel

class UpdateController(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.model = UpdateModel()

    def check_version(self):
        try:
            current_ver = self.model.get_current_version()
            latest_ver = self.model.get_latest_version()
            self.log_signal.emit(f"当前版本: {current_ver} 最新版本: {latest_ver}")
            return latest_ver > current_ver
        except Exception as e:
            self.log_signal.emit(f"版本检查失败: {str(e)}")
            return False

    def execute_update(self):
        if not self.check_version():
            self.log_signal.emit("当前已是最新版本")
            return

        try:
            self.log_signal.emit("开始执行固件升级...")
            success = self.model.download_update()
            if success:
                self.model.apply_update()
                self.log_signal.emit("升级成功，请重启设备")
            else:
                self.log_signal.emit("下载更新包失败")
        except Exception as e:
            self.log_signal.emit(f"升级过程中发生错误: {str(e)}")

    def import_package(self, file_paths):
        try:
            self.log_signal.emit("开始导入更新包...")
            results = self.model.import_package(file_paths)
            for result in results:
                self.log_signal.emit(result)
            if any("失败" in result or "未连接" in result for result in results):
                self.log_signal.emit("导入过程中出现错误")
            else:
                self.log_signal.emit("导入成功")
        except Exception as e:
            self.log_signal.emit(f"导入更新包失败: {str(e)}")

    def execute_flash(self, config):
        try:
            self.log_signal.emit("开始执行固件烧录...")
            self.model.execute_flash(config)
            self.log_signal.emit("烧录成功")
        except Exception as e:
            self.log_signal.emit(f"固件烧录失败: {str(e)}")

    def execute_ota(self, package_name):
        pass