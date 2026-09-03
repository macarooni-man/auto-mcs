from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
import html
import json
import time
import ast
import os
import re


# ---------------------- locale-gen ----------------------
#
#    Discovers and generates translations for the UI
#
# --------------------------------------------------------


root_dir = Path(__file__).resolve().parents[1]
source_dir = root_dir / 'source'
ui_dir = source_dir / 'ui'
desktop_dir = ui_dir / 'desktop'
locale_dir = root_dir / 'locales'

locale_codes = ('de', 'e2', 'en', 'es', 'fi', 'fr', 'it', 'nl', 'pt', 'sv')
deepl_targets = {'de': 'DE', 'es': 'ES', 'fi': 'FI', 'fr': 'FR', 'it': 'IT', 'nl': 'NL', 'pt': 'PT-PT', 'sv': 'SV'}
deepl_api_key = os.getenv('DEEPL_AUTH_KEY', '')
deepl_context = 'auto-mcs is a cross-platform graphical application for managing Minecraft servers. Preserve product names such as auto-mcs, Minecraft, Java, Modrinth, Telepath, and playit.gg. Preserve commands, file paths, keyboard shortcuts, and placeholders exactly.'
deepl_max_bytes = 120 * 1024

# Function: (positional args, keyword args)
scan_calls = {
    'HeaderText':         ((0, 1), ('display_text', 'more_text')),
    'MainButton':         ((0,), ('name',)),
    'ColorButton':        ((0,), ('name',)),
    'WaitButton':         ((0,), ('name',)),
    'NextButton':         ((0,), ('name',)),
    'ExitButton':         ((0,), ('name',)),
    'InputButton':        ((0,), ('name', 'title')),
    'IconButton':         ((0,), ('name',)),
    'RelativeIconButton': ((0,), ('name',)),
    'AnimButton':         ((0,), ('name',)),
    'BigModeButton':      ((0, 4), ('name', 'icon_name')),
    'BigIconButton':      ((0,), ('name',)),
    'ParagraphObject':    ((1,), ('name',)),
    'DropButton':         ((0, 2), ('name', 'options_list')),
    'BannerObject':       ((), ('text',)),
    'show_popup':         ((1, 2), ('title', 'content')),
    'show_banner':        ((1,), ('text',)),
    'generate_title':     ((0,), ('title',)),
    'generate_list':      ((1, 5), ('blank_text', 'empty_text')),
    'file_popup':         ((5,), ('title',)),
    'update_text':        ((0,), ('text',)),
    'change_text':        ((0,), ('text',))
}

scan_attrs = {'text', 'hint_text', 'title_text'}
page_keys = {'title', 'header', 'default_error'}
ignored_values = {'splash'}
ignored_suffixes = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.json', '.ini', '.yaml', '.yml', '.txt', '.log', '.ttf', '.otf', '.wav', '.mp3')
dynamic_marker = '\x00'

# Protect auto-mcs placeholders/formatting from DeepL
placeholder_re = re.compile(
    r'\$\$|\$[^$\n]+\$|%\([^)]+\)[#0 +\-]*\d*(?:\.\d+)?[a-zA-Z]|'
    r'%[#0 +\-]*\d*(?:\.\d+)?[a-zA-Z]|\{\{[^{}]+\}\}|\{[^{}]+\}|'
    r'(?i:\b(?:ctrl|alt|shift|cmd|command|option|win)(?:[+-](?:ctrl|alt|shift|cmd|command|option|win|[a-z0-9]))+\b)|'
    r'\[/?[a-zA-Z][^\]]*\]'
)
protected_tag_re = re.compile(r'<x\s+id="(\d+)"\s*/\s*>|<x\s+id="(\d+)"\s*>\s*</x\s*>', re.IGNORECASE)


def node_name(node):
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute): return node.attr
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value == 'translate': return 'translate'
    return ''

def expr_name(node):
    try: return ast.unparse(node)
    except: return ''

