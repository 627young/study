from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QTextEdit, QFileDialog,
                            QMessageBox, QGroupBox, QInputDialog, QDialog, QStackedWidget,
                            QProgressBar, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import os
import shlex
import shutil
import subprocess
import time
from PyQt5.QtCore import QThread, pyqtSignal

os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = '1'
os.environ['OPENSSL_CONF'] = '/dev/null'  # 或者设置为空配置

class ImportProgressDialog(QDialog):
    def __init__(self, total_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("正在导入文件")
        self.setWindowModality(Qt.WindowModal)
        self.setFixedSize(400, 200)

        # 主布局
        layout = QVBoxLayout()

        # 总进度标签和进度条
        self.total_label = QLabel(f"总进度: 0/{total_files}")
        layout.addWidget(self.total_label)

        self.total_progress = QProgressBar()
        self.total_progress.setMaximum(total_files)
        self.total_progress.setValue(0)
        layout.addWidget(self.total_progress)

        # 当前文件进度标签和进度条
        self.current_label = QLabel("当前文件: 准备中...")
        layout.addWidget(self.current_label)

        self.current_progress = QProgressBar()
        self.current_progress.setMaximum(100)
        self.current_progress.setValue(0)
        layout.addWidget(self.current_progress)

        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def update_total_progress(self, current, total):
        """更新总进度"""
        self.total_progress.setMaximum(total)
        self.total_progress.setValue(current)
        self.total_label.setText(f"总进度: {current}/{total}")
        # 强制刷新界面
        QApplication.processEvents()

    def update_current_file_progress(self, percent, filename):
        """更新当前文件进度"""
        self.current_progress.setValue(percent)
        self.current_label.setText(f"当前文件: {filename}")

class OTAApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.burn_path = "/online/burn_dir/"
        self.ota_path = "/media/sdcard/ota/"
        self.app_log_path = "/media/sdcard/log/logs/"
        self.mcu_log_path = "/media/sdcard/data/tbox_log/"
        self.configs_path = "/oemdata/configs/tbox_config.cfg.rw"
        self.initUI()
        self.log_content = []
        self.log_viewer = []
        # 导入取消标记
        self.import_cancelled = False
        self.last_scp_ip = ""

    def initUI(self):
        self.setWindowTitle("RedCap-OTA升级工具 v4.4")
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

        self.btn_import = QPushButton("ADB导入")
        self.btn_import.clicked.connect(self.import_ota_package)
        group1_layout.addWidget(self.btn_import)

        self.btn_import_scp = QPushButton("局域网导入")
        self.btn_import_scp.clicked.connect(self.import_ota_package_scp)
        group1_layout.addWidget(self.btn_import_scp)

        self.btn_clean = QPushButton("清空升级路径")
        self.btn_clean.clicked.connect(self.clean_target_path)
        group1_layout.addWidget(self.btn_clean)

        group1.setLayout(group1_layout)
        top_btn_layout.addWidget(group1)

        # 第二组按钮（烧录操作）
        group2 = QGroupBox("烧录/本地升级")
        group2_layout = QVBoxLayout()

        self.btn_flash = QPushButton("烧录升级")
        self.btn_flash.clicked.connect(self.execute_flash)
        group2_layout.addWidget(self.btn_flash)

        self.btn_ota = QPushButton("本地升级")
        self.btn_ota.clicked.connect(self.ota_upgrade)
        group2_layout.addWidget(self.btn_ota)

        self.btn_ssh_upgrade = QPushButton("局域网升级")
        self.btn_ssh_upgrade.clicked.connect(self.ssh_upgrade)
        group2_layout.addWidget(self.btn_ssh_upgrade)

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

    class ImportPackageThread(QThread):
        update_signal = pyqtSignal(str)
        finished_signal = pyqtSignal(list)
        # 新增：单文件与整体进度信号
        file_progress_signal = pyqtSignal(int, str)  # percent, filename
        overall_progress_signal = pyqtSignal(int, int)  # current, total

        def __init__(self, file_paths, burn_path, ota_path):
            super().__init__()
            self.file_paths = file_paths
            self.burn_path = burn_path
            self.ota_path = ota_path
            # 取消控制
            self._cancelled = False
            self.current_process = None

        def request_cancel(self):
            self._cancelled = True
            try:
                if self.current_process is not None and self.current_process.poll() is None:
                    self.current_process.terminate()
            except Exception:
                pass

        def run(self):
            results = []
            total_files = len(self.file_paths)
            processed_files = 0
            self.overall_progress_signal.emit(0, total_files)
            for file_path in self.file_paths:
                if self._cancelled:
                    break
                try:
                    # 根据文件类型选择目标路径
                    if file_path.endswith('.img'):
                        dest_path = self.burn_path
                        # 使用 adb shell ls 检查 burn 路径是否存在
                        check_path_process = subprocess.run(
                            ["adb", "shell", "ls", dest_path],
                            capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            text=True
                        )
                        if "No such file or directory" in check_path_process.stdout:
                            create_path_process = subprocess.run(
                                ["adb", "shell", "mkdir", "-p", dest_path],
                                capture_output=True,
                                creationflags=subprocess.CREATE_NO_WINDOW,
                                text=True
                            )
                            if create_path_process.returncode != 0:
                                results.append((file_path, Exception(f"创建 {dest_path} 失败: {create_path_process.stderr}")))
                                # 仍然推进整体进度
                                processed_files += 1
                                self.overall_progress_signal.emit(processed_files, total_files)
                                continue
                    else:
                        dest_path = self.ota_path

                    # 获取源文件大小
                    source_size = os.path.getsize(file_path)
                    current_filename = os.path.basename(file_path)

                    # 开始推送，开启进度输出 (-p)
                    self.current_process = subprocess.Popen([
                                                 "adb", "push", "-p", file_path, dest_path
                                               ],
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE,
                                              creationflags=subprocess.CREATE_NO_WINDOW,
                                              universal_newlines=True,
                                              bufsize=1)

                    last_percent = -1
                    # 使用du命令监控目标文件大小来计算进度
                    while True:
                        if self._cancelled:
                            try:
                                if self.current_process is not None and self.current_process.poll() is None:
                                    self.current_process.terminate()
                            except Exception:
                                pass
                            break

                        # 检查进程是否结束
                        if self.current_process.poll() is not None:
                            break

                        # 使用du命令获取目标文件大小
                        try:
                            du_result = subprocess.run([
                                "adb", "shell", "du", "-b", f"{dest_path}{current_filename}"
                            ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

                            if du_result.returncode == 0 and du_result.stdout.strip():
                                # 解析du命令输出，获取已传输的字节数
                                transferred_size = int(du_result.stdout.split()[0])
                                percent_val = min(100, int((transferred_size / source_size) * 100))

                                if percent_val != last_percent:
                                    last_percent = percent_val
                                    self.file_progress_signal.emit(percent_val, current_filename)
                        except (ValueError, IndexError, subprocess.SubprocessError):
                            # 如果du命令失败，继续等待
                            pass

                        # 短暂等待避免过度占用CPU
                        time.sleep(1)

                    stdout, stderr = self.current_process.communicate()
                    result = subprocess.CompletedProcess(args=["adb", "push", file_path, dest_path],
                                                          returncode=self.current_process.returncode,
                                                          stdout=stdout,
                                                          stderr=stderr)
                    self.current_process = None
                    results.append((file_path, result))
                except Exception as e:
                    results.append((file_path, e))
                finally:
                    processed_files += 1
                    self.overall_progress_signal.emit(processed_files, total_files)
                    if self._cancelled:
                        break
            self.finished_signal.emit(results)

    class SCPImportThread(QThread):
        update_signal = pyqtSignal(str)
        finished_signal = pyqtSignal(list)
        file_progress_signal = pyqtSignal(int, str)
        overall_progress_signal = pyqtSignal(int, int)

        def __init__(self, file_paths, burn_path, ota_path, host, username, password):
            super().__init__()
            self.file_paths = file_paths
            self.burn_path = burn_path
            self.ota_path = ota_path
            self.host = host
            self.username = username
            self.password = password
            self.port = 8024
            self._cancelled = False
            self.current_process = None

            # 检测可用的scp和ssh命令，优先使用Windows系统的OpenSSH（避免Git for Windows的弹窗）
            if os.name == "nt":
                # Windows: 优先使用系统的OpenSSH
                system_scp = r"C:\Windows\System32\OpenSSH\scp.exe"
                system_ssh = r"C:\Windows\System32\OpenSSH\ssh.exe"

                if os.path.exists(system_scp) and os.path.exists(system_ssh):
                    self.scp_cmd = system_scp
                    self.ssh_cmd = system_ssh
                else:
                    # 如果没有系统的，使用PATH中的
                    self.scp_cmd = shutil.which("scp")
                    self.ssh_cmd = shutil.which("ssh")
            else:
                self.scp_cmd = shutil.which("scp")
                self.ssh_cmd = shutil.which("ssh")

            if not self.scp_cmd:
                raise RuntimeError("未找到 scp 命令，请确保已安装 OpenSSH 客户端")

            # 确保ssh命令也存在
            if not hasattr(self, 'ssh_cmd') or not self.ssh_cmd:
                self.ssh_cmd = shutil.which("ssh")
                if not self.ssh_cmd:
                    raise RuntimeError("未找到 ssh 命令，请确保已安装 OpenSSH 客户端")

        def request_cancel(self):
            self._cancelled = True
            try:
                if self.current_process and self.current_process.poll() is None:
                    self.current_process.terminate()
            except Exception:
                pass

        def _execute_in_cmd_terminal(self, cmd_list, description=""):
            """在cmd终端中执行命令（可见窗口，用户可以输入密码）"""
            if os.name == "nt":
                # Windows: 在新cmd窗口中执行命令
                title = description if description else "SSH命令"

                if isinstance(cmd_list, list):
                    process = subprocess.Popen(
                        cmd_list,
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                        cwd=os.getcwd()
                    )
                else:
                    process = subprocess.Popen(
                        cmd_list,
                        shell=True,
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                        cwd=os.getcwd()
                    )

                # 保存进程引用，用于等待完成
                self.current_process = process
                return process

        def _group_files_by_destination(self):
            """将文件按照远程目录分组"""
            groups = {}
            for file_path in self.file_paths:
                dest_dir = self.burn_path if file_path.endswith('.img') else self.ota_path
                dest_dir = dest_dir.rstrip("/") + "/"
                groups.setdefault(dest_dir, []).append(file_path)
            return list(groups.items())

        def _build_scp_command(self, local_paths, remote_dir):
            """构建scp命令"""
            destination = f"{self.username}@{self.host}:{remote_dir}"
            scp_cmd = [
                self.scp_cmd,
                "-P", str(self.port),
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                *local_paths,
                destination
            ]
            return scp_cmd

        def _transfer_file_with_progress(self, local_path, remote_dir):
            """使用scp命令在cmd终端中传输文件"""
            filename = os.path.basename(local_path)
            source_size = os.path.getsize(local_path)
            remote_path = f"{remote_dir.rstrip('/')}/{filename}"

            if source_size == 0:
                self.file_progress_signal.emit(100, filename)
                return

            # 发送初始进度
            self.file_progress_signal.emit(0, filename)
            self.update_signal.emit(f"正在传输: {filename}")

            # 构建scp命令
            cmd = self._build_scp_command([local_path], remote_dir)

            # 在cmd终端中执行scp命令，让用户输入密码
            process = self._execute_in_cmd_terminal(cmd, f"SCP传输: {filename}")

            # 等待进程完成
            return_code = process.wait()

            # 检查传输结果
            if return_code == 0:
                # 传输成功
                self.file_progress_signal.emit(100, filename)
            else:
                # 传输失败
                raise RuntimeError(f"SCP传输失败，返回码: {return_code}")


        def run(self):
            """执行SCP导入操作"""
            results = []
            total_files = len(self.file_paths)
            processed_files = 0

            # 发送初始总文件数
            self.overall_progress_signal.emit(0, total_files)

            self.update_signal.emit("提示: SSH命令将在cmd终端中执行，请在终端中输入密码")

            try:
                # 按照目标路径分组文件
                groups = self._group_files_by_destination()

                for dest_dir, file_paths in groups:
                    if self._cancelled:
                        break

                    # 传输这一组文件
                    for file_path in file_paths:
                        if self._cancelled:
                            break

                        filename = os.path.basename(file_path)

                        try:
                            self._transfer_file_with_progress(file_path, dest_dir)
                            results.append((file_path, subprocess.CompletedProcess(
                                args=[], returncode=0, stdout="", stderr=""
                            )))
                            self.update_signal.emit(f"成功传输: {filename}")
                        except Exception as e:
                            error_msg = str(e)
                            results.append((file_path, Exception(error_msg)))
                            self.update_signal.emit(f"传输失败 {filename}: {error_msg}")

                        processed_files += 1
                        self.overall_progress_signal.emit(processed_files, total_files)

            except Exception as e:
                error_msg = str(e)
                self.update_signal.emit(f"传输过程中出错: {error_msg}")
                # 如果出现未处理的异常，为剩余文件创建错误结果
                for file_path in self.file_paths:
                    if not any(r[0] == file_path for r in results):
                        results.append((file_path, Exception(error_msg)))
                        processed_files += 1
                        self.overall_progress_signal.emit(processed_files, total_files)
            finally:
                # 发送完成信号
                self.finished_signal.emit(results)

    def import_ota_package(self):
        ## adb shell检查设备连接状态
        if not self.check_device_connected():
            QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
            return

        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择镜像/升级包", "", "所有文件 (*)"
        )
        if file_paths:
            self.log("开始导入镜像/升级包...")
            self.import_thread = self.ImportPackageThread(file_paths, self.burn_path, self.ota_path)
            self.import_thread.update_signal.connect(self.log)
            self.import_thread.finished_signal.connect(self.handle_import_result)

            # 创建自定义进度对话框
            self.import_progress = ImportProgressDialog(len(file_paths), self)

            # 连接进度信号
            self.import_thread.file_progress_signal.connect(self.on_import_file_progress)
            self.import_thread.overall_progress_signal.connect(self.on_import_overall_progress)
            self.import_thread.finished_signal.connect(lambda _: self.import_progress.close())

            # 取消按钮逻辑
            self.import_progress.cancel_button.clicked.connect(self.cancel_import)

            self.import_thread.start()
            self.import_progress.show()

    def import_ota_package_scp(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择镜像/升级包", "", "所有文件 (*)"
        )
        if not file_paths:
            return

        self.last_scp_ip = "192.168.16.43"

        if not self.is_host_reachable(self.last_scp_ip):
            warning_msg = f"无法连接到 {self.last_scp_ip}，请检查IP是否正确或网络是否可达。"
            self.log(warning_msg)
            QMessageBox.warning(self, "网络不可达", warning_msg)
            return

        self.log(f"开始通过SSH导入镜像/升级包，目标IP：{self.last_scp_ip}")

        try:
            self.import_thread = self.SCPImportThread(
                file_paths,
                self.burn_path,
                self.ota_path,
                self.last_scp_ip,
                "sshclient",
                "123456"
            )
        except Exception as e:
            error_msg = f"创建SSH导入线程失败: {str(e)}"
            QMessageBox.critical(self, "错误", error_msg)
            self.log(error_msg)
            return
        self.import_thread.update_signal.connect(self.log)
        self.import_thread.finished_signal.connect(self.handle_import_result)

        self.import_thread.start()

    def cancel_import(self):
        """取消导入操作"""
        try:
            if hasattr(self, 'import_thread') and self.import_thread is not None:
                self.import_thread.request_cancel()
            if hasattr(self, 'import_progress') and self.import_progress is not None:
                self.import_progress.current_label.setText("已取消导入")
            self.import_cancelled = True
        except Exception:
            pass

    def is_host_reachable(self, host):
        """检查给定主机是否可达"""
        try:
            count_flag = "-n" if os.name == "nt" else "-c"
            result = subprocess.run(
                ["ping", count_flag, "1", host],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as exc:
            self.log(f"PING {host} 失败：{str(exc)}")
            return False

    def on_import_file_progress(self, percent, filename):
        """导入单个文件进度回调"""
        if hasattr(self, 'import_progress') and self.import_progress is not None:
            self.import_progress.update_current_file_progress(percent, filename)
            QApplication.processEvents()

    def on_import_overall_progress(self, current, total):
        """整体导入进度回调"""
        if hasattr(self, 'import_progress') and self.import_progress is not None:
            self.import_progress.update_total_progress(current, total)
            QApplication.processEvents()

    class ClearLogThread(QThread):
        finished_signal = pyqtSignal()


    def handle_clear_log_finished(self):
        """处理清除日志完成"""
        self.log_area.clear()
        self.log_content = []

    def clear_log(self):
        """清除日志内容"""
        self.handle_clear_log_finished()


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

    def handle_import_result(self, results):
        if self.import_cancelled:
            self.log("导入已取消")
            QMessageBox.information(self, "提示", "已取消导入")
            self.import_cancelled = False
            return
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

        # 让用户选择要清理的路径
        path_options = ["烧录路径", "升级路径"]
        dialog = QInputDialog()
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        selected_path, ok = dialog.getItem(
            self,
            "选择清理路径",
            "请选择要清理的路径：",
            path_options,
            0,
            False
        )

        if not ok or not selected_path:
            self.log("用户取消清理操作。")
            return

        if selected_path == "烧录路径":
            target_path = self.burn_path
        else:
            target_path = self.ota_path

        self.log(f"开始检查{selected_path}...")
        try:
            # 获取目标路径下的所有文件
            result = subprocess.run(["adb", "shell", "ls -Al", f"{target_path}*"],
                                    capture_output=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW,
                                    text=True)

            if "No such file or directory" in result.stdout:
                self.log(f"{selected_path}为空，无需清理。")
                QMessageBox.information(self, "提示", f"{selected_path}为空，无需清理")
                return

            files = [line.strip() for line in result.stdout.splitlines() if line.strip()]

            # 弹框选择要删除的文件
            dialog = QInputDialog()
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            selected_files, ok = dialog.getItem(
                self,
                f"选择删除{selected_path}的文件",
                f"请选择要删除{selected_path}的文件（选择'全部'删除所有文件）：",
                ["全部"]+[os.path.basename(f) for f in files],
                0,
                False
            )

            if not ok or not selected_files:
                self.log("用户取消删除操作。")
                return

            self.log(f"开始清理{selected_path}：{selected_files}")
            self.clean_thread = self.CleanPathThread(selected_files, target_path)
            self.clean_thread.update_signal.connect(self.log)
            self.clean_thread.finished_signal.connect(lambda: self.log(f"{selected_path}清理完成"))
            self.clean_thread.start()
            QMessageBox.information(self, "提示", f"{selected_path}清理完成")

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
                    self.update_signal.emit("开始擦除boot分区...")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", "shell", "upg_test", "erase", self.config["MTD_BOOT"]],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit("boot分区擦除完成。")
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
                    self.update_signal.emit("开始擦除dt分区...")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", "shell", "upg_test", "erase", self.config["MTD_DT"]],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit(f"dt分区擦除完成。")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", "shell", "upg_test", "writeraw", self.config["MTD_DT"], self.config["DT_PACKED_IMG"]],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit("dt_packed.img 升级完成。")
                    with open("burn.log", "a") as log_file:
                        subprocess.run(["adb", "shell", "rm", f"{self.burn_path}dt_packed.img"],
                                     stdout=log_file, stderr=log_file, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_signal.emit("dt_packed.img 删除完成。")
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


                #检查是否需要重启
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

         # 添加导入状态检查
        if hasattr(self, 'import_thread') and self.import_thread.isRunning():
            QMessageBox.warning(self, "提示", "镜像正在导入中，请稍后再试")
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
        ## 弹框选择是否开始烧录
        reply = QMessageBox.question(self, "提示", "是否开始烧录？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            self.log("用户取消烧录操作。")
            return
        ## 检查烧录路径下是否有boot.img、dt_packed.img、custapp.img,需要同时存在
        try:
            result = subprocess.run(["adb", "shell", "ls", f"{self.burn_path}*.img"],
                                     capture_output=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW,
                                     text=True)
            error_msg = result.stdout.lower()
            if ("no such file or directory" in error_msg or
                "未找到" in error_msg or
                "boot.img" not in result.stdout or
                "dt_packed.img" not in result.stdout or
                "custapp.img" not in result.stdout):
                self.log("img文件缺失，请检查烧录路径下boot.img、dt_packed.img、custapp.img文件是否同时存在。")
                QMessageBox.warning(self, "警告", "请检查烧录路径下是否有img文件是否完整！\n烧录路径：/online/burn_dir/")
                return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"检查烧录路径失败：{str(e)}")
            self.log(f"检查烧录路径失败：{str(e)}")
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

             # 添加导入状态检查
            if hasattr(self, 'import_thread') and self.import_thread.isRunning():
                QMessageBox.warning(self, "提示", "升级包正在导入中，请稍后再试")
                return

            result = subprocess.run(
                ["adb", "shell", "ls", "-al", f"{self.ota_path}*.zip"],
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
            dialog = QInputDialog()
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            selected_file, ok = dialog.getItem(
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

    def ssh_upgrade(self):
        """通过SSH执行升级"""
        # 选择升级包文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择升级包", "", "ZIP文件 (*.zip);;所有文件 (*)"
        )
        if not file_path:
            return

        filename = os.path.basename(file_path)
        self.last_scp_ip = "192.168.16.43"

        # 检查IP是否可达
        if not self.is_host_reachable(self.last_scp_ip):
            warning_msg = f"无法连接到 {self.last_scp_ip}，请检查IP是否正确或网络是否可达。"
            self.log(warning_msg)
            QMessageBox.warning(self, "网络不可达", warning_msg)
            return

        self.log(f"开始通过SSH执行升级，目标IP：{self.last_scp_ip}，升级包：{filename}")

        # 构建SSH命令
        upgrade_command = f'source /oemapp/scripts/env; /oemapp/app/bin/set_tuid -u /media/sdcard/ota/{filename}'

        # 检测SSH命令路径
        if os.name == "nt":
            system_ssh = r"C:\Windows\System32\OpenSSH\ssh.exe"
            if os.path.exists(system_ssh):
                ssh_cmd = system_ssh
            else:
                ssh_cmd = shutil.which("ssh")
        else:
            ssh_cmd = shutil.which("ssh")

        if not ssh_cmd:
            error_msg = "未找到 ssh 命令，请确保已安装 OpenSSH 客户端"
            QMessageBox.critical(self, "错误", error_msg)
            self.log(error_msg)
            return

        try:
            # 在cmd终端中执行SSH命令，让用户输入密码
            if os.name == "nt":
                remote_cmd_quoted = f'"{upgrade_command}"'
                ssh_command_str = f'{ssh_cmd} sshclient@{self.last_scp_ip} {remote_cmd_quoted}'

                start_cmd = f'start "SSH升级" cmd /k "{ssh_command_str}"'

                subprocess.run(
                    start_cmd,
                    shell=True
                )

                QMessageBox.information(self, "提示", "SSH升级命令执行成功")

        except Exception as e:
            error_msg = f"执行SSH升级命令失败: {str(e)}"
            QMessageBox.critical(self, "错误", error_msg)
            self.log(error_msg)

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

            # 获取日志列表
            log_files = self.acquire_log_list()

            if not log_files:
                QMessageBox.information(self, "提示", "没有找到任何日志文件")
                return


            # 让用户选择要导出的日志
            dialog = QInputDialog()
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            selected_log, ok = dialog.getItem(
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
                QMessageBox.information(self, "提示", "日志导出完成")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取日志列表失败：{str(e)}")
            self.log(f"获取日志列表失败：{str(e)}")

    def log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_content.append(log_message)
        self.log_area.append(log_message)
        # 将滚动条移动到最下方
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.log_area.ensureCursorVisible()

    def show_version(self):
        """查看版本信息"""
        if not self.check_device_connected():
            QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
            return

        # 创建版本信息窗口
        self.version_window = QDialog(self)
        self.version_window.setWindowTitle("版本信息")
        self.version_window.setGeometry(100, 100, 500, 300)

        # 主布局
        layout = QVBoxLayout()

        # 添加翻页按钮
        btn_layout = QHBoxLayout()
        self.prev_btn = QPushButton("< 上一页")
        self.next_btn = QPushButton("下一页 >")
        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.next_btn)
        layout.addLayout(btn_layout)

        # 添加堆栈窗口
        self.stacked_widget = QStackedWidget()

        # 第一页：配置文件版本信息
        self.page1 = QTextEdit()
        self.page1.setReadOnly(True)
        self.stacked_widget.addWidget(self.page1)

        # 第二页：tbox版本信息
        self.page2 = QTextEdit()
        self.page2.setReadOnly(True)
        self.stacked_widget.addWidget(self.page2)

        layout.addWidget(self.stacked_widget)
        self.version_window.setLayout(layout)

        # 连接按钮信号
        self.prev_btn.clicked.connect(self.show_prev_page)
        self.next_btn.clicked.connect(self.show_next_page)

        # 加载第一页数据
        self.load_config_version()
        self.version_window.exec_()

    def load_config_version(self):
        """加载配置文件版本信息"""
        try:
            result = subprocess.run(
                ["adb", "shell", "cat", f"{self.configs_path}", "|", "grep", "ware"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True
            )

            if result.returncode == 0:
                version_info = result.stdout
                # 使用与系统一致的字体
                version_info_format = '<pre style="font-family: inherit;">'
                for line in version_info.splitlines():
                    if "=" and ";" and " " in line:
                        line = line.replace(";", "")
                        line = line.replace('"', "")
                        key, value = line.split("=", 1)
                        version_info_format += f"{key.strip()}: {value.strip().center(20, ' ')}\n"
                        version_info_format += "\n"
                version_info_format += '</pre>'
                self.page1.setHtml(version_info_format)
                version_info_format = version_info_format.replace('<pre style="font-family: inherit;">', '').replace('</pre>', '')
                self.log(f"配置文件版本信息：\n\n{version_info_format}")
                self.load_tbox_version()
            else:
                QMessageBox.warning(self, "警告", "获取版本信息失败")
        except Exception as e:
            QMessageBox.critical(self, "正在获取，请稍等")

    def load_tbox_version(self):
        """加载tbox版本信息"""
        try:
            result = subprocess.run(
                ["adb", "shell", "cat", "/oemapp/tbox-version"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True
            )

            if result.returncode == 0:
                tbox_info = result.stdout
                tbox_info_format = '<pre style="font-family: inherit;">'
                tbox_info_format += tbox_info
                tbox_info_format += "\n"
                tbox_info_format += '</pre>'
                self.page2.setHtml(tbox_info_format)
            else:
                self.page2.setText("获取tbox版本信息失败")
        except Exception as e:
            self.page2.setText(f"获取tbox版本信息时出错：{str(e)}")

    def show_prev_page(self):
        """显示上一页"""
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)

    def show_next_page(self):
        """显示下一页"""
        current_index = self.stacked_widget.currentIndex()
        if current_index < self.stacked_widget.count() - 1:
            self.stacked_widget.setCurrentIndex(current_index + 1)


    def view_log(self):
        """查看日志"""
        if not self.check_device_connected():
            QMessageBox.critical(self, "错误", "设备未连接，请先连接设备。")
            return

        try:
            # 让用户选择日志类型
            log_types = ["MPU日志", "MCU日志"]
            dialog = QInputDialog()
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            selected_type, ok = dialog.getItem(
                self,
                "选择日志类型",
                "请选择要查看的日志类型：",
                log_types,
                0,
                False
            )

            if not ok or not selected_type:
                self.log("用户取消日志查看操作。")
                return

            # 根据选择的类型获取日志文件列表
            if selected_type == "MPU日志":
                log_files = self.acquire_log_list("/oemdata/logs/")
                log_path = "/oemdata/logs/"
            else:  # MCU日志
                log_files = self.acquire_log_list("/media/sdcard/data/tbox_log/")
                log_path = "/media/sdcard/data/tbox_log/"

            if not log_files:
                QMessageBox.information(self, "提示", f"没有找到任何{selected_type}文件")
                return

            # 获取用户选择的日志文件
            selected_log = self.get_selected_log(log_files)
            if not selected_log:
                return

            # 创建并显示日志查看窗口
            self.create_log_viewer(selected_log, log_path)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取日志列表失败：{str(e)}")
            self.log(f"获取日志列表失败：{str(e)}")

    def get_selected_log(self, log_files):
        """获取用户选择的日志文件"""
        # 直接显示所有日志文件的下拉选项
        dialog = QInputDialog()
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        selected_log, ok = dialog.getItem(
            self,
            "选择日志文件",
            "请选择要查看的日志文件：",
            log_files,
            0,
            False
        )

        if not ok or not selected_log:
            self.log("用户取消日志查看操作。")
            return None

        return selected_log

    def create_log_viewer(self, selected_log, log_path):
        """创建并显示日志查看窗口"""
        # 清理已关闭的日志窗口
        self.log_viewer = [viewer for viewer in self.log_viewer if viewer.isVisible()]

        # 创建新的日志查看窗口
        log_viewer = LogViewerWindow(f"{log_path}{selected_log}")
        log_viewer.show()
        self.log_viewer.append(log_viewer)

    def acquire_log_list(self, log_path=None):
        """获取日志列表"""
        if log_path is None:
            # 获取两个目录的日志文件列表（用于导出日志功能）
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
        else:
            # 获取指定路径的日志文件列表
            result = subprocess.run(
                ["adb", "shell", f"ls -lA {log_path} | awk '{{print $9}}'"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True
            )
            log_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]

        return log_files


class LogViewerWindow(QMainWindow):
    def __init__(self, log_file):
        super().__init__()
        self.log_file = log_file
        self.is_paused = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"{os.path.basename(self.log_file)}")
        self.setGeometry(200, 200, 1200, 600)

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
        self.view_log_thread.finished_signal.connect(self.handle_log_finished)
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
            # 将滑动块移动到最下方
            scrollbar = self.log_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            self.log_area.ensureCursorVisible()

    def log(self, message):
        """直接添加日志内容"""
        self.log_area.append(message)
        self.log_area.ensureCursorVisible()

    def handle_log_finished(self):
        """处理日志查看结束"""
        self.log("日志查看结束")
        QMessageBox.information(self, "提示", "日志查看已结束")

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