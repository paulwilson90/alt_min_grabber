import json

def convert_to_json():
    with open('alternate_list.txt', "r") as file:
        lines = file.readlines()

    destinations_data = {}

    for line in lines:
        line = (line.strip()).split(")")
        current_destination = line[0][1:]
        minima = json.loads(line[1])
        if current_destination not in destinations_data:
            destinations_data[current_destination] = []

        destinations_data[current_destination] += minima


    with open("alternate_json.json", "w") as a:
        a.write(json.dumps(destinations_data))

