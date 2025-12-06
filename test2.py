from texasholdem import TexasHoldEm
from texasholdem.gui.text_gui import TextGUI
from texasholdem.agents import openai_agent, claude_agent

hand_index = 0

while True:
    game = TexasHoldEm(buyin=10000, big_blind=2, small_blind=1, max_players=2)
    gui = TextGUI(game=game)

    if hand_index % 2 == 0:
        agent0 = claude_agent
        agent1 = openai_agent
    else:
        agent0 = openai_agent
        agent1 = claude_agent

    game.start_hand()
    while game.is_hand_running():
        if game.current_player == 0:
            game.take_action(*agent0(game))
        else:
            game.take_action(*agent1(game))

    path = game.export_history('./hand_history/test3.tight_aware/texas.pgn')
    hand_index += 1
