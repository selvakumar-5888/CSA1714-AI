
def f(x):
    return -(x - 5) ** 2 + 25

x = 0
step = 1

print("States visited:")

while True:
    current = f(x)
    left = f(x - step)
    right = f(x + step)

    print("x =", x, "Value =", current)

    if left > current:
        x = x - step
    elif right > current:
        x = x + step
    else:
        break

print("Maximum value =", f(x))
print("Best state =", x)
