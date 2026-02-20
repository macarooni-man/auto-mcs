from source.ui.headless.commands import *
from source.ui.headless.utility import *
from source.ui.headless import utility


# ---------------------------------------------------- Main Menu -------------------------------------------------------

class MainMenuScreen(MenuBackground):

    def __init__(self):

        self.command_header = '   ' if advanced_term else ' >>  '
        self.response_header = '❯ ' if advanced_term else '> '

        self.logo_widget = urwid.Text([('command', '\n'.join(constants.text_logo))], align='center')

        if constants.dev_version:
            self.splash_widget = urwid.Text([('info', f"{constants.format_version()}\n")], align='center')
        else:
            self.splash_widget = urwid.Text([('info', f"{constants.session_splash}\n")], align='center')

        self.telepath_content = urwid.Text([('info', 'Initializing...')])

        # Home screen status
        content = []
        if not constants.app_latest:
            content.extend([
                ("parameter", self.response_header),
                ("parameter", "(!) An update for auto-mcs is available. Run "),
                ("command", "update "),
                ("sub_command", "info "),
                ("parameter", "to learn more\n\n")
            ])
        content.extend([('info', self.response_header), ('normal', "Type a command, ?, or "), ('command', 'help')])
        self.command_content = urwid.Text(content)

        # Contains updating text in box
        self.console = urwid.Pile([
            ('flow', self.telepath_content),
            urwid.Filler(self.command_content, valign='bottom')
        ])

        self.title = f"auto-mcs v{constants.app_version}"
        if constants.dev_version: self.title += " (dev)"
        self.title += f" (headless)" if constants.app_latest else " (!)"

        self.message_box = urwid.AttrMap(
            urwid.LineBox(
                self.console,
                title = self.title,
                title_attr = ('normal' if constants.app_latest else 'parameter')
            ),
            'menu_line'
        )

        self.disable_commands = False
        self.command_history: list[str] = []
        self.history_index = 0

        # Create the Edit widget for command input
        self.command_edit = self.CommandInput(self, caption=self.command_header)

        # Create a Pile for stacking widgets vertically
        self.pile = urwid.Pile([
            ('flow', self.logo_widget),
            ('flow', self.splash_widget),
            ('weight', 0.5, urwid.Padding(self.message_box, left=1, right=1)),
            ('flow', self.command_edit)
        ])
        self.top_widget = urwid.Padding(self.pile)
        self.menu = urwid.Frame(self.top_widget)


    # Input handler
    def handle_input(self, key):
        command = self.command_edit.get_edit_text().replace(self.command_header, '')

        # Submit/process command on ENTER
        if key == 'enter' and not self.disable_commands:
            self.process_command(command)

        # Modulate command history with arrow keys
        elif key in ['up', 'down'] and self.command_history:

            if key == 'down':
                if self.history_index > 0:
                    self.history_index -= 1
                else:
                    self.command_edit.set_edit_text('')
                    return

            # Constrain history_index to valid range
            self.history_index = max(0, min(self.history_index, len(self.command_history) - 1))

            # Set the command text based on the updated index
            new_text = self.command_history[self.history_index]
            self.command_edit.set_edit_text(new_text)
            self.command_edit.set_edit_pos(len(new_text))

            if key == 'up':
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1

    def process_command(self, cmd: str):
        self.history_index = 0
        success = True

        if cmd not in self.command_history[:1]:
            self.command_history.insert(0, cmd)

            # Limit size of command history
            if len(self.command_history) > 100:
                self.command_history.pop()

        self.command_edit.set_edit_text('')
        response = [('normal', "Type a command, ?, or "), ('command', 'help')]

        if cmd.strip():
            try:
                # Format raw data into command, and args
                raw = [a.strip() for a in cmd.split(' ') if a.strip()]
                cmd_name = raw[0]
                args = () if len(raw) < 2 else raw[1:]

                # Process command and return output
                command = commands[cmd_name]
                send_log('process_command', f"issued command: '{' '.join(raw)}'", 'info')
                output = command.exec(args)

                if isinstance(output, tuple):
                    success = 'fail' != output[1]
                    output = output[0]

                if output is not None:
                    response = output

            except KeyError:
                response = [("info", "Unknown command "), ("fail", cmd), ("normal", '\n'), *response]

        self.command_content.set_text([('success' if success else 'fail', self.response_header), *response])

    def update_console(self, text: str | tuple):
        self.command_content.set_text(text)
        utility.screen_manager._loop.draw_screen()



    class CommandInput(urwid.Edit):
        def __init__(self, screen: 'MainMenuScreen', *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.screen = screen

            self.hint_text = ''
            self.is_valid = False
            self.hint_params = 0

        def _valid(self, valid=True):
            self.is_valid = valid
            color = get_color('command') if valid else get_color('fail')
            utility.screen_manager._loop.screen.register_palette_entry('input', *color[1:])

        def _get_hint_text(self, input_text):
            # Insert version hints
            version_hints = [f'{t.replace("craft", "")}:latest' for t in foundry.latestMC.keys() if t != 'builds']
            version_hints.insert(0, 'latest')

            # Insert instant template hints
            version_hints.extend([f"instant:{f[:-4]}" for f in foundry.ist_data.keys()])

            if input_text:
                command_name = input_text.split(' ')[0]
                self.hint_text = ''

                # Get root command object
                for command in commands.values():
                    if command.name.startswith(command_name):
                        self._valid(True)

                        # Attempt to find sub-commands for a hint
                        if input_text.startswith(command.name) and command.sub_commands and input_text not in commands:
                            args = input_text.replace(command.name, '').strip().split(' ')
                            sub_hint = command.get_hints(args)
                            if not sub_hint:
                                self._valid(False)
                                return ""
                            else:
                                self.hint_text = f'{command.name} {sub_hint}'

                        # Check if there are parameters for root command instead
                        self.hint_params = 0
                        if not self.hint_text and command.params:
                            self.hint_params = 1
                            self._valid(True)
                            if input_text.strip().endswith(command.name) and ' ' not in input_text.strip():
                                self.hint_text = f'{command.name} {" ".join(["<" + p + ">" for p in command.params])}'

                            # Override "server name" parameter to display server names
                            elif command.name in input_text and list(command.params.items())[0][0] == 'server name':
                                partial_name = input_text.split(' ', 1)[-1].strip()
                                for server in constants.server_manager.server_list:
                                    if server.lower().startswith(partial_name.lower()):
                                        self.hint_text = f'{command.name} {server}'
                                        break

                            # Override "command" parameter to display commands
                            elif command.name in input_text and list(command.params.items())[0][0] == 'command':
                                command_start = ' '.join(input_text.split(' ', 1)[:1])
                                partial_name = input_text.split(' ', 1)[-1].strip()
                                for c in commands:
                                    if c.lower().startswith(partial_name.lower()):
                                        self.hint_text = f'{command_start} {c}'
                                        break

                        if input_text.startswith(command.name) and command.sub_commands:
                            for sc in command.sub_commands.values():
                                if sc.params:
                                    self.hint_params = 2
                                    param_index = 0
                                    args = ()

                                    if len(sc.params) > 1:
                                        try:
                                            args = input_text.strip().split(' ', len(sc.params) + self.hint_params)[self.hint_params:]
                                        except:
                                            args = ()

                                        param_index = len(args)
                                        if param_index < 0:
                                            param_index = 0
                                        elif param_index > len(sc.params):
                                            param_index = len(sc.params)

                                        self._valid(True)

                                        if param_index >= len(sc.params):
                                            break

                                    if input_text.endswith(sc.name + ' ') or (len(args) > 0 and input_text.endswith(' ')):
                                        self.hint_text = f'{input_text.strip()} <{list(sc.params.keys())[param_index]}>'

                                    # Override "server name" parameter to display server names
                                    elif sc.name in input_text and list(sc.params.items())[0][0] == 'server name':
                                        command_start = ' '.join(input_text.split(' ', 2)[:2])
                                        partial_name = input_text.split(' ', 2)[-1].strip()
                                        if command_start != 'server create':
                                            for server in constants.server_manager.server_list:
                                                if server.lower().startswith(partial_name.lower()):
                                                    self.hint_text = f'{command_start} {server}'
                                                    break

                                    # Override "vendor ID" parameter to display Java vendors
                                    elif sc.name in input_text and list(sc.params.items())[0][0] == 'vendor ID':
                                        from source.core.tools import java
                                        command_start = ' '.join(input_text.split(' ', 2)[:2])
                                        partial_name = input_text.split(' ', 2)[-1].strip()
                                        for vendor in java.manager.supported_vendors:
                                            if vendor.lower().startswith(partial_name.lower()):
                                                self.hint_text = f'{command_start} {vendor}'
                                                break

                                    # Override "type:version" parameter to display latest versions
                                    elif sc.name in input_text and list(sc.params.items())[0][0] == 'type:version':
                                        command_start = ' '.join(input_text.split(' ', 2)[:2])
                                        partial_name = input_text.split(' ', 2)[-1].strip()
                                        for version in version_hints:
                                            if version.startswith(partial_name):
                                                self.hint_text = f'{command_start} {version} '
                                                break

                        if not self.hint_text:
                            self.hint_text = command.name

                        # Return the rest of the command as the hint
                        return self.hint_text[len(input_text):]

            self._valid(False)
            return ""

        def get_text(self):
            input_text = super().get_edit_text()
            hint_text = self._get_hint_text(input_text)
            if hint_text:
                return self.hint_text, len(input_text)
            return input_text, len(input_text)

        def render(self, size, focus=False):
            original_text = input_text = super().get_edit_text()

            caption_space = ('caption_space', re.search(r'^\s+', self.caption)[0])
            caption_marker = ('caption_marker', self.caption.lstrip())

            if ' ' in input_text and self.is_valid:
                command = f"{original_text.split(' ', 1)[0]} "
                sub_command = ''
                if self.hint_params != 1:
                    sub_command = original_text.split(' ')[1]
                    try:
                        sub_command = sub_command + re.search(r'\s+', original_text[len(command + sub_command):])[0]
                    except:
                        pass

                param = ''
                if 0 < self.hint_params <= original_text.strip().count(' '):
                    param = original_text.split(' ', self.hint_params)[-1].replace(sub_command.strip(), '')

                input_text = []
                if command:
                    input_text.append(('command', command))
                if sub_command:
                    input_text.append(('sub_command', sub_command))

                if param:
                    if commands[command.strip()].sub_commands:
                        params = []
                        try:
                            params = commands[command.strip()].sub_commands[sub_command.strip()].params
                            args = param.split()
                            if len(args) > len(params):
                                args = list(args[:len(params) - 1]) + [' '.join(args[len(params) - 1:])]
                                args = tuple(args)
                        except:
                            args = ()

                        for x, arg in enumerate(args, 0):
                            found_type = False
                            try:
                                arg = re.findall(fr'{arg}\s*', param)[0]
                            except:
                                pass

                            if params and args:
                                param_type = list(params.keys())[x]
                                if ':' in param_type:
                                    found_type = True

                                    if ':' in arg and not arg.endswith(':'):
                                        type_a, type_b = arg.split(':', 1)
                                        input_text.extend([
                                            ('type_a', type_a),
                                            ('hint', ':'),
                                            ('type_b', type_b)
                                        ])
                                    elif ':' in arg:
                                        input_text.extend([
                                            ('type_a', arg.strip(':')),
                                            ('hint', ':')
                                        ])
                                    else:
                                        s = arg.strip().lower()
                                        color = 'type_b' if s.replace('.', '').isdigit() or s == 'latest' else 'type_a'
                                        input_text.append((color, arg))

                            if not found_type:
                                input_text.append(('parameter', arg))
                    else:
                        input_text.append(('parameter', param))
            else:
                input_text = ('input', input_text)

            if isinstance(input_text, list):
                final_space = ''
                if original_text.endswith(' '):
                    final_space = (len(original_text) - len(original_text.rstrip())) * ' '
                original_text = re.sub(r'\s*\:\s*', ':', ' '.join([s[1].strip() for s in input_text])) + final_space

            hint_text = self._get_hint_text(original_text)
            combined_text = [caption_space, caption_marker, input_text, ('hint', hint_text)]

            text_widget = urwid.Text(combined_text)
            canvas = text_widget.render(size)

            if focus:
                canvas = urwid.CompositeCanvas(canvas)
                cursor_position = len(self.caption) + self.edit_pos
                canvas.cursor = (cursor_position, 0)

            return canvas

        def cursor_x(self, size):
            return self.get_cursor_coords(size)[0] - len(self.caption)

        def keypress(self, size, key):
            actual_text = self.edit_text
            actual_index = self.get_cursor_coords(size)[0]

            if (key in ('meta backspace', 'ctrl w')) and (actual_index - len(self.caption) == len(actual_text)):
                text, index = constants.control_backspace(actual_text, self.cursor_x(size))
                new_index = self.cursor_x(size) - index + len(self.caption)
                self.set_edit_text(text.strip())

                if text.endswith(' '):
                    self.keypress(size, ' ')

                self.set_edit_pos(new_index)
                return None

            if key == ' ':
                pos = self.cursor_x(size)
                txt = self.text
                if pos == 0:
                    return
                if pos > 0 and txt[pos - 1] == ' ':
                    return

            if key == '?':
                help_content = commands['help'].show_command_help(self.get_edit_text().split(' '))
                if help_content:
                    self.screen.command_content.set_text([('info', self.screen.response_header), *help_content])
                return

            if key in ('tab', 'right') and self.cursor_x(size) >= len(actual_text):
                if self.hint_text:
                    if self.hint_text in commands.keys():
                        if commands[self.hint_text].sub_commands:
                            self.hint_text += ' '

                    if ' ' in self.hint_text.strip():
                        command = self.hint_text.split(' ', 1)[0].strip()
                        sub_command = self.hint_text.split(' ', 1)[-1].strip()
                        if sub_command in commands[command].sub_commands.keys():
                            if commands[command].sub_commands[sub_command].params:
                                self.set_edit_text(self.text + (' ' if not self.get_edit_text().endswith(' ') else ''))
                                self.set_edit_pos(len(self.get_edit_text()))
                                return None

                    if '<' in self.hint_text and '>' in self.hint_text and ' ' in self.edit_text:
                        return None
                    elif ('<' in self.hint_text and '>' in self.hint_text) or (self.hint_text in commands and commands[self.hint_text].params):
                        self.set_edit_text(self.hint_text.split(' ', 1)[0] + ' ')
                        self.set_edit_pos(len(self.get_edit_text()))
                        return None

                    if ':' in self.hint_text and ':' not in self.get_edit_text().rsplit(' ', 1)[-1]:
                        self.hint_text = self.hint_text.rsplit(':')[0] + ':'

                    self.set_edit_text(self.hint_text)
                    self.set_edit_pos(len(self.get_edit_text()))
                    return None

            result = super().keypress(size, key)
            self.set_edit_pos(self.edit_pos)
            utility.screen_manager._loop.draw_screen()
            return result

        def get_cursor_coords(self, size):
            return (len(self.caption) + self.edit_pos, 0)
