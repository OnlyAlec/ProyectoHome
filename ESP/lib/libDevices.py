from machine import Pin, PWM, ADC
from libSensors import MQ2, MFRC522
import utime

HOUSE_ID = "4UqXejWukZOcnwPnRauD"


def wipeAll():
    r = Rooms()
    for key, value in r.pinMapping.items():
        for pin in value:
            p = Pin(pin, Pin.OUT)
            p.value(0)
    print("! All devices wiped\n\n")


tones = {
    'C0': 16,
    'C#0': 17,
    'D0': 18,
    'D#0': 19,
    'E0': 21,
    'F0': 22,
    'F#0': 23,
    'G0': 24,
    'G#0': 26,
    'A0': 28,
    'A#0': 29,
    'B0': 31,
    'C1': 33,
    'C#1': 35,
    'D1': 37,
    'D#1': 39,
    'E1': 41,
    'F1': 44,
    'F#1': 46,
    'G1': 49,
    'G#1': 52,
    'A1': 55,
    'A#1': 58,
    'B1': 62,
    'C2': 65,
    'C#2': 69,
    'D2': 73,
    'D#2': 78,
    'E2': 82,
    'F2': 87,
    'F#2': 92,
    'G2': 98,
    'G#2': 104,
    'A2': 110,
    'A#2': 117,
    'B2': 123,
    'C3': 131,
    'C#3': 139,
    'D3': 147,
    'D#3': 156,
    'E3': 165,
    'F3': 175,
    'F#3': 185,
    'G3': 196,
    'G#3': 208,
    'A3': 220,
    'A#3': 233,
    'B3': 247,
    'C4': 262,
    'C#4': 277,
    'D4': 294,
    'D#4': 311,
    'E4': 330,
    'F4': 349,
    'F#4': 370,
    'G4': 392,
    'G#4': 415,
    'A4': 440,
    'A#4': 466,
    'B4': 494,
    'C5': 523,
    'C#5': 554,
    'D5': 587,
    'D#5': 622,
    'E5': 659,
    'F5': 698,
    'F#5': 740,
    'G5': 784,
    'G#5': 831,
    'A5': 880,
    'A#5': 932,
    'B5': 988,
    'C6': 1047,
    'C#6': 1109,
    'D6': 1175,
    'D#6': 1245,
    'E6': 1319,
    'F6': 1397,
    'F#6': 1480,
    'G6': 1568,
    'G#6': 1661,
    'A6': 1760,
    'A#6': 1865,
    'B6': 1976,
    'C7': 2093,
    'C#7': 2217,
    'D7': 2349,
    'D#7': 2489,
    'E7': 2637,
    'F7': 2794,
    'F#7': 2960,
    'G7': 3136,
    'G#7': 3322,
    'A7': 3520,
    'A#7': 3729,
    'B7': 3951,
    'C8': 4186,
    'C#8': 4435,
    'D8': 4699,
    'D#8': 4978,
    'E8': 5274,
    'F8': 5588,
    'F#8': 5920,
    'G8': 6272,
    'G#8': 6645,
    'A8': 7040,
    'A#8': 7459,
    'B8': 7902,
    'C9': 8372,
    'C#9': 8870,
    'D9': 9397,
    'D#9': 9956,
    'E9': 10548,
    'F9': 11175,
    'F#9': 11840,
    'G9': 12544,
    'G#9': 13290,
    'A9': 14080,
    'A#9': 14917,
    'B9': 15804
}


