"""
AI agents are included in this module:
    - :func:`openai_agent`
"""

import json
import os
from typing import Tuple, Optional
from dotenv import load_dotenv
load_dotenv()

from texasholdem.game.game import TexasHoldEm
from texasholdem.game.action_type import ActionType
from texasholdem.game.player_state import PlayerState
from texasholdem.agents.player_context import create_player_context
from openai import OpenAI
import google.generativeai as genai

def openai_agent(
    game: TexasHoldEm,
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0,
  ) -> Tuple[ActionType, Optional[int]]:
      """
      An agent that uses OpenAI to make decisions based on the game context.
      
      This agent creates a PlayerContext, converts it to a dictionary, sends it to
      OpenAI with instructions to return a valid poker action, and parses the response.
      
      Arguments:
          game (TexasHoldEm): The TexasHoldEm game
          api_key (str, optional): OpenAI API key. If None, uses OPENAI_API_KEY env var.
          model (str): OpenAI model to use, default "gpt-3.5-turbo" (cheapest option)
          temperature (float): Temperature for the model, default 0.7
      
      Returns:
          Tuple[ActionType, Optional[int]]: An action tuple (action_type, total)
      
      Raises:
          ImportError: If openai package is not installed
          ValueError: If API key is not provided and not in environment
          ValueError: If OpenAI response cannot be parsed
      
      Example:
          >>> game = TexasHoldEm(buyin=500, big_blind=5, small_blind=2)
          >>> game.start_hand()
          >>> action, total = openai_agent(game, api_key="your-api-key")
      """
      
      # Get API key
      if api_key is None:
          api_key = os.getenv("OPENAI_API_KEY")
          if api_key is None:
              raise ValueError(
                  "OpenAI API key not provided. Either pass api_key argument "
                  "or set OPENAI_API_KEY environment variable."
              )
      
      # Create context and convert to dictionary
      context = create_player_context(game)
      context_dict = context.to_dict()
      
      # Create the prompt
      raise_range_info = ""
      if context_dict['raise_range']:
          raise_range_info = f"- The raise total must be between {context_dict['raise_range']['min']} and {context_dict['raise_range']['max']}"
      else:
          raise_range_info = "- RAISE is not available in this situation"
      
      prompt = f"""You are playing Texas Hold'em poker. Here is the current game state:

  {json.dumps(context_dict, indent=2)}

  You must choose one of the available actions: {', '.join(context_dict['available_actions'])}.

  Rules:
  - If you choose RAISE, you must provide a "total" amount (the total amount to raise to)
  {raise_range_info}
  - For other actions (CALL, CHECK, FOLD), do not provide a total value (set it to null)
  - You have {context_dict['chips']} chips
  - You need to call {context_dict['chips_to_call']} chips to stay in
  - The pot is {context_dict['total_pot_size']} chips

  Respond with a JSON object in this exact format:
  {{"action": "ACTION_NAME", "total": null}}

  For RAISE actions, use:
  {{"action": "RAISE", "total": <number>}}

  For other actions, use:
  {{"action": "ACTION_NAME", "total": null}}

  Choose the best action based on your hand, the board, pot odds, and game situation."""

      # Call OpenAI
      client = OpenAI(api_key=api_key)
      
      try:
          response = client.chat.completions.create(
              model=model,
              messages=[
                  {
                      "role": "system",
                      "content": "You are a poker player making decisions in Texas Hold'em. Always respond with valid JSON containing 'action' and 'total' fields."
                  },
                  {
                      "role": "user",
                      "content": prompt
                  }
              ],
              temperature=temperature,
              response_format={"type": "json_object"}
          )
          
          # Parse the response
          response_text = response.choices[0].message.content
          response_json = json.loads(response_text)
          
          # Extract action
          action_str = response_json.get("action", "").upper()
          total = response_json.get("total")
          
          # Convert string to ActionType
          try:
              action = ActionType[action_str]
          except KeyError:
              raise ValueError(
                  f"Invalid action '{action_str}' from OpenAI. "
                  f"Valid actions: {[a.name for a in context.available_actions]}"
              )
          
          # Validate action is available
          if action not in context.available_actions:
              raise ValueError(
                  f"Action '{action_str}' is not available. "
                  f"Available actions: {[a.name for a in context.available_actions]}"
              )
          
          # Validate raise total if action is RAISE
          if action == ActionType.RAISE:
              if total is None:
                  raise ValueError("RAISE action requires a 'total' value")
              if context.raise_range and (total < context.raise_range.start or total >= context.raise_range.stop):
                  raise ValueError(
                      f"Raise total {total} is out of range. "
                      f"Valid range: {context.raise_range.start} to {context.raise_range.stop - 1}"
                  )
              return action, total
          else:
              # For non-raise actions, total should be None
              return action, None
              
      except json.JSONDecodeError as e:
          raise ValueError(f"Failed to parse OpenAI response as JSON: {e}")
      except Exception as e:
          if isinstance(e, ValueError):
              raise
          raise ValueError(f"Error calling OpenAI API: {e}")

