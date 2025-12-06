from texasholdem import TexasHoldEm
from texasholdem.gui.text_gui import TextGUI
from texasholdem.agents import random_agent, call_agent, openai_agent, gemini_agent, claude_agent

game = TexasHoldEm(buyin=1000000, big_blind=2, small_blind=1, max_players=3)
gui = TextGUI(game=game)

while game.is_game_running():
    game.start_hand()
    while game.is_hand_running():
      if game.current_player == 0:
        game.take_action(*gemini_agent(game))
      elif game.current_player == 1:
        game.take_action(*claude_agent(game))
      else:
        game.take_action(*openai_agent(game))

    path = game.export_history('./hand_history/test1.2/texas.pgn') 