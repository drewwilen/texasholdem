import csv
import glob
import os
import re

WINNERS_PATTERN = re.compile(r"\[(.*?)\]")
PLAYER_CHIPS_PATTERN = re.compile(r"Player Chips:\s*([0-9,\s]+)")
BIG_BLIND_PATTERN = re.compile(r"Big Blind:\s*(\d+)")
SMALL_BLIND_PATTERN = re.compile(r"Small Blind:\s*(\d+)")
ACTION_PATTERN = re.compile(r"\((\d+),(\w+)(?:,(\d+))?\)")

def extract_winner(line):
    m = WINNERS_PATTERN.search(line)
    if not m:
        return None
    x = m.group(1).strip()
    if x == "":
        return None
    # Handle multiple winners (tie) - split by comma and strip spaces
    winners = [int(w.strip()) for w in x.split(",")]
    if len(winners) == 1:
        return winners[0]
    elif len(winners) > 1:
        return None  # Tie - multiple winners
    else:
        return None

def extract_starting_chips(line):
    m = PLAYER_CHIPS_PATTERN.search(line)
    if not m:
        return None
    return [int(x) for x in m.group(1).split(",")]

def extract_blinds(lines):
    """Extract big blind and small blind amounts from PREHAND section."""
    big_blind = None
    small_blind = None
    for line in lines:
        s = line.strip()
        if s.startswith("Big Blind:"):
            m = BIG_BLIND_PATTERN.search(s)
            if m:
                big_blind = int(m.group(1))
        elif s.startswith("Small Blind:"):
            m = SMALL_BLIND_PATTERN.search(s)
            if m:
                small_blind = int(m.group(1))
    return big_blind, small_blind

def parse_preflop_actions(lines):
    """Parse PREFLOP section to extract betting actions."""
    preflop_actions = []
    in_preflop = False
    
    for line in lines:
        s = line.strip()
        if s == "PREFLOP":
            in_preflop = True
            continue
        if in_preflop:
            if s.startswith("FLOP") or s.startswith("SETTLE") or s.startswith("TURN") or s.startswith("RIVER"):
                break
            # Parse actions like: "1. (0,RAISE,6);(1,CALL)"
            if s and not s.startswith("New Cards:"):
                # Extract all actions from this line
                actions = ACTION_PATTERN.findall(s)
                for player_id, action_type, total in actions:
                    preflop_actions.append({
                        'player_id': int(player_id),
                        'action': action_type,
                        'total': int(total) if total else None
                    })
    
    return preflop_actions

def calculate_voluntary_pot_and_preflop_raise(preflop_actions, num_players, big_blind, small_blind):
    """
    Calculate voluntary pot contributions and pre-flop raise status for each player.
    
    Voluntary pot = all chips put in pot during PREFLOP betting round (excluding mandatory blinds).
    Pre-flop raise = whether player made a RAISE action in PREFLOP.
    
    Note: Blinds are posted before PREFLOP actions start. We track:
    - Small blind (typically player 1): posts small_blind amount
    - Big blind (typically player 2): posts big_blind amount
    - All other actions are voluntary contributions
    
    Returns:
        - voluntary_pot: dict mapping player_id -> voluntary chips put in pot (excluding blinds)
        - preflop_raised: dict mapping player_id -> bool (whether they raised pre-flop)
    """
    voluntary_pot = {i: 0 for i in range(num_players)}
    preflop_raised = {i: False for i in range(num_players)}
    
    # Track current bet amounts per player in this round
    # Initialize with blinds (assuming standard rotation: button=0, SB=1, BB=2)
    player_bets = {i: 0 for i in range(num_players)}
    
    # Set initial blind amounts
    if small_blind is not None and 1 < num_players:
        player_bets[1] = small_blind
    if big_blind is not None and 2 < num_players:
        player_bets[2] = big_blind
    
    # Current bet level starts at big blind
    current_raise_to = big_blind if big_blind is not None else 0
    
    # Process actions to track betting
    for action in preflop_actions:
        player_id = action['player_id']
        action_type = action['action']
        total = action['total']
        
        if action_type == 'RAISE':
            preflop_raised[player_id] = True
            if total is not None:
                # Total is the amount player has bet total (including blinds)
                amount_to_add = total - player_bets[player_id]
                player_bets[player_id] = total
                current_raise_to = total
                voluntary_pot[player_id] += amount_to_add
            else:
                # RAISE without total - this shouldn't happen, but handle it
                # Assume minimum raise
                min_raise = current_raise_to * 2 if current_raise_to > 0 else (big_blind * 2 if big_blind else 0)
                amount_to_add = min_raise - player_bets[player_id]
                if amount_to_add > 0:
                    player_bets[player_id] = min_raise
                    current_raise_to = min_raise
                    voluntary_pot[player_id] += amount_to_add
        elif action_type == 'CALL':
            if total is not None:
                # Total amount player has bet (including blinds)
                amount_to_add = total - player_bets[player_id]
                player_bets[player_id] = total
                voluntary_pot[player_id] += amount_to_add
            else:
                # CALL without total means calling the current bet level
                amount_to_add = current_raise_to - player_bets[player_id]
                if amount_to_add > 0:
                    player_bets[player_id] = current_raise_to
                    voluntary_pot[player_id] += amount_to_add
        elif action_type == 'CHECK':
            # No additional voluntary contribution (player already has chips in from blind or previous action)
            pass
        elif action_type == 'FOLD':
            # No additional voluntary contribution
            pass
    
    return voluntary_pot, preflop_raised

