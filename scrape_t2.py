import csv
import os
from pathlib import Path
from texasholdem.game.history import History
from texasholdem.game.game import TexasHoldEm

def get_pgn_files(directory):
    """Get all PGN files in order: texas.pgn, texas(1).pgn, texas(2).pgn, ..."""
    pgn_files = []
    base_path = Path(directory)
    
    # First add texas.pgn
    first_file = base_path / "texas.pgn"
    if first_file.exists():
        pgn_files.append(first_file)
    
    # Then add numbered files
    i = 1
    while True:
        numbered_file = base_path / f"texas({i}).pgn"
        if numbered_file.exists():
            pgn_files.append(numbered_file)
            i += 1
        else:
            break
    
    return pgn_files

def parse_pgn_file(pgn_path, game_index):
    """Parse a PGN file and return game results mapped to agents."""
    # Import history
    history = History.import_history(pgn_path)
    
    # Get starting chips
    starting_chips = history.prehand.player_chips
    player0_start = starting_chips[0]
    player1_start = starting_chips[1]
    
    # Replay the hand to get final chip counts
    game_iterator = TexasHoldEm._import_history(history)
    final_game = None
    for game_state in game_iterator:
        final_game = game_state
    
    if final_game is None:
        raise ValueError(f"Could not replay hand from {pgn_path}")
    
    # Get final chips
    player0_final = final_game.players[0].chips
    player1_final = final_game.players[1].chips
    
    # Calculate net gains for players
    player0_net = player0_final - player0_start
    player1_net = player1_final - player1_start
    
    # Determine which agent is which based on hand index (matching test2.py logic)
    # hand_index % 2 == 0: agent0 = claude, agent1 = openai
    # hand_index % 2 == 1: agent0 = openai, agent1 = claude
    if game_index % 2 == 0:
        # Even hands: player0 = Claude, player1 = OpenAI
        claude_net = player0_net
        openai_net = player1_net
        claude_start = player0_start
        openai_start = player1_start
    else:
        # Odd hands: player0 = OpenAI, player1 = Claude
        claude_net = player1_net
        openai_net = player0_net
        claude_start = player1_start
        openai_start = player0_start
    
    # Get winner from settle phase and map to agent
    settle = history.settle
    if settle and settle.pot_winners:
        # Get the first pot's winners (usually only one pot in heads-up)
        pot_data = list(settle.pot_winners.values())[0]
        winners = pot_data[2]  # List of winner player IDs
        if len(winners) == 1:
            winner_player = winners[0]
            # Map player ID to agent
            if game_index % 2 == 0:
                # Even: player0=Claude, player1=OpenAI
                winner_agent = 'claude' if winner_player == 0 else 'openai'
            else:
                # Odd: player0=OpenAI, player1=Claude
                winner_agent = 'openai' if winner_player == 0 else 'claude'
        elif len(winners) > 1:
            winner_agent = 'tie'
        else:
            winner_agent = 'tie'
    else:
        winner_agent = 'tie'
    
    return {
        'winner': winner_agent,
        'claude_start': claude_start,
        'openai_start': openai_start,
        'claude_net': claude_net,
        'openai_net': openai_net,
    }

def main():
    pgn_directory = './hand_history/test3.tight'
    output_file = 'test3_tight.csv'
    
    # Get all PGN files in order
    pgn_files = get_pgn_files(pgn_directory)
    print(f"Found {len(pgn_files)} PGN files")
    
    # Parse each file and collect results
    results = []
    for game_index, pgn_path in enumerate(pgn_files):
        try:
            result = parse_pgn_file(pgn_path, game_index)
            result['game_index'] = game_index
            results.append(result)
            print(f"Parsed {pgn_path.name}: Winner={result['winner']}, "
                  f"Claude_net={result['claude_net']}, OpenAI_net={result['openai_net']}")
        except Exception as e:
            print(f"Error parsing {pgn_path.name}: {e}")
            continue
    
    # Write to CSV
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['game_index', 'winner', 'claude_start', 'openai_start', 
                     'claude_net', 'openai_net']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"\nSaved {len(results)} results to {output_file}")

if __name__ == '__main__':
    main()
