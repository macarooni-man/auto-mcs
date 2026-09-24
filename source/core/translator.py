from source.core.constants import paths, format_traceback
from source.core import constants
from typing import Any
import unicodedata
import json
import re
import os



# ---------------------------------------------- Global Variables ------------------------------------------------------

# Only loads the active locale into memory, and reloads when changed
loaded_locale: dict[str, Any] = {'code': None, 'data': {}, 'transform': None}


# Locale codes for translation methods below and the UI
available_locales:   dict[str, dict] = {
    "English":    {"name": 'English',    "code": 'en', "transform": 'identity'},
    "Spanish":    {"name": 'Español',    "code": 'es', "transform": 'lower-first'},
    "French":     {"name": 'Français',   "code": 'fr', "transform": 'lower-first'},
    "Italian":    {"name": 'Italiano',   "code": 'it', "transform": 'lower-first'},
    "German":     {"name": 'Deutsch',    "code": 'de', "transform": 'preserve-first'},
    "Dutch":      {"name": 'Nederlands', "code": 'nl', "transform": 'lower-first'},
    "Portuguese": {"name": 'Português',  "code": 'pt', "transform": 'lower-first'},
    "Swedish":    {"name": 'Svenska',    "code": 'sv', "transform": 'lower-first'},
    "Finnish":    {"name": 'Suomi',      "code": 'fi', "transform": 'lower-first'},
    "Latvian":    {"name": 'Latviešu',   "code": 'lv', "transform": 'lower-first'},
    "Turkish":    {"name": 'Türkçe',     "code": 'tr', "transform": 'turkish'},
    "English 2":  {"name": 'English 2',  "code": 'e2', "transform": 'preserve'}
}



# ----------------------------------------------- Utility Methods ------------------------------------------------------

# Log wrapper
def send_log(object_data, message, level=None, *a):
    try: from source.core import logger
    except: return
    return logger.send_log(f'{__name__}.{object_data}', message, level, 'core')


# Return formatted locale string: 'Title (code)'
# 'english' = True, Title should display in English, native if False
def get_locale_string(english=False, *a) -> str:
    for k, v in available_locales.items():
        if constants.app_config.locale == v['code']:
            return f'{k if english else v["name"]} ({v["code"]})'


# Loads active locale data from disk
def load_locale() -> dict[str, str]:
    def _from_disk(name: str) -> dict:
        if name == 'en': return {}
        path = os.path.join(paths.locales, f'{name}.json')

        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_data = json.load(f)
                    if isinstance(raw_data, dict): return raw_data

            except (OSError, json.JSONDecodeError) as e:
                send_log('load_locale', f"failed to load locale '{name}': {format_traceback(e)}", 'error')

        return {}

    locale = constants.app_config.locale
    if loaded_locale['code'] == locale:
        return loaded_locale['data']

    data = _from_disk(locale)
    locale_info = _locale_map.get(locale, _locale_map['en'])

    loaded_locale.update({
        'code': locale,
        'data': data,
        'transform': _transforms[locale_info['transform']]
    })

    return data


# Retrieves a valid translation string from English string
def search_data(data: dict, value: str) -> str | None:
    def _lookup(text):
        return data.get(text.lower()) or data.get(text)

    # Always prefer an exact translation
    translated = _lookup(value)
    if translated:
        return translated

    # Retry while progressively stripping trailing punctuation
    stripped = value.rstrip()
    punctuation = ''
    while stripped and unicodedata.category(stripped[-1]).startswith('P'):
        punctuation = stripped[-1] + punctuation
        stripped = stripped[:-1].rstrip()

        translated = _lookup(stripped)
        if translated:

            # Restore runtime punctuation if the translation doesn't already contain it
            if punctuation and not translated.rstrip().endswith(punctuation):
                translated += punctuation

            return translated

    return None


