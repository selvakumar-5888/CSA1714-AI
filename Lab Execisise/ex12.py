
# Tic-Tac-Toe Game for Two Players

board = [' '] * 9


def display_board():
    print()
    for i in range(0, 9, 3):
        print(" " + " | ".join(board[i:i + 3]))
        if i < 6:
            print("---+---+---")
    print()


def check_winner(player):
    winning_positions = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]

    for a, b, c in winning_positions:
        if board[a] == board[b] == board[c] == player:
            return True
    return False


def play_game():
    current_player = 'X'

    print("TIC-TAC-TOE")
    print("Positions are numbered 1 to 9:")
    print(" 1 | 2 | 3")
    print("---+---+---")
    print(" 4 | 5 | 6")
    print("---+---+---")
    print(" 7 | 8 | 9")

    while True:
        display_board()

        try:
            position = int(
                input(f"Player {current_player}, enter position (1-9): ")
            ) - 1
        except ValueError:
            print("Invalid input. Enter a number.")
            continue

        if position < 0 or position > 8 or board[position] != ' ':
            print("Invalid position. Try again.")
            continue

        board[position] = current_player

        if check_winner(current_player):
            display_board()
            print("Player", current_player, "wins!")
            break

        if ' ' not in board:
            display_board()
            print("The game is a draw!")
            break

        current_player = 'O' if current_player == 'X' else 'X'


play_game()
