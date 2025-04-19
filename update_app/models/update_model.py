import os
from config.settings import Settings
from utils.adb_helper import ADBHelper

class UpdateModel:
    def __init__(self):
        self.adb = ADBHelper()
        
    def import_package(self, file_paths):
        """导入升级包"""
        results = []
        for file_path in file_paths:
            try:
                dest_path = Settings.BURN_PATH if file_path.endswith('.img') else Settings.OTA_PATH
                result = self.adb.push_file(file_path, dest_path)
                results.append((file_path, result))
            except Exception as e:
                results.append((file_path, e))
        return results
        
    def execute_flash(self, config):
        """执行烧录"""
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
        """执行OTA升级"""
        try:
            commands = [
                'export DBUS_SESSION_BUS_ADDRESS=$(cat /tmp/.default-msgbus-session-address)',
                'export LD_LIBRARY_PATH=/oemapp/lib:$LD_LIBRARY_PATH',
                f'/oemapp/app/bin/set_tuid -u {Settings.OTA_PATH}{package_name}'
            ]
            return self.adb.execute_script(commands)
        except Exception as e:
            raise Exception(f"OTA升级失败: {str(e)}")