from pydantic import BaseModel, Field


class GameState(BaseModel):
    session_id: str
    game_language_code: str = Field(
        description="Language code in which the game is being played (e.g., 'de' for German)"
    )
    situation_name: str = Field(description="Name of the situation")
    situation_description: str = Field(description="Detailed description of the situation")
    time_of_day: str = Field(description="Current time of day in the scene")
    location_name: str = Field(description="Current location of the player in the scene")
    location_description: str = Field(description="Brief description of the current location")
    world_facts: list[str] = Field(
        default_factory=list,
        description="List of facts about the world that the NPC and Player might know or not know",
    )
    active_npcs: list[str] = Field(
        default_factory=list, description="List of active NPCs in the scene by their npc_id"
    )


class NPCState(BaseModel):
    npc_id: str
    name: str = Field(description="Name of the NPC")
    personality: str = Field(description="Brief description of the NPC's personality")
    mood: str = Field("neutral", description="Current mood of the NPC (e.g., happy, sad, angry)")
    knows_about_player: list[str] = Field(
        default_factory=list,
        description="List of things the NPC knows about the player. One fact per item.",
    )
    goals: list[str] = Field(
        default_factory=list, description="List of the NPC's current goals in the scene"
    )


class PlayerState(BaseModel):
    name: str = Field(description="Name of the player character")
    description: str = Field(description="Brief description of the player character")
    inventory: list[str] = Field(
        default_factory=list, description="List of items the player is currently carrying"
    )


class NarratorResponse(BaseModel):
    narrator_action: str = Field(
        description="The narrator's action or event in response to the player's last action and game history"
    )


#     npcs_to_react: list[str] = Field(
#         default_factory=list,
#         description="""
# List of npc_id that should react to the player's last action based on the narrator's description.
# If player action is expected and NPCs should wait for it, this list will be empty,
# but the narrator_text will include instructions for the player that some action is expected.
# """,
#     )
# game_state_updates: dict[str, Any] = Field(
#     default_factory=dict,
#     description="Dictionary of updates to the game state based on the narrator's description"
#     " (e.g., {'world_facts': {'it_is_raining': True}})",
# )
# location_changed_de: str | None = Field(
#     None,
#     description="If the narrator's description indicates a location change,"
#     " this field should contain the new location name in German. Otherwise, it should be None.",
# )


class NPCResponse(BaseModel):
    npc_id: str
    action_or_speech: str = Field(
        description="The NPC's action or speech in response to the player's last message"
    )
    mood_update: str | None = Field(
        None,
        description="If the NPC's response indicates a mood change, this field should contain the new mood"
        " (e.g., happy, sad, angry). Otherwise, it should be None.",
    )
    learns_about_player: list[str] = Field(
        default_factory=list,
        description="List of new things the NPC learns about the player based on the player's last message"
        " (e.g., ['player_is_a_teacher', 'player_likes_coffee'])",
    )
