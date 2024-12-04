import ufirestore
import ufirebase
from ufireauth import FirebaseAuth

# HOUSE_ID = "8zOslJW2Xp6softlHE7R"
HOUSE_ID = "4UqXejWukZOcnwPnRauD"


def tracebackException(e):
    import sys
    sys.print_exception(e)
    sys.exit(0)


class FirebaseStorage:
    def __init__(self):
        self.auth = None
        self.token = None
        self.initAuth()

    def initAuth(self):
        print(">> Getting auth...")
        self.auth = FirebaseAuth("AIzaSyB42-sJ5ZfH_t-PWjk5VPVukYjNwnZxSTs")
        self.auth.sign_in("a.ct@lasallistas.org.mx", "@lexis_HM.2003")

        self.token = self.auth.session.access_token
        if not self.token:
            print(">> Error getting token!")
            return None

        print("<< Token found!")
        return self.token

    def getRoomName(self, path):
        print("> Getting room name...")
        ufirestore.set_project_id("my-smart-home-d0a40")
        ufirestore.set_access_token(self.token)
        raw_doc = ufirestore.get(path)
        print(raw_doc)
        print(type(raw_doc))
        # TODO: Check if the room exists in array
        return raw_doc['name']


class FirebaseRealtime:
    def __init__(self, roomCatalog):
        self.r = roomCatalog
        self.initFirebase()

    def initFirebase(self):
        ufirebase.setURL("https://my-smart-home-d0a40-default-rtdb.firebaseio.com/")
        ufirebase.get("houses/"+HOUSE_ID, "Sensors", id=0, bg=False, cb=(self._fetchData, ("Sensors", True)), limit=False)
        ufirebase.get("houses/"+HOUSE_ID, "Devices", id=0, bg=False, cb=(self._fetchData, ("Devices", True)), limit=False)

    def _fetchData(self, varname, start=False):
        print(f"> Getting {varname}...")
        try:
            print("=" * 10)
            dictData = getattr(ufirebase, varname)
            for device in dictData[varname]:
                typeRoom, roomID = device.split("_")[0], device.split("_")[1]
                print(">> Habitacion: ", roomID)
                print(">> Tipo: ", typeRoom)
                for key, value in dictData[varname][device].items():
                    if start:
                        if varname == "Devices":
                            self.r.addDevice(key, device.split("_"), value)
                        else:
                            self.r.addSensor(key, device.split("_"), value)
                    else:
                        print("  >> Name: ", value['deviceName'])
                        d = self.r.getDevice(key, device.split("_"))
                        if d is None:
                            continue
                        d.setDeviceState(value['state'])

                    print("-" * 10)
            print("<< Devices fetched!")
            print("=" * 10)
        except Exception as e:
            tracebackException(e)

    def sendData(self, data):
        print("> Sending data...")
        # {
        #     path: {
        #         "latestData": {
        #             "time": "2024-11-21T21:40:33.732664",
        #             "value": 0
        #         },
        #     }
        # }
        for key, value in data.items():
            print(">> Updating: ", key)
            ufirebase.patch(key, value, bg=False, cb=None, id=0)
            print("-" * 10)
        print("< Data sent!")

    def receiveDataDevices(self):
        print("> Receiving data devices...")
        ufirebase.get("houses/"+HOUSE_ID, "Devices", id=0, bg=False, cb=(self._fetchData, ("Devices")), limit=False)
        print("< Data received!")
