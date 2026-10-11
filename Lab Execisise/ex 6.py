
rooms = {
    'A': 'Dirty',
    'B': 'Dirty'
}

location = 'A'

while True:
    print("Vacuum is in Room", location)

    if rooms[location] == 'Dirty':
        print("Cleaning Room", location)
        rooms[location] = 'Clean'
    else:
        print("Room", location, "is already clean")

    if location == 'A':
        location = 'B'
    else:
        if all(status == 'Clean' for status in rooms.values()):
            break
        location = 'A'

    if all(status == 'Clean' for status in rooms.values()):
        break

print("\nFinal Room Status:")
for room, status in rooms.items():
    print("Room", room, ":", status)

print("All rooms are clean.")
