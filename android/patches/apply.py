from pathlib import Path
import py_compile
import textwrap
import ast
import re
import sys

import source


# ---------------------------------------------- Global Variables ------------------------------------------------------
# <editor-fold desc="Global Variables">

baseline = '16c06e6a4e11f31c0dbf45a6c702cf98addc1cd5'

# </editor-fold>



# ------------------------------------------------ Patch Engine ---------------------------------------------------------
# <editor-fold desc="Patch Engine">

def fail(message):
    raise RuntimeError(f'[android patch] {message}')


class SourcePatch():
    _registry = []

    def __init__(self, path):
        self.path = Path(path)
        self.name = self.path.with_suffix('').as_posix().rsplit('/source/', 1)[-1].replace('/', '.')
        self._patches = []
        self._result = None
        self._applied = []

        if any(patch.path == self.path for patch in self._registry):
            fail(f"duplicate source patch registered for '{self.path}'")

        self._registry.append(self)


    # Exact replacement with an automatic whitespace-tolerant fallback.
    def replace(self, old, new, description, fuzzy=True):
        self._patches.append({
            'type': 'replace',
            'old': old,
            'new': new,
            'description': description,
            'fuzzy': fuzzy,
        })
        return self


    # Raw regex replacement for patches that need more control than fuzzy matching.
    def regex(self, pattern, new, description, flags=re.MULTILINE, count=1):
        self._patches.append({
            'type': 'regex',
            'pattern': pattern,
            'new': new,
            'description': description,
            'flags': flags,
            'count': count,
        })
        return self


    # Replaces an entire top-level function by locating it through the AST.
    # The source can change internally without invalidating the patch.
    def function(self, name, new, description):
        self._patches.append({
            'type': 'ast',
            'target': name,
            'node_type': 'function',
            'new': new,
            'description': description,
        })
        return self


    # Replaces an entire class method by locating Class.method through the AST.
    def method(self, class_name, name, new, description):
        return self.function(f'{class_name}.{name}', new, description)


    # Replaces an entire class by locating it through the AST.
    def class_(self, name, new, description):
        self._patches.append({
            'type': 'ast',
            'target': name,
            'node_type': 'class',
            'new': new,
            'description': description,
        })
        return self


    @staticmethod
    def _fuzzy_pattern(value):
        lines = value.strip('\n').splitlines()
        pattern = []
        blank = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                blank = True
                continue

            if pattern:
                if blank: pattern.append(r'(?:[ \t]*\r?\n)+')
                else:     pattern.append(r'[ \t]*\r?\n')

            line_pattern = []
            for part in re.split(r'([ \t]+)', stripped):
                if not part: continue
                if part.isspace(): line_pattern.append(r'[ \t]+')
                else:              line_pattern.append(re.escape(part))

            pattern.append(r'[ \t]*' + ''.join(line_pattern) + r'[ \t]*')
            blank = False

        return ''.join(pattern)


    def _replace(self, text, patch):
        old = patch['old']
        new = patch['new']
        description = patch['description']
        count = text.count(old)

        if count == 1:
            self._applied.append((description, 'exact'))
            return text.replace(old, new, 1)

        if count > 1:
            fail(f"{description}: expected exactly one source anchor in '{self.path}', found {count}. Current overlay baseline is {baseline}.")

        if patch['fuzzy']:
            pattern = self._fuzzy_pattern(old)
            matches = list(re.finditer(pattern, text, re.MULTILINE))

            if len(matches) == 1:
                self._applied.append((description, 'fuzzy'))
                return re.sub(pattern, lambda _: new, text, count=1, flags=re.MULTILINE)

            fail(f"{description}: exact source anchor was not found in '{self.path}', and fuzzy matching found {len(matches)} candidates. Current overlay baseline is {baseline}.")

        fail(f"{description}: source anchor was not found in '{self.path}'. Current overlay baseline is {baseline}.")


    def _regex(self, text, patch):
        matches = list(re.finditer(patch['pattern'], text, patch['flags']))
        if len(matches) != patch['count']:
            fail(f"{patch['description']}: expected {patch['count']} regex match(es) in '{self.path}', found {len(matches)}. Current overlay baseline is {baseline}.")

        self._applied.append((patch['description'], 'regex'))
        return re.sub(patch['pattern'], patch['new'], text, count=patch['count'], flags=patch['flags'])


    def _ast_node(self, text, target, node_type):
        try: tree = ast.parse(text)
        except SyntaxError as e: fail(f"failed to parse '{self.path}' before AST patch '{target}': {e}")

        parts = target.split('.')
        body = tree.body
        node = None

        for index, part in enumerate(parts):
            matches = [
                item for item in body
                if isinstance(item, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == part
            ]

            if len(matches) != 1:
                fail(f"AST target '{target}' expected exactly one '{part}' in '{self.path}', found {len(matches)}. Current overlay baseline is {baseline}.")

            node = matches[0]
            if index < len(parts) - 1:
                body = getattr(node, 'body', [])

        if node_type == 'function' and not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fail(f"AST target '{target}' in '{self.path}' is not a function")

        if node_type == 'class' and not isinstance(node, ast.ClassDef):
            fail(f"AST target '{target}' in '{self.path}' is not a class")

        return node


    def _ast(self, text, patch):
        node = self._ast_node(text, patch['target'], patch['node_type'])
        lines = text.splitlines(keepends=True)

        decorators = getattr(node, 'decorator_list', [])
        start = min([node.lineno] + [decorator.lineno for decorator in decorators]) - 1
        end = node.end_lineno

        replacement = textwrap.dedent(patch['new']).strip('\n')
        indent = ' ' * node.col_offset
        replacement = '\n'.join(f'{indent}{line}' if line else '' for line in replacement.splitlines())

        if lines[end - 1].endswith('\n'):
            replacement += '\n'

        self._applied.append((patch['description'], 'ast'))
        return ''.join(lines[:start]) + replacement + ''.join(lines[end:])


    def _validate(self, text=None):
        if text is None:
            text = self.path.read_text(encoding='utf-8')

        try: compile(text, str(self.path), 'exec')
        except SyntaxError as e: fail(f"syntax validation failed for '{self.path}': {e}")

        return True


    def _apply(self):
        if not self.path.is_file():
            fail(f"missing source file '{self.path}'")

        text = self.path.read_text(encoding='utf-8')
        self._applied = []

        for patch in self._patches:
            if patch['type'] == 'replace': text = self._replace(text, patch)
            elif patch['type'] == 'regex': text = self._regex(text, patch)
            elif patch['type'] == 'ast':   text = self._ast(text, patch)
            else: fail(f"unknown patch type '{patch['type']}' for '{self.path}'")

        self._validate(text)
        self._result = text


    def _write(self):
        if self._result is None:
            fail(f"source patch '{self.name}' was not prepared before writing")

        self.path.write_text(self._result, encoding='utf-8')

        for description, mode in self._applied:
            suffix = f' ({mode})' if mode != 'exact' else ''
            print(f'[android patch] {self.path}: {description}{suffix}')


    @classmethod
    def clear(cls):
        cls._registry = []


    @classmethod
    def apply_all(cls):
        # Prepare and validate every file before changing the staged source tree.
        for patch in cls._registry:
            patch._apply()

        # Only write after every patch has matched and compiled successfully.
        for patch in cls._registry:
            patch._write()


    @classmethod
    def validate_all(cls):
        for patch in cls._registry:
            patch._validate()

# </editor-fold>



# -------------------------------------------------- Validation ---------------------------------------------------------
# <editor-fold desc="Validation">

def validate(stage):
    SourcePatch.validate_all()

    # Android-owned runtime files are copied directly rather than patched.
    # Validate every Python file at the stage root so this list stays automatic.
    for path in sorted(stage.glob('*.py')):
        py_compile.compile(str(path), doraise=True)

    print('[android patch] Python syntax validation passed')

# </editor-fold>



# -------------------------------------------------- Entry Point --------------------------------------------------------
# <editor-fold desc="Entry Point">

def main():
    if len(sys.argv) != 2:
        fail('Usage: apply.py <staged-app-root>')

    stage = Path(sys.argv[1]).resolve()
    source_path = stage / 'source'

    if not source_path.is_dir():
        fail(f"Missing staged source directory: '{source_path}'")

    SourcePatch.clear()
    source.register(source_path, SourcePatch)

    SourcePatch.apply_all()
    validate(stage)

    print(f'[android patch] Done (baseline {baseline})')


if __name__ == '__main__':
    main()

# </editor-fold>
