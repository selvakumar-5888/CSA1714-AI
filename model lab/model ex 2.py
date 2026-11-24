
N = 4
board = [-1] * N
count = 0

def is_safe(row, col):
    for i in range(row):
        if board[i] == col:
            return False

        if abs(board[i] - col) == abs(i - row):
            return False

    return True

def solve(row):
    global count

    if row == N:
        count += 1
        print("Solution", count)

        for i in range(N):
            for j in range(N):
                if board[i] == j:
                    print("Q", end=" ")
                else:
                    print(".", end=" ")
            print()
        print()
        return

    for col in range(N):
        if is_safe(row, col):
            board[row] = col
            solve(row + 1)
            board[row] = -1

solve(0)
print("Total Solutions:", count)
