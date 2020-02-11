from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QFont, QColor, QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QLineEdit
from . import Globals
from .TritonWidget import TritonWidget, ImageButton

class ProviderButton(ImageButton):

    def __init__(self, base, provider):
        ImageButton.__init__(self, QPixmap(provider['logo']).scaled(150, 150))
        self.base = base
        self.provider = provider
        self.clicked.connect(self.beginConnect)
    
    def beginConnect(self):
        self.base.beginConnect(self.provider)

class ProviderWidget(TritonWidget):

    def __init__(self, base):
        TritonWidget.__init__(self, base)

        self.setWindowTitle('NextcloudRestore')
        self.setBackgroundColor(self, Qt.white)
        
        self.setContentsMargins(20, 20, 20, 20)
        
        self.verticalLayout = QVBoxLayout()
        
        self.label = QLabel('Choose your cloud provider')
        self.label.setFont(QFont('SansSerif', 20))
        self.label.setAlignment(Qt.AlignCenter)
        
        self.providerWidget = QWidget()
        self.providerLayout = QHBoxLayout()
        
        for providerType in Globals.ProviderNames:
            button = ProviderButton(self.base, Globals.Providers[providerType])
            self.providerLayout.addWidget(button)

        self.providerWidget.setLayout(self.providerLayout)
        
        self.verticalLayout.addWidget(self.label)
        self.verticalLayout.addWidget(self.providerWidget)
        
        self.setLayout(self.verticalLayout)
        self.resizeAndCenter()
        self.show()