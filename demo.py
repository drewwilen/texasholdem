from texasholdem import TexasHoldEm
from texasholdem.gui.text_gui import TextGUI
from texasholdem.agents import random_agent, call_agent, openai_agent, gemini_agent, claude_agent
import time

# User vs OPENAI vs GEMINI vs CLAUDE
game = TexasHoldEm(buyin=500, big_blind=2, small_blind=1, max_players=4)
gui = TextGUI(game=game, visible_players=[0])

while game.is_game_running():
  game.start_hand()

  while game.is_hand_running():
    if game.current_player == 0:
      gui.run_step()
    elif game.current_player == 1:
      gui.display_state()
      game.take_action(*gemini_agent(game))
    elif game.current_player == 2:
      gui.display_state()
      game.take_action(*claude_agent(game))
    else:
      gui.display_state()
      game.take_action(*openai_agent(game))

  # show cards
  old_vis = gui.visible_players         
  gui.visible_players = list(range(game.max_players))  
  gui.display_state() 
  time.sleep(5)
  gui.visible_players = old_vis

  path = game.export_history('./hand_history')
