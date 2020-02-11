def startProgram():
    from .NextcloudRestore import NextcloudRestore

    base = NextcloudRestore()
    base.chooseProvider()
    base.mainLoop()