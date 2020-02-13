from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QFont, QColor, QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QLineEdit, QSizePolicy, QTabWidget, QListWidget, QMenuBar
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView,QWebEngineSettings, QWebEngineProfile
from .TritonWidget import TritonWidget, ImageButton
from . import Globals
import requests
import json, os

class ManifestRetriever(QThread):
    signal = pyqtSignal(object)

    def __init__(self, drive):
        QThread.__init__(self)
        self.drive = drive

    def run(self):
        self.drive.connect()
        manifests = self.drive.get_manifests()
        self.signal.emit(manifests)

class ManifestDownloader(QThread):
    signal = pyqtSignal(str, object, str)

    def __init__(self, name, manifest, destination):
        QThread.__init__(self)
        self.name = name
        self.manifest = manifest
        self.destination = destination

    def run(self):
        with requests.get(self.manifest['link'], stream=True) as r:
            r.raise_for_status()

            with open(self.destination, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        self.signal.emit(self.name, self.manifest, self.destination)

class ManifestTab(QWidget):

    def __init__(self, widget, folder, files):
        QWidget.__init__(self)
        self.widget = widget
        self.folder = folder
        self.files = files
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.listBox = QListWidget()

        for file in sorted(files.keys(), reverse=True):
            self.listBox.addItem(file)
        
        self.listBox.itemDoubleClicked.connect(self.choseItem)
        self.layout.addWidget(self.listBox)
        self.setLayout(self.layout)
    
    def choseItem(self, item):
        name = item.text()
        self.widget.downloadManifest(name, self.files[name])

class ManifestWidget(TritonWidget):

    def __init__(self, base, drive):
        TritonWidget.__init__(self, base)
        self.drive = drive

        self.setWindowTitle('NextcloudRestore')
        self.setBackgroundColor(self, Qt.white)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.menuBar = QMenuBar()
        fileMenu = self.menuBar.addMenu('File')

        self.label = QLabel('Searching for manifests...')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont('Sans Serif', 20))

        self.tabs = QTabWidget()
        self.tabs.setMinimumSize(300, 300)
        self.tabs.setMaximumSize(300, 300)
        self.tabs.hide()

        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.menuBar)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.resizeAndCenter()
        self.show()

        self.retriever = ManifestRetriever(self.drive)
        self.retriever.signal.connect(self.gotManifests)
        self.retriever.start()

        self.downloader = None

    def gotManifests(self, manifests):
        self.label.setText('Choose the manifest to recover:')

        for folder in sorted(manifests.keys()):
            files = manifests[folder]
            tab = ManifestTab(self, folder, files)

            self.tabs.addTab(tab, folder)
        
        self.tabs.show()
        self.resizeAndCenter()
    
    def downloadManifest(self, name, manifest):
        destination = self.base.tmp.getFile(name)

        if os.path.exists(destination):
            self.downloadedManifest(name, manifest, destination)
            return

        self.label.setText('Downloading manifest...')
        self.tabs.setEnabled(False)

        self.downloader = ManifestDownloader(name, manifest, destination)
        self.downloader.signal.connect(self.downloadedManifest)
        self.downloader.start()
    
    def downloadedManifest(self, name, manifest, destination):
        self.label.setText('Manifest downloaded.')
        self.tabs.setEnabled(True)