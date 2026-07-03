import os
import sys
import ast
import json
import re
from pathlib import Path

def main():
    print("Starting locale synchronization...")
    all_terms = []
    
    # Path setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.abspath(os.path.join(current_dir, '..', 'source'))
    locales_dir = os.path.abspath(os.path.join(current_dir, '..', 'locales'))
    
    skip_basenames = {
        'desktop.py', 'logviewer.py', 'amseditor.py',
        'backup.py', 'acl.py', 'constants.py', 'init.py',
        'launcher.py', 'addons.py', 'amscript.py', 'foundry.py',
        'java.py', 'playit.py', 'audio.py', 'logger.py'
    }
    skip_dirs = {'.git', '__pycache__', '.venv', 'venv', 'env', 'build', 'dist', 'headless'}
    
    # Gather files
    root = Path(source_dir)
    py_files = []
    for p in root.rglob('*.py'):
        if any(part in skip_dirs for part in p.parts): continue
        if p.name in skip_basenames: continue
        py_files.append(str(p.resolve()))

    py_files = sorted(set(py_files))
    
    # Extract terms
    for script in py_files:
        try:
            with open(script, 'r', encoding='utf-8', errors='ignore') as py:
                content = py.read()
                tree = ast.parse(content)
        except Exception as e:
            print(f"Error parsing {script}: {e}")
            continue

        last_line = 0
        for node in ast.walk(tree):
            string = None
            if hasattr(ast, 'Constant') and isinstance(node, ast.Constant) and isinstance(node.value, str):
                string = node.value
            elif hasattr(ast, 'Str') and isinstance(node, getattr(ast, 'Str')):
                string = getattr(node, 's', None)
                
            if string is None:
                continue

            lineno = getattr(node, 'lineno', 0)
            
            basename = os.path.basename(script)
            if basename == 'constants.py' and (lineno < 4400 and lineno not in range(550,600) and lineno not in range(1900,2100)):
                continue
            if basename == 'amseditor.py' and lineno < 880:
                continue

            if "-XX:+UseG1GC" in string or "xbox-achievements-enabled: true" in string:
                continue

            if "namespace eval tabdrag" in string or re.match(r'^\<.*\>$', string) or re.match(r'[A-Z][a-z]+\.[A-Z][a-z]+', string):
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
            if re.match(r'^\w+Screen$', string):
                continue
            if not string.strip():
                continue
            if not re.sub(r'[^a-zA-Z0-9$]', '', string):
                continue
                
            partial_matches = ("'$", "$'", '$$', '$)')
            if string.count('$') < 2 and string.strip() != '$' and string.strip() not in partial_matches:
                if len(re.sub(r'[a-zA-Z0-9 ]', '', string)) > len(re.sub(r'[^a-zA-Z0-9 ]', '', string)):
                    continue

            # Get a unique list of strings
            if string not in all_terms or '$' in string:
                # Concatenate dollar sign markers for word replacement
                if '$' in string and lineno == last_line and all_terms and '$' in all_terms[-1]:
                    all_terms[-1] += string
                else:
                    all_terms.append(string)

            last_line = lineno

    # Load en.json
    en_json_path = os.path.join(locales_dir, 'en.json')
    en_data = {}
    if os.path.isfile(en_json_path):
        with open(en_json_path, 'r', encoding='utf-8') as f:
            try:
                en_data = json.load(f)
            except Exception as e:
                print(f"Error loading en.json: {e}")

    # Process extracted terms and add to en_data
    added_to_en = 0
    for string in all_terms:
        # Format dollar signs exactly like the original
        if string.count('$') == 1:
            string = string.replace('$', '$$')
        if "'$$" in string and "'$$'" not in string:
            string = string.replace("'$$", "'$$'")
        if "$$'" in string and "'$$'" not in string:
            string = string.replace("$$'", "'$$'")

        key = string.lower().strip()
        if '$' in key:
            key = re.sub(r'\$[^$]*\$', '$$', key)

        if key not in en_data:
            # Overrides
            if key == 'okay':
                translate_val = 'understood'
            else:
                translate_val = string
            en_data[key] = translate_val
            added_to_en += 1

    # Save en.json back
    with open(en_json_path, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=4, sort_keys=True)
    
    print(f"Added {added_to_en} new string(s) to en.json.")

    # Synchronize with all other locales
    sync_count = 0
    locale_files = [f for f in os.listdir(locales_dir) if f.endswith('.json') and f != 'en.json']
    
    for filename in locale_files:
        file_path = os.path.join(locales_dir, filename)
        lang_data = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                lang_data = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load {filename}: {e}")
                continue
                
        added_to_lang = 0
        for key, english_value in en_data.items():
            if key not in lang_data:
                # Add english fallback
                lang_data[key] = english_value
                added_to_lang += 1
                sync_count += 1
                
        if added_to_lang > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(lang_data, f, ensure_ascii=False, indent=4, sort_keys=True)
            print(f"Synchronized {added_to_lang} missing string(s) to {filename}")

    if sync_count == 0:
        print("All language files are already synchronized.")
    else:
        print(f"Finished synchronizing {sync_count} total strings across other locales.")

if __name__ == '__main__':
    main()