def gemini_agent(
    game: TexasHoldEm,
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
    temperature: float = 0,
  ) -> Tuple[ActionType, Optional[int]]:
      """
      An agent that uses Google Gemini to make decisions based on the game context.

      This agent creates a PlayerContext, converts it to a dictionary, sends it to
      Gemini with instructions to return a valid poker action, and parses the response.
      
      Arguments:
          game (TexasHoldEm): The TexasHoldEm game
          api_key (str, optional): OpenAI API key. If None, uses OPENAI_API_KEY env var.
          model (str): OpenAI model to use, default "gpt-3.5-turbo" (cheapest option)
          temperature (float): Temperature for the model, default 0.7
      
      Returns:
          Tuple[ActionType, Optional[int]]: An action tuple (action_type, total)
      
      Raises:
          ImportError: If openai package is not installed
          ValueError: If API key is not provided and not in environment
          ValueError: If OpenAI response cannot be parsed
      
      Example:
          >>> game = TexasHoldEm(buyin=500, big_blind=5, small_blind=2)
          >>> game.start_hand()
          >>> action, total = openai_agent(game, api_key="your-api-key")
      """
      # Get API key
      if api_key is None:
          api_key = os.getenv("GEMINI_API_KEY")
          if api_key is None:
              raise ValueError(
                  "Gemini API key not provided. Pass api_key or set GEMINI_API_KEY env var."
              )

      genai.configure(api_key=api_key)

      # Create context dictionary
      context = create_player_context(game)
      context_dict = context.to_dict()

      # Raise info text
      if context_dict["raise_range"]:
          raise_range_info = (
              f"- The raise total must be between "
              f"{context_dict['raise_range']['min']} "
              f"and {context_dict['raise_range']['max']}"
          )
      else:
          raise_range_info = "- RAISE is not available in this situation"

      # Prompt
      prompt = f"""You are playing Texas Hold'em poker. Here is the current game state:

  {json.dumps(context_dict, indent=2)}

  You must choose one of the available actions: {', '.join(context_dict['available_actions'])}.

  Rules:
  - If you choose RAISE, you must provide a "total" amount (the total amount to raise to)
  {raise_range_info}
  - For CALL, CHECK, or FOLD, set total=null
  - You have {context_dict['chips']} chips
  - You need to call {context_dict['chips_to_call']} chips
  - The pot is {context_dict['total_pot_size']} chips

  Respond ONLY with a JSON object:
  {{"action": "ACTION_NAME", "total": null}}
  or if raising:
  {{"action": "RAISE", "total": <number>}}

  Choose the best action based on your hand, the board, pot odds, and game situation.
  """

      # Call Gemini
      model_obj = genai.GenerativeModel(model)
      response = model_obj.generate_content(
          prompt,
          generation_config=genai.types.GenerationConfig(
              temperature=temperature,
              response_mime_type="application/json"
          )
      )

      try:
          response_text = response.text
          response_json = json.loads(response_text)
      except Exception as e:
          raise ValueError(f"Could not parse Gemini response as JSON: {e}")

      # Extract fields
      action_str = response_json.get("action", "").upper()
      total = response_json.get("total")

      # Convert to ActionType
      try:
          action = ActionType[action_str]
      except KeyError:
          raise ValueError(
              f"Invalid action '{action_str}' from Gemini. "
              f"Valid actions: {[a.name for a in context.available_actions]}"
          )

      # Validate availability
      if action not in context.available_actions:
          raise ValueError(
              f"Action '{action_str}' is not available. "
              f"Available: {[a.name for a in context.available_actions]}"
          )

      # Validate total if RAISE
      if action == ActionType.RAISE:
          if total is None:
              raise ValueError("RAISE requires a 'total' value")
          if context.raise_range and (
              total < context.raise_range.start or total >= context.raise_range.stop
          ):
              raise ValueError(
                  f"Raise total {total} is out of range. "
                  f"Valid: {context.raise_range.start} to {context.raise_range.stop - 1}"
              )
          return action, total

      return action, None