def dict_key(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None

def call_parts(node):
    name, args = node_name(node.func), node.args
    if name == 'partial' and args: name, args = node_name(args[0]), args[1:]
    return name, args, node.keywords

def normalize(text):
    text = text.strip()
    if not text or not re.search(r'[A-Za-z]', text): return None
    if text.lower() in ignored_values: return None
    if text.startswith(('http://', 'https://')): return None
    if text.lower().endswith(ignored_suffixes): return None
    if re.fullmatch(r'\w+Screen', text): return None

    if text.count('$') == 1: text = text.replace('$', '$$')
    if "'$$" in text and "'$$'" not in text: text = text.replace("'$$", "'$$'")
    if "$$'" in text and "'$$'" not in text: text = text.replace("$$'", "'$$'")
    return text

def sanitize_markers(text):
    count = text.count('$')
    if count >= 2 and count % 2 == 0: text = re.sub(r'\$[^$]*\$', '$$', text)
    return text


class LocaleVisitor(ast.NodeVisitor):

    def __init__(self, path, desktop_file=False):
        self.path = path
        self.desktop_file = desktop_file
        self.scopes = [{}]
        self.disabled = [set()]
        self.terms = {}

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope: return scope[name]
        return set()

    def bind(self, target, values):
        if isinstance(target, ast.Name) and values: self.scopes[-1].setdefault(target.id, set()).update(values)

    def is_disabled(self, name):
        return any(name in disabled for disabled in reversed(self.disabled))

    def resolve(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str): return {node.value}
        if isinstance(node, ast.Name): return self.lookup(node.id)

        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            values = set()
            for item in node.elts: values.update(self.resolve(item))
            return values

        if isinstance(node, ast.Dict):
            values = set()
            for key in node.keys:
                if key is not None: values.update(self.resolve(key))
            return values

        if isinstance(node, ast.IfExp): return self.resolve(node.body) | self.resolve(node.orelse)

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = self.resolve(node.left), self.resolve(node.right)
            if left and right and len(left) * len(right) <= 64: return {a + b for a in left for b in right}
            return set()

        if isinstance(node, ast.JoinedStr):
            values = {''}
            for part in node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str): pieces = {part.value}
                elif isinstance(part, ast.FormattedValue): pieces = self.resolve(part.value) or {dynamic_marker}
                else: return set()
                if len(values) * len(pieces) > 64: return set()
                values = {a + str(b) for a in values for b in pieces}

            output = set()
            for text in values:
                text = text.replace(f'${dynamic_marker}$', '$$')
                if dynamic_marker not in text: output.add(text)
            return output

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            values, method = self.resolve(node.func.value), node.func.attr
            if values and method in ('strip', 'lower', 'upper', 'title', 'capitalize') and not node.args:
                return {getattr(value, method)() for value in values}

        return set()

    def add(self, node, source):
        for text in self.resolve(node):
            text = normalize(text)
            if not text: continue
            key = text.lower().strip()
            if '$' in key: key = re.sub(r'\$[^$]*\$', '$$', key)

            self.terms.setdefault(key, {'text': text, 'locations': []})
            self.terms[key]['locations'].append((self.path, getattr(node, 'lineno', 0), source))

    def add_named(self, node, key_name, source):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if dict_key(key) == key_name: self.add(value, source)
                self.add_named(value, key_name, source)
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for value in node.elts: self.add_named(value, key_name, source)

    def add_first(self, node, source):
        if not isinstance(node, (ast.List, ast.Tuple, ast.Set)): return
        for item in node.elts:
            if isinstance(item, (ast.List, ast.Tuple)) and item.elts: self.add(item.elts[0], source)

    def add_steps(self, node):
        if not isinstance(node, (ast.List, ast.Tuple, ast.Set)): return
        for item in node.elts:
            if isinstance(item, (ast.List, ast.Tuple)) and item.elts: self.add(item.elts[0], 'function_list')

    def add_page_contents(self, node):
        if not isinstance(node, ast.Dict): return
        for key, value in zip(node.keys, node.values):
            key = dict_key(key)
            if key in page_keys: self.add(value, f"page_contents['{key}']")
            elif key == 'function_list': self.add_steps(value)

    def add_footer(self, node):
        for text in self.resolve(node):
            for item in text.split(', '):
                value = ast.Constant(value=item)
                value.lineno = getattr(node, 'lineno', 0)
                self.add(value, 'generate_footer')

    def add_banner_text(self, node):
        if isinstance(node, ast.Dict):
            data = {dict_key(k): v for k, v in zip(node.keys, node.values) if dict_key(k)}
            disabled = data.get('__translate__')

            if 'text' in data and not (isinstance(disabled, ast.Constant) and disabled.value is False):
                self.add(data['text'], 'banner.text')

        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for value in node.elts: self.add_banner_text(value)

    @staticmethod
    def translation_disabled(node):
        return any(kw.arg == '__translate__' and isinstance(kw.value, ast.Constant) and kw.value.value is False for kw in node.keywords)

    @staticmethod
    def header_enabled(node, index):
        for kw in node.keywords:
            if kw.arg != '__translate__' or not isinstance(kw.value, (ast.Tuple, ast.List)): continue
            if index < len(kw.value.elts):
                flag = kw.value.elts[index]
                if isinstance(flag, ast.Constant) and flag.value is False: return False
        return True

    def visit_Dict(self, node):
        if self.desktop_file: self.add_named(node, 'status_text', 'status_text')
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.scopes.append({})
        self.disabled.append(set())
        for child in node.body: self.visit(child)
        self.disabled.pop()
        self.scopes.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_For(self, node):
        self.bind(node.target, self.resolve(node.iter))
        self.visit(node.iter)
        for child in node.body + node.orelse: self.visit(child)

    visit_AsyncFor = visit_For

    def process_target(self, target, value, values):
        self.bind(target, values)

        if isinstance(target, ast.Attribute) and target.attr == '__translate__':
            name = expr_name(target.value)
            if isinstance(value, ast.Constant):
                if value.value is False: self.disabled[-1].add(name)
                elif value.value is True: self.disabled[-1].discard(name)
            return

        if not self.desktop_file: return

        if isinstance(target, ast.Attribute) and target.attr in scan_attrs and not self.is_disabled(expr_name(target.value)):
            self.add(value, f'.{target.attr}')

        name = target.id if isinstance(target, ast.Name) else target.attr if isinstance(target, ast.Attribute) else ''
        if name == 'page_contents': self.add_page_contents(value)
        elif name == 'function_list': self.add_steps(value)
        elif name == 'context_options': self.add_named(value, 'name', 'context_options')
        elif name == 'actions': self.add_first(value, 'actions')
        elif name == 'banners': self.add_banner_text(value)

        if isinstance(target, ast.Subscript) and expr_name(target.value).endswith('page_contents'):
            key = dict_key(target.slice)
            if key in page_keys: self.add(value, f"page_contents['{key}']")
            elif key == 'function_list': self.add_steps(value)

    def visit_Assign(self, node):
        values = self.resolve(node.value)
        for target in node.targets: self.process_target(target, node.value, values)
        self.visit(node.value)

    def visit_AnnAssign(self, node):
        if node.value is None: return
        self.process_target(node.target, node.value, self.resolve(node.value))
        self.visit(node.value)

    def visit_Call(self, node):
        name, args, keywords = call_parts(node)

        if name == 'translate':
            if args: self.add(args[0], 'translate')
            else:
                for kw in keywords:
                    if kw.arg == 'text': self.add(kw.value, 'translate')

        if self.desktop_file:
            if name == 'generate_footer' and args: self.add_footer(args[0])

            if name == 'show_context_menu':
                if len(args) > 1: self.add_named(args[1], 'name', 'show_context_menu')
                for kw in keywords:
                    if kw.arg in ('options', 'options_list'): self.add_named(kw.value, 'name', 'show_context_menu')

            if name in scan_calls and not self.translation_disabled(node):
                positions, names = scan_calls[name]
                for index in positions:
                    if index < len(args) and (name != 'HeaderText' or self.header_enabled(node, index)): self.add(args[index], name)
                for kw in keywords:
                    if kw.arg in names: self.add(kw.value, name)

            if not self.translation_disabled(node):
                for kw in keywords:
                    if kw.arg in scan_attrs: self.add(kw.value, f'{name}.{kw.arg}')

        self.generic_visit(node)


