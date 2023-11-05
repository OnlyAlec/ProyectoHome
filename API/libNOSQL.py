import os
from firebase_admin import db, credentials, initialize_app


class NODB:
    def __init__(self):
        self.connection = db
        self.allTables = []
        self.connect()

    def connect(self):
        cred = credentials.Certificate('./Auth/firebase.json')
        initialize_app(cred, {'databaseURL': os.getenv('URL_FIREBASE')})


class Firebase:
    def __init__(self):
        self.type = None
        self.space = None
        self.dataSensor = None

    def createAlert(self):
        pass

    def createData(self):
        pass

    def setLastData(self):
        pass

    def setLastDataSpace(self):
        pass
