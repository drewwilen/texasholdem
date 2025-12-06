import csv
import glob
import os
import re

WINNERS_PATTERN = re.compile(r"\[(.*?)\]")
PLAYER_CHIPS_PATTERN = re.compile(r"Player Chips:\s*([0-9,\s]+)")

def extract_winner(line):
    m = WINNERS_PATTERN.search(line)
    if not m:
        return None
    x = m.group(1).strip()
    return None if x == "" else int(x)

def extract_starting_chips(line):
    m = PLAYER_CHIPS_PATTERN.search(line)
    if not m:
        return None
    return [int(x) for x in m.group(1).split(",")]

def extract_file_index(name):
    base = os.path.basename(name)
    m = re.match(r"texas(?:\((\d+)\))?\.pgn$", base)
    return int(m.group(1)) if m and m.group(1) else 0

def rotate_right(chips, shift):
    shift %= len(chips)
    return chips[-shift:] + chips[:-shift]

def main():
    paths = sorted(glob.glob("hand_history/test1.2/texas*.pgn"), key=extract_file_index)
    hands = []
    game_index = 0

    for path in paths:
        starting_chips = None
        winner = None

        with open(path) as f:
            for line in f:
                s = line.strip()
                if starting_chips is None and s.startswith("Player Chips:"):
                    starting_chips = extract_starting_chips(s)
                if s.startswith("Winners:"):
                    winner = extract_winner(s)

        if starting_chips is None:
            continue

        r = rotate_right(starting_chips, game_index % 3)

        hands.append((game_index, winner, r))
        game_index += 1

    rows = []

    for i, (g, w, chips) in enumerate(hands):
        if i < len(hands) - 1:
            next_chips = hands[i+1][2]
            net0 = next_chips[0] - chips[0]
            net1 = next_chips[1] - chips[1]
            net2 = next_chips[2] - chips[2]
        else:
            net0 = net1 = net2 = ""

        rows.append({
            "game_index": g,
            "winner": w,
            "player0_start": chips[0],
            "player1_start": chips[1],
            "player2_start": chips[2],
            "player0_net": net0,
            "player1_net": net1,
            "player2_net": net2,
        })

    with open("test1_2.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            ["game_index","winner","player0_start","player1_start","player2_start",
             "player0_net","player1_net","player2_net"]
        )
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    main()
