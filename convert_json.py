import json

# Read data from the text file
with open('alternate_list.txt', "r") as file:
    lines = file.readlines()

# Process the lines to create a dictionary
destinations_data = {}
current_destination = None
current_letter = None

for line in lines:
    line = (line.strip()).split(")")
    current_destination = line[0][1:]
    minima = json.loads(line[1])
    if current_destination not in destinations_data:
        destinations_data[current_destination] = []

    destinations_data[current_destination] += minima

# Create the final data dictionary
data = destinations_data
print(data)
