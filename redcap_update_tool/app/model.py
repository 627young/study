from PyQt5.QtCore import QThread, pyqtSignal
from adb_helper import ADBHelper
from settings import Settings
import subprocess
import os

class AdbModel:
    def __init__(self):
        self.burn_path = "/online/"
        self.ota_path = "/media/sdcard/ota/"
        self.app_log_path = "/media/sdcard/log/logs/"
        self.mcu_log_path = "/media/sdcard/data/tbox_log/"

    def check_device_connected(self):
        try:
            output = subprocess.check_output(['adb', 'devices'], timeout=5)
            return 'device' in output.decode()
        except subprocess.CalledProcessError:
            return False

    def push_package(self, file_path):
        temp_dir = '/sdcard/temp'
        subprocess.run(['adb', 'shell', 'mkdir', '-p', temp_dir])
        result = subprocess.run(['adb', 'push', file_path, temp_dir], capture_output=True)
        return result.returncode == 0

    def clean_temp_directory(self):
        try:
            subprocess.run(['adb', 'shell', 'rm', '-rf', '/sdcard/temp/*'])
            return True
        except Exception:
            return False

class FlashThread(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            for i in range(1, 101):
                self.progress_updated.emit(i)
                self.msleep(50)
            subprocess.check_output(['adb', 'reboot'], timeout=30)
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def start_flash_thread(self):
        return FlashThread()

class DeviceModel:
    def __init__(self):
        self.adb = ADBHelper()

    def check_connection(self):
        try:
            result = self.adb.execute_command(['devices'])
            connected_devices = [line for line in result.stdout.split('\n')
                               if 'device' in line and 'offline' not in line]
            return len(connected_devices) > 0
        except Exception as e:
            raise ConnectionError(f"设备连接检查失败: {str(e)}")

    def get_device_info(self):
        try:
            manufacturer = self.adb.execute_command(['shell', 'getprop', 'ro.product.manufacturer']).stdout.strip()
            model = self.adb.execute_command(['shell', 'getprop', 'ro.product.model']).stdout.strip()
            android_version = self.adb.execute_command(['shell', 'getprop', 'ro.build.version.release']).stdout.strip()
            return {
                "manufacturer": manufacturer,
                "model": model,
                "android_version": android_version
            }
        except Exception as e:
            raise RuntimeError(f"获取设备信息失败: {str(e)}")

class PackageImporter(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(list)

    def __init__(self, file_paths, burn_path, ota_path):
        super().__init__()
        self.file_paths = file_paths
        self.burn_path = burn_path
        self.ota_path = ota_path

    def run(self):
        # 迁移后的ADB操作代码将放在这里
        pass


class UpdateModel:
    def __init__(self):
        self.adb = ADBHelper()

    def import_package(self, file_paths):
        results = []
        try:
            if not self.adb.check_connection():
                results.append("设备未连接")
                return results
        except Exception as e:
            results.append(f"连接检查失败: {str(e)}")
            return results

        for file_path in file_paths:
            if not os.path.exists(file_path):
                results.append(f"{file_path} 不存在")
                continue
            if file_path.endswith(".zip"):
                dest_path = os.path.join(Settings.OTA_PATH, os.path.basename(file_path))
                try:
                    push_result = self.adb.push_file(file_path, dest_path)
                    if push_result.returncode == 0:
                        results.append(f"{file_path} 导入成功")
                    else:
                        results.append(f"{file_path} 导入失败: {push_result.stderr}")
                except Exception as e:
                    results.append(f"{file_path} 导入异常: {str(e)}")
            elif file_path.endswith(".img"):
                dest_path = os.path.join(Settings.BURN_PATH, os.path.basename(file_path))
                try:
                    push_result = self.adb.push_file(file_path, dest_path)
                    if push_result.returncode == 0:
                        results.append(f"{file_path} 导入成功")
                    else:
                        results.append(f"{file_path} 导入失败: {push_result.stderr}")
                except Exception as e:
                    results.append(f"{file_path} 导入异常: {str(e)}")
            else:
                results.append(f"{file_path} 格式不支持")
        return results

    def execute_flash(self, config):
        try:
            if self._check_and_flash_boot(config):
                config["NEED_REBOOT"] = 1
            if self._check_and_flash_custapp(config):
                config["NEED_REBOOT"] = 1
            if self._check_and_flash_dt(config):
                config["NEED_REBOOT"] = 1

            if config["NEED_REBOOT"] == 1:
                self._set_boot_flag()
                self.adb.reboot()

        except Exception as e:
            raise Exception(f"烧录失败: {str(e)}")

    def execute_ota(self, package_name):
        try:
            commands = [
                'export DBUS_SESSION_BUS_ADDRESS=$(cat /tmp/.default-msgbus-session-address)',
                'export LD_LIBRARY_PATH=/oemapp/lib:$LD_LIBRARY_PATH',
                f'/oemapp/app/bin/set_tuid -u {Settings.OTA_PATH}{package_name}'
            ]
            return self.adb.execute_script(commands)
        except Exception as e:
            raise Exception(f"OTA升级失败: {str(e)}")