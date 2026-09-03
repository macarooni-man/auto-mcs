from source.core.constants import paths
from source.core import constants
import json
import re
import os



# Only loads the active locale into memory, and reloads when changed
locale_data:   dict[str, str] = {}
loaded_locale: str | None = None

def load_locale(locale) -> dict[str, str]:
    if locale.startswith('en'): return {}

    path = os.path.join(paths.locales, f'{locale}.json')
    if not os.path.isfile(path): return {}

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as e:
        print(f"[Translator] Failed to load locale '{locale}': {e}")
        return {}

def get_locale_data() -> dict[str, str]:
    global locale_data, loaded_locale
    locale = constants.app_config.locale

    if loaded_locale != locale:
        locale_data = load_locale(locale)
        loaded_locale = locale

    return locale_data


# Locale codes for translation methods below and the UI
available_locales:   dict[str, dict] = {
    "English":    {"name": 'English', "code": 'en'},
    "Spanish":    {"name": 'Español', "code": 'es'},
    "French":     {"name": 'Français', "code": 'fr'},
    "Italian":    {"name": 'Italiano', "code": 'it'},
    "German":     {"name": 'Deutsch', "code": 'de'},
    "Dutch":      {"name": 'Nederlands', "code": 'nl'},
    "Portuguese": {"name": 'Português', "code": 'pt'},
    "Swedish":    {"name": 'Suédois', "code": 'sv'},
    "Finnish":    {"name": 'Suomi', "code": 'fi'},
    "English 2":  {"name": 'English 2', "code": 'e2'}

    # Requires special fonts:

    # "Chinese":  {"name": '中文', "code": 'zh-CN'},
    # "Japanese": {"name": '日本語', "code": 'ja'},
    # "Korean":   {"name": '한국어', "code": 'ko'},
    # "Arabic":   {"name": 'العربية', "code": 'ar'},
    # "Russian":  {"name": 'Русский', "code": 'ru'},
    # "Ukranian": {"name": 'Українська', "code": 'uk'},
    # "Serbian":  {"name": 'Cрпски', "code": 'sr'},
    # "Japanese": {"name": '日本語', "code": 'ja'}
}

# Return formatted locale string: 'Title (code)'
# 'english' = True, Title should display in English, native if False
def get_locale_string(english=False, *a) -> str:
    for k, v in available_locales.items():
        if constants.app_config.locale in v.values():
            return f'{k if english else v["name"]} ({v["code"]})'


# Translate any string into relevant locale
def translate(text: str) -> str:
    if not text.strip() or constants.app_config.locale.startswith('en'): return text

    data = get_locale_data()
    before = text[:len(text) - len(text.lstrip())]
    after = text[len(text.rstrip()):]
    text = original_text = text.strip()

    def search_data(value):
        return data.get(value.lower()) or data.get(value)

    # Extract protected proper nouns
    dollar_pattern = re.compile(r'\$([^$]+)\$')
    conserve = dollar_pattern.findall(text)
    text = dollar_pattern.sub('$$', text)

    # Exact translation first
    new_text = search_data(text)

    # Only fall back to word translation if there's one visible word
    if not new_text:
        parts = re.split(r'(\[[^\]]+\])', text)
        visible = ''.join(p for p in parts if not (p.startswith('[') and p.endswith(']'))).replace('$$', '')
        words = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", visible)

        if len(words) == 1:
            word = words[0]
            translated = search_data(word)

            if translated:
                for index, part in enumerate(parts):
                    if part.startswith('[') and part.endswith(']'): continue
                    parts[index], count = re.subn(rf'(?<!\w){re.escape(word)}(?!\w)', translated, part, count=1, flags=re.IGNORECASE)
                    if count: break

                new_text = ''.join(parts)

    # No match - return original content
    if not new_text:
        return before + dollar_pattern.sub(r'\1', original_text) + after

    # Preserve casing from the original string
    if text == text.title(): new_text = new_text.title()
    elif text.isupper():     new_text = new_text.upper()
    elif text.islower():     new_text = new_text.lower()
    elif text and text[0].isupper():
        new_text = new_text[0].upper() + new_text[1:]

    # Restore protected proper nouns
    for match in conserve:
        new_text = new_text.replace('$$', match, 1)

    new_text = dollar_pattern.sub(r'\1', new_text)
    return before + new_text + after
