import csv
import glob
import os
import re

# Matches: Winners: (Pot 0,20,-1,[0])
WINNERS_PATTERN = re.compile(r"\[(.*?)\]")

def extract_winner(line: str):
    """Extract winner from a 'Winners:' line. Returns int or None."""
    m = WINNERS_PATTERN.search(line)
    if not m:
        return None
    inner = m.group(1).strip()
    if inner == "":
        return None
    return int(inner)  # only 1 winner in 1v1 games

def extract_file_index(name: str) -> int:
    """
    Sort files like:
    texas.pgn -> 0
    texas(1).pgn -> 1
    texas(5).pgn -> 5
    """
    base = os.path.basename(name)
    m = re.match(r"texas(?:\((\d+)\))?\.pgn$", base)
    if not m:
        return 999999
    if m.group(1) is None:
        return 0
    return int(m.group(1))

def main():
    paths = sorted(
        glob.glob(os.path.join("hand_history", "texas*.pgn")),
        key=extract_file_index
    )

    rows = []
    game_number = 0

    for path in paths:
        with open(path, "r") as f:
            for raw_line in f:
                line = raw_line.strip()
                if line.startswith("Winners:"):
                    winner = extract_winner(line)
                    rows.append({"game_number": game_number, "winner": winner})
                    game_number += 1

    # Write CSV
    with open("games_summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["game_number", "winner"])
        writer.writeheader()
        writer.writerows(rows)

    print("Wrote games_summary.csv with", len(rows), "games.")

if __name__ == "__main__":
    main()
