import csv
import glob
import os
import re

# Matches: Winners: (Pot 0,20,-1,[0])
WINNERS_PATTERN = re.compile(r"\[(.*?)\]")
# Matches: Player Chips: 500,495,507
PLAYER_CHIPS_PATTERN = re.compile(r"Player Chips:\s*([0-9,\s]+)")

def extract_winner(line: str):
    """Extract winner from a 'Winners:' line. Returns int or None."""
    m = WINNERS_PATTERN.search(line)
    if not m:
        return None
    inner = m.group(1).strip()
    if inner == "":
        return None
    return int(inner)

def extract_starting_chips(line: str):
    """Extract starting chip counts from a 'Player Chips:' line."""
    m = PLAYER_CHIPS_PATTERN.search(line)
    if not m:
        return None
    nums = m.group(1)
    return [int(x.strip()) for x in nums.split(",") if x.strip() != ""]

def extract_file_index(name: str) -> int:
    """Sort files logically by game number."""
    base = os.path.basename(name)
    m = re.match(r"texas(?:\((\d+)\))?\.pgn$", base)
    if not m:
        return 999999
    return int(m.group(1)) if m.group(1) else 0

def main():
    paths = sorted(
        glob.glob(os.path.join("hand_history/test1.1", "texas*.pgn")),
        key=extract_file_index,
    )

    hands = []
    game_number = 0

    for path in paths:
        starting_chips = None
        winner = None

        with open(path, "r") as f:
            for raw_line in f:
                line = raw_line.strip()

                if starting_chips is None and line.startswith("Player Chips:"):
                    starting_chips = extract_starting_chips(line)

                if line.startswith("Winners:"):
                    winner = extract_winner(line)

        if starting_chips is None:
            continue

        hands.append(
            {
                "game_number": game_number,
                "winner": winner,
                "starting_chips": starting_chips,   # <-- NEW
            }
        )
        game_number += 1

    if not hands:
        print("No hands found.")
        return

    num_players = len(hands[0]["starting_chips"])

    rows = []
    for i, hand in enumerate(hands):
        profits = [None] * num_players

        if i < len(hands) - 1:
            cur_chips = hand["starting_chips"]
            next_chips = hands[i + 1]["starting_chips"]

            n = min(len(cur_chips), len(next_chips), num_players)
            profits = [next_chips[j] - cur_chips[j] for j in range(n)]

        row = {
            "game_number": hand["game_number"],
            "winner": hand["winner"],
        }

        # ---- NEW: Add starting chip columns
        for p in range(num_players):
            row[f"player{p}_start"] = hand["starting_chips"][p]

        # ---- Existing: Net profit columns
        for p in range(num_players):
            key = f"player{p}_net"
            val = profits[p] if p < len(profits) else None
            row[key] = "" if val is None else val

        rows.append(row)

    # ---- NEW: CSV header includes start + net columns
    fieldnames = (
        ["game_number", "winner"]
        + [f"player{p}_start" for p in range(num_players)]   # <-- NEW
        + [f"player{p}_net" for p in range(num_players)]
    )

    with open("games_summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Wrote games_summary.csv with", len(rows), "games.")
    print("Players:", num_players)

if __name__ == "__main__":
    main()
