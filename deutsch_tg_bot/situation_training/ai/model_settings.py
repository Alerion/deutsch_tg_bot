from pydantic_ai.models.google import GoogleModelSettings

google_model_settings = GoogleModelSettings(
    temperature=0.8,
    # google_thinking_config={'thinking_level': 'low'},
    # google_safety_settings=[
    #     {
    #         'category': HarmCategory.HARM_CATEGORY_UNSPECIFIED,
    #         'threshold': HarmBlockThreshold.OFF,
    #     },
    #     {
    #         'category': HarmCategory.HARM_CATEGORY_HARASSMENT,
    #         'threshold': HarmBlockThreshold.OFF,
    #     },
    #     {
    #         'category': HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
    #         'threshold': HarmBlockThreshold.OFF,
    #     },
    #     {
    #         'category': HarmCategory.HARM_CATEGORY_HATE_SPEECH,
    #         'threshold': HarmBlockThreshold.OFF,
    #     },
    # ]
)
