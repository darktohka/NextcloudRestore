import tempfile, atexit, shutil, random, string, os

NAME = 'NextcloudRestore'

class TempFileProvider(object):

    def __init__(self):
        self.baseFolder = tempfile.gettempdir()
        self.tempFolder = None
        atexit.register(self.removeTempFolder)
    
    def removeTempFolder(self):
        if not self.tempFolder:
            return
        
        shutil.rmtree(self.tempFolder)
        self.tempFolder = None
    
    def getRandomString(self, length=32):
        """Generate a random string of fixed length """
        letters = string.ascii_lowercase + string.ascii_uppercase
        return ''.join(random.choice(letters) for i in range(stringLength))

    def getTempFolder(self):
        if not self.tempFolder:
            self.tempFolder = os.path.join(self.baseFolder, NAME)

            if not os.path.exists(self.tempFolder):
                os.mkdir(self.tempFolder)

        return self.tempFolder
    
    def getFile(self, filename=None):
        if not filename:
            filename = self.getRandomString(32)
        
        return os.path.join(self.getTempFolder(), filename)