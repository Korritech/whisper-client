from whisper_client.config import LANGUAGE, MODEL, PROMPTS
from whisper_client.settings import MAX_PROMPT_CHARS, Settings, load, save


def test_defaults_when_no_file(tmp_path):
    settings = load(tmp_path / "settings.json")

    assert settings.model == MODEL
    assert settings.language == LANGUAGE
    assert settings.vocabulary == []


def test_save_then_load(tmp_path):
    path = tmp_path / "sub" / "settings.json"

    save(Settings(model="tiny.en.pt", language="en", vocabulary=["AWS", "RDS"]), path)
    settings = load(path)

    assert settings.model == "tiny.en.pt"
    assert settings.language == "en"
    assert settings.vocabulary == ["AWS", "RDS"]


def test_corrupted_file_gives_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{ not json")

    assert load(path) == Settings()


def test_unknown_keys_are_ignored(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"model": "tiny.en.pt", "old_option": true}')

    assert load(path) == Settings(model="tiny.en.pt")


def test_each_settings_has_its_own_vocabulary():
    first, second = Settings(), Settings()
    first.vocabulary.append("AWS")

    assert second.vocabulary == []


def test_french_and_english_are_available():
    assert {"fr", "en"} <= set(PROMPTS)


def test_prompt_without_vocabulary_is_the_base_prompt_of_the_language():
    assert Settings(language="fr").prompt() == PROMPTS["fr"]
    assert Settings(language="en").prompt() == PROMPTS["en"]


def test_prompt_contains_the_vocabulary():
    prompt = Settings(language="en", vocabulary=["AWS", "RDS"]).prompt()

    assert prompt.startswith(PROMPTS["en"])
    assert "AWS" in prompt and "RDS" in prompt


def test_prompt_stays_under_the_server_limit_and_keeps_recent_terms():
    terms = [f"terme{i:03d}" for i in range(300)]

    prompt = Settings(vocabulary=terms).prompt()

    assert len(prompt) <= MAX_PROMPT_CHARS
    assert "terme299" in prompt
    assert "terme000" not in prompt
