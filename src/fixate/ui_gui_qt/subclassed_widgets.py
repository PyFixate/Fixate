from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal


class ResizeImageView(QtWidgets.QGraphicsView):
    def __init__(self, parent):
        super().__init__(parent)
        self.scene = None

    def set_scene(self, scene):
        self.scene = scene

    def resizeEvent(self, event):
        if self.scene is not None:
            self.fitInView(
                0, 0, self.scene.width(), self.scene.height(), QtCore.Qt.KeepAspectRatio
            )


class SubmissionTextBox(QtWidgets.QPlainTextEdit):
    submit = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            self.submit.emit()
        else:
            super().keyPressEvent(event)
