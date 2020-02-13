def startProgram():
    from .NextcloudRestore import NextcloudRestore

    base = NextcloudRestore()
    base.initialize()
    base.mainLoop()