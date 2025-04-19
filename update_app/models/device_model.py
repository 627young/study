import subprocess
from config.settings import Settings
from utils.adb_helper import ADBHelper
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QInputDialog

class DeviceModel:
    def __init__(self):
        self.adb = ADBHelper()
        
    def check_connection(self):
        """检查设备连接状态"""
        try:
            result = self.adb.execute_command(["shell", "echo", "connected"])
            if "connected" not in result.stdout.lower():
                QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
        except Exception:
            print("设备未连接")
            return False
            
    def get_version_info(self):
        """获取版本信息"""
        try:
            result = self.adb.execute_command(
                ["shell", "cat", Settings.CONFIGS_PATH, "|", "grep", "ware"]
            )
            return self._parse_version_info(result.stdout)
        except Exception as e:
            raise Exception(f"获取版本信息失败: {str(e)}")
            
    def parse_version_info(self, version_str):
        """解析版本信息"""
        version_info = {}
        for line in version_str.splitlines():
            if "=" in line and ";" in line:
                line = line.replace(";", "").replace('"', "")
                key, value = line.split("=", 1)
                version_info[key.strip()] = value.strip()
        return version_info
    
    def export_logs(self):
        # 检查设备连接状态
        if not self.check_device_connected():
            QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
            return
        
        try:
            # 获取日志列表
            log_files = self.acquire_log_list()

            if not log_files:
                QMessageBox.information(self, "提示", "没有找到任何日志文件")
                return

            # 让用户选择要导出的日志
            selected_log, ok = QInputDialog.getItem(
                self,
                "选择日志文件",
                "请选择要导出的日志文件（选择'全部'导出所有日志）：",
                ["全部"] + log_files,
                0,
                False
            )
            
            if not ok or not selected_log:
                self.log("用户取消日志导出操作。")
                return
                
            file_path = QFileDialog.getExistingDirectory(
                self, "选择保存日志的目录"
            )

            if file_path:
                self.log("开始导出日志...")
                if selected_log == "全部":
                    for log_file in log_files:
                        self.adb.pull_file(
                            f"{Settings.MCU_LOG_PATH}{log_file}",
                            f"{file_path}/{log_file}"
                        )
                else:
                    self.adb.pull_file(
                        f"{Settings.MCU_LOG_PATH}{selected_log}",
                        f"{file_path}/{selected_log}"
                    )
                self.log("日志导出完成。")
                QMessageBox.information(self, "提示", "日志导出成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"日志导出失败: {str(e)}")
