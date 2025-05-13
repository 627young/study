from PyQt5.QtCore import QObject, pyqtSignal, Qt, QThread
from PyQt5.QtGui import QIcon
from model import AdbModel, PackageImporter
from view import MainView
import subprocess
import os

from device_controller import DeviceController
from update_controller import UpdateController

class MainController(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # 初始化数据模型
        self.model = AdbModel()

        # 初始化子控制器
        self.device_ctrl = DeviceController()
        self.update_ctrl = UpdateController()

        # 注入主控制器引用到子控制器
        self.device_ctrl.main_ctrl = self
        self.update_ctrl.main_ctrl = self

        # 初始化视图
        self.view = MainView(self)
        self.connect_signals()

    def connect_signals(self):
        # 连接按钮事件
        # 连接设备控制信号
        self.device_ctrl.log_signal.connect(self.view.append_log)
        # 连接升级控制信号
        self.update_ctrl.log_signal.connect(self.view.append_log)
        # 连接日志信号
        self.log_signal.connect(self.view.log_area.append)

    def handle_import(self):
        if not self.model.check_device_connected():
            self.log_signal.emit("设备未连接")
            return

        file_path = self.view.select_package_file()
        if not file_path:
            self.log_signal.emit("未选择任何文件")
            return

        try:
            self.log_signal.emit(f"开始推送文件: {os.path.basename(file_path)}")
            result = self.model.push_package(file_path)
            if result:
                self.log_signal.emit("文件推送成功")
                self.view.update_progress(100)
            else:
                self.log_signal.emit("文件推送失败")
        except Exception as e:
            self.log_signal.emit(f"发生异常: {str(e)}")

    def handle_clean(self):
        try:
            if self.model.clean_temp_directory():
                self.log_signal.emit("临时目录清理成功")
            else:
                self.log_signal.emit("清理失败，请检查权限")
        except Exception as e:
            self.log_signal.emit(f"清理异常: {str(e)}")

    def handle_flash(self):
        self.flash_thread = self.model.start_flash_thread()
        self.flash_thread.progress_updated.connect(self.view.update_progress)
        self.flash_thread.finished.connect(lambda: self.log_signal.emit("烧录完成"))
        self.flash_thread.error_occurred.connect(lambda e: self.log_signal.emit(f"烧录错误: {e}"))
        self.flash_thread.start()

    def set_window_icon(self):
        app_icon = QIcon()
        app_icon.addFile(':/icon/icon.png', Qt.Normal, QIcon.Off)