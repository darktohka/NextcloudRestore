from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QPalette, QFont, QColor, QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QLineEdit, QSizePolicy
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView,QWebEngineSettings, QWebEngineProfile
from .TritonWidget import TritonWidget, ImageButton
from . import Globals
import json

class ConnectWidget(TritonWidget):

    def __init__(self, base, provider):
        TritonWidget.__init__(self, base)
        self.loaded = False
        self.complete = False
        self.provider = provider

        self.resize(640, 480)
        
        self.setWindowTitle('Loading {0} page...'.format(provider['name']))
        self.setBackgroundColor(self, Qt.white)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.browser = QWebEngineView()

        self.browser.page().profile().setHttpUserAgent(Globals.UserAgent)
        self.browser.load(QUrl(self.base.getConnectUrl(provider)))
        self.browser.urlChanged.connect(self.urlChanged)
        self.browser.loadFinished.connect(self.loadFinished)

        self.layout.addWidget(self.browser)
        self.setLayout(self.layout)
        self.resizeAndCenter()
        self.show()

    def closeEvent(self, event):
        if not self.complete:
            self.base.chooseProvider()

    def loadFinished(self):
        if not self.loaded:
            self.setWindowTitle('Login to {0}'.format(self.provider['name']))
            self.loaded = True

    def urlChanged(self, url):
        if url.path().split('/')[-1] == 'authorized':
            self.browser.page().toPlainText(self.contentChanged)
    
    def contentChanged(self, content):
        try:
            content = json.loads(content)
        except:
            self.browser.page().toPlainText(self.contentChanged)
            return

        self.complete = True
        self.close()
        self.base.connectionComplete(self.provider, content)