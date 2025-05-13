import sys
from PyQt5.QtWidgets import QApplication
from controller import MainController

if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = MainController()
    controller.view.set_window_icon(r"./icon/icon.jpg")
    controller.view.show()
    sys.exit(app.exec_())