class music:
    def __init__(self, songString='0 D4 8 0', looping=True, tempo=3, duty=2512, pin=None, pins=[Pin(0)]):
        self.tempo = tempo
        self.song = songString
        self.looping = looping
        self.duty = duty

        self.stopped = False

        self.timer = -1
        self.beat = -1
        self.arpnote = 0

        self.pwms = []

        if (not (pin is None)):
            pins = [pin]
        self.pins = pins
        for pin in pins:
            self.pwms.append(PWM(pin, freq=50))

        self.notes = []

        self.playingNotes = []
        self.playingDurations = []

        # Find the end of the song
        self.end = 0
        splitSong = self.song.split(";")
        for note in splitSong:
            snote = note.split(" ")
            testEnd = round(float(snote[0])) + ceil(float(snote[2]))
            if (testEnd > self.end):
                self.end = testEnd

        # Create empty song structure
        while (self.end > len(self.notes)):
            self.notes.append(None)

        # Populate song structure with the notes
        for note in splitSong:
            snote = note.split(" ")
            beat = round(float(snote[0]))

            if (self.notes[beat] == None):
                self.notes[beat] = []
            self.notes[beat].append([snote[1], ceil(float(snote[2]))])  # Note, Duration

        # Round up end of song to nearest bar
        self.end = ceil(self.end / 8) * 8

    def stop(self):
        for pwm in self.pwms:
            pwm.deinit()
        self.stopped = True

    def restart(self):
        self.beat = -1
        self.timer = 0
        self.stop()
        self.pwms = []
        for pin in self.pins:
            self.pwms.append(PWM(pin))
        self.stopped = False

    def resume(self):
        self.stop()
        self.pwms = []
        for pin in self.pins:
            self.pwms.append(PWM(pin))
        self.stopped = False

    def tick(self):
        if (not self.stopped):
            self.timer = self.timer + 1

            # Loop
            if (self.timer % (self.tempo * self.end) == 0 and (not (self.timer == 0))):
                if (not self.looping):
                    self.stop()
                    return False
                self.beat = -1
                self.timer = 0

            # On Beat
            if (self.timer % self.tempo == 0):
                self.beat = self.beat + 1

                # Remove expired notes from playing list
                i = 0
                while (i < len(self.playingDurations)):
                    self.playingDurations[i] = self.playingDurations[i] - 1
                    if (self.playingDurations[i] <= 0):
                        self.playingNotes.pop(i)
                        self.playingDurations.pop(i)
                    else:
                        i = i + 1

                # Add new notes and their durations to the playing list

                """
                #Old method runs for every note, slow to process on every beat and causes noticeable delay
                ssong = song.split(";")
                for note in ssong:
                    snote = note.split(" ")
                    if int(snote[0]) == beat:
                        playingNotes.append(snote[1])
                        playingDurations.append(int(snote[2]))
                """

                if (self.beat < len(self.notes)):
                    if (self.notes[self.beat] != None):
                        for note in self.notes[self.beat]:
                            self.playingNotes.append(note[0])
                            self.playingDurations.append(note[1])

                # Only need to run these checks on beats
                i = 0
                for pwm in self.pwms:
                    if (i >= len(self.playingNotes)):
                        if hasattr(pwm, 'duty_u16'):
                            pwm.duty_u16(0)
                        else:
                            pwm.duty(0)
                    else:
                        # Play note
                        if hasattr(pwm, 'duty_u16'):
                            pwm.duty_u16(self.duty)
                        else:
                            pwm.duty(self.duty)
                        pwm.freq(tones[self.playingNotes[i]])
                    i = i + 1

            # Play arp of all playing notes
            if (len(self.playingNotes) > len(self.pwms)):
                p = self.pwms[len(self.pwms)-1]
                if hasattr(p, 'duty_u16'):
                    p.duty_u16(self.duty)
                else:
                    p.duty(self.duty)

                if (self.arpnote > len(self.playingNotes)-len(self.pwms)):
                    self.arpnote = 0
                self.pwms[len(self.pwms)-1].freq(tones[self.playingNotes[self.arpnote+(len(self.pwms)-1)]])
                self.arpnote = self.arpnote + 1

            return True
        else:
            return False


