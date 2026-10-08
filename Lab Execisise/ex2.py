N = 8

board = [[0 for _ in range(N)] for _ in range(N)]


def is_safe(row, col):

    for i in range(row):
        if board[i][col] == 1:
            return False

    i = row - 1
    j = col - 1

    while i >= 0 and j >= 0:
        if board[i][j] == 1:
            return False
        i -= 1
        j -= 1

    i = row - 1
    j = col + 1

    while i >= 0 and j < N:
        if board[i][j] == 1:
            return False
        i -= 1
        j += 1

    return True


def solve(row):

    if row == N:
        return True

    for col in range(N):

        if is_safe(row, col):
            board[row][col] = 1

            if solve(row + 1):
                return True

            board[row][col] = 0

    return False


if solve(0):

    print("Solution for 8-Queen Problem:\n")

    for row in board:
        print(" ".join("Q" if cell == 1 else "." for cell in row))

else:
    print("No solution exists.")