# Translate any string into relevant locale
def translate(text: str) -> str:
    if not text.strip(): return text

    data = load_locale()
    if loaded_locale['code'].startswith('en'): return text

    before = text[:len(text) - len(text.lstrip())]
    after = text[len(text.rstrip()):]
    text = original_text = text.strip()

    # Extract protected proper nouns
    dollar_pattern = re.compile(r'\$([^$]+)\$')
    conserve = dollar_pattern.findall(text)
    text = dollar_pattern.sub('$$', text)

    # Exact translation first
    new_text = search_data(data, text)

    # Only fall back to word translation if there's one visible word
    if not new_text:
        parts = re.split(r'(\[[^\]]+\])', text)
        visible = ''.join(p for p in parts if not (p.startswith('[') and p.endswith(']'))).replace('$$', '')
        words = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", visible)

        if len(words) == 1:
            word = words[0]
            translated = search_data(data, word)

            if translated:
                for index, part in enumerate(parts):
                    if part.startswith('[') and part.endswith(']'): continue
                    parts[index], count = re.subn(rf'(?<!\w){re.escape(word)}(?!\w)', translated, part, count=1, flags=re.IGNORECASE)
                    if count: break

                new_text = ''.join(parts)

    # No match - return original content
    if not new_text:
        return before + dollar_pattern.sub(r'\1', original_text) + after

    # Transform casing based on locale rules
    new_text = loaded_locale['transform'](text, new_text)

    # Restore protected proper nouns
    for match in conserve:
        new_text = new_text.replace('$$', match, 1)

    new_text = dollar_pattern.sub(r'\1', new_text)
    return before + new_text + after



# ----------------------------------------------- Case Transforms ------------------------------------------------------

class Transform:
    id = 'identity'

    protected = {
        # Product and project names
        'rich presence': 'Rich Presence',
        'craftbukkit':   'CraftBukkit',
        'playit.gg':     'playit.gg',
        'auto-mcs':      'auto-mcs',
        'github':        'GitHub',
        'discord':       'Discord',
        'docker':        'Docker',
        'minecraft':     'Minecraft',
        'modrinth':      'Modrinth',
        'curseforge':    'CurseForge',
        'telepath':      'Telepath',
        'bedrock':       'Bedrock',
        'fabric':        'Fabric',
        'forge':         'Forge',
        'purpur':        'Purpur',
        'spigot':        'Spigot',
        'vanilla':       'Vanilla',
        'java':          'Java',
        'paper':         'Paper',
        'neoforge':      'NeoForge',
        'geyser':        'Geyser',
        'amscript':      'amscript',
        'randomtickspeed': 'randomTickSpeed',

        # Technical acronyms
        'api':           'API',
        'cpu':           'CPU',
        'dns':           'DNS',
        'tb':            'TB',
        'gb':            'GB',
        'mb':            'MB',
        'kb':            'KB',
        'http':          'HTTP',
        'https':         'HTTPS',
        'ide':           'IDE',
        'ip':            'IP',
        'isp':           'ISP',
        'jar':           'JAR',
        'json':          'JSON',
        'jvm':           'JVM',
        'lan':           'LAN',
        'ipv4':          'IPv4',
        'ipv6':          'IPv6',
        'motd':          'MOTD',
        'pvp':           'PVP',
        'ram':           'RAM',
        'tcp':           'TCP',
        'udp':           'UDP',
        'url':           'URL',
        'uuid':          'UUID',
        'vps':           'VPS',
        'yaml':          'YAML'
    }

    markup_re = re.compile(r'(\[[^\]]+\])')
    protected_re = re.compile(
        rf'(?i:(?<!\w)(?:{"|".join(re.escape(value) for value in sorted(protected, key=len, reverse=True))})(?!\w))'
        r'|(?i:\b(?:ctrl|cmd|command|alt|shift|option|win)(?:[+-](?:ctrl|cmd|command|alt|shift|option|win|[a-z0-9]))+\b)'
        r'|\b(?:TAB|SPACE)\b'
        r'|\b[\w.-]+\.(?:jar|json|zip|yml|yaml|ini|ams)\b'
    )

    def __call__(self, source: str, text: str) -> str:
        return self._transform(source, text)

    def _transform(self, source: str, text: str) -> str:
        return text

    def _upper(self, text: str) -> str:
        return text.upper()

    def _lower(self, text: str) -> str:
        return text.lower()

    def _title(self, text: str) -> str:
        return text.title()

    # Return only user-visible text, ignoring Kivy markup
    def _visible(self, text: str) -> str:
        return ''.join(
            part for part in self.markup_re.split(text)
            if not (part.startswith('[') and part.endswith(']'))
        )

    # Determine casing intent from the English source
    def _style(self, source: str) -> str | None:
        text = self._visible(source).replace('$$', '').strip()

        if not text: return None
        if text.isupper(): return 'upper'
        if text.islower(): return 'lower'
        if text == text.title(): return 'title'

        for char in text:
            if char.isalpha():
                return 'sentence' if char.isupper() else None

        return None

    # Apply a transform without changing protected technical values
    def _map_plain(self, text: str, transform, upper_protected=False) -> str:
        output = []
        position = 0

        for match in self.protected_re.finditer(text):
            output.append(transform(text[position:match.start()]))

            value = match.group(0)
            canonical = self.protected.get(value.lower())

            if upper_protected:
                value = (canonical or value).upper()

            elif canonical:
                value = canonical

            output.append(value)
            position = match.end()

        output.append(transform(text[position:]))
        return ''.join(output)

    # Apply a transform to visible text without modifying Kivy markup
    def _map_visible(self, text: str, transform, upper_protected=False) -> str:
        parts = self.markup_re.split(text)

        for index, part in enumerate(parts):
            if part.startswith('[') and part.endswith(']'): continue
            parts[index] = self._map_plain(part, transform, upper_protected)

        return ''.join(parts)

    # Change only the first visible character
    def _first(self, text: str, upper=True) -> str:
        visible = self._visible(text).lstrip()

        placeholder = visible.find('$$')
        first_alpha = next((index for index, char in enumerate(visible) if char.isalpha()), -1)

        # A protected runtime value begins the sentence
        if placeholder >= 0 and (first_alpha < 0 or placeholder < first_alpha):
            return text

        parts = self.markup_re.split(text)

        for part_index, part in enumerate(parts):
            if part.startswith('[') and part.endswith(']'): continue

            protected = list(self.protected_re.finditer(part))

            for index, char in enumerate(part):
                if not char.isalpha(): continue

                # The first word is a protected value, leave its casing alone
                if any(match.start() <= index < match.end() for match in protected):
                    return text

                parts[part_index] = (
                    part[:index]
                    + (self._upper(char) if upper else self._lower(char))
                    + part[index + 1:]
                )

                return ''.join(parts)

        return text