class Device:
    def __init__(self, uid, name, roomID, value=None):
        self.uid = uid
        self.name = name
        self.room = roomID
        self.pin = None
        self.pwm = None
        self.state = value
        self.sensor = False

    def setDeviceState(self, value):
        print(">> Setting device state...")
        if self.state == value:
            print("<< State already set!")
            return

        if self.sensor:
            print("<< Sensor can't change state!")
            return

        self.state = value

        if self.room == "kitchen" and self.state is True:
            self.beep()

        if self.pwm is not None:
            self.pwm.duty(123 if self.state is True else 26)
        else:
            self.pin.value(self.state)
        print("<< Device state set!")

    def setDevicePin(self, index, validPins, typeDevice):
        print(">> Setting device pin...")
        print(">>> Pin Number: ", validPins[index])
        self.pin = Pin(validPins[index], Pin.OUT)

        # ! Devices types
        if typeDevice == "mechanism":
            self.pwm = PWM(self.pin, freq=50)
            self.pwm.duty(123 if self.state is True else 26)
        elif typeDevice in ("light", "alarm"):
            self.pin.value(self.state)
        # ! Sensor types
        elif typeDevice in ("temperature", "humidity",  "lights"):
            self.pin = ADC(validPins[index])
            self.sensor = True
        elif typeDevice == "gas":
            self.pin = MQ2(pinData=validPins[index], baseVoltage=3.3)
            self.pin.calibrate()
            self.sensor = True
        else:
            print("<< Device type not found!")
            return
        print("<< Device/Sensor added!")

    def getDeviceValue(self):
        if isinstance(self.pin, ADC):
            return self.pin.read_u16()
        if isinstance(self.pin, MQ2):
            return self.pin.readMethane()
        return self.state

    def beep(self):


