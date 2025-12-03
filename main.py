from texasholdem import TexasHoldEm
from texasholdem.gui.text_gui import TextGUI
from texasholdem.agents import random_agent, call_agent, openai_agent, gemini_agent

game = TexasHoldEm(buyin=500, big_blind=5, small_blind=2, max_players=2)
gui = TextGUI(game=game)


while game.is_game_running():
    game.start_hand()

    while game.is_hand_running():
      if game.current_player == 0:
        gui.run_step()
      else:
        game.take_action(*gemini_agent(game))

    path = game.export_history('./hand_history')     # save history
    # gui.replay_history(path)                 # replay history


