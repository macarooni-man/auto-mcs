from concurrent.futures import ThreadPoolExecutor
from glob import glob
import googletrans
import requests
import json
import time
import ast
import sys
import os
import re


# ---------------------- locale-gen ----------------------
#
#    Automates the creation of translations for the UI
#
#    - Changes made to the source will be translated
#          automatically when building a binary
#
# --------------------------------------------------------



# Iterate over every script to find unique strings
all_terms = []
source_dir = os.path.join('..', 'source')
sys.path.append(source_dir)
import constants


for script in glob(os.path.join(source_dir, '*.py')):

    if os.path.basename(script) not in ['menu.py', 'logviewer.py', 'amseditor.py', 'backup.py', 'acl.py', 'constants.py']:
        continue

    # Open script content and loop over the AST matches
    with open(script, 'r', encoding='utf-8', errors='ignore') as py:
        root = ast.parse(py.read())
        last_line = 0
        for node in ast.walk(root):
            if isinstance(node, ast.Str):
                string = node.s

                # Exclusions from translation
                if os.path.basename(script) == 'constants.py' and (node.lineno < 4400 and node.lineno not in range(550,600) and node.lineno not in range(1900,2100)):
                    continue
                if os.path.basename(script) == 'amseditor.py' and node.lineno < 880:
                    continue

                if "-XX:+UseG1GC" in string or "xbox-achievements-enabled: true" in string:
                    continue

                if "namespace eval tabdrag" in string or re.match('^\<.*\>$', string) or re.match('[A-Z][a-z]+\.[A-Z][a-z]+', string):
                    continue

                if '$' not in string:
                    if re.search(r'^(http|\!|\#|\.|\&|\-|\[\^|\[\/|\/|\\|\*|\@)', string) or re.search(r'(\.txt|\.png|\.json|\.ini)$', string):
                        continue
                    if string.count('%') > 2:
                        continue
                    if string in ('macos', 'linux', 'windows', 'user32', 'utf-8', 'uuid'):
                        continue
                    if "_" in string and " " not in string:
                        continue
                    if '[color=' in string or '[/color]' in string or '.*' in string or '- Internal use only' in string:
                        continue
                    if re.search(r'v?\d+(\.?\d+)+\w?', string) and " " not in string:
                        continue
                    spaces = re.findall(r'\s+', string)
                    if spaces:
                        if len(max(spaces, key=len)) > 5:
                            continue

                    # Text overrides
                    if 'Manager: ' in string:
                        string = string.split(':', 1)[0]


                # Global ignores
                if "\ngenerate-structures=true\nspawn-animals=true\nsnooper-enabled=true\n" in string:
                    continue
                if re.match('^\w+Screen$', string):
                    continue
                if not string.strip():
                    continue
                if not re.sub('[^a-zA-Z0-9$]', '', string):
                    continue
                partial_matches = ("'$", "$'", '$$', '$)')
                if string.count('$') < 2 and string.strip() != '$' and string.strip() not in partial_matches:
                    if len(re.sub('[a-zA-Z0-9 ]', '', string)) > len(re.sub('[^a-zA-Z0-9 ]', '', string)):
                        continue

                # Get a unique list of strings
                if string not in all_terms or '$' in string:

                    # Concatenate dollar sign markers for word replacement
                    if '$' in string and node.lineno == last_line and '$' in all_terms[-1]:
                        all_terms[-1] += string
                    else:
                        all_terms.append(string)

                last_line = node.lineno


# Translate English 2
def is_emoji(char):
    """Determine if a character is an emoji based on Unicode ranges."""
    # Define Unicode ranges for emojis
    emoji_ranges = [
        (0x1F600, 0x1F64F),  # Emoticons
        (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
        (0x1F680, 0x1F6FF),  # Transport and Map
        (0x2600, 0x26FF),    # Misc symbols
        (0x2700, 0x27BF),    # Dingbats
        (0xFE00, 0xFE0F),    # Variation Selectors
        (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
        (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
        (0x200D, 0x200D),    # Zero Width Joiner
    ]
    codepoint = ord(char)
    return any(start <= codepoint <= end for start, end in emoji_ranges)
def escape_emojis(text, allow_breaks=True):
    def is_valid_char(char):
        return char.isprintable() and not is_emoji(char)

    # Remove non-printable characters
    sanitized_text = ''.join(c for c in text if is_valid_char(c) or (allow_breaks and c == '\n'))
    return sanitized_text

    # Dirty fix for the meantime to prevent crashing when pasting emojis
    return ''.join(f"{char}" if is_emoji(char) else char for char in text)
token = None
def to_english_2(text: str):
    global token
    if not token:
        token = re.search(
            r'(?<=name\=\"translator_nonce\" value=\")\S+(?=\"\s)',
            requests.get('https://anythingtranslate.com/translators/brain-rot-translator/').text
        )[0]
    def get_content():
        data = {'action': 'do_translation', 'translator_nonce': token, 'post_id': '17141', 'to_translate': text}
        r = requests.post('https://anythingtranslate.com/wp-admin/admin-ajax.php', data=data, timeout=5)
        if r.status_code == 200:
            return escape_emojis(r.json()['data'])
    while True:
        try:
            data = get_content()
            if data:
                return data
        except:
            pass
        time.sleep(1)
        # print('Fail!')

# Translate list of terms
t = googletrans.Translator()
locale_file = os.path.join(source_dir, 'locales.json')
locale_codes = [c['code'] for c in constants.available_locales.values()]

locale_data = {}
if os.path.isfile(locale_file):
    with open(locale_file, 'r') as f:
        locale_data = json.loads(f.read())

for x, string in enumerate(all_terms, 1):

    # Format dollar signs for proper string replacement later
    if string.count('$') == 1:
        string = string.replace('$', '$$')
    if "'$$" in string and "'$$'" not in string:
        string = string.replace("'$$", "'$$'")
    if "$$'" in string and "'$$'" not in string:
        string = string.replace("$$'", "'$$'")

    progress = round((x / len(all_terms)*100), 1)
    try:
        print(f'[ {progress}% ]  Translating "{string}"')
    except UnicodeEncodeError:
        print(f'[ {progress}% ]  Translating <not shown: unicode error>')

    def process_locale(code, *a):
        if code == 'en':
            return

        key = string.lower().strip()

        # Remove content between dollar signs for the key
        if '$' in key:
            key = re.sub(r'\$[^$]*\$', '$$', key)
        
        if key not in locale_data:
            locale_data[key] = {}

        if code not in locale_data[key]:

            # Override strings
            if key == 'okay':
                translate = 'understood'
            else:
                translate = string

            if code == 'e2':
                text = to_english_2(translate)
            else:
                text = t.translate(translate, src='en', dest=code).text
            locale_data[key][code] = text

    with ThreadPoolExecutor(max_workers=20) as pool:
        pool.map(process_locale, locale_codes)

with open(locale_file, "w") as f:
    f.write(json.dumps(locale_data))
