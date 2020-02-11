from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QFont, QColor, QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QLineEdit, QSizePolicy, QTabWidget, QListWidget
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView,QWebEngineSettings, QWebEngineProfile
from .TritonWidget import TritonWidget, ImageButton
from . import Globals
import json

class ManifestRetriever(QThread):
    signal = pyqtSignal(object)

    def __init__(self, drive):
        QThread.__init__(self)
        self.drive = drive

    def run(self):
        self.drive.connect()
        manifests = self.drive.get_manifests()
        self.signal.emit(manifests)

class ManifestTab(QWidget):

    def __init__(self, folder, files):
        QWidget.__init__(self)
        self.folder = folder
        self.files = files
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)

        self.listBox = QListWidget()

        for file in files:
            self.listBox.addItem(file['name'])

        self.layout.addWidget(self.listBox)
        self.setLayout(self.layout)

class ManifestWidget(TritonWidget):

    def __init__(self, base, drive):
        TritonWidget.__init__(self, base)
        self.drive = drive
        
        self.setWindowTitle('NextcloudRestore')
        self.setBackgroundColor(self, Qt.white)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        self.label = QLabel('Searching for manifests...')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont('Sans Serif', 20))

        self.tabs = QTabWidget()
        self.tabs.setMinimumSize(300, 300)
        self.tabs.setMaximumSize(300, 300)
        self.tabs.hide()

        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.resizeAndCenter()
        self.show()

        self.retriever = ManifestRetriever(self.drive)
        self.retriever.signal.connect(self.gotManifests)
        self.retriever.start()

    def gotManifests(self, manifests):
        self.label.setText('Choose the manifest to recover:')

        for folder in sorted(manifests.keys()):
            files = manifests[folder]
            tab = ManifestTab(folder, files)

            self.tabs.addTab(tab, folder)
        
        self.tabs.show()
        self.resizeAndCenter()