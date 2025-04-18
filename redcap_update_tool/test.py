from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                            QTextEdit, QVBoxLayout, QWidget, QInputDialog, QMessageBox)
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.highlight_words = []
        self.last_keywords = ""  # 新增上次输入记录
        self.initUI()
        self.load_sample_logs()

    def set_highlight(self):
        """设置高亮关键词"""
        keywords, ok = QInputDialog.getText(
            self, 
            "输入关键词", 
            "多个关键词用逗号分隔:",
            text=self.last_keywords  # 修改为使用上次输入
        )
        if ok:
            self.last_keywords = keywords  # 记录最新输入
            self.highlight_words = [kw.strip() for kw in keywords.split(',') if kw.strip()]
            if not self.highlight_words:
                self.clear_highlight()
            else:
                self.highlight_matches()

    def initUI(self):
        self.setWindowTitle("高亮功能测试窗口")
        self.setGeometry(300, 300, 800, 600)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # 日志显示区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        # 操作按钮
        self.btn_highlight = QPushButton("关键词高亮")
        self.btn_highlight.clicked.connect(self.set_highlight)
        layout.addWidget(self.btn_highlight)

        # 测试控制按钮
        self.btn_pause = QPushButton("暂停滚动")
        self.btn_pause.clicked.connect(self.pause_log)
        layout.addWidget(self.btn_pause)

        self.btn_resume = QPushButton("继续滚动")
        self.btn_resume.clicked.connect(self.resume_log)
        layout.addWidget(self.btn_resume)

        main_widget.setLayout(layout)

    def load_sample_logs(self):
        """加载测试日志"""
        sample_log = """
[2023-08-20 10:00:00] 系统启动成功
[2023-08-20 10:00:05] 检测到错误代码：500
[2023-08-20 10:00:10] 警告：内存使用率超过80%
[2023-08-20 10:00:15] 网络连接正常
[2023-08-20 10:00:20] 错误：文件未找到
[2023-08-20 10:00:25] 警告：磁盘空间不足
        """
        self.log_area.setPlainText(sample_log.strip())

    def resume_log(self):
        """模拟继续滚动"""
        self.highlight_words = []  # 新增清空关键词列表
        self.clear_highlight()

    def highlight_matches(self):
        """执行高亮操作"""
        self.clear_highlight()
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("yellow"))
        match_count = 0  # 新增匹配计数器

        for word in self.highlight_words:
            if not word: continue
            while True:
                cursor = self.log_area.document().find(word, cursor)
                if cursor.isNull():
                    break
                cursor.mergeCharFormat(highlight_format)
                match_count += 1  # 计数匹配项

        # 新增未匹配提示
        if match_count == 0:
            QMessageBox.warning(self, "提示", "未找到匹配项！")

    def pause_log(self):
        """模拟暂停滚动"""
        self.clear_highlight()

    def clear_highlight(self):
        """清除所有高亮"""
        cursor = self.log_area.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(QTextCharFormat())
        cursor.clearSelection()

if __name__ == "__main__":
    app = QApplication([])
    window = TestWindow()
    window.show()
    app.exec_()