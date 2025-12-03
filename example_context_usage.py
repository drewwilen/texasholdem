"""
Example script demonstrating how to use PlayerContext for agent decision-making.

This script shows how to create a PlayerContext object and access the
essential information needed for making poker decisions.
"""

from texasholdem import TexasHoldEm
from texasholdem.agents.player_context import create_player_context
from texasholdem.agents.basic import context_agent


def main():
    # Create a game
    game = TexasHoldEm(buyin=500, big_blind=5, small_blind=2, max_players=6)
    game.start_hand()
    
    print("=" * 60)
    print("PlayerContext Example (Simplified)")
    print("=" * 60)
    
    # Create context for the current player
    context = create_player_context(game)
    
    print(f"\nPlayer ID: {context.player_id}")
    print(f"Hand: {[str(card) for card in context.hand]}")
    print(f"Board Cards: {[str(card) for card in context.board_cards]}")
    print(f"Hand Phase: {context.hand_phase.name}")
    print(f"\nPlayer Chips: {context.chips}")
    print(f"Chips to Call: {context.chips_to_call}")
    print(f"Total Pot Size: {context.total_pot_size}")
    print(f"Min Raise Amount: {context.min_raise_amount}")
    
    print(f"\nOther Players:")
    for pid, chips in context.other_players_chips.items():
        state = context.other_players_states[pid]
        print(f"  Player {pid}: {chips} chips, State: {state.name}")
    
    print(f"\nAvailable Actions: {[a.name for a in context.available_actions]}")
    if context.raise_range:
        print(f"Raise Range: {context.raise_range.start} to {context.raise_range.stop - 1}")
    
    print(f"\n" + "=" * 60)
    print("Converting to Dictionary (useful for LLM input):")
    print("=" * 60)
    context_dict = context.to_dict()
    print(f"\nContext Dictionary:")
    for key, value in context_dict.items():
        print(f"  {key}: {value}")
    
    print(f"\n" + "=" * 60)
    print("Using context_agent (example agent that uses PlayerContext):")
    print("=" * 60)
    action, total = context_agent(game)
    print(f"Agent chose: {action.name}" + (f" to {total}" if total else ""))


if __name__ == "__main__":
    main()
