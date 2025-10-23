from aiogram.fsm.state import State, StatesGroup

class GameStates(StatesGroup):
    associations = State()
    riddles = State()
    story = State()

class HotPicsStates(StatesGroup):
    waiting_for_prompt = State()
    generating_image = State()

class PersonalizationStates(StatesGroup):
    choosing_personality = State()
    choosing_communication_style = State()
    custom_traits = State()
    custom_phrases = State()
    confirmation = State()

class RoleplayStates(StatesGroup):
    choosing_game = State()
    playing_game = State()