def generate_locale_files():
    locale_dir.mkdir(exist_ok=True)
    created = []

    for code in locale_codes:
        path = locale_dir / f'{code}.json'
        if path.exists(): continue
        path.write_text('{}\n', encoding='utf-8')
        created.append(path.name)

    return created


def scan():
    terms = {}
    source_count = ui_count = 0

    for path in sorted(source_dir.rglob('*.py')):
        if '__pycache__' in path.parts: continue
        source_count += 1
        if path.is_relative_to(ui_dir): ui_count += 1

        try: tree = ast.parse(path.read_text(encoding='utf-8', errors='ignore'))
        except (OSError, SyntaxError) as e:
            print(f'[!] {path.relative_to(root_dir)}: {e}')
            continue

        visitor = LocaleVisitor(path.relative_to(root_dir), path.is_relative_to(desktop_dir))
        visitor.visit(tree)

        for key, data in visitor.terms.items():
            terms.setdefault(key, {'text': data['text'], 'locations': []})
            terms[key]['locations'].extend(data['locations'])

    return terms, source_count, ui_count


# Translate English 2
def is_emoji(char):
    emoji_ranges = [
        (0x1F600, 0x1F64F), (0x1F300, 0x1F5FF), (0x1F680, 0x1F6FF),
        (0x2600, 0x26FF), (0x2700, 0x27BF), (0xFE00, 0xFE0F),
        (0x1F900, 0x1F9FF), (0x1FA70, 0x1FAFF), (0x200D, 0x200D)
    ]
    codepoint = ord(char)
    return any(start <= codepoint <= end for start, end in emoji_ranges)

