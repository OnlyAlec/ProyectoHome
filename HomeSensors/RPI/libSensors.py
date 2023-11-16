
def sGas(**kwargs):
    # results = [kwargs["Smoke"], kwargs["LPG"],
    #            kwargs["Methane"], kwargs["Hydrogen"]]
    results = kwargs["Methane"]
    if results > 10000:
        action = {
            "function": "buzzerAction", "args": {
                "buzzer": "BUZZER_COCINA", "state": "ON"
            }
        }

    else:
        action = {
            "function": "buzzerAction", "args": {
                "buzzer": "BUZZER_COCINA", "state": "OFF"
            }
        }

    return action, {"gas": results}, "Pico"


def sHumedad(**kwargs):
    vAnalog = kwargs["valueAnalog"]
    humedad = (vAnalog / 65535) * 100
    # print(f'\t\t◈  Humedad: {humedad}')
    if humedad < 30:
        notification = {
            "type": "notification",
            "title": "¡Recomedacion sobre Jardin!",
            "message": "Es momento de regar el jardín, la humedad de la tierra esta baja."
        }
        return notification, {"humedad": humedad}, "Rpi"
    return None, {"humedad": humedad}, "Rpi"


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
                "args": {"led": "LED_HABITACION", "state": "ON"}
            },
            {
                "function": "ledChange",
                "args": {"led": "LED_JARDIN_LUZ", "state": "ON"}
            }
        ]
    else:
        action = [
            {
                "function": "ledChange",
                "args": {"led": "LED_HABITACION", "state": "OFF"}
            },
            {
                "function": "ledChange",
                "args": {"led": "LED_JARDIN_LUZ", "state": "OFF"}
            }
        ]
    return action, {"luz": porcentaje}, "Pico"


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
    return action, {"IR": status}, "Pico"


def sTemp(**kwargs):
    vAnalog = kwargs["valueAnalog"]
    conversionFactor = 3.3 / (65535)
    v = vAnalog * conversionFactor
    temp = 27 - (v - 0.706)/0.001721
    if temp > 30:
        notification = {
            "type": "notification",
            "title": "¡Recomedacion de Temperatura!",
            "message": "Lleva ropa ligera, la temperatura del dia de hoy es alta."
        }
        return notification, {"temperatura": temp}, "Rpi"
    if temp < 15:
        notification = {
            "type": "notification",
            "title": "¡Recomedacion de Temperatura!",
            "message": "Está haciendo mucho frío, no olvides abrigarte al salir."
        }
        return notification, {"temperatura": temp}, "Rpi"
    return None, {"temperatura": temp}, None
