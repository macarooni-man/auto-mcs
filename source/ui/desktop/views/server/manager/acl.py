from ui.desktop.views.server.create import CreateServerAclScreen, CreateServerAclRuleScreen
from source.ui.desktop.views.server.manager.components import *



# Server Access Control ------------------------------------------------------------------------------------------------

class ServerAclScreen(CreateServerAclScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_taskbar = None

    def generate_menu(self, **kwargs):

        # If self._hash doesn't match, set list to ops by default
        if self._hash != constants.server_manager.current_server._hash:
            self.acl_object = constants.server_manager.current_server.acl
            self._hash = constants.server_manager.current_server._hash
            self.current_list = 'ops'

        self.show_panel = False

        self.filter_text = ""
        self.currently_filtering = False

        # Scroll list
        self.scroll_widget = RecycleViewWidget(position=(0.5, 0.455), view_class=RuleButton)
        self.scroll_layout = RecycleGridLayout(spacing=[110, -15], size_hint_y=None, padding=[60, 20, 0, 30])
        test_rule = RuleButton()

        # Bind / cleanup height on resize
        def resize_scroll(*args):
            self.scroll_widget.height = Window.height // 1.69
            rule_width = test_rule.width + self.scroll_layout.spacing[0] + 2
            rule_width = int(((Window.width // rule_width) // 1) - 2)

            self.scroll_layout.cols = rule_width
            self.scroll_layout.rows = 2 if len(self.scroll_widget.data) <= rule_width else None

            self.user_panel.x = Window.width - (self.user_panel.size_hint_max[0] * 0.93)

            # Reposition header
            for child in self.header.children:
                if child.id == "text":
                    child.halign = "left"
                    child.text_size[0] = 500
                    child.x = Window.width / 2 + 240
                    break

            self.search_label.pos_hint = {"center_x": (0.28 if Window.width < 1300 else 0.5), "center_y": 0.42}
            self.search_label.text_size = (Window.width / 3, 500)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.735}, pos=self.scroll_widget.pos,
                                       size=(self.scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.175}, pos=self.scroll_widget.pos,
                                          size=(self.scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        selector_text = "operators" if self.current_list == "ops" else "bans" if self.current_list == "bans" else "whitelist"
        self.page_selector = DropButton(selector_text, (0.5, 0.89), options_list=['operators', 'bans', 'whitelist'],
                                        input_name='ServerAclTypeInput', x_offset=-210, facing='center',
                                        custom_func=self.update_list)
        header_content = ""
        self.header = HeaderText(header_content, '', (0, 0.89), fixed_x=True, no_line=True)

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Search bar
        self.search_bar = AclInput(pos_hint={"center_x": 0.5, "center_y": 0.815})
        buttons.append(input_button('Add Rules...', (0.5, 0.815), input_name='AclInput'))

        # Whitelist toggle button
        def toggle_whitelist(boolean):
            self.acl_object.enable_whitelist(boolean)

            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                    f"Server whitelist {'en' if boolean else 'dis'}abled",
                    "shield-checkmark-outline.png" if boolean else "shield-disabled-outline.png",
                    2,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

            # Update list
            self.update_list('wl', reload_children=True, reload_panel=True)

        self.whitelist_toggle = toggle_button('whitelist', (0.5, 0.89),
                                              default_state=self.acl_object._server['whitelist'], x_offset=-395,
                                              custom_func=toggle_whitelist)

        # Legend for rule types
        self.list_header = BoxLayout(orientation="horizontal", pos_hint={"center_x": 0.5, "center_y": 0.749},
                                     size_hint_max=(400, 100))
        self.list_header.global_rule = RelativeLayout()
        self.list_header.global_rule.add_widget(
            BannerObject(size=(120, 32), color=test_rule.global_icon_color, text="global", icon="earth-sharp.png",
                         icon_side="left"))
        self.list_header.add_widget(self.list_header.global_rule)

        self.list_header.enabled_rule = RelativeLayout()
        self.list_header.enabled_rule.add_widget(
            BannerObject(size=(120, 32), color=(1, 1, 1, 1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.enabled_rule)

        self.list_header.disabled_rule = RelativeLayout()
        self.list_header.disabled_rule.add_widget(
            BannerObject(size=(120, 32), color=(1, 1, 1, 1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.disabled_rule)

        # Add blank label to the center, then load self.gen_search_results()
        self.blank_label = Label()
        self.blank_label.text = ""
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.blank_label.font_size = sp(23)
        self.blank_label.opacity = 0
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        # Lol search label idek
        self.search_label = Label()
        self.search_label.text = ""
        self.search_label.halign = "center"
        self.search_label.valign = "center"
        self.search_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.search_label.pos_hint = {"center_x": 0.28, "center_y": 0.42}
        self.search_label.font_size = sp(25)
        self.search_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.search_label)

        # Controls button
        def show_controls():

            controls_text = """This menu shows enabled rules from files like 'ops.json', and disabled rules as others who have joined. Global rules are applied to every server. Rules can be modified in a few different ways:

• Right-click a rule to view, and see more options

• Left-click a rule to toggle permission

• Press middle-mouse to toggle globally

Rules can be filtered with the search bar, and can be added with the 'Add Rules' button or by pressing 'TAB'. The visible list can be switched between operators, bans, and the whitelist from the drop-down at the top."""

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "controls",
                    "Controls",
                    controls_text,
                    (None)
                ),
                0
            )

        self.controls_button = IconButton('controls', {}, (70, 110), (None, None), 'question.png', clickable=True,
                                          anchor='right', click_func=show_controls)

        # User panel
        self.user_panel = AclRulePanel()
        self.user_panel.pos_hint = {"center_y": 0.44}

        # Append scroll view items
        self.scroll_widget.add_widget(self.scroll_layout)
        float_layout.add_widget(self.scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.page_selector)
        float_layout.add_widget(self.list_header)
        float_layout.add_widget(self.search_bar)
        float_layout.add_widget(self.whitelist_toggle)
        float_layout.add_widget(self.user_panel)

        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"{constants.server_manager.current_server.name}, Access Control"
        float_layout.add_widget(
            generate_title(f"Access Control Manager: '{constants.server_manager.current_server.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='access control')
        self.add_widget(self.menu_taskbar)

        # Add controls after taskbar because it's unclickable for some reason
        float_layout.add_widget(self.controls_button)

        # Generate page content
        self.update_list(self.current_list, reload_children=True)

        # Generate user panel info
        current_list = acl.deepcopy(self.acl_object.rules[self.current_list])
        if self.current_list == "bans":
            current_list.extend(acl.deepcopy(self.acl_object.rules['subnets']))

        if self.acl_object.displayed_rule and current_list:
            global_rules = acl.load_global_acl()
            self.acl_object.displayed_rule.acl_group = self.current_list
            rule_scope = acl.check_global_acl(global_rules, self.acl_object.displayed_rule).rule_scope
            self.update_user_panel(self.acl_object.displayed_rule.rule, rule_scope)
        else:
            self.update_user_panel(None, None)


class ServerAclRuleScreen(CreateServerAclRuleScreen):

    def generate_menu(self, **kwargs):
        # Generate buttons on page load

        class HintLabel(RelativeLayout):

            def icon_pos(self, *args):
                self.text.texture_update()
                self.icon.pos_hint = {"center_x": 0.57 - (0.005 * self.text.texture_size[0]), "center_y": 0.95}

            def __init__(self, pos, label, **kwargs):
                super().__init__(**kwargs)

                self.pos_hint = {"center_x": 0.5, "center_y": pos}
                self.size_hint_max = (100, 50)

                self.text = Label()
                self.text.id = 'text'
                self.text.size_hint = (None, None)
                self.text.markup = True
                self.text.halign = "center"
                self.text.valign = "center"
                self.text.text = "        " + label
                self.text.font_size = sp(22)
                self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
                self.text.color = (0.6, 0.6, 1, 0.55)

                self.icon = Image()
                self.icon.id = 'icon'
                self.icon.source = os.path.join(paths.ui_assets, 'icons', 'information-circle-outline.png')
                self.icon.pos_hint = {"center_y": 0.95}
                self.icon.color = (0.6, 0.6, 1, 1)

                self.add_widget(self.text)
                self.add_widget(self.icon)

                self.bind(size=self.icon_pos)
                self.bind(pos=self.icon_pos)

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        self.current_list = utility.screen_manager.get_screen("ServerAclScreen").current_list
        self.acl_object = utility.screen_manager.get_screen("ServerAclScreen").acl_object

        if self.current_list == "bans":
            header_message = "Enter usernames/IPs delimited, by, commas"
            float_layout.add_widget(
                HintLabel(0.464, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))
            float_layout.add_widget(HintLabel(0.374,
                                              "You can ban IP ranges/whitelist:   [color=#FF6666]192.168.0.0-150[/color], [color=#66FF88]!w 192.168.1.1[/color]"))
        else:
            header_message = "Enter usernames delimited, by, commas"
            float_layout.add_widget(
                HintLabel(0.425, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))

        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.72}))
        float_layout.add_widget(HeaderText(header_message, '', (0, 0.8)))
        self.acl_input = AclRuleInput(pos_hint={"center_x": 0.5, "center_y": 0.64}, text="")
        float_layout.add_widget(self.acl_input)

        buttons.append(next_button('Add Rules', (0.5, 0.24), True, next_screen='ServerAclScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"{constants.server_manager.current_server.name}, Access Control"
        list_name = "Operators" if self.current_list == "ops" else "Bans" if self.current_list == "bans" else "Whitelist"
        float_layout.add_widget(generate_title(f"Access Control Manager: Add {list_name}"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)
        self.acl_input.grab_focus()
