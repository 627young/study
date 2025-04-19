from models.update_model import UpdateModel
from models.device_model import DeviceModel

class UpdateController:
    def __init__(self):
        self.updare_model = UpdateModel()
        self.device_model = DeviceModel()

        # self.logger = Logger()
        
    def import_package(self, file_paths):
        """导入升级包"""
        self.device_model.check_connection()
        try:
            results = self.updare_model.import_package(file_paths)
            self._handle_import_results(results)
        except Exception as e:
            # self.view.show_error(f"导入失败: {str(e)}")
            return
            
    def execute_flash(self):
        """执行烧录"""
        self.device_model.check_connection()
        try:
            config = self._prepare_flash_config()
            self.model.execute_flash(config)
            # self.view.show_success("烧录完成")
        except Exception as e:
            # self.view.show_error(f"烧录失败: {str(e)}")
            return
            
    def execute_ota(self, package_name):
        """执行OTA升级"""
        self.device_model.check_connection()
            
        try:
            result = self.model.execute_ota(package_name)
            self._handle_ota_result(result)
        except Exception as e:
            # self.view.show_error(f"OTA升级失败: {str(e)}")
            return