def escape_emojis(text, allow_breaks=True):
    def is_valid_char(char): return char.isprintable() and not is_emoji(char)
    return ''.join(c for c in text if is_valid_char(c) or (allow_breaks and c == '\n'))

token = None
def to_english_2(text: str):
    global token
    if not token:
        token = re.search(
            r'(?<=name=\"translator_nonce\" value=\")\S+(?=\"\s)',
            requests.get('https://anythingtranslate.com/translators/brain-rot-translator/').text
        )[0]

    def get_content():
        data = {'action': 'do_translation', 'translator_nonce': token, 'post_id': '17141', 'to_translate': text}
        r = requests.post('https://anythingtranslate.com/wp-admin/admin-ajax.php', data=data, timeout=5)
        if r.status_code == 200: return escape_emojis(r.json()['data'])

    while True:
        try:
            data = get_content()
            if data: return data
        except: pass
        time.sleep(1)


# DeepL translation
def shield_placeholders(text):
    tokens = []
    parts = []
    position = 0

    for match in placeholder_re.finditer(text):
        parts.append(html.escape(text[position:match.start()], quote=False))
        tokens.append(match.group(0))
        parts.append(f'<x id="{len(tokens) - 1}"/>')
        position = match.end()

    parts.append(html.escape(text[position:], quote=False))
    return ''.join(parts), tokens

def restore_placeholders(text, tokens):
    identifiers = []

    def replace(match):
        identifier = int(match.group(1) or match.group(2))
        if identifier >= len(tokens): raise RuntimeError('DeepL returned an unknown protected placeholder')
        identifiers.append(identifier)
        return tokens[identifier]

    restored = protected_tag_re.sub(replace, text)
    if sorted(identifiers) != list(range(len(tokens))): raise RuntimeError('DeepL changed, removed, or duplicated a protected placeholder')
    return html.unescape(restored)

def deepl_payload(texts, target):
    return {
        'text': texts,
        'source_lang': 'EN',
        'target_lang': target,
        'context': deepl_context,
        'model_type': 'prefer_quality_optimized',
        'tag_handling': 'xml',
        'ignore_tags': ['x'],
        'split_sentences': 'nonewlines'
    }

def deepl_batches(texts, target):
    batches = []
    current = []

    def size(values):
        return len(json.dumps(deepl_payload(values, target), ensure_ascii=False, separators=(',', ':')).encode('utf-8'))

    for text in texts:
        if size([text]) > deepl_max_bytes: raise RuntimeError('A single UI string exceeds the DeepL request limit')
        if current and size(current + [text]) > deepl_max_bytes:
            batches.append(current)
            current = [text]
        else: current.append(text)

    if current: batches.append(current)
    return batches

def deepl_request(method, path, payload=None):
    endpoint = 'https://api-free.deepl.com' if deepl_api_key.endswith(':fx') else 'https://api.deepl.com'
    headers = {'Authorization': f'DeepL-Auth-Key {deepl_api_key}', 'Content-Type': 'application/json'}

    for attempt in range(4):
        try: response = requests.request(method, f'{endpoint}{path}', headers=headers, json=payload, timeout=30)
        except requests.RequestException as e:
            if attempt == 3: raise RuntimeError(f'Unable to reach DeepL: {e}') from e
            time.sleep(2 ** attempt)
            continue

        if response.status_code == 456: raise RuntimeError('DeepL quota is exhausted')
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == 3: raise RuntimeError(f'DeepL request failed with HTTP {response.status_code}')
            retry = response.headers.get('Retry-After', '')
            time.sleep(float(retry) if retry.replace('.', '', 1).isdigit() else 2 ** attempt)
            continue

        try:
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e: raise RuntimeError(f'DeepL request failed with HTTP {response.status_code}') from e
        except ValueError as e: raise RuntimeError('DeepL returned invalid JSON') from e
        return data

    raise RuntimeError('DeepL request failed')

def check_deepl_quota(required):
    if not required: return
    data = deepl_request('GET', '/v2/usage')
    used, limit = data.get('character_count'), data.get('character_limit')
    if not isinstance(used, int) or not isinstance(limit, int): raise RuntimeError('DeepL returned invalid usage data')
    if required > limit - used: raise RuntimeError(f'DeepL has {limit - used:,} characters remaining, but {required:,} are required')

