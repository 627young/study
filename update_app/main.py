from PyQt5.QtWidgets import QApplication
from views.main_window import MainWindow
from controllers.device_controller import DeviceController
from controllers.update_controller import UpdateController
from models.device_model import DeviceModel
from models.update_model import UpdateModel
from utils.adb_helper import ADBHelper
from utils.logger import Logger

def main():
    app = QApplication([])

    # 初始化控制器
    device_controller = DeviceController()
    update_controller = UpdateController()

    # 初始化主窗口
    main_window = MainWindow(device_controller, update_controller)

    # 显示窗口
    main_window.show()
    return app.exec_()

if __name__ == "__main__":
    main()