class Rooms:
    def __init__(self):
        self.bano = []
        self.banoPin = [4, 5, 6]
        self.salon = []
        self.salonPin = [7, 15, 16]
        self.dormitorio = []
        self.dormitorioPin = [17, 18, 8]
        self.patio = []
        self.patioPin = [3, 46, 9]
        self.garaje = []
        self.garajePin = [10, 11, 37]
        self.balcon = []
        self.balconPin = [13, 14, 1]
        self.cocina = []
        self.cocinaPin = [2, 42, 41]
        self.comedor = []
        self.comedorPin = [40, 39, 38]
        self.lavadero = []
        self.lavaderoPin = [12, 36, 35]
        self.oficina = []
        self.oficinaPin = [47, 21, 20]

        self.mapping = {
            "bathroom": self.bano,
            "livingRoom": self.salon,
            "bedroom": self.dormitorio,
            "yard": self.patio,
            "garage": self.garaje,
            "balcony": self.balcon,
            "kitchen": self.cocina,
            "diningRoom": self.comedor,
            "laundryRoom": self.lavadero,
            "homeOffice": self.oficina
        }
        self.pinMapping = {
            "bathroom": self.banoPin,
            "livingRoom": self.salonPin,
            "bedroom": self.dormitorioPin,
            "yard": self.patioPin,
            "garage": self.garajePin,
            "balcony": self.balconPin,
            "kitchen": self.cocinaPin,
            "diningRoom": self.comedorPin,
            "laundryRoom": self.lavaderoPin,
            "homeOffice": self.oficinaPin
        }

    # Example of Device:
    # {
    #     "650a3464-f681-4b97-b26e-c1fc59dbd2a0":{
    #         "totalOnTime":0,
    #         "deviceName":"Foco",
    #         "state":false
    #     }
    # }
    def addDevice(self, uidDevice, room, deviceInfo):
        print(">> Adding device to room...")
        roomName = room[0]
        roomID = room[1]

        if roomName in self.mapping:
            deviceName = deviceInfo['deviceName']
            deviceValue = deviceInfo['state']
            deviceType = deviceInfo['type']

            print(">>> Device: ", deviceName)
            print(">>> Value: ", deviceValue)
            print(">>> Type: ", deviceType)

            if len(self.mapping[roomName]) >= 3:
                print("<< Room is full!")
                return

            device = Device(uidDevice, deviceName, roomID, deviceValue)
            device.setDevicePin(len(self.mapping[roomName]), self.pinMapping[roomName], deviceType)
            self.mapping[roomName].append(device)
        else:
            print("<< Room not found!")

    # Example of Sensor:
    # {
    #     "4b5f52bd-0325-480a-b52e-07f8899aadc6": {
    #         "latestData": {
    #           "time": "2024-11-21T21:40:33.732664",
    #           "value": 0
    #         },
    #         "sensorName": "Hot",
    #         "type": "temperature"
    #     }
    # }
    def addSensor(self, uidSensor, room, sensorInfo):
        print(">> Adding sensor to room...")
        roomName = room[0]
        roomID = room[1]

        print(">>> Room: ", roomName)
        print(">>> Room ID: ", roomID)

        if roomName in self.mapping:
            sensorName = sensorInfo['sensorName']
            sensorType = sensorInfo['type']

            print(">>> Sensor: ", sensorName)
            print(">>> Type: ", sensorType)

            if len(self.mapping[roomName]) >= 3:
                print("<<< Room is full!")
                return

            device = Device(uidSensor, sensorName, roomID)
            device.setDevicePin(len(self.mapping[roomName]), self.pinMapping[roomName], sensorType)
            self.mapping[roomName].append(device)
            print("<< Sensor added!")
        else:
            print("<< Room not found!")

    def readSensors(self):
        print("> Reading sensors...")
        res = {}
        pathLatest, pathHistory, ctime = "", "", None
        for key, value in self.mapping.items():
            print(f">> Room: {key}")
            if len(value) == 0:
                print("  << No devices found!")
                continue

            path = f"houses/{HOUSE_ID}/Sensors/{key}_"
            for device in value:
                print(f"  >>> Name: {device.name}")
                if not device.sensor:
                    continue

                pathLatest += path + device.room + "/" + device.uid + "/latestData/"

                ctime = utime.localtime()
                timestamp = f"{ctime[0]:04d}-{ctime[1]:02d}-{ctime[2]:02d}T{ctime[3]:02d}:{ctime[4]:02d}:{ctime[5]:02d}"
                res[pathLatest] = {
                    "value": device.getDeviceValue(),
                    "time": timestamp
                }

                dateHistory = f"{ctime[0]:04d}-{ctime[1]:02d}-{ctime[2]:02d}"
                timeHistory = f"{ctime[3]:02d}:{ctime[4]:02d}:{ctime[5]:02d}"
                timestampHistory = dateHistory + "T" + timeHistory
                pathHistory += path + device.room + "/" + device.uid + "/history/" + dateHistory + "/" + timeHistory + "/"
                res[pathHistory] = {
                    "time": timestampHistory,
                    "value": device.getDeviceValue()
                }

                pathLatest = ""
                pathHistory = ""
                print("-" * 10)
        print("< Sensors read!\n")
        return res

    def getDevice(self, uid, room):
        print(">>> Getting device...")
        roomName = room[0]
        roomID = room[1]

        for device in self.mapping[roomName]:
            if device.uid == uid and device.room == roomID:
                print(">>>> Device Name: ", device.name)
                print(">>>> Device Pin: ", device.pin)
                print(">>>> Device PWM: ", device.pwm)
                print("<<< Device found!")
                return device

        print("<<< Device not found!")
        return None

    def showDevices(self):
        print("> Showing devices...")
        for key, value in self.mapping.items():
            if (len(value) == 0):
                print(f"<< No devices found in {key}!")
                continue

            print(f">> Room: {key}")
            for device in value:
                print(f"  >>> Name: {device.name}")
                print(f"  >>> State: {device.state}")
                print(f"  >>> Pin: {device.pin}")
                print(f"  >>> PWM: {device.pwm}")
                print(f"  >>> Sensor: {device.sensor}")
                print(f"  >>> UID: {device.uid}")
                print(f"  >>> Room: {device.room}")
                print("-" * 10)
        print("< Devices shown!")
