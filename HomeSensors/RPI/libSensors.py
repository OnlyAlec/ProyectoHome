from math import exp, log


def sGas(**kwargs):
    vAnalog = kwargs["valueAnalog"]
    ro = kwargs["ro"]
    # ^LPG, Methane, Smoke, Hydrogen
    listValues = [(-0.45, 2.95), (-0.38, 3.21), (-0.42, 3.54), (-0.48, 3.32)]
    results = []
    for (a, b) in listValues:
        ratio = vAnalog/ro
        results.append(exp(log(ratio-b)/a))
    # print('\t\t◈  Gas:',
    #       f'LPG: {results[0]},',
    #       f'Methane: {results[1]},',
    #       f'Smoke: {results[2]},',
    #       f'Hydrogen: {results[3]}', sep='\n\t\t\t'
    #       )
    action = [
        {
            "function": "buzzerAction", "args": {
                "buzzer": "BUZZER_COCINA", "state": "ON", "time": 0.5
            }
        },
        {
            "function": "ledChange", "args": {
                "led": "LED_COCINA", "state": "ON"
            }
        }
    ]
    return action, {"gas": results}


def sHumedad(**kwargs):
    vAnalog = kwargs["valueAnalog"]
    humedad = (vAnalog / 65535) * 100
    # print(f'\t\t◈  Humedad: {humedad}')
    action = {
        "function": "ledChange",
        "args": {"led": "LED_JARDIN_HUMEDAD", "state": "ON"}
    }
    return action, {"humedad": humedad}
    # *Si no hay mucha humedad animacion de led azules


def sRFID(**kwargs):
    pass


def sLuz(**kwargs):
    maxDark = 65535
    minLight = 0
    vAnalog = kwargs["valueAnalog"]

    porcentaje = ((vAnalog - minLight) / (maxDark - minLight)) * 100
    porcentaje = 100 - porcentaje
    porcentaje = max(0, min(100, porcentaje))

    # print(f'\t\t◈  Luz: {porcentaje}')
    if porcentaje < 30:
        action = [
            {
                "function": "ledChange",
                "args": {"led": "LED_JARDIN_LUZ", "state": "ON"}
            },
            {
                "function": "ledChange",
                "args": {"led": "LED_HABITACION", "state": "ON"}
            },
            {
                "function": "servoAction",
                "args": {"servo": "SERVO_HABITACION", "state": "ON"}
            }
        ]
    else:
        action = [
            {
                "function": "ledChange",
                "args": {"led": "LED_JARDIN", "state": "OFF"}
            },
            {
                "function": "ledChange",
                "args": {"led": "LED_HABITACION", "state": "OFF"}
            },
            {
                "function": "servoAction",
                "args": {"servo": "SERVO_HABITACION", "state": "OFF"}
            }
        ]
    return action, {"luz": porcentaje}


def sIR(**kwargs):
    status = kwargs["status"]
    # print(f'\t\t◈  Estado IR: {status}')
    if status == "True":
        action = {
            "function": "ledChange",
            "args": {"led": "LED_ENTRADA", "state": "ON"}
        }
    else:
        action = {
            "function": "ledChange",
            "args": {"led": "LED_ENTRADA", "state": "OFF"}
        }
    return action, {"IR": status}


def sTemp(**kwargs):
    vAnalog = kwargs["valueAnalog"]
    conversionFactor = 3.3 / (65535)
    v = vAnalog * conversionFactor
    temp = 27 - (v - 0.706)/0.001721
    # print(f'\t\t◈  Temperatura: {temp}')
    return None, {"temperatura": temp}
