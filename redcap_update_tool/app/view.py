from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class MainView(QMainWindow):
    def __init__(self, main_controller):
        super().__init__()
        self.main_controller = main_controller
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        self.setWindowTitle('固件升级工具')
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        # 功能区域布局
        top_layout = QHBoxLayout()
        top_layout.addWidget(self._create_import_group())
        top_layout.addWidget(self._create_update_group())
        top_layout.addWidget(self._create_log_group())
        main_layout.addLayout(top_layout)

        # 日志显示区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)

        main_widget.setLayout(main_layout)

    def _create_import_group(self):
        group = QGroupBox("导入/清空")
        layout = QVBoxLayout()

        self.btn_import = QPushButton("导入镜像/升级包")
        self.btn_clean = QPushButton("清空升级路径")

        layout.addWidget(self.btn_import)
        layout.addWidget(self.btn_clean)
        group.setLayout(layout)
        return group

    def _create_update_group(self):
        group = QGroupBox("烧录/OTA")
        layout = QVBoxLayout()

        self.btn_flash = QPushButton("烧录升级")
        self.btn_ota = QPushButton("OTA升级")

        layout.addWidget(self.btn_flash)
        layout.addWidget(self.btn_ota)
        group.setLayout(layout)
        return group

    def _create_log_group(self):
        group = QGroupBox("日志/版本")
        layout = QVBoxLayout()

        self.btn_export = QPushButton("导出日志")
        self.btn_version = QPushButton("查看版本")

        layout.addWidget(self.btn_export)
        layout.addWidget(self.btn_version)
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        self.btn_import.clicked.connect(self.main_controller.update_ctrl.import_package)
        self.btn_clean.clicked.connect(self.main_controller.device_ctrl.clean_upgrade_path)
        self.btn_flash.clicked.connect(self.main_controller.update_ctrl.execute_flash)
        self.btn_ota.clicked.connect(self.main_controller.update_ctrl.execute_ota)
        self.btn_export.clicked.connect(self.main_controller.device_ctrl.export_logs)
        self.btn_version.clicked.connect(self.main_controller.device_ctrl.show_version)

    def append_log(self, message):
        self.log_area.append(message)

    def set_window_icon(self, icon_path):
        self.setWindowIcon(QIcon(icon_path))