# Reproduce the current English-style casing behavior
class TransformPreserve(Transform):
    id = 'preserve'

    def _transform(self, source: str, text: str) -> str:
        style = self._style(source)

        if style == 'upper':
            return self._map_visible(text, self._upper, True)

        if style == 'lower':
            return self._map_visible(text, self._lower)

        if style == 'title':
            return self._map_visible(text, self._title)

        if style == 'sentence':
            text = self._map_visible(text, lambda x: x)
            return self._first(text, True)

        return self._map_visible(text, lambda x: x)


# Use sentence casing while retaining capitalization of protected values
class TransformLowerFirst(Transform):
    id = 'lower-first'

    def _transform(self, source: str, text: str) -> str:
        style = self._style(source)

        if style == 'upper':
            return self._map_visible(text, self._upper, True)

        if style == 'lower':
            return self._map_visible(text, self._lower)

        if style == 'title':
            text = self._map_visible(text, self._lower)
            return self._first(text, True)

        if style == 'sentence':
            text = self._map_visible(text, lambda x: x)
            return self._first(text, True)

        return self._map_visible(text, lambda x: x)


# Preserve native casing while supporting headings and all-caps
class TransformPreserveFirst(Transform):
    id = 'preserve-first'

    def _transform(self, source: str, text: str) -> str:
        style = self._style(source)

        if style == 'upper':
            return self._map_visible(text, self._upper, True)

        if style == 'lower':
            return self._map_visible(text, self._lower)

        text = self._map_visible(text, lambda x: x)

        if style in ('title', 'sentence'):
            return self._first(text, True)

        return text


# Turkish has locale-specific dotted/dotless 'I' casing
class TransformTurkish(TransformLowerFirst):
    id = 'turkish'

    def _upper(self, text: str) -> str:
        return text.translate(str.maketrans({'i': 'İ', 'ı': 'I'})).upper()

    def _lower(self, text: str) -> str:
        return text.translate(str.maketrans({'I': 'ı', 'İ': 'i'})).lower()



# ------------------------------------------- Dynamic Initialization ---------------------------------------------------

_locale_map = {
    locale['code']: locale for locale in available_locales.values()
}

_transforms = {
    cls.id: cls() for cls in globals().values()
    if isinstance(cls, type) and issubclass(cls, Transform)
}
