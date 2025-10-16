from source.core.constants import paths
from source.core import constants
import json
import re
import os



# Loads all translation data from disk into memory
locale_data:   dict[str, dict] = {}
if os.path.isfile(paths.locales):
    with open(paths.locales, 'r', encoding='utf-8', errors='ignore') as f:
        locale_data = json.load(f)

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
    global locale_data

    # Ignore if text is blank, or locale is set to english
    if not text.strip() or constants.app_config.locale.startswith('en'):
        return text


    # Searches locale_data for string
    def search_data(s, *a):
        try: return locale_data[s.strip().lower()][constants.app_config.locale]
        except KeyError: pass
        try: return locale_data[s.strip()][constants.app_config.locale]
        except KeyError: pass


    # Extract proper noun if present with flag
    conserve = []
    if text.count('$') >= 2:
        dollar_pattern = re.compile(r'\$([^\$]+)\$')
        conserve = [i for i in re.findall(dollar_pattern, text)]
        text = re.sub(dollar_pattern, '$$', text)


    # First, attempt to get translation through locale_data directly
    new_text = search_data(text, False)

    # Second, attempt to translate matched words with regex
    if not new_text:
        def match_data(s, *a):
            try: return locale_data[s.group(0).strip().lower()][constants.app_config.locale]
            except KeyError: pass
            return s.group(0)
        new_text = re.sub(r'\b\S+\b', match_data, text)


    # If a match was found, return text in its original case
    if new_text:

        # Escape proper nouns that ignore translation
        overrides = ('server.properties', 'server.jar', 'amscript', 'Geyser', 'Java', 'GB', '.zip', 'Telepath', 'telepath', 'ngrok', 'playit')
        for o in overrides:
            new_key = search_data(o)
            if not new_key:
                continue

            if new_key in new_text:
                new_text = new_text.replace(new_key, o)
            elif new_key.upper() in new_text:
                new_text = new_text.replace(new_key.upper(), o.upper())
            elif new_key.lower() in new_text:
                new_text = new_text.replace(new_key.lower(), o.lower())


        # Manual overrides
        if constants.app_config.locale == 'es':
            new_text = re.sub(r'servidor\.properties', 'server.properties', new_text, flags=re.IGNORECASE)
            new_text = re.sub(r'servidor\.jar', 'server.jar', new_text, flags=re.IGNORECASE)
            new_text = re.sub(r'control S', 'Administrar', new_text, flags=re.IGNORECASE)
        if constants.app_config.locale == 'it':
            new_text = re.sub(r'ESENTATO', 'ESCI', new_text, flags=re.IGNORECASE)
        if constants.app_config.locale == 'fr':
            new_text = re.sub(r'moire \(Go\)', 'moire (GB)', new_text, flags=re.IGNORECASE)
            new_text = re.sub(r'dos', 'retour', new_text, flags=re.IGNORECASE)


        # Get the spacing in front and after the text
        if text.startswith(' ') or text.endswith(' '):
            try:    before = re.search(r'(^\s+)', text).group(1)
            except: before = ''
            try:    after = re.search(r'(?=.*)(\s+$)', text).group(1)
            except: after = ''
            new_text = f'{before}{new_text}{after}'


        # Keep case from original text
        if text == text.title(): new_text = new_text.title()
        elif text == text.upper():
            new_text = new_text.upper()
        elif text == text.lower():
            new_text = new_text.lower()
        elif text.strip() == text[0].strip().upper() + text[1:].strip().lower():
            new_text = new_text[0].upper() + new_text[1:].lower()


        # Replace proper noun (rework this to iterate over each match, in case there are multiple
        for match in conserve:
            new_text = new_text.replace('$$', match, 1)

        # Remove dollar signs if they are still present for some reason
        new_text = re.sub(r'\$([^\$]+)\$', r'\g<1>', new_text)

        return new_text

    # If not, return original text
    else: return re.sub(r'\$(.*)\$', r'\g<1>', text)
