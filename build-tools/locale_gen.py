from pathlib import Path
import requests
import time
import ast
import re


# ---------------------- locale-gen ----------------------
#
#    Discovers translatable strings from the UI
#
# --------------------------------------------------------


root_dir = Path(__file__).resolve().parents[1]
source_dir = root_dir / 'source'
ui_dir = source_dir / 'ui'
desktop_dir = ui_dir / 'desktop'

# Function: (positional args, keyword args)
scan_calls = {
    'HeaderText':         ((0, 1), ('display_text', 'more_text')),
    'MainButton':         ((0,), ('name',)),
    'WaitButton':         ((0,), ('name',)),
    'NextButton':         ((0,), ('name',)),
    'ExitButton':         ((0,), ('name',)),
    'InputButton':        ((0,), ('name', 'title')),
    'IconButton':         ((0,), ('name',)),
    'RelativeIconButton': ((0,), ('name',)),
    'BigModeButton':      ((0,), ('name',)),
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


if __name__ == '__main__':
    terms, source_count, ui_count = scan()
    print(f'\nScanned {source_count} source files ({ui_count} UI files)')
    print(f'{len(terms)} translation candidates\n')

    for data in sorted(terms.values(), key=lambda x: x['text'].lower()):
        path, line, source = data['locations'][0]
        print(f'{path}:{line} [{source}] {data["text"]!r}')