def extract_file_index(name):
    base = os.path.basename(name)
    m = re.match(r"texas(?:\((\d+)\))?\.pgn$", base)
    return int(m.group(1)) if m and m.group(1) else 0

def rotate_right(chips, shift):
    shift %= len(chips)
    return chips[-shift:] + chips[:-shift]

def main():
    paths = sorted(glob.glob("hand_history/test1.3/texas*.pgn"), key=extract_file_index)
    hands = []
    game_index = 0

    for path in paths:
        starting_chips = None
        winner = None
        big_blind = None
        small_blind = None
        preflop_actions = []
        
        with open(path) as f:
            lines = f.readlines()
            for line in lines:
                s = line.strip()
                if starting_chips is None and s.startswith("Player Chips:"):
                    starting_chips = extract_starting_chips(s)
                if s.startswith("Winners:"):
                    winner = extract_winner(s)
            
            # Extract blinds
            big_blind, small_blind = extract_blinds(lines)
            
            # Parse preflop actions
            preflop_actions = parse_preflop_actions(lines)

        if starting_chips is None:
            continue

        num_players = len(starting_chips)
        r = rotate_right(starting_chips, game_index % num_players)
        
        # Calculate voluntary pot and preflop raise
        voluntary_pot, preflop_raised = calculate_voluntary_pot_and_preflop_raise(
            preflop_actions, num_players, big_blind, small_blind
        )
        
        # Rotate voluntary pot and preflop_raised to match chip rotation
        voluntary_pot_rotated = {}
        preflop_raised_rotated = {}
        for i in range(num_players):
            new_idx = (i + (game_index % num_players)) % num_players
            voluntary_pot_rotated[i] = voluntary_pot[new_idx]
            preflop_raised_rotated[i] = preflop_raised[new_idx]

        hands.append((game_index, winner, r, voluntary_pot_rotated, preflop_raised_rotated))
        game_index += 1

    rows = []

    for i, (g, w, chips, vp, pr) in enumerate(hands):
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
            "player0_voluntary_pot": vp[0],
            "player1_voluntary_pot": vp[1],
            "player2_voluntary_pot": vp[2],
            "player0_preflop_raise": 1 if pr[0] else 0,
            "player1_preflop_raise": 1 if pr[1] else 0,
            "player2_preflop_raise": 1 if pr[2] else 0,
        })

    with open("test1_3_advanced.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            ["game_index","winner","player0_start","player1_start","player2_start",
             "player0_net","player1_net","player2_net",
             "player0_voluntary_pot","player1_voluntary_pot","player2_voluntary_pot",
             "player0_preflop_raise","player1_preflop_raise","player2_preflop_raise"]
        )
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    main()

