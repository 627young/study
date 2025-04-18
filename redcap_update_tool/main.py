from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QTextEdit, QFileDialog,
                            QMessageBox, QGroupBox, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import os
import subprocess
import time
from PyQt5.QtCore import QThread, pyqtSignal

class OTAApp(QMainWindow):
    class ImportPackageThread(QThread):
        update_signal = pyqtSignal(str)
        finished_signal = pyqtSignal(list)
    
        def __init__(self, file_paths, burn_path, ota_path):
            super().__init__()
            self.file_paths = file_paths
            self.burn_path = burn_path
            self.ota_path = ota_path
    
        def run(self):
            results = []
            for file_path in self.file_paths:
                try:
                    # 根据文件类型选择目标路径
                    if file_path.endswith('.img'):
                        dest_path = self.burn_path
                    else:
                        dest_path = self.ota_path

                    process = subprocess.Popen(["adb.exe", "push", file_path, dest_path],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            creationflags=subprocess.CREATE_NO_WINDOW,
                                            universal_newlines=True,
                                            bufsize=1)
                    stdout, stderr = process.communicate()
                    result = subprocess.CompletedProcess(args=["adb", "push", file_path, dest_path],
                                                      returncode=process.returncode,
                                                      stdout=stdout,
                                                      stderr=stderr)
                    results.append((file_path, result))
                except Exception as e:
                    results.append((file_path, e))
            self.finished_signal.emit(results)

    def import_ota_package(self):
        ## adb shell检查设备连接状态
        if not self.check_device_connected():
            QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
            return
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择镜像/升级包", "", "ZIP文件 (*.zip);;IMG文件 (*.img);;所有文件 (*)" 
        )
        if file_paths:
            self.log("开始导入镜像/升级包...")
            self.import_thread = self.ImportPackageThread(file_paths, self.burn_path, self.ota_path)
            self.import_thread.update_signal.connect(self.log)
            self.import_thread.finished_signal.connect(self.handle_import_result)
            self.import_thread.start()

    def __init__(self):
        super().__init__()
        self.burn_path = "/online/"
        self.ota_path = "/media/sdcard/ota/"
        self.app_log_path = "/media/sdcard/log/logs/"
        self.mcu_log_path = "/media/sdcard/data/tbox_log/"
        self.configs_path = "/oemdata/configs/tbox_config.cfg.rw"
        self.initUI()
        self.log_content = []

    def initUI(self):
        self.setWindowTitle("RedCap-OTA升级工具 v2.0")
        self.setGeometry(100, 100, 600, 600)
        
        # 设置应用程序图标
        self.setWindowIcon(QIcon(r"./icon/icon.jpg"))
        app.setWindowIcon(QIcon(r"./icon/icon.jpg"))

        # 主窗口布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        
        # 上部按钮区域
        top_btn_layout = QHBoxLayout()


        
        # 第一组按钮（导入和清空）
        group1 = QGroupBox("导入/清空")
        group1_layout = QVBoxLayout()
        
        self.btn_import = QPushButton("导入镜像/升级包")
        self.btn_import.clicked.connect(self.import_ota_package)
        group1_layout.addWidget(self.btn_import)
        
        self.btn_clean = QPushButton("清空升级路径")
        self.btn_clean.clicked.connect(self.clean_target_path)
        group1_layout.addWidget(self.btn_clean)
        
        group1.setLayout(group1_layout)
        top_btn_layout.addWidget(group1)
        
        # 第二组按钮（烧录操作）
        group2 = QGroupBox("烧录/OTA")
        group2_layout = QVBoxLayout()
                   
        self.btn_flash = QPushButton("烧录升级")
        self.btn_flash.clicked.connect(self.execute_flash)
        group2_layout.addWidget(self.btn_flash)
        
        self.btn_ota = QPushButton("OTA升级")
        self.btn_ota.clicked.connect(self.ota_upgrade)
        group2_layout.addWidget(self.btn_ota)
        
        group2.setLayout(group2_layout)
        top_btn_layout.addWidget(group2)
        
        # 第三组按钮（日志操作）
        group3 = QGroupBox("日志/版本")
        group3_layout = QVBoxLayout()
        
        self.btn_export = QPushButton("导出日志")
        self.btn_export.clicked.connect(self.export_logs)
        group3_layout.addWidget(self.btn_export)

        self.btn_view_log = QPushButton("查看日志")
        self.btn_view_log.clicked.connect(self.view_log)
        group3_layout.addWidget(self.btn_view_log)

        # 添加查看版本按钮
        self.btn_version = QPushButton("查看版本")
        self.btn_version.clicked.connect(self.show_version)
        group3_layout.addWidget(self.btn_version)
        
        group3.setLayout(group3_layout)
        top_btn_layout.addWidget(group3)
        
        main_layout.addLayout(top_btn_layout)
        
        # 日志区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)
        
        # 添加清除日志按钮
        self.btn_clear_log = QPushButton("清除窗口")
        self.btn_clear_log.clicked.connect(self.clear_log)
        main_layout.addWidget(self.btn_clear_log)
        
        main_widget.setLayout(main_layout)

    class ClearLogThread(QThread):
        finished_signal = pyqtSignal()
        
        def run(self):
            try:
                # 模拟清除操作，添加延迟
                time.sleep(1)
                self.finished_signal.emit()
            except Exception as e:
                print(f"清除日志时出错：{str(e)}")

    def clear_log(self):
        """清除日志内容"""
        self.clear_thread = self.ClearLogThread()
        self.clear_thread.finished_signal.connect(self.handle_clear_log_finished)
        self.clear_thread.start()

    def handle_clear_log_finished(self):
        """处理清除日志完成"""
        self.log_area.clear()
        self.log_content = []

    def check_device_connected(self):
        """检查设备是否连接"""
        try:
            result = subprocess.run(["adb", "shell", "echo", "connected"],
                                 capture_output=True,
                                 creationflags=subprocess.CREATE_NO_WINDOW,
                                 text=True)
            return "connected" in result.stdout.lower()
        except Exception as e:
            self.log(f"设备连接检查失败：{str(e)}")
            return False

    def import_ota_package(self):
        ## adb shell检查设备连接状态
        if not self.check_device_connected():
            QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
            return
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择镜像/升级包", "", "(*.img;*.zip);" 
        )
        if file_paths:
            self.log("开始导入镜像/升级包...")
            self.import_thread = self.ImportPackageThread(file_paths, self.burn_path, self.ota_path)
            self.import_thread.update_signal.connect(self.log)
            self.import_thread.finished_signal.connect(self.handle_import_result)
            self.import_thread.start()

    def handle_import_result(self, results):
        for file_path, result in results:
            if isinstance(result, Exception):
                self.log(f"镜像/升级包 {os.path.basename(file_path)} 推送失败，请检查设备连接。")
            else:
                self.log(f"已选择镜像/升级包：{os.path.basename(file_path)}")
                if result.stdout:
                    self.log(result.stdout.strip())
                if result.stderr:
                    self.log(result.stderr.strip())
        self.log("导入完成")
        QMessageBox.information(self, "提示", "镜像/升级包导入完成")

    class CleanPathThread(QThread):
        update_signal = pyqtSignal(str)
        finished_signal = pyqtSignal()
    
        def __init__(self, selected_files, ota_path):
            super().__init__()
            self.selected_files = selected_files
            self.ota_path = ota_path
    
        def run(self):
            try:
                if self.selected_files == "全部":
                    result = subprocess.run(["adb", "shell", "rm", "-rf", f"{self.ota_path}*"],
                                         capture_output=True,
                                         creationflags=subprocess.CREATE_NO_WINDOW,
                                         text=True)
                else:
                    result = subprocess.run(["adb", "shell", "rm", "-rf", f"{self.ota_path}{self.selected_files}"],
                                         capture_output=True,
                                         creationflags=subprocess.CREATE_NO_WINDOW,
                                         text=True)
                
                if result.stdout:
                    self.update_signal.emit(result.stdout.strip())
                if result.stderr:
                    self.update_signal.emit(result.stderr.strip())
                
                self.finished_signal.emit()
            except Exception as e:
                self.update_signal.emit(f"操作失败：{str(e)}")
    
    def clean_target_path(self):
        ## adb shell检查设备连接状态
        if not self.check_device_connected():
            QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
            return
        self.log("开始检查升级路径...")
        try:
            # 获取升级路径下的所有文件
            result = subprocess.run(["adb", "shell", "ls -a", f"{self.ota_path}*"],
                                    capture_output=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW,
                                    text=True)
            
            if "No such file or directory" in result.stdout:
                self.log("升级路径为空，无需清理。")
                QMessageBox.information(self, "提示", "升级路径为空，无需清理")
                return

            files = [line.strip() for line in result.stdout.splitlines() if line.strip()]

            # 弹框选择要删除的文件
            selected_files, ok = QInputDialog.getItem(
                self,
                "选择删除文件",
                "请选择要删除的文件（选择'全部'删除所有文件）：",
                ["全部"]+[os.path.basename(f) for f in files],
                0,
                False
            )

            if not ok or not selected_files:
                self.log("用户取消删除操作。")
                return

            self.log(f"开始清理：{selected_files}")
            self.clean_thread = self.CleanPathThread(selected_files, self.ota_path)
            self.clean_thread.update_signal.connect(self.log)
            self.clean_thread.finished_signal.connect(lambda: self.log("清理完成"))
            self.clean_thread.start()
            QMessageBox.information(self, "提示", "清理完成")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"操作失败：{str(e)}")
            self.log(f"操作失败：{str(e)}")


    class FlashThread(QThread):
        update_signal = pyqtSignal(str)
        finished_signal = pyqtSignal()

        def __init__(self, config, burn_path):
            super().__init__()
            self.config = config
            self.burn_path = burn_path  # 添加 burn_path 参数

        def run(self):
            try:
                # 检查并升级boot.img
                self.update_signal.emit("开始检查并升级boot.img...")
                result = subprocess.run(["adb", "shell", "ls", f"{self.burn_path}boot.img"],  # 使用 f-string
                                     capture_output=True, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                error_msg = result.stdout.lower()
                if ("no such file or directory" in error_msg):
                    self.update_signal.emit("未找到boot.img，跳过升级。")
                else:
                    self.update_signal.emit("开始执行升级boot...")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", "shell", "upg_test", "writeraw", self.config["MTD_BOOT"], self.config["BOOT_IMG"]],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit("boot.img 升级完成。")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", "shell", "rm", f"{self.burn_path}boot.img"],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit("boot.img 删除完成。")
                    self.config["NEED_REBOOT"] = 1

                # 检查并升级custapp.img
                self.update_signal.emit("开始检查并升级custapp.img...")
                result = subprocess.run(["adb", "shell", "ls", f"{self.burn_path}custapp.img"],
                                     capture_output=True, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                error_msg = result.stdout.lower()
                if ("no such file or directory" in error_msg):
                    self.update_signal.emit("未找到custapp.img，跳过升级。")
                else:
                    self.update_signal.emit("开始执行升级custapp...")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", "shell", "upg_test", "writeubifs", "custapp", self.config["APP_IMG"]],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                        subprocess.run(["adb", "shell", "upg_test", "writeubifs", "custappbak", self.config["APP_IMG"]],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit("custapp.img 升级完成。")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", "shell", "rm", f"{self.burn_path}custapp.img"],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit("custapp.img 删除完成。")
                    self.config["NEED_REBOOT"] = 1

                # 检查并升级dt_packed.img
                self.update_signal.emit("开始检查并升级dt_packed.img...")
                result = subprocess.run(["adb", "shell", "ls", f"{self.burn_path}dt_packed.img"],
                                     capture_output=True, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                error_msg = result.stdout.lower()
                if ("no such file or directory" in error_msg):
                    self.update_signal.emit("未找到dt_packed.img，跳过升级。")
                else:
                    self.update_signal.emit("开始执行升级dt_packed...")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", " shell", "upg_test", "writeraw", self.config["MTD_DT"], self.config["DT_PACKED_IMG"]],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit("dt_packed.img 升级完成。")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", "shell", "rm", f"{self.burn_path}dt_packed.img"],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit("dt_packed.img 删除完成。")
                    self.config["NEED_REBOOT"] = 1


                # 检查是否需要重启
                if self.config["NEED_REBOOT"] == 1:
                    # 设置boot_flgg为1 adb shell "upg_test setbootflag 1"
                    self.update_signal.emit("检测到需要重启，开始重启...")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", "shell", "upg_test", "setbootflag", "1"],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                        subprocess.run(["adb", "shell", "reboot"],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit("设备正在重启...")

                self.finished_signal.emit()
            except Exception as e:
                self.update_signal.emit(f"烧录失败：{str(e)}")

    def execute_flash(self):
        ## 使用adb shell命令检查设备连接
        if not self.check_device_connected():
            QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
            return
        try:
            result = subprocess.run(["adb", "shell", "echo", "connected"],
                                 capture_output=True,
                                 creationflags=subprocess.CREATE_NO_WINDOW,
                                 text=True)
            if "connected" not in result.stdout.lower():
                QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
                return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设备连接失败：{str(e)}")
            self.log(f"设备连接失败：{str(e)}")
            return
        ## 检查升级路径是否存在.img文件
        try:
            result = subprocess.run(["adb", "shell", "ls", f"{self.burn_path}*.img"],
                                 capture_output=True,
                                 creationflags=subprocess.CREATE_NO_WINDOW,
                                 text=True)
            error_msg = result.stdout.lower()
            if ("no such file or directory" in error_msg or
                "未找到" in error_msg or
                not result.stdout.strip()):
                self.log("未找到任何.img文件，请先导入.img文件。")
                QMessageBox.warning(self, "警告", "未找到任何.img文件！")
                return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"检查升级路径失败：{str(e)}")
            self.log(f"检查升级路径失败：{str(e)}")
            return
        # 创建并初始化burn.log文件
        with open("burn.log", "w") as log_file:
            log_file.write("=== 烧录日志 ===\n")
            log_file.write(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        self.log("开始执行烧录...")
        # 配置路径
        config = {
            "BOOT_IMG": f"{self.burn_path}boot.img",
            "APP_IMG": f"{self.burn_path}custapp.img",
            "DT_PACKED_IMG": f"{self.burn_path}dt_packed.img",
            "MTD_BOOT": "/dev/mtd/mtd28",
            "MTD_DT": "/dev/mtd/mtd21",
            "UNMOUNT_POINT": "/oemapp",
            "NEED_REBOOT": 0  # 标记是否需要重启 
        }

        # 创建并启动烧录线程
        self.flash_thread = self.FlashThread(config, self.burn_path)
        self.flash_thread.update_signal.connect(self.log)
        self.flash_thread.finished_signal.connect(lambda: self.log("烧录完成"))
        self.flash_thread.finished_signal.connect(lambda: QMessageBox.information(self, "提示", "烧录完成"))
        self.flash_thread.start()


    class OTAUpgradeThread(QThread):
        update_signal = pyqtSignal(str)
        finished_signal = pyqtSignal()

        def __init__(self, selected_file, ota_path):
            super().__init__()
            self.selected_file = selected_file
            self.ota_path = ota_path

        def run(self):
            try:
                commands = [
                    'export DBUS_SESSION_BUS_ADDRESS=$(cat /tmp/.default-msgbus-session-address)',
                    'export LD_LIBRARY_PATH=/oemapp/lib:$LD_LIBRARY_PATH',
                    f'/oemapp/app/bin/set_tuid -u {self.ota_path}{self.selected_file}'
                ]

                # 将命令写入临时脚本文件
                script_content = '#!/bin/sh\n' + '\n'.join(commands)
                process = subprocess.Popen(
                    ['adb', 'shell', 'echo', f"'{script_content}'", '>', '/tmp/ota_upgrade.sh', '&&', 'sh', '/tmp/ota_upgrade.sh'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    universal_newlines=True
                )

                # 实时读取并记录输出
                while process.poll() is None:
                    output = process.stdout.readline()
                    if output:
                        self.update_signal.emit(output.strip())
                    error = process.stderr.readline()
                    if error:
                        self.update_signal.emit(error.strip())
                    QApplication.processEvents()

                self.finished_signal.emit()
            except Exception as e:
                self.update_signal.emit(f"OTA升级失败：{str(e)}")

    def ota_upgrade(self):
        try:
            ## 使用adb shell命令检查设备连接
            if not self.check_device_connected():
                QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
                return
            result = subprocess.run(
                ["adb", "shell", "ls", f"{self.ota_path}*.zip"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True
            )
            error_msg = result.stdout.lower()   
            if ("no such file or directory" in error_msg or
                "未找到" in error_msg or
                not result.stdout.strip()):
                self.log("未找到任何.zip升级包，请先导入.zip升级包。")
                QMessageBox.warning(self, "警告", "未找到任何zip升级包！")
                return
            self.log("开始执行OTA升级...")
            zip_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]

            # 选择升级包
            selected_file, ok = QInputDialog.getItem(
                self,
                "选择升级包",
                "请选择要升级的ZIP包：",
                [os.path.basename(f) for f in zip_files],
                0,
                False
            )

            if not ok or not selected_file:
                self.log("用户取消选择升级包。")
                return

            self.log(f"已选择升级包：{selected_file}")

            # 创建并启动OTA升级线程
            self.ota_thread = self.OTAUpgradeThread(selected_file, self.ota_path)
            self.ota_thread.update_signal.connect(self.log)
            self.ota_thread.finished_signal.connect(lambda: QMessageBox.information(self, "提示", "请通过日志查询升级结果"))
            self.ota_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"检测升级包失败：{str(e)}")
            self.log(f"检测升级包失败：{str(e)}")
            return


    class ExportLogsThread(QThread):
        update_signal = pyqtSignal(str)
        finished_signal = pyqtSignal()
    
        def __init__(self, dest_path, selected_log, app_log_path, mcu_log_path):
            super().__init__()
            self.dest_path = dest_path
            self.selected_log = selected_log
            self.app_log_path = app_log_path
            self.mcu_log_path = mcu_log_path

    
        def run(self):
            try:
                if self.selected_log == "全部":
                    process = subprocess.Popen(["adb", "pull", self.app_log_path, self.dest_path],
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE,
                                            creationflags=subprocess.CREATE_NO_WINDOW,
                                            universal_newlines=True)
                    process = subprocess.Popen(["adb", "pull", self.mcu_log_path, self.dest_path],
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE,
                                            creationflags=subprocess.CREATE_NO_WINDOW,
                                            universal_newlines=True)
                else:
                    result = subprocess.run(["adb", "shell", "ls", f"{self.app_log_path}/{self.selected_log}"],
                                         capture_output=True, text=True,
                                         creationflags=subprocess.CREATE_NO_WINDOW)
                    if "no such file or directory" in result.stdout.lower():
                        process = subprocess.Popen(["adb", "pull", f"{self.mcu_log_path}/{self.selected_log}", self.dest_path],
                                                stdout=subprocess.PIPE, 
                                                stderr=subprocess.PIPE,
                                                creationflags=subprocess.CREATE_NO_WINDOW,
                                                universal_newlines=True)
                        
                    else:
                        process = subprocess.Popen(["adb", "pull", f"{self.app_log_path}/{self.selected_log}", self.dest_path],
                                                stdout=subprocess.PIPE, 
                                                stderr=subprocess.PIPE,
                                                creationflags=subprocess.CREATE_NO_WINDOW,
                                                universal_newlines=True)
                
                while process.poll() is None:
                    output = process.stdout.readline()
                    if output:
                        self.update_signal.emit(output.strip())
                    error = process.stderr.readline()
                    if error:
                        self.update_signal.emit(error.strip())
                
                self.finished_signal.emit()
            except Exception as e:
                self.update_signal.emit(f"日志导出失败：{str(e)}")

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
                
                # 创建并启动导出线程
                self.export_thread = self.ExportLogsThread(file_path, selected_log, self.app_log_path, self.mcu_log_path)
                self.export_thread.update_signal.connect(self.log)
                self.export_thread.finished_signal.connect(lambda: self.log("日志导出完成"))
                self.export_thread.start()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取日志列表失败：{str(e)}")
            self.log(f"获取日志列表失败：{str(e)}")

    def log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_content.append(log_message)
        self.log_area.append(log_message)
        self.log_area.ensureCursorVisible()

    def show_version(self):
        """查看版本信息"""
        if not self.check_device_connected():
            QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
            return
        
        try:
            result = subprocess.run(
                ["adb", "shell", "cat", f"{self.configs_path}", "|", "grep", "ware"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True
            )
            
            if result.returncode == 0:
                version_info = result.stdout
                version_info_format = ''
                for line in version_info.splitlines():
                    if "=" and ";" and " " in line:
                        line = line.replace(";", "")
                        line = line.replace('"', "")
                        key, value = line.split("=", 1)
                        version_info_format += f"{key.strip()}: {value.strip().center(20, ' ')}\n"
                self.log(f"\n{version_info_format}")
            else:
                QMessageBox.warning(self, "警告", "获取版本信息失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取版本信息时出错：{str(e)}")

    

    def view_log(self):
        """查看日志"""
        if not self.check_device_connected():
            QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
            return
        
        try:
            # 获取日志文件列表
            log_files = self.acquire_log_list()
            
            if not log_files:
                QMessageBox.information(self, "提示", "没有找到任何日志文件")
                return

            # 选择要查看的日志文件
            selected_log, ok = QInputDialog.getItem(
                self,
                "选择日志文件",
                "请选择要查看的日志文件：",
                log_files,
                0,
                False
            )

            if not ok or not selected_log:
                self.log("用户取消日志查看操作。")
                return

            # 创建并显示日志查看窗口
            self.log_viewer = LogViewerWindow(f"/oemdata/logs/{selected_log}")
            self.log_viewer.show()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取日志列表失败：{str(e)}")
            self.log(f"获取日志列表失败：{str(e)}")
    
    def acquire_log_list(self):
        """获取日志列表"""
        # 获取两个目录的日志文件列表
        result1 = subprocess.run(
            ["adb", "shell", f"ls -lA {self.app_log_path} | awk '{{print $9}}'"],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            text=True
        )
        result2 = subprocess.run(
            ["adb", "shell", f"ls -lA {self.mcu_log_path} | awk '{{print $9}}'"],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            text=True
        )

        log_files = [line.strip() for line in result1.stdout.splitlines() if line.strip()]
        log_files += [line.strip() for line in result2.stdout.splitlines() if line.strip()]
        
        return log_files


class LogViewerWindow(QMainWindow):
    def __init__(self, log_file):
        super().__init__()
        self.log_file = log_file
        self.is_paused = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"{os.path.basename(self.log_file)}")
        self.setGeometry(200, 200, 800, 600)

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 添加暂停按钮
        self.pause_button = QPushButton("暂停滚动")
        self.pause_button.clicked.connect(self.pause_log)
        button_layout.addWidget(self.pause_button)

        # 添加继续按钮
        self.resume_button = QPushButton("继续滚动")
        self.resume_button.clicked.connect(self.resume_log)
        self.resume_button.setEnabled(False)
        button_layout.addWidget(self.resume_button)

        layout.addLayout(button_layout)

        # 日志显示区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        main_widget.setLayout(layout)

        # 启动日志查看线程
        self.view_log_thread = ViewLogThread(self.log_file)
        self.view_log_thread.update_signal.connect(self.update_log)
        self.view_log_thread.finished_signal.connect(lambda: self.log("日志查看结束"))
        self.view_log_thread.start()

    def pause_log(self):
        """暂停日志滚动"""
        self.is_paused = True
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(True)

    def resume_log(self):
        """继续日志滚动"""
        self.is_paused = False
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)

    def update_log(self, message):
        """更新日志内容"""
        if not self.is_paused:
            self.log_area.append(message)
            self.log_area.ensureCursorVisible()

    def log(self, message):
        """直接添加日志内容"""
        self.log_area.append(message)
        self.log_area.ensureCursorVisible()

class ViewLogThread(QThread):
        update_signal = pyqtSignal(str)
        finished_signal = pyqtSignal()

        def __init__(self, log_file):
            super().__init__()
            self.log_file = log_file

        def run(self):
            try:
                process = subprocess.Popen(
                    ['adb', 'shell', 'tail', '-f', self.log_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    universal_newlines=True
                )

                while process.poll() is None:
                    output = process.stdout.readline()
                    if output:
                        self.update_signal.emit(output.strip())
                    QApplication.processEvents()

                self.finished_signal.emit()
            except Exception as e:
                self.update_signal.emit(f"查看日志失败：{str(e)}")

if __name__ == "__main__":
    app = QApplication([])
    window = OTAApp()
    window.show()
    app.exec_()