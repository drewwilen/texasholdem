"""
Player context data structure for agent decision-making.

This module provides a simple data structure that captures the essential
information a player needs to make a decision in Texas Hold'em.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

from texasholdem.game.game import TexasHoldEm
from texasholdem.game.action_type import ActionType
from texasholdem.game.player_state import PlayerState
from texasholdem.game.hand_phase import HandPhase
from texasholdem.card.card import Card


@dataclass
class PlayerContext:
    """
    Simple context information for a player to make a decision.
    
    This data structure captures the essential information a player needs
    to make a decision in Texas Hold'em, suitable for passing to an LLM
    or other decision-making system.
    """
    
    # Current player's information
    player_id: int
    hand: List[Card]
    chips: int
    chips_to_call: int
    
    # Game state
    hand_phase: HandPhase
    board_cards: List[Card]
    
    # Pot and betting
    total_pot_size: int
    min_raise_amount: int
    
    # Other players (simplified)
    other_players_chips: Dict[int, int]  # player_id -> chips
    other_players_states: Dict[int, PlayerState]  # player_id -> state
    
    # Available moves
    available_actions: List[ActionType]
    raise_range: Optional[range] = None
    
    def to_dict(self) -> Dict:
        """
        Convert the context to a dictionary for easy serialization.
        Useful for passing to LLMs or logging.
        """
        RANK_ORDER = "23456789TJQKA"
        rank_value = {r: i for i, r in enumerate(RANK_ORDER)}
        sorted_cards = sorted(self.hand, key=lambda c: rank_value[str(c)[0]], reverse=True)
        card_strings = [str(card) for card in sorted_cards]

        return {
            "player_id": self.player_id,
            "hand": card_strings,
            "chips": self.chips,
            "chips_to_call": self.chips_to_call,
            "hand_phase": self.hand_phase.name,
            "board_cards": [str(card) for card in self.board_cards],
            "total_pot_size": self.total_pot_size,
            "min_raise_amount": self.min_raise_amount,
            "other_players": {
                str(pid): {
                    "chips": chips,
                    "state": self.other_players_states[pid].name
                }
                for pid, chips in self.other_players_chips.items()
            },
            "available_actions": [action.name for action in self.available_actions],
            "raise_range": (
                {"min": self.raise_range.start, "max": self.raise_range.stop - 1}
                if self.raise_range else None
            ),
        }


def create_player_context(game: TexasHoldEm, player_id: Optional[int] = None) -> PlayerContext:
    """
    Create a PlayerContext object from a TexasHoldEm game state.
    
    Arguments:
        game (TexasHoldEm): The current game state
        player_id (int, optional): The player ID to create context for.
            If None, uses the current player.
    
    Returns:
        PlayerContext: A simple context object with essential information
    """
    if player_id is None:
        player_id = game.current_player
    
    current_player = game.players[player_id]
    
    # Calculate total pot size
    total_pot = sum(pot.get_total_amount() for pot in game.pots)
    
    # Get other players info
    other_players_chips = {}
    other_players_states = {}
    for pid in range(game.max_players):
        if pid != player_id:
            other_players_chips[pid] = game.players[pid].chips
            other_players_states[pid] = game.players[pid].state
    
    # Get available moves
    available_moves = game.get_available_moves()
    available_actions = available_moves.action_types
    raise_range = available_moves.raise_range if available_moves.raise_range else None
    
    hand=game.get_hand(player_id)
    # Create context
    context = PlayerContext(
        player_id=player_id,
        hand=game.get_hand(player_id),
        chips=current_player.chips,
        chips_to_call=game.chips_to_call(player_id),
        hand_phase=game.hand_phase,
        board_cards=list(game.board),
        total_pot_size=total_pot,
        min_raise_amount=game.min_raise(),
        other_players_chips=other_players_chips,
        other_players_states=other_players_states,
        available_actions=available_actions,
        raise_range=raise_range,
    )
    
    return context
