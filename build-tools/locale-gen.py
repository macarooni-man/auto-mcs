from concurrent.futures import ThreadPoolExecutor
from glob import glob
import googletrans
import json
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
                if os.path.basename(script) == 'constants.py' and (node.lineno < 4400 and node.lineno not in range(550,600)):
                    continue
                if os.path.basename(script) == 'amseditor.py' and node.lineno < 880:
                    continue

                if "namespace eval tabdrag" in string or re.match('^\<.*\>$', string) or re.match('[A-Z][a-z]+\.[A-Z][a-z]+', string):
                    continue

                if '$' not in string:
                    if re.search(r'^(http|\!|\#|\.|\&|\-|\[\^|\[\/|\/|\\|\*|\@)', string) or re.search(r'(?=.*)(\.txt|\.png|\.json|\.ini$)', string):
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
                if re.match('^\w+Screen$', string):
                    continue
                if not string.strip():
                    continue
                if not re.sub('[^a-zA-Z0-9$]', '', string):
                    continue
                if string.count('$') < 2 and string.strip() != '$':
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

    print(f'[ {round((x / len(all_terms)*100), 1)}% ]  Translating "{string}"')
    def process_locale(code, *a):
        if code == 'en':
            return

        key = string.lower().strip()
        if key not in locale_data:
            locale_data[key] = {}

        if code not in locale_data[key]:

            # Override strings
            if key == 'okay':
                translate = 'understood'
            else:
                translate = string

            locale_data[key][code] = t.translate(translate, src='en', dest=code).text

    with ThreadPoolExecutor(max_workers=20) as pool:
        pool.map(process_locale, locale_codes)
        
with open(locale_file, "w") as f:
    f.write(json.dumps(locale_data))
