import json
import os
from pydantic import BaseModel, Field

CONFIG_FILE = "data/settings.json"

class PromptDef(BaseModel):
    id: str
    name: str
    text: str

class SettingsModel(BaseModel):
    model: str = "gemini-1.5-pro-latest"
    input_cost_per_m: float = 1.25
    output_cost_per_m: float = 5.0
    prompts: list[PromptDef] = Field(default_factory=lambda: [
        PromptDef(id="default", name="Default", text="Analyze the visual and narrative content of this video deeply.")
    ])
    active_prompt_id: str = "default"
    keep_downloaded_videos: bool = False

def load_settings() -> SettingsModel:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return SettingsModel(**data)
        except Exception:
            pass
    return SettingsModel()

def save_settings(settings: SettingsModel):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings.model_dump(), f)