def to_deepl(texts, code):
    unique = list(dict.fromkeys(texts))
    protected = [shield_placeholders(text) for text in unique]
    translated = {}
    offset = 0

    for batch in deepl_batches([data[0] for data in protected], deepl_targets[code]):
        data = deepl_request('POST', '/v2/translate', deepl_payload(batch, deepl_targets[code]))
        values = data.get('translations')

        if not isinstance(values, list) or len(values) != len(batch): raise RuntimeError(f'DeepL returned incomplete translations for {code}')

        for index, item in enumerate(values):
            if not isinstance(item, dict) or not isinstance(item.get('text'), str): raise RuntimeError(f'DeepL returned invalid translations for {code}')
            source = unique[offset + index]
            translated[source] = restore_placeholders(item['text'], protected[offset + index][1])

        offset += len(batch)

    return translated


# Synchronize locale files
def load_locale(code):
    path = locale_dir / f'{code}.json'
    try: data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as e: raise RuntimeError(f'Failed to load {path}: {e}') from e
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise RuntimeError(f'{path} must contain a JSON object with string keys and values')

    if code == 'en': return data, data

    clean = {}
    for key, value in data.items():
        new_key = sanitize_markers(key)
        new_value = sanitize_markers(value)
        if new_value.count('$$') != new_key.count('$$'): new_value = ''
        if new_key not in clean or new_key == key: clean[new_key] = new_value

    return data, clean

def write_locale(code, data):
    (locale_dir / f'{code}.json').write_text(json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True) + '\n', encoding='utf-8')

def machine_text(key, text):
    text = sanitize_markers(text)
    return 'understood' if key == 'okay' else text

def sync_locales(terms):
    source = {key: data['text'] for key, data in terms.items()}
    loaded = {code: load_locale(code) for code in locale_codes}
    raw = {code: data[0] for code, data in loaded.items()}
    existing = {code: data[1] for code, data in loaded.items()}
    catalogs = {'en': dict(source)}
    purged = {'en': len(set(existing['en']) - set(source))}

    for code in locale_codes:
        if code == 'en': continue
        catalogs[code] = {key: value for key, value in existing[code].items() if key in source}
        purged[code] = len(existing[code]) - len(catalogs[code])

    missing = {
        code: [key for key in sorted(source) if not catalogs[code].get(key, '').strip()]
        for code in locale_codes if code != 'en'
    }

    deepl_missing = {code: keys for code, keys in missing.items() if code in deepl_targets and keys}
    if deepl_missing and not deepl_api_key:
        total = sum(len(keys) for keys in deepl_missing.values())
        raise RuntimeError(f'{total} DeepL translation(s) are missing; set DEEPL_AUTH_KEY before running locale_gen.py')

    required = sum(
        sum(len(text) for text in {machine_text(key, source[key]) for key in keys})
        for code, keys in deepl_missing.items()
    )
    if required: check_deepl_quota(required)

    print('\nSynchronizing locale files...')
    for code in locale_codes:
        if code == 'en': continue
        print(f'[{code}] {purged[code]} stale removed, {len(missing[code])} missing')

    active = [code for code in locale_codes if code != 'en' and missing[code]]

    def generate(code):
        data = dict(catalogs[code])
        keys = missing[code]

        if code == 'e2':
            for key in keys:
                value = sanitize_markers(to_english_2(machine_text(key, source[key])))
                if value.count('$$') != key.count('$$'):
                    print(f'[e2] invalid markers: {key!r}')
                    value = machine_text(key, source[key])
                data[key] = value
        else:
            texts = [machine_text(key, source[key]) for key in keys]
            translated = to_deepl(texts, code)
            for key, text in zip(keys, texts): data[key] = sanitize_markers(translated[text])

        return code, data

    if active:
        with ThreadPoolExecutor(max_workers=len(active)) as pool:
            for code, data in pool.map(generate, active): catalogs[code] = data

    changed = []
    for code in locale_codes:
        if catalogs[code] == raw[code]: continue
        write_locale(code, catalogs[code])
        changed.append(code)

    translated = sum(len(keys) for keys in missing.values())
    removed = sum(purged.values())
    print(f'\nUpdated {len(changed)} locale file(s): {", ".join(changed) if changed else "none"}')
    print(f'Added {translated} missing translation(s), removed {removed} stale key(s)')


if __name__ == '__main__':
    created = generate_locale_files()
    terms, source_count, ui_count = scan()

    if created: print(f'\nCreated {len(created)} locale files: {", ".join(created)}')
    print(f'\nScanned {source_count} source files ({ui_count} UI files)')
    print(f'{len(terms)} translation candidates\n')

    # Print translation targets
    for data in sorted(terms.values(), key=lambda x: x['text'].lower()):
        path, line, source = data['locations'][0]
        print(f'{path}:{line} [{source}] {data["text"]!r}')

    sync_locales(terms)
