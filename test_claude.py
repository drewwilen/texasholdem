"""
Example script demonstrating how to use the Claude AI agent.

Note: This requires the anthropic package and an API key.
Install with: pip install anthropic
Set API key: export ANTHROPIC_API_KEY="your-key-here"
"""

import os
from texasholdem import TexasHoldEm
from texasholdem.agents.ai import claude_agent


def main():
    # Check if API key is set
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return
    
    # Create a game
    game = TexasHoldEm(buyin=500, big_blind=5, small_blind=2, max_players=6)
    game.start_hand()
    
    print("=" * 60)
    print("Claude Agent Example")
    print("=" * 60)
    print(f"\nCurrent Player: {game.current_player}")
    print(f"Hand: {[str(card) for card in game.get_hand(game.current_player)]}")
    print(f"Board: {[str(card) for card in game.board]}")
    print(f"Chips: {game.players[game.current_player].chips}")
    print(f"Chips to Call: {game.chips_to_call(game.current_player)}")
    
    print("\nCalling Claude agent...")
    try:
        # Call the Claude agent (using claude-3-5-haiku-latest by default)
        action, total = claude_agent(game)
        
        print(f"\nAgent chose: {action.name}" + (f" to {total}" if total else ""))
        
        # Validate the move
        try:
            game.validate_move(action=action, total=total, throws=True)
            print("✓ Move is valid!")
        except ValueError as e:
            print(f"✗ Move is invalid: {e}")
            
    except ImportError as e:
        print(f"\nError: {e}")
        print("Install the anthropic package with: pip install anthropic")
    except ValueError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    main()
