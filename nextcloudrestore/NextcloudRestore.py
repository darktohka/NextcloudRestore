from PyQt5.QtWidgets import QApplication
from .ProviderWidget import ProviderWidget
from .ConnectWidget import ConnectWidget
from .ManifestWidget import ManifestWidget
import sys

class NextcloudRestore(object):

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.providerWidget = None
        self.connectWidget = None
        self.manifestWidget = None
        self.provider = None
        self.access_token = None
    
    def getConnectUrl(self, provider):
        return 'https://auth.tohka.us/{0}'.format(provider['type'])
    
    def createProvider(self, type, access_token):
        if type == 'onedrive':
            from .providers.OneDrive import OneDrive
            return OneDrive(access_token)

    def chooseProvider(self):
        self.stopChooseProvider()
        self.stopConnect()
        self.stopManifest()
        self.providerWidget = ProviderWidget(self)
    
    def stopChooseProvider(self):
        if self.providerWidget:
            self.providerWidget.close()
            self.providerWidget = None

    def beginConnect(self, provider):
        self.stopChooseProvider()
        self.stopConnect()
        self.stopManifest()
        self.connectWidget = ConnectWidget(self, provider)
    
    def stopConnect(self):
        if self.connectWidget:
            self.connectWidget.close()
            self.connectWidget = None

    def stopManifest(self):
        if self.manifestWidget:
            self.manifestWidget.close()
            self.manifestWidget = None

    def connectionComplete(self, provider, access_token):
        self.provider = provider
        self.access_token = access_token

        drive = self.createProvider(self.provider['type'], self.access_token)

        self.stopChooseProvider()
        self.stopConnect()
        self.stopManifest()
        self.manifestWidget = ManifestWidget(self, drive)

    def mainLoop(self):
        self.app.exec_()