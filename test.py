import json

jsonData = [

    "{\"data\": {\"inicio\": 928024693, \"fin\": 928024737}, \"type\": \"Ultrasonico\", \"time\": [2021, 1, 1, 0, 15, 29, 4, 1]}",

    "{\"data\": {\"inicio\": 928528413, \"fin\": 928528443}, \"type\": \"Ultrasonico\", \"time\": [2021, 1, 1, 0, 15, 29, 4, 1]}",

    "{\"data\": {\"inicio\": 929031760, \"fin\": 929031805}, \"type\": \"Ultrasonico\", \"time\": [2021, 1, 1, 0, 15, 30, 4, 1]}",

    "{\"data\": {\"inicio\": 929535091, \"fin\": 929535117}, \"type\": \"Ultrasonico\", \"time\": [2021, 1, 1, 0, 15, 30, 4, 1]}",

    "{\"data\": {\"inicio\": 930038363, \"fin\": 930038404}, \"type\": \"Ultrasonico\", \"time\": [2021, 1, 1, 0, 15, 31, 4, 1]}",

    "{\"data\": {\"inicio\": 930541654, \"fin\": 930541697}, \"type\": \"Ultrasonico\", \"time\": [2021, 1, 1, 0, 15, 31, 4, 1]}",

    "{\"data\": {\"inicio\": 931045128, \"fin\": 931045172}, \"type\": \"Ultrasonico\", \"time\": [2021, 1, 1, 0, 15, 32, 4, 1]}",

    "{\"data\": {\"inicio\": 931548503, \"fin\": 931548547}, \"type\": \"Ultrasonico\", \"time\": [2021, 1, 1, 0, 15, 32, 4, 1]}",

    "{\"data\": {\"inicio\": 932051803, \"fin\": 932051849}, \"type\": \"Ultrasonico\", \"time\": [2021, 1, 1, 0, 15, 33, 4, 1]}",

    "{\"data\": {\"inicio\": 932555109, \"fin\": 932555153}, \"type\": \"Ultrasonico\", \"time\": [2021, 1, 1, 0, 15, 33, 4, 1]}"

]

for i, d in enumerate(jsonData):
    d = json.loads(d)
    print(d)
