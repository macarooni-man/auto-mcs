from pathlib import Path
import py_compile
import textwrap
import ast
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


    # ----------------------------------------------- Patch Definitions ------------------------------------------------

    # Insert code immediately before a class or function.
    def before(self, target, content, description):
        return self._add('before', target=target, content=content, description=description)


    # Replace only the value of an assignment, preserving its annotation and formatting.
    def set(self, target, value, description):
        return self._add('set', target=target, value=value, description=description)


    # Insert code immediately after a named assignment inside a class or function.
    def after_assignment(self, target, name, content, description):
        return self._add('after_assignment', target=target, name=name, content=content, description=description)


    # Insert a new elif branch after an existing if branch.
    def elif_(self, after, condition, content, description):
        return self._add('elif', after=after, condition=condition, content=content, description=description)


    # Insert code relative to an import without depending on neighboring imports.
    def before_import(self, module, content, description, name=None):
        return self._add('import', module=module, name=name, content=content, after=False, description=description)


    def after_import(self, module, content, description, name=None):
        return self._add('import', module=module, name=name, content=content, after=True, description=description)


    # Insert code at the beginning of a class/function body.
    def prepend(self, target, content, description):
        return self._add('prepend', target=target, content=content, description=description)


    # Remove a call while preserving the surrounding implementation.
    def remove_call(self, target, call, description, args=None):
        return self._add('remove_call', target=target, call=call, args=args or [], description=description)


    # Guard a call while preserving the surrounding implementation.
    def guard_call(self, target, call, condition, description, args=None):
        return self._add('guard_call', target=target, call=call, condition=condition, args=args or [], description=description)


    # Guard the contiguous statement block that initializes/uses an object.
    def guard_object(self, target, object_name, condition, description):
        return self._add('guard_object', target=target, object_name=object_name, condition=condition, description=description)


    # Insert Android as the first platform branch inside a selected parent branch.
    def platform(self, target, branch, content, description):
        return self._add('platform', target=target, branch=branch, content=content, description=description)


    # Replace an entire function/class when Android intentionally owns the full implementation.
    def function(self, target, content, description):
        return self._add('replace_node', target=target, node_type='function', content=content, description=description)


    def class_(self, target, content, description):
        return self._add('replace_node', target=target, node_type='class', content=content, description=description)


    def _add(self, patch_type, **data):
        data['type'] = patch_type
        self._patches.append(data)
        return self


    # ------------------------------------------------ AST Helpers ------------------------------------------------------

    def _parse(self, text, description):
        try: return ast.parse(text)
        except SyntaxError as e: fail(f"{description}: failed to parse '{self.path}': {e}")


    @staticmethod
    def _expr(value):
        try: return ast.parse(value, mode='eval').body
        except SyntaxError as e: fail(f"invalid patch expression '{value}': {e}")


    @staticmethod
    def _same(left, right):
        if type(left) is not type(right): return False
        if not isinstance(left, ast.AST): return left == right

        for field in left._fields:
            if field == 'ctx': continue

            left_value = getattr(left, field)
            right_value = getattr(right, field)

            if isinstance(left_value, list):
                if len(left_value) != len(right_value): return False
                if not all(SourcePatch._same(a, b) for a, b in zip(left_value, right_value)): return False

            elif isinstance(left_value, ast.AST):
                if not SourcePatch._same(left_value, right_value): return False

            elif left_value != right_value:
                return False

        return True


    @staticmethod
    def _attribute_name(node):
        parts = []

        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value

        if isinstance(node, ast.Name):
            parts.append(node.id)
            return '.'.join(reversed(parts))

        return None


    @staticmethod
    def _decorated_start(node):
        decorators = getattr(node, 'decorator_list', [])
        return min([node.lineno] + [decorator.lineno for decorator in decorators])


    @staticmethod
    def _format(content, indent=0):
        content = textwrap.dedent(content).strip('\n')
        prefix = ' ' * indent
        return '\n'.join(f'{prefix}{line}' if line else '' for line in content.splitlines())


    @staticmethod
    def _lines(text):
        return text.splitlines(keepends=True)


    @staticmethod
    def _offset(text, line, column):
        lines = text.splitlines(keepends=True)
        return sum(len(item) for item in lines[:line - 1]) + column


    def _replace_node_text(self, text, node, replacement):
        start = self._offset(text, node.lineno, node.col_offset)
        end = self._offset(text, node.end_lineno, node.end_col_offset)
        return text[:start] + replacement + text[end:]


    def _scope(self, tree, target, description):
        parts = target.split('.')
        body = tree.body
        node = None

        for part in parts:
            matches = [
                item for item in body
                if isinstance(item, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == part
            ]

            if len(matches) != 1:
                fail(f"{description}: expected exactly one source target '{target}' in '{self.path}', found {len(matches)} at '{part}'")

            node = matches[0]
            body = node.body

        return node


    def _assignment(self, scope, name, description):
        matches = []

        for node in scope.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
                matches.append(node)

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        matches.append(node)
                        break

        if len(matches) != 1:
            fail(f"{description}: expected exactly one assignment '{name}' in '{self.path}', found {len(matches)}")

        return matches[0]


    @staticmethod
    def _assignment_value(node):
        return node.value


    def _find_if(self, scope, condition, description):
        expected = self._expr(condition)
        matches = []

        def walk(body):
            for node in body:
                if isinstance(node, ast.If) and self._same(node.test, expected):
                    matches.append(node)

                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    continue

                for field in ('body', 'orelse', 'finalbody'):
                    child = getattr(node, field, None)
                    if isinstance(child, list): walk(child)

                for handler in getattr(node, 'handlers', []):
                    walk(handler.body)

        body = scope.body if hasattr(scope, 'body') else scope
        walk(body)

        if len(matches) != 1:
            fail(f"{description}: expected exactly one branch '{condition}' in '{self.path}', found {len(matches)}")

        return matches[0]


    @staticmethod
    def _iter_statements(body):
        for node in body:
            yield node

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue

            for field in ('body', 'orelse', 'finalbody'):
                child = getattr(node, field, None)
                if isinstance(child, list):
                    yield from SourcePatch._iter_statements(child)

            for handler in getattr(node, 'handlers', []):
                yield from SourcePatch._iter_statements(handler.body)


    @staticmethod
    def _contains(node, expected):
        return any(SourcePatch._same(child, expected) for child in ast.walk(node))


    @staticmethod
    def _assigns(node, expected):
        targets = []

        if isinstance(node, ast.Assign): targets = node.targets
        elif isinstance(node, ast.AnnAssign): targets = [node.target]
        elif isinstance(node, ast.AugAssign): targets = [node.target]

        return any(SourcePatch._same(target, expected) for target in targets)


    def _find_import(self, tree, module, name, description):
        matches = []

        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == module:
                if name is None or any(alias.name == name for alias in node.names):
                    matches.append(node)

            elif isinstance(node, ast.Import):
                if any(alias.name == module and (name is None or alias.asname == name) for alias in node.names):
                    matches.append(node)

        if len(matches) != 1:
            label = f'{module}.{name}' if name else module
            fail(f"{description}: expected exactly one import '{label}' in '{self.path}', found {len(matches)}")

        return matches[0]


    # ----------------------------------------------- Patch Actions ----------------------------------------------------

    def _before(self, text, patch):
        tree = self._parse(text, patch['description'])
        node = self._scope(tree, patch['target'], patch['description'])
        lines = self._lines(text)
        index = self._decorated_start(node) - 1
        content = self._format(patch['content'], node.col_offset)

        lines.insert(index, content + '\n\n')
        return ''.join(lines)


    def _set(self, text, patch):
        tree = self._parse(text, patch['description'])
        parts = patch['target'].split('.')

        if len(parts) < 2:
            fail(f"{patch['description']}: assignment target must include its scope, got '{patch['target']}'")

        scope = self._scope(tree, '.'.join(parts[:-1]), patch['description'])
        node = self._assignment(scope, parts[-1], patch['description'])
        return self._replace_node_text(text, self._assignment_value(node), patch['value'])


    def _after_assignment(self, text, patch):
        tree = self._parse(text, patch['description'])
        scope = self._scope(tree, patch['target'], patch['description'])
        node = self._assignment(scope, patch['name'], patch['description'])
        lines = self._lines(text)
        content = self._format(patch['content'], node.col_offset)

        lines.insert(node.end_lineno, '\n' + content + '\n')
        return ''.join(lines)


    def _elif(self, text, patch):
        tree = self._parse(text, patch['description'])
        node = self._find_if(tree, patch['after'], patch['description'])
        lines = self._lines(text)

        indent = node.col_offset
        body_indent = node.body[0].col_offset if node.body else indent + 4
        content = self._format(patch['content'], body_indent)

        branch = f"{' ' * indent}elif {patch['condition']}:\n{content}\n\n"
        lines.insert(node.body[-1].end_lineno, branch)
        return ''.join(lines)


    def _import(self, text, patch):
        tree = self._parse(text, patch['description'])
        node = self._find_import(tree, patch['module'], patch['name'], patch['description'])
        lines = self._lines(text)
        content = self._format(patch['content'], node.col_offset)

        index = node.end_lineno if patch['after'] else node.lineno - 1
        lines.insert(index, content + '\n')
        return ''.join(lines)


    def _prepend(self, text, patch):
        tree = self._parse(text, patch['description'])
        node = self._scope(tree, patch['target'], patch['description'])
        lines = self._lines(text)

        body = node.body
        index = 0

        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            index = 1

        if index < len(body):
            line = body[index].lineno - 1
            indent = body[index].col_offset
        else:
            line = node.end_lineno
            indent = node.col_offset + 4

        content = self._format(patch['content'], indent)
        lines.insert(line, content + '\n\n')
        return ''.join(lines)


    def _find_call(self, scope, call_name, args, description):
        expected_args = [self._expr(arg) for arg in args]
        matches = []

        for statement in self._iter_statements(scope.body):
            if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
                continue

            call = statement.value
            if self._attribute_name(call.func) != call_name:
                continue

            if len(call.args) < len(expected_args):
                continue

            if all(self._same(call.args[index], value) for index, value in enumerate(expected_args)):
                matches.append(statement)

        if len(matches) != 1:
            fail(f"{description}: expected exactly one call '{call_name}' in '{self.path}', found {len(matches)}")

        return matches[0]


    def _remove_call(self, text, patch):
        tree = self._parse(text, patch['description'])
        scope = self._scope(tree, patch['target'], patch['description'])
        statement = self._find_call(scope, patch['call'], patch['args'], patch['description'])
        return self._replace_node_text(text, statement, 'pass')


    def _guard_call(self, text, patch):
        tree = self._parse(text, patch['description'])
        scope = self._scope(tree, patch['target'], patch['description'])
        statement = self._find_call(scope, patch['call'], patch['args'], patch['description'])
        parents = {}

        for parent in ast.walk(scope):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent

        parent = parents.get(statement)

        # A one-line parent statement owns the same physical source line as the call
        # Guard the parent so the patch never has to split Python syntax textually
        if isinstance(parent, ast.If) and parent.lineno == statement.lineno:
            statement = parent

        return self._guard_lines(text, statement.lineno, statement.end_lineno, statement.col_offset, patch['condition'])


    def _guard_object(self, text, patch):
        tree = self._parse(text, patch['description'])
        scope = self._scope(tree, patch['target'], patch['description'])
        expected = self._expr(patch['object_name'])

        start = None
        end = None

        for index, statement in enumerate(scope.body):
            if self._assigns(statement, expected):
                start = index
                end = index

                while end + 1 < len(scope.body) and self._contains(scope.body[end + 1], expected):
                    end += 1

                break

        if start is None:
            fail(f"{patch['description']}: could not find initialization for '{patch['object_name']}' in '{patch['target']}'")

        first = scope.body[start]
        last = scope.body[end]
        return self._guard_lines(text, first.lineno, last.end_lineno, first.col_offset, patch['condition'])


    def _guard_lines(self, text, start, end, indent, condition):
        lines = self._lines(text)
        block = lines[start - 1:end]

        guarded = [f"{' ' * indent}if {condition}:\n"]
        for line in block:
            if line.strip(): guarded.append('    ' + line)
            else:            guarded.append(line)

        lines[start - 1:end] = guarded
        return ''.join(lines)


    def _platform(self, text, patch):
        tree = self._parse(text, patch['description'])
        scope = self._scope(tree, patch['target'], patch['description'])
        parent = self._find_if(scope, patch['branch'], patch['description'])
        expected_os = self._expr('constants.os_name')
        matches = []

        for statement in parent.body:
            if isinstance(statement, ast.If) and self._contains(statement.test, expected_os):
                matches.append(statement)

        if len(matches) != 1:
            fail(f"{patch['description']}: expected exactly one desktop OS branch under '{patch['branch']}', found {len(matches)}")

        desktop = matches[0]
        lines = self._lines(text)
        header = desktop.lineno - 1

        # Keep comments documenting the desktop branch attached to that branch.
        insert = header
        while insert > parent.lineno:
            previous = lines[insert - 1]
            stripped = previous.strip()

            if not stripped or stripped.startswith('#'):
                insert -= 1
                continue

            break

        current = lines[header]
        prefix = current[:len(current) - len(current.lstrip())]
        remainder = current[len(prefix):]

        if not remainder.startswith('if '):
            fail(f"{patch['description']}: expected desktop platform branch to start with 'if' in '{self.path}'")

        lines[header] = prefix + 'elif ' + remainder[3:]

        body_indent = desktop.body[0].col_offset if desktop.body else desktop.col_offset + 4
        content = self._format(patch['content'], body_indent)
        branch = f"{' ' * desktop.col_offset}if constants.is_android:\n{content}\n\n"

        lines.insert(insert, branch)
        return ''.join(lines)


    def _replace_node(self, text, patch):
        tree = self._parse(text, patch['description'])
        node = self._scope(tree, patch['target'], patch['description'])

        if patch['node_type'] == 'function' and not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fail(f"{patch['description']}: '{patch['target']}' is not a function")

        if patch['node_type'] == 'class' and not isinstance(node, ast.ClassDef):
            fail(f"{patch['description']}: '{patch['target']}' is not a class")

        lines = self._lines(text)
        start = self._decorated_start(node)
        end = node.end_lineno
        content = self._format(patch['content'], node.col_offset)

        if lines[end - 1].endswith('\n'): content += '\n'
        lines[start - 1:end] = [content]

        return ''.join(lines)


    # ---------------------------------------------- Apply / Validate --------------------------------------------------

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

        actions = {
            'before': self._before,
            'set': self._set,
            'after_assignment': self._after_assignment,
            'elif': self._elif,
            'import': self._import,
            'prepend': self._prepend,
            'remove_call': self._remove_call,
            'guard_call': self._guard_call,
            'guard_object': self._guard_object,
            'platform': self._platform,
            'replace_node': self._replace_node,
        }

        for patch in self._patches:
            action = actions.get(patch['type'])
            if not action: fail(f"unknown patch type '{patch['type']}' for '{self.path}'")

            text = action(text, patch)
            self._validate(text)
            self._applied.append(patch['description'])

        self._result = text


    def _write(self):
        if self._result is None:
            fail(f"source patch '{self.name}' was not prepared before writing")

        self.path.write_text(self._result, encoding='utf-8')

        for description in self._applied:
            print(f'[android patch] {self.path}: {description}')


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
