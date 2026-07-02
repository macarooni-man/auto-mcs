from source.core.constants import paths
from source.core import constants
import json
import sys
import re
import os

_current_locale: str | None = None
_current_data: dict[str, str] = {}

def _load_locale(locale: str) -> dict[str, str]:
    if locale.startswith('en'):
        return {}
    file_path = os.path.join(paths.locales_dir, f"{locale}.json")
    if os.path.isfile(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[Translator Error] Failed to decode JSON for '{locale}': {e}", file=sys.stderr)
        except Exception as e:
            print(f"[Translator Error] Failed to load locale '{locale}': {e}", file=sys.stderr)
    return {}

def get_locale_data() -> dict[str, str]:
    global _current_locale, _current_data
    locale = constants.app_config.locale
    if _current_locale != locale:
        _current_data = _load_locale(locale)
        _current_locale = locale
    return _current_data

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
}

_valid_codes = {'en'}
if os.path.isdir(paths.locales_dir):
    for _f in os.listdir(paths.locales_dir):
        if _f.endswith('.json'):
            _valid_codes.add(_f[:-5])

available_locales = {k: v for k, v in available_locales.items() if v['code'] in _valid_codes}

def get_locale_string(english=False, *a) -> str:
    for k, v in available_locales.items():
        if constants.app_config.locale in v.values():
            return f'{k if english else v["name"]} ({v["code"]})'

def translate(text: str) -> str:
    if not text.strip() or constants.app_config.locale.startswith('en'):
        return text

    lang_data = get_locale_data()

    def search_data(s, *a):
        stripped = s.strip()
        lower_val = lang_data.get(stripped.lower())
        if lower_val is not None:
            return lower_val
        return lang_data.get(stripped)

    conserve = []
    if text.count('$') >= 2:
        dollar_pattern = re.compile(r'\$([^\$]+)\$')
        conserve = [i for i in re.findall(dollar_pattern, text)]
        text = re.sub(dollar_pattern, '$$', text)

    new_text = search_data(text)

    if new_text:
        stripped_text = text.strip()
        if stripped_text:
            if stripped_text == stripped_text.upper():
                new_text = new_text.upper()
            elif stripped_text == stripped_text.title():
                new_text = new_text.title()
            elif stripped_text == stripped_text.lower():
                new_text = new_text.lower()
            elif stripped_text == stripped_text[0].upper() + stripped_text[1:].lower():
                if len(new_text) > 0:
                    new_text = new_text[0].upper() + new_text[1:].lower()

        if text.startswith(' ') or text.endswith(' '):
            before = ''
            after = ''
            match_before = re.search(r'(^\s+)', text)
            if match_before: before = match_before.group(1)
            
            match_after = re.search(r'(\s+$)', text)
            if match_after: after = match_after.group(1)
            
            new_text = f'{before}{new_text}{after}'

        for match in conserve:
            new_text = new_text.replace('$$', match, 1)

        new_text = re.sub(r'\$([^\$]+)\$', r'\g<1>', new_text)

        return new_text

    else: 
        if constants.app_config.locale != 'en' and not constants.app_config.locale.startswith('en'):
            stripped = text.strip()
            if stripped and not stripped.isnumeric() and len(stripped) > 1:
                lower_key = stripped.lower()
                if lower_key not in lang_data and stripped not in lang_data:
                    lang_data[lower_key] = stripped
                    file_path = os.path.join(paths.locales_dir, f"{constants.app_config.locale}.json")
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(lang_data, f, ensure_ascii=False, indent=4)
                    except Exception as e:
                        print(f"[Translator Error] Failed to auto-save missing string: {e}", file=sys.stderr)

        return re.sub(r'\$(.*)\$', r'\g<1>', text)
