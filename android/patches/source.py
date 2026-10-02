import re


# ---------------------------------------------- Patch Utilities -------------------------------------------------------

def _prepend_body(match, content):
    indent = match.group('indent') + '    '
    lines = content.strip('\n').splitlines()
    content = '\n'.join(f'{indent}{line}' if line else '' for line in lines)
    return f'{match.group(0)}{content}\n'


def _guard_block(match, condition):
    indent = match.group('indent')
    block = match.group('block')
    output = [f'{indent}if {condition}:\n']

    for line in block.splitlines(keepends=True):
        if line.startswith(indent): line = line[len(indent):]
        output.append(f'{indent}    {line}')

    return ''.join(output)


def _platform_branch(match, content):
    indent = match.group('indent')
    body_indent = indent + '    '
    content = '\n'.join(f'{body_indent}{line}' if line else '' for line in content.strip('\n').splitlines())

    return (
        f"{match.group('prefix')}"
        f'{indent}if constants.is_android:\n'
        f'{content}\n\n'
        f"{indent}elif {match.group('condition')}:"
    )



# --------------------------------------------- Source Patches ---------------------------------------------------------

def register(source, SourcePatch):

    # ----------------------------------------------- core/constants.py -------------------------------------------------
    constants = SourcePatch(source / 'core' / 'constants.py')

    # Expose an Android runtime flag before 'paths' is evaluated
    # Anchored to the class instead of the current os_name implementation so OS detection can change freely
    constants.regex(
        r'(?m)^(?P<paths>(?:@[^\n]+\n)*class\s+paths\s*:)',
        '# Android is injected only into the generated build tree.\n'
        'is_android = os.environ.get("AUTO_MCS_ANDROID") == "1"\n\n\n'
        r'\g<paths>',
        'add Android runtime flag',
    )

    # Keep the generated application state in Android-private storage
    # Match the field itself rather than its current desktop value
    constants.regex(
        r'(?m)^(?P<indent>[ \t]+)user_home(?:\s*:\s*[^=\n]+)?\s*=\s*[^\n]+$',
        r"\g<indent>user_home:            str = os.environ.get('ANDROID_PRIVATE', os.path.expanduser('~')) if is_android else os.path.expanduser('~')",
        'use Android private storage as home',
    )

    # Do not create the normal hidden Linux-style application directory on Android
    constants.regex(
        r'(?m)^(?P<indent>[ \t]+)app_folder(?:\s*:\s*[^=\n]+)?\s*=\s*[^\n]+$',
        r"\g<indent>app_folder:           str = os.path.join(appdata, ('auto-mcs' if (os_name == 'macos' or is_android) else '.auto-mcs'))",
        'use non-hidden Android app data directory',
    )

    # /tmp is not a suitable writable application temp directory on Android
    constants.regex(
        r'(?m)^(?P<indent>[ \t]+)os_temp(?:\s*:\s*[^=\n]+)?\s*=\s*[^\n]+$',
        r"\g<indent>os_temp:              str = os.path.join(user_home, 'tmp') if is_android else os.getenv('TEMP') if os_name == 'windows' else '/tmp'",
        'keep Android temporary files in private storage',
    )

    # Return Android release/API data before the normal desktop OS formatting
    # This only depends on format_os() continuing to resolve the local 'arch' string
    constants.regex(
        r'(?ms)(?P<prefix>^def\s+format_os\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:\s*\n.*?^[ \t]+arch\s*=\s*[^\n]+\n)',
        r'''\g<prefix>
    if is_android:
        import runtime
        version, api = runtime.os_version()

        if version and api:
            return f"Android {version} (API {api}, {arch})"
        elif version:
            return f"Android {version} ({arch})"
        else:
            return f"Android ({arch})"
''',
        'report Android platform information',
        flags = re.MULTILINE | re.DOTALL,
    )


    # ----------------------------------------------- core/telepath.py --------------------------------------------------
    telepath = SourcePatch(source / 'core' / 'telepath.py')

    # Insert Android identity between the persistent Docker identity and the normal desktop fallback
    # The desktop identity implementation may change internally without affecting this patch
    telepath.regex(
        r'''(?m)(?P<docker>^if\s+constants\.is_docker\s*:\s*\n(?:(?:^[ \t]+.*|^[ \t]*)\n)+?)(?P<gap>(?:(?:^#.*|^[ \t]*)\n)*)(?P<fallback>^else\s*:)''',
        r'''\g<docker>elif constants.is_android:
    UNIQUE_ID = hashlib.sha256(f"{constants.app_title}::{constants.username}::{ID_HASH}::{constants.machine_id}".encode()).hexdigest()
\g<gap>\g<fallback>''',
        'use persistent Android Telepath identity',
    )


    # --------------------------------------------- ui/desktop/init.py --------------------------------------------------
    init = SourcePatch(source / 'ui' / 'desktop' / 'init.py')

    # Configure Android immediately before the desktop utility import can initialize Kivy Window
    init.regex(
        r'(?m)^(?P<utility_import>from\s+source\.ui\.desktop\.utility\s+import\s+\*[ \t]*)$',
        'import runtime\n'
        'runtime.configure_kivy(Config)\n\n'
        r'\g<utility_import>',
        'install Android window and input configuration before Kivy Window import',
    )

    # Bind the desktop utility module to the logical Android surface size as soon as it is imported
    init.regex(
        r'(?m)^(?P<utility_import>from\s+source\.ui\.desktop\s+import\s+utility[ \t]*)$',
        r'\g<utility_import>' '\n'
        'runtime.bind_utility(utility)',
        'bind Android logical resolution to desktop UI utility',
    )

    # Android owns window sizing/positioning. Return before whatever desktop implementation follows
    init.regex(
        r'(?m)^(?P<indent>[ \t]+)def\s+_configure_window\s*\(\s*self[^)]*\)\s*(?:->\s*[^:]+)?\s*:\s*\n',
        lambda match: _prepend_body(
            match,
            "if constants.is_android:\n"
            "    utility.window_size = runtime.window_size\n"
            "    self.configured_window = True\n"
            "    return True"
        ),
        'skip desktop window positioning on Android',
    )

    # Do not invoke native desktop window operations on Android
    # Patch only the individual calls so unrelated MainApp.build() changes are retained
    init.regex(
        r'(?m)^(?P<indent>[ \t]+)if\s+constants\.app_config\.fullscreen\s*:\s*Window\.maximize\(\)[ \t]*$',
        r'\g<indent>if not constants.is_android and constants.app_config.fullscreen: Window.maximize()',
        'skip desktop maximize operation on Android',
    )

    init.regex(
        r'(?m)^(?P<indent>[ \t]+)Window\.show\(\)[ \t]*$',
        r'\g<indent>if not constants.is_android: Window.show()',
        'skip desktop show operation on Android',
    )

    init.regex(
        r'(?m)^(?P<indent>[ \t]+)Clock\.schedule_once\(\s*raise_window\s*,\s*(?P<delay>[^)\n]+)\)[ \t]*$',
        r'\g<indent>if not constants.is_android: Clock.schedule_once(raise_window, \g<delay>)',
        'skip desktop raise operation on Android',
    )


    # ----------------------------------------- ui/desktop/widgets/buttons.py -------------------------------------------
    buttons = SourcePatch(source / 'ui' / 'desktop' / 'widgets' / 'buttons.py')

    # Normalize Android touches independently of the desktop wm_touch behavior
    # This does not depend on the existing desktop input condition remaining unchanged
    buttons.regex(
        r'(?m)^(?P<indent>[ \t]+)def\s+onPressed\s*\(\s*self\s*,\s*instance\s*,\s*touch\s*\)\s*(?:->\s*[^:]+)?\s*:\s*\n',
        lambda match: _prepend_body(match, "if constants.is_android: touch.button = 'left'"),
        'normalize Android button presses to left click',
    )


    # ----------------------------------------- ui/desktop/views/templates.py ------------------------------------------
    templates = SourcePatch(source / 'ui' / 'desktop' / 'views' / 'templates.py')

    # Guard the complete keyboard request/bind block instead of matching its exact contents
    # Additional self._keyboard.bind() calls are automatically included
    templates.regex(
        r'''(?m)^(?P<block>(?P<indent>[ \t]+)self\._keyboard\s*=\s*Window\.request_keyboard\([^\n]*\)[ \t]*\n(?:(?P=indent)self\._keyboard\.bind\([^\n]*\)[ \t]*\n)*)''',
        lambda match: _guard_block(match, 'not constants.is_android'),
        'skip desktop keyboard capture on Android',
    )


    # --------------------------------------------- ui/desktop/utility.py -----------------------------------------------
    utility = SourcePatch(source / 'ui' / 'desktop' / 'utility.py')

    # Add Android as the first platform branch for file selection while preserving whichever
    utility.regex(
        r'''(?ms)(?P<prefix>^[ \t]+if\s+ask_type\s*==\s*["']file["']\s*:\s*\n.*?)(?P<indent>^[ \t]+)if\s+(?P<condition>constants\.os_name\s*==\s*["'][^"']+["'])\s*:''',
        lambda match: _platform_branch(
            match,
            "final_path = filechooser.open_file(title=title, filters=ext, path=start_dir, multiple=select_multiple)\n"
            "if isinstance(final_path, str) and final_path:\n"
            "    final_path = [final_path]"
        ),
        'route Android file selection through Plyer',
        flags = re.MULTILINE | re.DOTALL,
    )

    # Add Android as the first platform branch for directory selection
    utility.regex(
        r'''(?ms)(?P<prefix>^[ \t]+elif\s+ask_type\s*==\s*["']dir["']\s*:\s*\n.*?)(?P<indent>^[ \t]+)if\s+(?P<condition>constants\.os_name\s*==\s*["'][^"']+["'])\s*:''',
        lambda match: _platform_branch(
            match,
            "selected = filechooser.choose_dir(title=title, path=start_dir)\n"
            "final_path = selected[0] if isinstance(selected, (list, tuple)) and selected else selected or ''"
        ),
        'route Android directory selection through Plyer',
        flags = re.MULTILINE | re.DOTALL,
    )

    # open_folder() has no Android implementation
    utility.regex(
        r'(?m)^(?P<indent>[ \t]*)def\s+open_folder\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:\s*\n',
        lambda match: _prepend_body(
            match,
            "if constants.is_android:\n"
            "    send_log('open_folder', f\"opening '{path}' in file browser\")\n"
            "    return False"
        ),
        'prevent desktop file-browser commands on Android',
    )
