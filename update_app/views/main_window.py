from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QPushButton, QTextEdit, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from config.settings import Settings

class MainWindow(QMainWindow):
    def __init__(self, device_controller, update_controller):
        """初始化主窗口"""
        super().__init__()
        self.device_controller = device_controller
        self.update_controller = update_controller
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(Settings.WINDOW_TITLE)
        self.setGeometry(*Settings.WINDOW_GEOMETRY)
        self.setWindowIcon(QIcon(Settings.WINDOW_ICON))
        
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        
        # 添加功能分组
        top_layout = QHBoxLayout()
        top_layout.addWidget(self._create_import_group())
        top_layout.addWidget(self._create_update_group())
        top_layout.addWidget(self._create_log_group())
        main_layout.addLayout(top_layout)
        
        # 添加日志区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)
        
        # # 添加清除按钮
        # self.btn_clear = QPushButton("清除窗口")
        # self.btn_clear.clicked.connect(self.clear_log)
        # main_layout.addWidget(self.btn_clear)
        
        main_widget.setLayout(main_layout)

        self._connect_signals()
        
    def _create_import_group(self):
        """创建导入分组"""
        group = QGroupBox("导入/清空")
        layout = QVBoxLayout()
        
        self.btn_import = QPushButton("导入镜像/升级包")
        self.btn_import.clicked.connect(self.update_controller.import_package)
        layout.addWidget(self.btn_import)
        
        self.btn_clean = QPushButton("清空升级路径")
        self.btn_clean.clicked.connect(self.device_controller.clean_upgrade_path)
        layout.addWidget(self.btn_clean)
        
        group.setLayout(layout)
        return group
        
    def _create_update_group(self):
        """创建升级分组"""
        group = QGroupBox("烧录/OTA")
        layout = QVBoxLayout()
        
        self.btn_flash = QPushButton("烧录升级")
        self.btn_flash.clicked.connect(self.update_controller.execute_flash)
        layout.addWidget(self.btn_flash)
        
        self.btn_ota = QPushButton("OTA升级")
        self.btn_ota.clicked.connect(self.update_controller.execute_ota)
        layout.addWidget(self.btn_ota)
        
        group.setLayout(layout)
        return group
        
    def _create_log_group(self):
        """创建日志分组"""
        group = QGroupBox("日志/版本")
        layout = QVBoxLayout()
        
        self.btn_export = QPushButton("导出日志")
        self.btn_export.clicked.connect(self.device_controller.export_logs)
        layout.addWidget(self.btn_export)
    
        # self.btn_view.clicked.connect(self.device_controller.view_log)
        # layout.addWidget(self.btn_view)
        
        self.btn_version = QPushButton("查看版本")
        self.btn_version.clicked.connect(self.device_controller.show_version)
        layout.addWidget(self.btn_version)
        
        group.setLayout(layout)
        return group
    def _connect_signals(self):
        """Connect UI signals to controller methods"""
        if self.update_controller:
            self.btn_import.clicked.connect(self.update_controller.import_package)
        if self.device_controller:
            self.btn_clean.clicked.connect(self.device_controller.clean_upgrade_path)