import json
from dataclasses import dataclass, asdict, field, fields
from pathlib import Path

from whisper_client.config import LANGUAGE,MODEL,PROMPTS

SETTINGS_PATH:Path =  Path.home() / "Library/Application Support/whisper-client/settings.json"
MAX_PROMPT_CHARS:int = 800

@dataclass
class Settings:
    language: str = LANGUAGE
    model: str = MODEL
    vocabulary: list[str] = field(default_factory=list)

    def prompt(self):
        prompt = PROMPTS[self.language]
        kept = []
        if len(self.vocabulary) > 0 and self.vocabulary is not None:
            for word in  reversed(self.vocabulary):
                if (len(f"{prompt} {', '.join([word] + kept)}.") ) < MAX_PROMPT_CHARS:
                    kept.insert(0,word)
                else:
                    break;
        if len(kept) > 0:
            return f"{prompt} {', '.join(kept)}."
        else :
            return prompt

def load(path=SETTINGS_PATH):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            known = {f.name for f in fields(Settings)}
            return Settings(**{name: value for name,value in data.items() if name in known})
    except (OSError, ValueError):
        return Settings()

def save(settings, path=SETTINGS_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as file:
        settings_str = json.dumps(asdict(settings), ensure_ascii=False)
        file.write(settings_str)
