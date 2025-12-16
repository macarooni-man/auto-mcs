from source.ui.desktop.views.server.manager.components import *



# ACL Menu Components --------------------------------------------------------------------------------------------------

class RuleButton(FloatLayout):

    def __setattr__(self, attr, value):

        # Change attributes dynamically based on rule
        if attr == "rule" and value:
            self.text.text = value.rule.replace("!w", "")
            self.change_properties(value)

        super().__setattr__(attr, value)


    # Modifies rule attributes based on rule.list_enabled status
    def change_properties(self, rule):

        # Prevent crash from spamming the back button
        if "Acl" not in utility.screen_manager.current_screen.name:
            return

        Animation.cancel_all(self.button)
        Animation.cancel_all(self.text)
        Animation.cancel_all(self.icon)

        self.button.id = f'rule_button{"_enabled" if rule.list_enabled else ""}'
        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.button.id}.png')
        self.button.background_down   = os.path.join(paths.ui_assets, f'{self.button.id}_click.png')

        # Change color attributes
        if utility.screen_manager.current_screen.current_list == "ops":
            self.color_id = self.button.color_id = [(0, 0, 0, 0.85), (0.439, 0.839, 1, 1)] if rule.list_enabled else [(0, 0, 0, 0.85), (0.6, 0.5, 1, 1)]
            self.hover_attr = (icon_path("close-circle.png"), 'DEMOTE', (1, 0.5, 0.65, 1)) if rule.list_enabled else (icon_path("promote.png"), 'PROMOTE', (0.3, 1, 0.6, 1))
        elif utility.screen_manager.current_screen.current_list == "bans":
            if rule.rule_type == "ip":
                self.color_id = self.button.color_id = [(0, 0, 0, 0.85), (1, 0.45, 0.85, 1)] if rule.list_enabled else [(0, 0, 0, 0.85), (0.4, 0.8, 1, 1)]
            else:
                self.color_id = self.button.color_id = [(0, 0, 0, 0.85), (1, 0.5, 0.65, 1)] if rule.list_enabled else [(0, 0, 0, 0.85), (0.3, 1, 0.6, 1)]
            if rule.list_enabled:
                self.hover_attr = (icon_path("lock-open.png"), 'PARDON', (0.3, 1, 0.6, 1))
            else:
                self.hover_attr = (icon_path("close-circle.png"), 'BAN' if rule.rule_type == 'player' else 'REMOVE', (1, 0.5, 0.65, 1))
        elif utility.screen_manager.current_screen.current_list == "wl":
            if utility.screen_manager.current_screen.acl_object._server['whitelist']:
                self.color_id = self.button.color_id = [(0, 0, 0, 0.85), (0.3, 1, 0.6, 1)] if rule.list_enabled else [(0, 0, 0, 0.85), (1, 0.5, 0.65, 1)]
            else:
                self.color_id = self.button.color_id = [(0, 0, 0, 0.85), (0.3, 1, 0.6, 1)] if rule.list_enabled else [(0, 0, 0, 0.85), (0.7, 0.7, 0.7, 1)]
            self.hover_attr = (icon_path("close-circle.png"), 'RESTRICT', (1, 0.5, 0.65, 1)) if rule.list_enabled else (icon_path("checkmark-circle-sharp.png"), 'PERMIT', (0.3, 1, 0.6, 1))

        new_color_id = (self.color_id[1][0], self.color_id[1][1], self.color_id[1][2], 1 if rule.list_enabled else 0.95)
        self.color_id[1] = new_color_id
        self.button.color_id[1] = new_color_id
        self.text.color = constants.brighten_color(new_color_id, 0.2)
        self.icon.color = constants.brighten_color(new_color_id, 0.2)
        self.icon.source = icon_path("earth-sharp.png")
        self.button.background_color = new_color_id


        # Change scope attributes
        if rule.rule_scope == "global":
            self.text.pos_hint["center_x"] = 0.5 + round(len(self.text.text) * 0.01, 2)
            self.icon.opacity = 1
            self.icon.color = self.global_icon_color
            if rule.rule_type == "player" or "/" in rule.rule:
                self.text.font_size = sp(19 - (0 if len(self.text.text) < 11 else (len(self.text.text) // 5)))

        else:
            self.text.pos_hint["center_x"] = 0.5
            self.icon.opacity = 0
            self.icon.color = self.color_id[1]
            if rule.rule_type == "player" or "/" in rule.rule:
                self.text.font_size = sp(19 - (0 if len(self.text.text) < 11 else (len(self.text.text) // 7)))

        if rule.rule_type == "ip" and "/" not in rule.rule:
            self.text.font_size = sp(19)

        self.original_font_size = self.text.font_size


    def highlight(self, original_color, original_text_color, original_hover_color):
        self.button.background_color = constants.brighten_color(original_hover_color, -0.15)
        self.text.color = constants.brighten_color(original_hover_color, -0.15)
        Animation(background_color=original_color, duration=1).start(self.button)
        Animation(color=original_text_color, duration=1).start(self.text)


    def __init__(self, name='', icon_name=None, width=None, icon_offset=None, auto_adjust_icon=False, **kwargs):
        super().__init__(**kwargs)

        position = (0.5, 0.5)
        self.size_hint_max_y = dp(60)
        self.rule = None
        self.id = 'rule_button'
        self.enabled = True
        self.original_font_size = None
        self.action_text = ''


        # Hover button object
        self.button = HoverButton()

        def on_enter(*args):

            Animation.cancel_all(self.button)
            Animation.cancel_all(self.text)
            Animation.cancel_all(self.icon)

            if not self.button.ignore_hover:
                self.text.font_size = sp(18)

                if self.rule.rule_scope == "global":
                    self.icon.source = icon_path("earth-strike.png")
                    self.text.text = translate("LOCALIZE")
                    self.action_text = "LOCALIZE"
                    self.button.background_color = self.global_icon_color

                else:
                    self.icon.source = self.hover_attr[0]
                    self.text.text = "   " + translate(self.hover_attr[1])
                    self.action_text = self.hover_attr[1]
                    self.button.background_color = self.hover_attr[2]
                    Animation(opacity=1, duration=0.05).start(self.icon)

                animate_button(self.button, image=os.path.join(paths.ui_assets, f'{self.button.id}_hover.png'), color=self.button.color_id[0], hover_action=True)

        def on_leave(*args):

            Animation.cancel_all(self.button)
            Animation.cancel_all(self.text)

            if not self.button.ignore_hover:
                self.text.font_size = self.original_font_size
                self.text.text = self.rule.rule.replace("!w", "")
                new_color_id = (self.color_id[1][0], self.color_id[1][1], self.color_id[1][2], 1 if self.rule.list_enabled else 0.95)
                animate_button(self.button, image=os.path.join(paths.ui_assets, f'{self.button.id}.png'), color=constants.brighten_color(self.button.color_id[1], 0.2), hover_action=False, _new_color=new_color_id)
                Animation.cancel_all(self.icon)
                if self.rule.rule_scope == "global":
                    Animation(color=self.global_icon_color, duration=0.1).start(self.icon)
                    self.icon.source = icon_path("earth-sharp.png")
                else:
                    Animation(opacity=0, duration=0.05).start(self.icon)

        def click_func(button_pressed=None, *args):

            if not button_pressed or not isinstance(button_pressed, str):
                button_pressed = self.button.button_pressed.lower().strip()

            button_text = self.action_text.lower().strip()
            current_list = utility.screen_manager.current_screen.current_list.lower().strip()
            acl_object = utility.screen_manager.current_screen.acl_object
            original_name = self.rule.rule
            filtered_name = self.rule.rule.replace("!w", "").replace("!g", "").strip()
            original_hover_attr = self.hover_attr
            new_scope = self.rule.rule_scope
            banner_text = ""
            reload_page = False
            localize = False


            # Left click on button (Local)
            if button_pressed == "left" and self.rule.rule_scope == "local":

                # Modify 'ops' list
                if current_list == "ops" and button_text in ['promote', 'demote']:
                    acl_object.op_player(self.rule.rule, remove=(button_text == "demote"))
                    banner_text = f"'${filtered_name}$' was {'demoted' if (button_text == 'demote') else 'promoted'}"
                    reload_page = True

                # Modify 'bans' list
                elif current_list == "bans" and button_text in ['ban', 'pardon', 'remove']:
                    acl_object.ban_player(self.rule.rule, remove=(button_text == "pardon") or ("!w" in self.rule.rule))

                    if button_text == "pardon":
                        try: ip_addr = acl.get_uuid(self.rule.rule)['latest-ip'].split(":")[0].strip()
                        except KeyError: ip_addr = ""

                        if ip_addr:
                            # Whitelist IP if it's still in the rule list
                            if ip_addr in acl.gen_iplist(acl_object.rules['subnets']):
                                acl_object.ban_player(f"!w{ip_addr}", remove=False)

                    banner_text = f"'${filtered_name}$' was removed" if button_text == 'remove' else f"'{filtered_name}' is {'pardoned' if (button_text == 'pardon') else 'banned'}"
                    reload_page = True

                # Modify 'wl' list
                elif current_list == "wl" and button_text in ['permit', 'restrict']:
                    acl_object.whitelist_player(self.rule.rule, remove=(button_text == "restrict"))
                    banner_text = f"'${filtered_name}$' is {'restricted' if (button_text == 'restrict') else 'permitted'}"
                    reload_page = True


            # Left click on button (global)
            elif button_pressed == "left" and self.rule.rule_scope == "global" and button_text == "localize":
                acl_object.add_global_rule(self.rule.rule, current_list, remove=True)
                original_hover_attr = (
                    icon_path("earth-strike.png"),
                    original_hover_attr[1],
                    self.color_id[1]
                )
                banner_text = f"'${filtered_name}$' rule is now locally applied"
                localize = True
                new_scope = "local"
                reload_page = True


            # Middle click on button
            elif button_pressed == "middle":
                acl_object.add_global_rule(self.rule.rule, current_list, remove=(button_text == 'localize'))
                original_hover_attr = (
                    icon_path(f"earth-{'strike' if (self.rule.rule_scope == 'global') else 'sharp'}.png"),
                    original_hover_attr[1],
                    self.global_icon_color if (self.rule.rule_scope == 'local') else self.color_id[1]
                )
                banner_text = f"'${filtered_name}$' is now {'local' if (self.rule.rule_scope == 'global') else 'global'}ly applied"
                localize    = self.rule.rule_scope == "global"
                new_scope   = "local" if localize else "global"
                reload_page = True



            if reload_page:
                # print(button_text, button_pressed, current_list)

                # If rule localized, enable on current list
                if localize:
                    if current_list == "ops":    acl_object.op_player(self.rule.rule)
                    elif current_list == "bans": acl_object.ban_player(self.rule.rule)
                    elif current_list == "wl":   acl_object.whitelist_player(self.rule.rule)


                self.button.on_leave()
                self.change_properties(self.rule)
                self.button.state = "normal"

                Animation.cancel_all(self.button)
                Animation.cancel_all(self.text)
                Animation.cancel_all(self.icon)

                utility.screen_manager.current_screen.update_list(current_list, reload_children=False)

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        original_hover_attr[2],
                        banner_text,
                        original_hover_attr[0],
                        2,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

                def trigger_highlight(*args):
                    for rule_button in utility.screen_manager.current_screen.scroll_layout.children:

                        if rule_button.rule.rule == original_name:
                            rule_button.highlight(rule_button.button.background_color, rule_button.text.color, original_hover_attr[2])

                        else:
                            rule_button.button.on_leave()
                            Animation.cancel_all(rule_button.button)
                            Animation.cancel_all(rule_button.text)
                            Animation.cancel_all(rule_button.icon)
                            rule_button.change_properties(rule_button.rule)

                        rule_button.button.ignore_hover = False

                Clock.schedule_once(trigger_highlight, 0)

            # Update display rule regardless of button pressed
            utility.screen_manager.current_screen.update_user_panel(self.rule.rule, new_scope)



        self.button.on_enter = on_enter
        self.button.on_leave = on_leave
        self.button.bind(on_press=click_func)
        self.button.id = 'rule_button'
        self.color_id = self.button.color_id = [(0.03, 0.03, 0.03, 1), (1, 1, 1, 1)]  # [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]
        self.hover_attr = (icon_path('close-circle.png'), 'hover text', (1, 1, 1, 1)) # Icon, Text, Hover color
        self.global_icon_color = (0.953, 0.929, 0.38, 1)

        self.button.size_hint = (None, None)
        self.button.size = (dp(190 if not width else width), self.size_hint_max_y)
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (-3, -3, -3, -3)
        self.button.background_normal = os.path.join(paths.ui_assets, 'rule_button.png')
        self.button.background_down = os.path.join(paths.ui_assets, 'rule_button_click.png')
        self.button.always_release = True

        self.text = Label()
        self.text.__translate__ = False
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = name
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = self.color_id[1]


        # Button click behavior
        self.button.on_release = functools.partial(button_action, name, self.button)
        self.add_widget(self.button)


        # Icon thingy
        self.icon = Image()
        self.icon.id = 'icon'
        self.icon.source = icon_path("earth-sharp.png") if not icon_name else icon_path(icon_name)
        self.icon.size = (25, 25)
        self.icon.size_hint = (None, None)
        self.icon.opacity = 0
        self.icon.color = self.color_id[1]
        self.icon.pos_hint = {"center_x": -0.2, "center_y": 0.5}


        self.add_widget(self.icon)
        self.add_widget(self.text)


class AclRulePanel(RelativeLayout):

    def __init__(self, **kw):
        super().__init__(**kw)

        class HeaderLabel(Label):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint = (None, None)
                self.markup = True
                self.font_size = sp(22)
                self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
                self.color = (0.6, 0.6, 1, 1)

        class ParagraphLabel(Label, HoverBehavior):

            def on_mouse_pos(self, *args):

                if "AclScreen" in utility.screen_manager.current_screen.name:

                    try: super().on_mouse_pos(*args)
                    except: pass

                    if self.text.count(".") > 3 and "IP" in self.text:
                        rel_y = args[1][1] - utility.screen_manager.current_screen.user_panel.y
                        if self.hovered and rel_y < 190:
                            self.on_leave()
                            self.hovered = False


            # Hover stuffies
            def on_enter(self, *args):

                # Change size of IP text
                if self.text.count(".") > 3 and "IP" in self.text:
                    rel_y = self.border_point[1] - utility.screen_manager.current_screen.user_panel.y
                    if rel_y < 190:
                        self.hovered = False
                        return None

                if self.copyable:
                    self.outline_width = 0
                    self.outline_color = constants.brighten_color(self.color, 0.05)
                    Animation(outline_width=1, duration=0.03).start(self)


            def on_leave(self, *args):

                if self.copyable:
                    Animation.stop_all(self)
                    self.outline_width = 0


            # Normal stuffies
            def on_ref_press(self, *args):
                if not self.disabled:

                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (0.85, 0.65, 1, 1),
                            "Copied text to clipboard",
                            "link-sharp.png",
                            2,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

                    Clipboard.copy(re.sub(r"\[.*?\]","",self.text))


            def ref_text(self, *args):

                self.copyable = not ((translate("unknown") in self.text.lower()) or (translate("online") in self.text.lower()) or (translate("access") in self.text.lower()))

                if '[ref=' not in self.text and '[/ref]' not in self.text and self.copyable:
                    self.text = f'[ref=none]{self.text}[/ref]'
                elif '[/ref]' in self.text:
                    self.text = self.text.replace("[/ref]","") + "[/ref]"

                self.texture_update()
                self.size = self.texture_size

                if self.text.count(".") > 3 and "IP" in self.text:
                    self.width = self.texture_size[0] / 1.5


            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint = (None, None)
                self.markup = True
                self.font_size = sp(18)
                self.copyable = True
                self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')
                self.default_color = (0.6, 0.6, 1, 1)
                self.color = self.default_color
                self.bind(text=self.ref_text)


        self.color_dict = {
            "blue":    "#70E6FF",
            "red":     "#FF8793",
            "green":   "#4CFF99",
            "white":   "#FFFFFF",
            "gray":    "#A0A0A0",
            "yellow":  "#F3ED61",
            "purple":  "#A699FF"
        }


        self.displayed_type = ""
        self.displayed_scope = "local"

        # User panel (I'm sorry in advance)
        # <editor-fold desc="User Panel SUFFERING">
        self.pos_hint = {"center_y": 0.42}
        self.size_hint_max = (500, 600)

        # Background image
        self.background = Image()
        self.background.id = 'background'
        self.background.source = os.path.join(paths.ui_assets, 'user_panel.png')
        self.background.color = (0.65, 0.6, 1, 1)
        self.background.opacity = 0

        # Label when no rule is displayed
        self.blank_label = Label()
        self.blank_label.id = 'blank_label'
        self.blank_label.text = "Right-click a rule to view"
        self.blank_label.text_size[0] = self.size_hint_max[0] * 0.7
        self.blank_label.halign = "center"
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.blank_label.font_size = sp(26)
        self.blank_label.color = (0.6, 0.6, 1, 0.4)
        self.blank_label.opacity = 0

        # Drop down options button
        self.options = DropButton('OPTIONS', (0.5, 0.192), options_list=['operators', 'bans', 'whitelist'], input_name='ServerAclOptionsInput', x_offset=-33, facing='center', custom_func=self.modify_rule, change_text=False)
        self.add_widget(self.options)


        # Player Layout
        # <editor-fold desc="Player Layout Widgets">
        self.player_layout = RelativeLayout()
        self.player_layout.id = 'player_layout'

        self.player_layout.header_icon = Image()
        self.player_layout.header_icon.source = icon_path('person-circle-sharp.png')
        self.player_layout.header_icon.allow_stretch = True
        self.player_layout.header_icon.size_hint_max = (36, 36)
        self.player_layout.header_icon.pos_hint = {"center_x": 0.5, "center_y": 0.808}
        self.player_layout.add_widget(self.player_layout.header_icon)

        # Make this copyable text
        self.player_layout.name_label = HeaderLabel()
        self.player_layout.name_label.__translate__ = False
        self.player_layout.name_label.pos_hint = {"center_x": 0.54, "center_y": 0.81}
        self.player_layout.name_label.font_size = sp(25)
        self.player_layout.add_widget(self.player_layout.name_label)

        self.player_layout.online_icon = Image()
        self.player_layout.online_icon.source = icon_path('radio-button-off-sharp.png')
        self.player_layout.online_icon.allow_stretch = True
        self.player_layout.online_icon.size_hint_max = (15, 15)
        self.player_layout.online_icon.pos_hint = {"center_x": 0.5, "center_y": 0.752}
        self.player_layout.add_widget(self.player_layout.online_icon)

        self.player_layout.online_label = ParagraphLabel()
        self.player_layout.online_label.font_size = sp(19)
        self.player_layout.online_label.pos_hint = {"center_x": 0.523, "center_y": 0.755}
        self.player_layout.add_widget(self.player_layout.online_label)

        self.player_layout.uuid_header = HeaderLabel()
        self.player_layout.uuid_header.__translate__ = False
        self.player_layout.uuid_header.pos_hint = {"center_x": 0.5, "center_y": 0.66}
        self.player_layout.add_widget(self.player_layout.uuid_header)

        # Make this copyable text
        self.player_layout.uuid_label = ParagraphLabel()
        self.player_layout.uuid_label.__translate__ = False
        self.player_layout.uuid_label.pos_hint = {"center_x": 0.5, "center_y": 0.619}
        self.player_layout.add_widget(self.player_layout.uuid_label)

        self.player_layout.ip_header = HeaderLabel()
        self.player_layout.ip_header.__translate__ = False
        self.player_layout.ip_header.pos_hint = {"center_x": 0.28, "center_y": 0.54}
        self.player_layout.add_widget(self.player_layout.ip_header)

        # Make this copyable text
        self.player_layout.ip_label = ParagraphLabel()
        self.player_layout.ip_label.__translate__ = False
        self.player_layout.ip_label.font_size = sp(20)
        self.player_layout.ip_label.pos_hint = {"center_x": 0.28, "center_y": 0.499}
        self.player_layout.add_widget(self.player_layout.ip_label)

        self.player_layout.geo_header = HeaderLabel()
        self.player_layout.geo_header.__translate__ = False
        self.player_layout.geo_header.pos_hint = {"center_x": 0.7, "center_y": 0.54}
        self.player_layout.add_widget(self.player_layout.geo_header)

        self.player_layout.geo_label = ParagraphLabel()
        self.player_layout.geo_label.__translate__ = False
        self.player_layout.geo_label.halign = "center"
        self.player_layout.geo_label.pos_hint = {"center_x": 0.7, "center_y": 0.499}
        self.player_layout.add_widget(self.player_layout.geo_label)

        self.player_layout.access_header = HeaderLabel()
        self.player_layout.access_header.pos_hint = {"center_x": 0.5, "center_y": 0.4}
        self.player_layout.access_header.font_size = sp(20)
        self.player_layout.add_widget(self.player_layout.access_header)

        self.player_layout.access_label = ParagraphLabel()
        self.player_layout.access_label.halign = "left"
        self.player_layout.access_label.valign = "top"
        self.player_layout.access_label.text_size = (250, 300)
        self.player_layout.access_label.font_size = sp(19)
        self.player_layout.access_label.line_height = sp(1.4)
        self.player_layout.access_label.pos_hint = {"center_x": 0.465, "center_y": 0.11}
        self.player_layout.add_widget(self.player_layout.access_label)

        self.player_layout.access_line_1 = Image()
        self.player_layout.access_line_1.size_hint_max = (35, 35)
        self.player_layout.access_line_1.pos_hint = {"center_x": 0.165, "center_y": 0.29}
        self.player_layout.access_line_1.allow_stretch = True
        self.player_layout.access_line_1.source = os.path.join(paths.ui_assets, "access_active.png")
        self.player_layout.add_widget(self.player_layout.access_line_1)

        self.player_layout.access_line_2 = Image()
        self.player_layout.access_line_2.size_hint_max = (35, 35)
        self.player_layout.access_line_2.pos_hint = {"center_x": 0.165, "center_y": 0.24}
        self.player_layout.access_line_2.allow_stretch = True
        self.player_layout.access_line_2.source = os.path.join(paths.ui_assets, "access_active.png")
        self.player_layout.add_widget(self.player_layout.access_line_2)

        self.player_layout.access_line_3 = Image()
        self.player_layout.access_line_3.size_hint_max = (35, 35)
        self.player_layout.access_line_3.pos_hint = {"center_x": 0.165, "center_y": 0.19}
        self.player_layout.access_line_3.allow_stretch = True
        self.player_layout.access_line_3.source = os.path.join(paths.ui_assets, "access_active.png")
        self.player_layout.add_widget(self.player_layout.access_line_3)

        self.player_layout.access_icon = Image()
        self.player_layout.access_icon.size_hint_max = (30, 30)
        self.player_layout.access_icon.pos_hint = {"center_x": 0.165, "center_y": 0.338}
        self.player_layout.add_widget(self.player_layout.access_icon)
        # </editor-fold>


        # IP Layout
        # <editor-fold desc="IP Layout Widgets">
        self.ip_layout = RelativeLayout()
        self.ip_layout.id = 'ip_layout'

        self.ip_layout.header_icon = Image()
        self.ip_layout.header_icon.source = icon_path('ethernet.png')
        self.ip_layout.header_icon.allow_stretch = True
        self.ip_layout.header_icon.size_hint_max = (36, 36)
        self.ip_layout.header_icon.pos_hint = {"center_x": 0.5, "center_y": 0.808}
        self.ip_layout.add_widget(self.ip_layout.header_icon)

        # Make this copyable text
        self.ip_layout.name_label = HeaderLabel()
        self.ip_layout.name_label.__translate__ = False
        self.ip_layout.name_label.pos_hint = {"center_x": 0.54, "center_y": 0.81}
        self.ip_layout.name_label.font_size = sp(25)
        self.ip_layout.add_widget(self.ip_layout.name_label)

        self.ip_layout.type_header = HeaderLabel()
        self.ip_layout.type_header.pos_hint = {"center_x": 0.28, "center_y": 0.64}
        self.ip_layout.add_widget(self.ip_layout.type_header)

        # Make ip copyable text
        self.ip_layout.type_label = ParagraphLabel()
        self.ip_layout.type_label.__translate__ = False
        self.ip_layout.type_label.font_size = sp(20)
        self.ip_layout.type_label.pos_hint = {"center_x": 0.28, "center_y": 0.598}
        self.ip_layout.add_widget(self.ip_layout.type_label)

        self.ip_layout.affected_header = HeaderLabel()
        self.ip_layout.affected_header = HeaderLabel()
        self.ip_layout.affected_header.pos_hint = {"center_x": 0.7, "center_y": 0.64}
        self.ip_layout.add_widget(self.ip_layout.affected_header)

        # Make ip copyable text
        self.ip_layout.affected_label = ParagraphLabel()
        self.ip_layout.affected_label.__translate__ = False
        self.ip_layout.affected_label.halign = "center"
        self.ip_layout.affected_label.font_size = sp(20)
        self.ip_layout.affected_label.pos_hint = {"center_x": 0.7, "center_y": 0.598}
        self.ip_layout.add_widget(self.ip_layout.affected_label)

        self.ip_layout.network_header = HeaderLabel()
        self.ip_layout.network_header.pos_hint = {"center_x": 0.5, "center_y": 0.458}
        self.ip_layout.add_widget(self.ip_layout.network_header)

        # Make IP copyable text
        self.ip_layout.network_label = ParagraphLabel()
        self.ip_layout.network_label.__translate__ = False
        self.ip_layout.network_label.halign = "center"
        self.ip_layout.network_label.valign = "top"
        self.ip_layout.network_label.text_size = (400, 150)
        self.ip_layout.network_label.font_size = sp(20)
        self.ip_layout.network_label.line_height = sp(1.4)
        self.ip_layout.network_label.pos_hint = {"center_x": 0.5, "center_y": 0.3}
        self.ip_layout.add_widget(self.ip_layout.network_label)
        # </editor-fold>


        for widget in self.player_layout.children: utility.hide_widget(widget, True)
        for widget in self.ip_layout.children:     utility.hide_widget(widget, True)

        self.add_widget(self.background)
        self.add_widget(self.blank_label)
        self.add_widget(self.player_layout)
        self.add_widget(self.ip_layout)
        # </editor-fold>


    # Actually updates data in panel based off of rule
    def update_panel(self, displayed_rule: acl.AclRule, rule_scope: str):

        self.displayed_scope = rule_scope
        filtered_name = displayed_rule.rule.replace("!g", "").replace("!w", "")
        panel_options = []

        # Player layout ------------------------------------------------------------------------------------------------
        if displayed_rule.rule_type == "player":

            # Effective access colors
            if displayed_rule.display_data['effective_access'] == translate("Operator access"):
                widget_color = self.color_dict['blue']
                self.player_layout.access_icon.source = icon_path('promote.png')
            elif displayed_rule.display_data['effective_access'] == translate("No access"):
                widget_color = self.color_dict['red']
                self.player_layout.access_icon.source = icon_path('close-circle-outline.png')
            else:
                widget_color = self.color_dict['purple']
                self.player_layout.access_icon.source = icon_path('chevron-up-circle-sharp.png')


            if self.displayed_type != "player":
                for widget in self.player_layout.children:
                    utility.hide_widget(widget, False)
                for widget in self.ip_layout.children:
                    utility.hide_widget(widget, True)


            # Change panel attributes ----------------------------------------------------------------------------------


            # Change name in header
            self.player_layout.name_label.text = filtered_name
            self.player_layout.name_label.texture_update()
            texture_size = 0.001 * self.player_layout.name_label.texture_size[0]
            self.player_layout.header_icon.pos_hint = {"center_x": 0.485 - texture_size, "center_y": 0.808}

            # Change icon in header
            # self.player_layout.header_icon.source = os.path.join(paths.gui_assets, 'steve.png')
            # def update_source(*a):
            #     source = manager.get_player_head(filtered_name)
            #     def main_thread(*b):
            #         if self.player_layout.name_label.text == filtered_name:
            #             self.player_layout.header_icon.source = source
            #     Clock.schedule_once(main_thread, 0)
            # dTimer(0, update_source).start()


            # Online status
            if constants.server_manager.current_server and constants.server_manager.current_server.user_online(displayed_rule.rule):
                self.player_layout.online_label.color = self.color_dict['green']
                self.player_layout.online_icon.color = self.color_dict['green']
                self.player_layout.online_label.text = "Currently online"
                self.player_layout.online_icon.source = icon_path('radio-button-on-sharp.png')

            else:
                self.player_layout.online_label.color = self.color_dict['gray']
                self.player_layout.online_icon.color = self.color_dict['gray']
                try:
                    last_login = (dt.now() - dt.strptime(displayed_rule.extra_data['latest-login'], '%Y-%m-%d %H:%M:%S'))
                    d = {"days": last_login.days}
                    d["years"], rem = divmod(last_login.days, 365)
                    d["months"], rem = divmod(last_login.days, 30)
                    d["hours"], rem = divmod(last_login.seconds, 3600)
                    d["minutes"], d["seconds"] = divmod(rem, 60)

                    if d['years'] > 0:
                        time_formatted = (f"{d['years']} {translate('year' + ('s' if d['years'] > 1 else ''))} " if d['years'] > 0 else "")
                    elif d['months'] > 0:
                        time_formatted = (f"{d['months']} {translate('month' + ('s' if d['months'] > 1 else ''))} " if d['months'] > 0 else "")
                    else:
                        time_formatted = (f"{d['days']}d " if d['days'] > 0 else "") + (f"{d['hours']}h " if d['hours'] > 0 else "") + (f"{d['minutes']}m " if d['minutes'] > 0 and d['days'] == 0 else "")

                    if not time_formatted:
                        time_formatted = 'seconds '

                    self.player_layout.online_label.text = f"Last online ${time_formatted}$ago"

                except ValueError:
                    self.player_layout.online_label.text = "Last online unknown"

                self.player_layout.online_icon.source = icon_path('radio-button-off-sharp.png')

            self.player_layout.online_label.texture_update()
            texture_size = 0.001 * self.player_layout.online_label.texture_size[0]
            self.player_layout.online_icon.pos_hint = {"center_x": 0.492 - texture_size, "center_y": 0.752}


            # Change UUID
            self.player_layout.uuid_label.text = displayed_rule.extra_data['uuid']


            # Change last IP
            if displayed_rule.extra_data['latest-ip'].startswith("127."):
                self.player_layout.ip_label.text = displayed_rule.extra_data['latest-ip']
            else:
                self.player_layout.ip_label.text = displayed_rule.extra_data['latest-ip'].split(":")[0]


            # Change location
            if " - " in displayed_rule.extra_data['ip-geo']:
                self.player_layout.geo_label.text = displayed_rule.extra_data['ip-geo'].replace(" - ", "\n")
                self.player_layout.geo_label.pos_hint = {"center_x": 0.7, "center_y": 0.48}
            else:
                self.player_layout.geo_label.text = displayed_rule.extra_data['ip-geo']
                self.player_layout.geo_label.pos_hint = {"center_x": 0.7, "center_y": 0.499}
            self.player_layout.geo_label.font_size = sp(20) if len(displayed_rule.extra_data['ip-geo']) < 15 else sp(18)


            # Change effective access
            very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["bold"])
            final_text = f"[color={widget_color}][font={very_bold_font}][size={round(sp(21))}]{displayed_rule.display_data['effective_access']}[/size][/font][/color]"
            banned = False

            # Display ban data
            if displayed_rule.display_data['ip_ban'] and displayed_rule.display_data['ban']:
                final_text += f"\n[color={self.color_dict['red']}]{translate('Banned IP & user')}[/color]"
                banned = True
            elif displayed_rule.display_data['ip_ban']:
                final_text += f"\n[color={self.color_dict['red']}]{translate('Banned IP')}[/color]"
                banned = True
            elif displayed_rule.display_data['ban']:
                final_text += f"\n[color={self.color_dict['red']}]{translate('Banned user')}[/color]"
                banned = True
            else:
                final_text += "\n"

            # Display OP data
            final_text += (f"\n[color={self.color_dict['blue']}]{translate('Operator')}[/color]" if displayed_rule.display_data['op'] else "\n")

            # Whitelist data
            if utility.screen_manager.current_screen.acl_object._server['whitelist']:
                self.player_layout.access_line_3.opacity = 1
                if constants.app_config.locale == 'en':
                    final_text += ("\n[color=" + (f"{self.color_dict['green']}]Whitelisted" if displayed_rule.display_data['wl'] else f"{self.color_dict['red']}]Not whitelisted") + "[/color]")
                else:
                    final_text += ("\n[color=" + (f"{self.color_dict['green']}]{translate('Allowed')}" if displayed_rule.display_data['wl'] else f"{self.color_dict['red']}]{translate('Denied')}") + "[/color]")
            else:
                self.player_layout.access_line_3.opacity = 0
                self.player_layout.access_line_1.source = os.path.join(paths.ui_assets, "access_active.png")
                self.player_layout.access_line_2.source = os.path.join(paths.ui_assets, "access_active.png")
                self.player_layout.access_line_3.source = os.path.join(paths.ui_assets, "access_active.png")

            self.player_layout.access_label.text = final_text


            # Adjust graphic data for access
            if utility.screen_manager.current_screen.acl_object._server['whitelist']:
                if displayed_rule.display_data['wl']:
                    self.player_layout.access_line_1.source = os.path.join(paths.ui_assets, "access_active.png")
                    self.player_layout.access_line_2.source = os.path.join(paths.ui_assets, "access_active.png")
                    self.player_layout.access_line_3.source = os.path.join(paths.ui_assets, "access_active.png")
                else:
                    self.player_layout.access_line_1.source = os.path.join(paths.ui_assets, "access_inactive.png")
                    self.player_layout.access_line_2.source = os.path.join(paths.ui_assets, "access_inactive.png")
                    self.player_layout.access_line_3.source = os.path.join(paths.ui_assets, "access_inactive.png")

                    if displayed_rule.display_data['op']:
                        self.player_layout.access_line_1.source = os.path.join(paths.ui_assets, "access_active.png")
                        self.player_layout.access_line_2.source = os.path.join(paths.ui_assets, "access_active.png")

            if banned:
                self.player_layout.access_line_1.source = os.path.join(paths.ui_assets, "access_inactive.png")
            elif displayed_rule.display_data['wl']:
                self.player_layout.access_line_1.source = os.path.join(paths.ui_assets, "access_active.png")


            # Set header names
            self.player_layout.uuid_header.text = "UUID"
            self.player_layout.ip_header.text = "IP"
            self.player_layout.geo_header.text = "Location"
            self.player_layout.access_header.text = f"Access to '${utility.screen_manager.current_screen.acl_object._server['name']}$':"



            # Change colors based on rule access attributes ------------------------------------------------------------
            self.background.color = widget_color
            for widget in self.player_layout.children:

                if widget is self.player_layout.online_label or widget is self.player_layout.online_icon:
                    continue

                if widget.__class__.__name__ in ['Image', 'HeaderLabel']:
                    if widget in [self.player_layout.header_icon, self.player_layout.name_label]:
                        widget.color = constants.brighten_color(widget_color, 0.12)
                    elif widget in [self.player_layout.access_icon, self.player_layout.access_line_1, self.player_layout.access_line_2, self.player_layout.access_line_3]:
                        widget.color = constants.brighten_color(widget_color, 0.2)
                    else:
                        widget.color = constants.brighten_color(widget_color, 0.34)

                elif widget.__class__.__name__ == "ParagraphLabel":
                    widget.color = self.color_dict['gray'] if translate("unknown") in widget.text.lower() else widget.default_color



            # Generate panel options -----------------------------------------------------------------------------------
            if utility.screen_manager.current_screen.current_list == "ops":
                panel_options.append("demote" if displayed_rule.display_data['op'] else "promote")

            elif utility.screen_manager.current_screen.current_list == "bans":
                if displayed_rule.display_data['ip_ban'] and displayed_rule.display_data['ban']:
                    panel_options.append("pardon IP & user")
                elif displayed_rule.display_data['ip_ban']:
                    if not displayed_rule.display_data['ban']:
                        panel_options.append("ban user")
                    panel_options.append("pardon IP")
                elif displayed_rule.display_data['ban']:
                    panel_options.append("pardon user")
                else:
                    panel_options.append("ban user")

                if displayed_rule.extra_data['latest-ip'] != "Unknown" and not displayed_rule.display_data['ip_ban']:
                    panel_options.append("ban IP")

            elif utility.screen_manager.current_screen.current_list == "wl":
                panel_options.append("restrict" if displayed_rule.display_data['wl'] else "permit")

            panel_options.append("localize rule" if rule_scope == "global" else "globalize rule")


        # IP Layout ----------------------------------------------------------------------------------------------------
        else:

            # Effective access colors
            if "whitelist" in displayed_rule.display_data['rule_info'].lower():
                widget_color = self.color_dict['blue']
            else:
                widget_color = self.color_dict['red']

            if not utility.screen_manager.current_screen.acl_object.rule_in_acl(displayed_rule.rule, 'subnets'):
                displayed_rule.display_data['rule_info'] = "Unaffected " + displayed_rule.display_data['rule_info'].split(" ")[0]
                displayed_rule.rule = displayed_rule.rule.replace("!w", "").replace("!g", "").strip()
                utility.screen_manager.current_screen.displayed_rule = displayed_rule
                widget_color = self.color_dict['purple']

            if self.displayed_type != "ip":
                for widget in self.player_layout.children:
                    utility.hide_widget(widget, True)
                for widget in self.ip_layout.children:
                    utility.hide_widget(widget, False)



            # Change panel attributes ----------------------------------------------------------------------------------


            # Change IP address in header
            self.ip_layout.name_label.text = filtered_name
            self.ip_layout.name_label.texture_update()
            texture_size = 0.001 * self.ip_layout.name_label.texture_size[0]
            self.ip_layout.header_icon.pos_hint = {"center_x": 0.485 - texture_size, "center_y": 0.808}


            # Change rule type
            self.ip_layout.type_label.text = displayed_rule.display_data['rule_info']


            # Change affected users
            users = displayed_rule.display_data['affected_users']
            if users == 0:
                self.ip_layout.affected_label.text = f"0 {translate('users')}"
                self.ip_layout.affected_label.color = self.color_dict['gray']
            else:
                self.ip_layout.affected_label.text = f"{users:,} {translate('user' + 's' if users > 1 else '')}"
                self.ip_layout.affected_label.color = self.color_dict['green'] if "whitelist" in displayed_rule.display_data['rule_info'].lower() else self.color_dict['red']


            # Change network info
            ip_count = acl.count_subnet(displayed_rule.rule.replace("!w", "").replace("!g", "").strip())
            ips = displayed_rule.display_data['ip_range'].split(" - ")
            self.ip_layout.network_label.text = f"{ips[0]} [color=#696997]-[/color] {ips[1]}"
            self.ip_layout.network_label.text += f"\n[color={self.color_dict['gray']}]{displayed_rule.display_data['subnet_mask']}"
            self.ip_layout.network_label.text += f"  ({ip_count:,} IP{'s' if ip_count > 1 else ''})[/color]"



            # Set header names
            self.ip_layout.type_header.text = "Rule Type"
            self.ip_layout.affected_header.text = "Affected"
            self.ip_layout.network_header.text = "Network"


            # Change colors based on rule access attributes ------------------------------------------------------------
            self.background.color = widget_color
            for widget in self.ip_layout.children:
                if widget.__class__.__name__ in ['Image', 'HeaderLabel']:
                    if widget in [self.ip_layout.header_icon, self.ip_layout.name_label]:
                        widget.color = constants.brighten_color(widget_color, 0.12)
                    else:
                        widget.color = constants.brighten_color(widget_color, 0.34)


            # Generate panel options -----------------------------------------------------------------------------------
            if utility.screen_manager.current_screen.current_list == "bans":
                after_text = 'subnet' if 'subnet' in displayed_rule.display_data['rule_info'].lower() else 'IP'
                if "unaffected" in displayed_rule.display_data['rule_info'].lower():
                    panel_options.append(f"ban {after_text}")
                    panel_options.append(f"whitelist {after_text}")

                else:
                    if "whitelist" in displayed_rule.display_data['rule_info'].lower():
                        panel_options.append("remove rule")
                        panel_options.append(f"ban {after_text}")
                    else:
                        panel_options.append(f"pardon {after_text}")
                        panel_options.append(f"whitelist {after_text}")

                    panel_options.append("localize rule" if rule_scope == "global" else "globalize rule")

        panel_options = panel_options if panel_options else ['no options']
        self.options.change_options(panel_options)
        self.displayed_type = displayed_rule.rule_type


    # Changes rule attributes from options drop-down
    def modify_rule(self, option: str):

        current_list = utility.screen_manager.current_screen.current_list.lower().strip()
        acl_object = utility.screen_manager.current_screen.acl_object
        original_name = acl_object.displayed_rule.rule
        filtered_name = acl_object.displayed_rule.rule.replace("!w", "").replace("!g", "").strip()
        new_name = original_name
        new_scope = self.displayed_scope
        banner_text = ""
        hover_attr = None
        reload_page = False
        localize = False

        try:
            ip_addr = acl_object.displayed_rule.extra_data['latest-ip'].split(":")[0].strip()
        except KeyError:
            ip_addr = ""


        # Global options
        if "local" in option or "global" in option:
            if "localize" in option:
                acl_object.add_global_rule(original_name, current_list, remove=True)

                # If rule localized, enable on current list
                if current_list == "ops":
                    acl_object.op_player(acl_object.displayed_rule.rule)
                elif current_list == "bans":
                    acl_object.ban_player(acl_object.displayed_rule.rule)
                elif current_list == "wl":
                    acl_object.whitelist_player(acl_object.displayed_rule.rule)

                hover_attr = (
                    icon_path("earth-strike.png"), 'LOCALIZE',
                    (0.439, 0.839, 1, 1) if current_list == "ops" else
                    (1, 0.5, 0.65, 1) if current_list == "bans" else
                    (0.3, 1, 0.6, 1)
                )
                banner_text = f"'${filtered_name}$' is now locally applied"
                new_scope = "local"
                reload_page = True

            elif "globalize" in option:
                acl_object.add_global_rule(original_name, current_list, remove=False)
                hover_attr = (icon_path("earth-sharp.png"), 'GLOBALIZE', (0.953, 0.929, 0.38, 1))
                banner_text = f"'${filtered_name}$' is now globally applied"
                new_scope = "global"
                reload_page = True


        # Operator options
        elif current_list == "ops":
            if "demote" in option:
                if self.displayed_scope == "global":
                    acl_object.add_global_rule(original_name, current_list, remove=True)
                else:
                    acl_object.op_player(original_name, remove=True)

                hover_attr = (icon_path("close-circle.png"), 'DEMOTE', (1, 0.5, 0.65, 1))
                banner_text = f"'${filtered_name}$' was demoted"
                new_scope = "local"
                reload_page = True

            elif "promote" in option:
                acl_object.op_player(original_name, remove=False)
                hover_attr = (icon_path("promote.png"), 'PROMOTE', (0.3, 1, 0.6, 1))
                banner_text = f"'${filtered_name}$' was promoted"
                reload_page = True


        # Ban options Player/IP
        elif current_list == "bans":
            if acl_object.displayed_rule.rule_type == "player":
                if "ban user" in option:
                    acl_object.ban_player(original_name, remove=False)
                    hover_attr = (icon_path("close-circle.png"), 'BAN', (1, 0.5, 0.65, 1))
                    banner_text = f"'${filtered_name}$' is banned"
                    reload_page = True

                elif "ban IP" in option:
                    acl_object.ban_player(ip_addr, remove=False)

                    if self.displayed_scope == "global":
                        acl_object.add_global_rule(original_name, current_list, remove=True)

                    acl_object.ban_player(f"!w{ip_addr}", remove=True)
                    hover_attr = (icon_path("close-circle.png"), 'BAN', (1, 0.5, 0.65, 1))
                    banner_text = f"'${filtered_name}$' is banned"
                    reload_page = True

                if "pardon IP" in option and "user" in option:
                    acl_object.ban_player([original_name, ip_addr], remove=True)

                    if self.displayed_scope == "global":
                        acl_object.add_global_rule(original_name, current_list, remove=True)

                    # Whitelist IP if it's still in the rule list
                    if ip_addr in acl.gen_iplist(acl_object.rules['subnets']):
                        acl_object.ban_player(f"!w{ip_addr}", remove=False)

                    hover_attr = (icon_path("lock-open.png"), 'PARDON', (0.3, 1, 0.6, 1))
                    banner_text = f"'${filtered_name}$' is pardoned"
                    new_scope = "local"
                    reload_page = True

                elif "pardon user" in option:
                    if self.displayed_scope == "global":
                        acl_object.add_global_rule(original_name, current_list, remove=True)
                    else:
                        acl_object.ban_player(original_name, remove=True)

                    hover_attr = (icon_path("lock-open.png"), 'PARDON', (0.3, 1, 0.6, 1))
                    banner_text = f"'${filtered_name}$' is pardoned"
                    new_scope = "local"
                    reload_page = True

                elif "pardon IP" in option:
                    acl_object.ban_player(ip_addr, remove=True)

                    # Whitelist IP if it's still in the rule list
                    if ip_addr in acl.gen_iplist(acl_object.rules['subnets']):
                        acl_object.ban_player(f"!w{ip_addr}", remove=False)

                    hover_attr = (icon_path("lock-open.png"), 'PARDON', (0.3, 1, 0.6, 1))
                    banner_text = f"'${filtered_name}$' is pardoned"
                    new_scope = "local"
                    reload_page = True


            # IP rules
            else:
                if "ban" in option:
                    # If rule is global and ban is added, switch scope to local
                    if "whitelist" in acl_object.displayed_rule.display_data['rule_info'] and self.displayed_scope == "global":
                        new_scope = "local"

                    if "!w" in original_name:
                        acl_object.ban_player(original_name, remove=True)
                        acl_object.ban_player(filtered_name, remove=False)
                    else:
                        acl_object.ban_player(original_name, remove=False)
                    hover_attr = (icon_path("close-circle.png"), 'BAN', (1, 0.5, 0.65, 1))
                    banner_text = f"'${filtered_name}$' is banned"
                    new_name = filtered_name
                    reload_page = True

                elif "pardon" in option:
                    if self.displayed_scope == "global":
                        acl_object.add_global_rule(original_name, current_list, remove=True)
                    else:
                        acl_object.ban_player(original_name, remove=True)

                    hover_attr = (icon_path("lock-open.png"), 'PARDON', (0.3, 1, 0.6, 1))
                    banner_text = f"'${filtered_name}$' is pardoned"
                    new_scope = "local"
                    reload_page = True

                elif "remove" in option:
                    if self.displayed_scope == "global":
                        acl_object.add_global_rule(original_name, current_list, remove=True)
                    else:
                        acl_object.ban_player(original_name, remove=True)

                    hover_attr = (icon_path("shield-disabled-outline.png"), 'REMOVE', (0.7, 0.7, 1, 1))
                    banner_text = f"'${filtered_name}$' was removed"
                    new_scope = "local"
                    reload_page = True

                elif "whitelist" in option:
                    # If rule is global and whitelist is added, switch scope to local
                    if "ban" in acl_object.displayed_rule.display_data['rule_info'] and self.displayed_scope == "global":
                        new_scope = "local"

                    acl_object.ban_player(original_name, remove=True)
                    acl_object.ban_player(f"!w{filtered_name}", remove=False)
                    hover_attr = (icon_path("shield-checkmark-outline.png"), 'WHITELIST', (0.439, 0.839, 1, 1))
                    banner_text = f"'${filtered_name}$' is whitelisted"
                    new_name = f"!w{filtered_name}"
                    reload_page = True


        # Whitelist options
        elif current_list == "wl":
            if "restrict" in option:
                if self.displayed_scope == "global":
                    acl_object.add_global_rule(original_name, current_list, remove=True)
                else:
                    acl_object.whitelist_player(original_name, remove=True)

                hover_attr = (icon_path("close-circle.png"), 'RESTRICT', (1, 0.5, 0.65, 1))
                banner_text = f"'{filtered_name}' is restricted"
                new_scope = "local"
                reload_page = True

            elif "permit" in option:
                acl_object.whitelist_player(original_name, remove=False)
                hover_attr = (icon_path("checkmark-circle-sharp.png"), 'PERMIT', (0.3, 1, 0.6, 1))
                banner_text = f"'{filtered_name}' is permitted"
                reload_page = True


        if reload_page:

            utility.screen_manager.current_screen.update_list(current_list, reload_children=False)

            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_banner,
                    hover_attr[2],
                    banner_text,
                    hover_attr[0],
                    2,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

            def trigger_highlight(*args):
                for rule_button in utility.screen_manager.current_screen.scroll_layout.children:

                    if rule_button.rule.rule == original_name:
                        rule_button.highlight(rule_button.button.background_color, rule_button.text.color, hover_attr[2])

                    else:
                        rule_button.button.on_leave()
                        Animation.cancel_all(rule_button.button)
                        Animation.cancel_all(rule_button.text)
                        Animation.cancel_all(rule_button.icon)
                        rule_button.change_properties(rule_button.rule)

                    rule_button.button.ignore_hover = False

            Clock.schedule_once(trigger_highlight, 0)

        # Update display rule regardless of button pressed
        utility.screen_manager.current_screen.update_user_panel(new_name, new_scope)

        # print(option)



# Create Server Step 5:  ACL Options -----------------------------------------------------------------------------------

class CreateServerAclScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self._ignore_keys = ['tab']
        self.header = None
        self.search_bar = None
        self.whitelist_toggle = None
        self.scroll_widget = None
        self.scroll_layout = None
        self.blank_label = None
        self.search_label = None
        self.list_header = None
        self.controls_button = None
        self.user_panel = None
        self.show_panel = False

        self.acl_object = None
        self._hash = None
        self.current_list = None

        self.filter_text = ""
        self.currently_filtering = False


    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        if ((keycode[1] == 'h' and control in modifiers and constants.os_name != 'macos') or (keycode[1] == 'h' and control in modifiers and 'shift' in modifiers and constants.os_name == 'macos')) and not self.popup_widget:
            self.controls_button.button.trigger_action()

        # Shortcut to press 'add' button with 'TAB'
        if keycode[1] == 'tab' and not self._input_focused and self.name == utility.screen_manager.current_screen.name:
            for button in self.walk():
                try:
                    if button.id == "input_button":
                        button.force_click()
                        break
                except AttributeError:
                    continue


    def update_user_panel(self, rule_name: str, rule_scope: str):

        # Generate rule list count
        rule_count = len(self.scroll_widget.data)
        panel_check = rule_count > 0


        # Hide user panel if there are no items
        if panel_check != self.show_panel:

            for child in self.user_panel.children:

                # Figure out how to make this not bug out when transitioning between rules, specifically with blank_text
                if child.__class__.__name__ == "Label":
                    child.opacity = (1 if panel_check else 0)
                else:
                    Animation(opacity=(1 if panel_check else 0), duration=0.3).start(child)

                # Make sure self.options shows and hides properly
                for widget in self.user_panel.options.children:
                    utility.hide_widget(widget, panel_check)

            self.show_panel = panel_check


        # Update displayed data on user panel
        if rule_name:
            self.acl_object.get_rule(rule_name)
            self.user_panel.update_panel(self.acl_object.displayed_rule, rule_scope)


        # If rule is displayed
        if self.acl_object.displayed_rule:

            if self.user_panel.blank_label.opacity > 0:
                Animation.stop_all(self.user_panel.blank_label)
                utility.hide_widget(self.user_panel.blank_label, True)
                for child in self.user_panel.options.children:
                    utility.hide_widget(child, False)

        # If rule is not displayed
        else:

            if self.user_panel.blank_label.opacity == 0:
                utility.hide_widget(self.user_panel.blank_label, False)
                for child in self.user_panel.options.children:
                    utility.hide_widget(child, True)


        if not panel_check:
            for widget in self.user_panel.options.children:
                utility.hide_widget(widget, True)


        if self.acl_object.displayed_rule:
            Animation.stop_all(self.user_panel.blank_label)
            utility.hide_widget(self.user_panel.blank_label, True)
            self.user_panel.blank_label.opacity = 0


    # Filter data from search bar
    def search_filter(self, query):

        def lock(*args):
            self.currently_filtering = False
            if self.filter_text != self.search_bar.text:
                self.search_filter(self.search_bar.text)

        # Prevent refreshes shorter than 0.5s
        if not self.currently_filtering:
            self.currently_filtering = True
            self.filter_text = query

            # Filter data

            # Reset scroll
            self.scroll_widget.scroll_y = 1

            total_list = [{'rule': rule} for rule in self.acl_object.list_items[self.current_list]['enabled']]
            total_list.extend([{'rule': rule} for rule in self.acl_object.list_items[self.current_list]['disabled']])

            original_len = len(total_list)

            if query:
                filtered_list = []
                for rule in total_list:
                    rule_obj = rule['rule']

                    # Name matches query
                    if query.lower().replace("!w", "").replace("!g", "") in rule_obj.rule.lower():
                        filtered_list.append(rule)

                    # Scope matches query
                    elif query.lower() == rule_obj.rule_scope:
                        filtered_list.append(rule)

                    # Rule type matches query
                    elif query.lower() == rule_obj.rule_type:
                        filtered_list.append(rule)

                    # Location matches query
                    else:
                        try:
                            location = acl.get_uuid(rule_obj.rule)['ip-geo']
                            if query.lower() in location.lower().replace(" - ", " ") and location != "Unknown":
                                filtered_list.append(rule)
                        except KeyError:
                            pass


                total_list = filtered_list
                del filtered_list

            # Show hint text if there are no rules

            self.set_data(total_list)


            # Show search label if it exists
            Animation.stop_all(self.search_label)
            if self.filter_text and len(self.scroll_widget.data) == 0 and original_len > 0:
                self.search_label.text = f"No results for '{self.filter_text}'"
                Animation(opacity=1, duration=0.2).start(self.search_label)
            else:
                Animation(opacity=0, duration=0.05).start(self.search_label)


            # Unlock the lock
            timer = dTimer(0.5, function=lock)
            timer.start()


    # ops, bans, wl
    def update_list(self, list_type: str, reload_children=True, reload_panel=False):

        if "op" in list_type:    list_type = "ops"
        elif "ban" in list_type: list_type = "bans"
        else:                    list_type = "wl"

        # Reset scroll
        list_changed = False
        if self.current_list != list_type:
            list_changed = True
            self.scroll_widget.scroll_y = 1

        # Create list data with list type
        self.current_list = list_type

        # Check if there's an active filter
        if self.filter_text: self.search_filter(self.filter_text)
        else:
            total_list = [{'rule': rule} for rule in self.acl_object.list_items[list_type]['enabled']]
            total_list.extend([{'rule': rule} for rule in self.acl_object.list_items[list_type]['disabled']])

            self.set_data(total_list)

        rule_count = len(self.acl_object.rules[list_type])
        if list_type == "bans": rule_count += len(self.acl_object.rules['subnets'])


        # Modify header content
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = (f'[color=#6A6ABA]{translate("No rules")}[/color]' if rule_count == 0 else f'[font={very_bold_font}]1[/font] {translate("rule")}' if rule_count == 1 else f'[font={very_bold_font}]{rule_count:,}[/font] {translate("rules")}')
        if list_type == "wl" and not self.acl_object._server['whitelist']: header_content += f" ({translate('inactive')})"

        # header_content = (" "*(len(header_content) - (55 if 'inactive' not in header_content else 50))) + header_content

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                child.halign = "left"
                child.text_size[0] = 500
                child.x = Window.width / 2 + 240
                break


        display_count = len(self.acl_object.list_items[list_type]['enabled']) + len(self.acl_object.list_items[list_type]['disabled'])

        # If there are no rules, say as much with a label
        utility.hide_widget(self.list_header.global_rule, display_count == 0)
        utility.hide_widget(self.list_header.enabled_rule, display_count == 0)
        utility.hide_widget(self.list_header.disabled_rule, display_count == 0)


        if display_count == 0:
            if self.blank_label.opacity < 1:
                self.blank_label.text = "No rules available, add them above"
                utility.hide_widget(self.blank_label, False)
                self.blank_label.opacity = 0
                Animation(opacity=1, duration=0.2).start(self.blank_label)
                Animation(opacity=0, duration=0.2).start(self.search_label)

        # If there are rules, display them here
        else:
            # Show search label if it exists
            Animation.stop_all(self.search_label)
            # print(len(self.scroll_widget.data))
            if self.filter_text and len(self.scroll_widget.data) == 0:
                self.search_label.text = f"{translate('No results for')} '{self.filter_text}'"
                Animation(opacity=1, duration=0.2).start(self.search_label)
            else:
                Animation(opacity=0, duration=0.2).start(self.search_label)

            self.list_header.remove_widget(self.list_header.enabled_rule)
            self.list_header.enabled_rule = RelativeLayout()
            self.list_header.enabled_rule.add_widget(
                BannerObject(
                    size=(120, 32),
                    color=(0.439, 0.839, 1, 1) if list_type == 'ops'
                    else (1, 0.5, 0.65, 1) if list_type == 'bans'
                    else (0.3, 1, 0.6, 1),

                    text="operator" if list_type == 'ops'
                    else "banned" if list_type == 'bans'
                    else "allowed",

                    icon="settings-sharp.png" if list_type == 'ops'
                    else "close-circle-sharp.png" if list_type == 'bans'
                    else "checkmark-circle-sharp.png"
                )
            )
            self.list_header.add_widget(self.list_header.enabled_rule)


            self.list_header.remove_widget(self.list_header.disabled_rule)
            self.list_header.disabled_rule = RelativeLayout()
            self.list_header.disabled_rule.add_widget(
                BannerObject(
                    size=(125, 32),
                    color=(0.6, 0.5, 1, 1) if list_type == 'ops'
                    else (0.3, 1, 0.6, 1) if list_type == 'bans'
                    else (1, 0.5, 0.65, 1) if self.acl_object._server['whitelist'] else(0.7, 0.7, 0.7, 1),

                    text="standard" if list_type == 'ops'
                    else "allowed" if list_type == 'bans'
                    else "restricted",

                    icon="person-circle-sharp.png" if list_type == 'ops'
                    else "checkmark-circle-sharp.png" if list_type == 'bans'
                    else "close-circle-sharp.png"
                )
            )
            self.list_header.add_widget(self.list_header.disabled_rule)

            utility.hide_widget(self.blank_label, True)

        # Change whitelist toggle visibility based on list_type
        utility.hide_widget(self.whitelist_toggle, list_type != 'wl')

        # Refresh all buttons
        if reload_children:
            for rule_button in self.scroll_layout.children:
                rule_button.change_properties(rule_button.rule)


            # Dirty fix to hide grid resize that fixes RuleButton text.pos_hint x
            if list_changed:
                self.scroll_widget.opacity = 0
                self.scroll_layout.cols = 1
                self.resize_bind()
                def animate_grid(*args):
                    Animation.stop_all(self.scroll_widget)
                    Animation(opacity=1, duration=0.3).start(self.scroll_widget)
                Clock.schedule_once(animate_grid, 0)


        # Update displayed rule options
        if (self.acl_object.displayed_rule and list_changed) or (reload_panel and self.acl_object.displayed_rule):
            global_rules = acl.load_global_acl()
            self.acl_object.displayed_rule.acl_group = list_type
            rule_scope = acl.check_global_acl(global_rules, self.acl_object.displayed_rule).rule_scope
            self.update_user_panel(self.acl_object.displayed_rule.rule, rule_scope)


    def set_data(self, data):

        if self.scroll_layout:
            self.scroll_layout.rows = None

        self.scroll_widget.data = data

        if self.resize_bind:
            self.resize_bind()


    def generate_menu(self, **kwargs):

        if not foundry.new_server_info['acl_object']:
            foundry.new_server_name()
            foundry.new_server_info['acl_object'] = acl.AclManager(foundry.new_server_info['name'])
            self.acl_object = foundry.new_server_info['acl_object']

        # If self._hash doesn't match, set list to ops by default
        if self._hash != foundry.new_server_info['_hash']:
            self.acl_object = foundry.new_server_info['acl_object']
            self._hash = foundry.new_server_info['_hash']
            self.current_list = 'ops'

        self.show_panel = False

        self.filter_text = ""
        self.currently_filtering = False


        # Scroll list
        self.scroll_widget = RecycleViewWidget(position=(0.5, 0.43), view_class=RuleButton)
        self.scroll_layout = RecycleGridLayout(spacing=[110, -15], size_hint_y=None, padding=[60, 20, 0, 30])
        test_rule = RuleButton()

        # Bind / cleanup height on resize
        def resize_scroll(*args):
            self.scroll_widget.height = Window.height // 1.65
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

            def update_background(*a): scroll_top.resize(); scroll_bottom.resize()
            Clock.schedule_once(update_background, 0)

            self.search_label.pos_hint = {"center_x": (0.28 if Window.width < 1300 else 0.5), "center_y": 0.42}
            self.search_label.text_size = (Window.width / 3, 500)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.735}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.14}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        selector_text = "operators" if self.current_list == "ops" else "bans" if self.current_list == "bans" else "whitelist"
        self.page_selector = DropButton(selector_text, (0.5, 0.89), options_list=['operators', 'bans', 'whitelist'], input_name='ServerAclTypeInput', x_offset=-210, facing='center', custom_func=self.update_list)
        header_content = ""
        self.header = HeaderText(header_content, '', (0, 0.89), fixed_x=True, no_line=True, __translate__ = (False, True))


        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)


        # Search bar
        self.search_bar = AclInput(pos_hint={"center_x": 0.5, "center_y": 0.815})
        buttons.append(InputButton('Add Rules...', (0.5, 0.815), input_name='AclInput'))


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

        self.whitelist_toggle = SwitchButton('whitelist', (0.5, 0.89), default_state=self.acl_object._server['whitelist'], x_offset=-395, custom_func=toggle_whitelist)


        # Legend for rule types
        self.list_header = BoxLayout(orientation="horizontal", pos_hint={"center_x": 0.5, "center_y": 0.749}, size_hint_max=(400, 100))
        self.list_header.global_rule = RelativeLayout()
        self.list_header.global_rule.add_widget(BannerObject(size=(120, 32), color=test_rule.global_icon_color, text="global", icon="earth-sharp.png", icon_side="left"))
        self.list_header.add_widget(self.list_header.global_rule)

        self.list_header.enabled_rule = RelativeLayout()
        self.list_header.enabled_rule.add_widget(BannerObject(size=(120, 32), color=(1,1,1,1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.enabled_rule)

        self.list_header.disabled_rule = RelativeLayout()
        self.list_header.disabled_rule.add_widget(BannerObject(size=(120, 32), color=(1,1,1,1), text=" ", icon="add.png"))
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
        self.search_label.__translate__ = False
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
        self.controls_button = IconButton('controls', {}, (70, 110), (None, None), 'question.png', clickable=True, anchor='right', click_func=show_controls)
        float_layout.add_widget(self.controls_button)


        # User panel
        self.user_panel = AclRulePanel()


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

        buttons.append(ExitButton('Back', (0.5, 0.099), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}', Access Control"
        float_layout.add_widget(generate_title(f"Access Control Manager: '{foundry.new_server_info['name']}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

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


class CreateServerAclRuleScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self._ignore_tree = True

        self.acl_input = None
        self.current_list = None
        self.acl_object = None
        self.next_button = None


    def apply_rules(self):

        # Actually apply rules
        def _apply_thread(*a):
            self.next_button.loading(True)
            original_list = self.acl_object._process_query(self.acl_input.text, self.current_list)

            applied_list = []
            applied_list.extend(original_list['global'])
            applied_list.extend(original_list['local'])


            # Generate banner
            banner_text = "Added "
            "Added '$$'"

            if len(applied_list) == 1:
                banner_text += f"'${acl.get_uuid(applied_list[0])['name'] if applied_list[0].count('.') < 3 else applied_list[0]}$'"
            elif len(applied_list) < 3:
                banner_text += f"'${', '.join([(acl.get_uuid(x)['name'] if x.count('.') < 3 else x) for x in applied_list[0:2]])}$'"
            else:
                banner_text += f"'${acl.get_uuid(applied_list[0])['name'] if applied_list[0].count('.') < 3 else applied_list[0]}$' and {len(applied_list) - 1:,} more"


            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_banner,
                    (0.553, 0.902, 0.675, 1),
                    banner_text,
                    "add-circle-sharp.png",
                    2.5,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

            # Return to previous screen
            self.acl_object.get_rule(applied_list[0])

            def update_panel(*args):
                utility.screen_manager.current_screen.update_list(self.current_list)
                utility.screen_manager.current_screen.update_user_panel(applied_list[0], applied_list[0] in original_list['global'])

            Clock.schedule_once(utility.screen_manager.previous_screen, 0)
            Clock.schedule_once(update_panel, 0)

            # Prevent back button from going back to this screen
            for screen in utility.screen_manager.screen_tree:
                if screen == self.name: utility.screen_manager.screen_tree.remove(self.name)

        dTimer(0, _apply_thread).start()

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

        self.current_list = utility.screen_manager.get_screen("CreateServerAclScreen").current_list
        self.acl_object = utility.screen_manager.get_screen("CreateServerAclScreen").acl_object

        if self.current_list == "bans":
            header_message = "Enter usernames/IPs delimited, by, commas"
            float_layout.add_widget(HintLabel(0.464, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))
            float_layout.add_widget(HintLabel(0.374, "You can ban IP ranges/whitelist:   [color=#FF6666]192.168.0.0-150[/color], [color=#66FF88]!w 192.168.1.1[/color]"))
        else:
            header_message = "Enter usernames delimited, by, commas"
            float_layout.add_widget(HintLabel(0.425, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))

        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.72}))
        float_layout.add_widget(HeaderText(header_message, '', (0, 0.8)))
        self.acl_input = AclRuleInput(pos_hint={"center_x": 0.5, "center_y": 0.64}, text="")
        float_layout.add_widget(self.acl_input)

        self.next_button = NextButton('Add Rules', (0.5, 0.24), True, show_load_icon=True)
        buttons.append(self.next_button)
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}', Access Control"
        list_name = "Operators" if self.current_list == "ops" else "Bans" if self.current_list == "bans" else "Whitelist"
        float_layout.add_widget(generate_title(f"Access Control Manager: Add {list_name}"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)
        self.acl_input.grab_focus()



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

            def update_background(*a): scroll_top.resize(); scroll_bottom.resize()
            Clock.schedule_once(update_background, 0)

            self.search_label.pos_hint = {"center_x": (0.28 if Window.width < 1300 else 0.5), "center_y": 0.42}
            self.search_label.text_size = (Window.width / 3, 500)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.735}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.175}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        selector_text = "operators" if self.current_list == "ops" else "bans" if self.current_list == "bans" else "whitelist"
        self.page_selector = DropButton(selector_text, (0.5, 0.89), options_list=['operators', 'bans', 'whitelist'], input_name='ServerAclTypeInput', x_offset=-210, facing='center', custom_func=self.update_list)
        header_content = ""
        self.header = HeaderText(header_content, '', (0, 0.89), fixed_x=True, no_line=True)

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Search bar
        self.search_bar = AclInput(pos_hint={"center_x": 0.5, "center_y": 0.815})
        buttons.append(InputButton('Add Rules...', (0.5, 0.815), input_name='AclInput'))

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

        self.whitelist_toggle = SwitchButton('whitelist', (0.5, 0.89), default_state=self.acl_object._server['whitelist'], x_offset=-395, custom_func=toggle_whitelist)

        # Legend for rule types
        self.list_header = BoxLayout(orientation="horizontal", pos_hint={"center_x": 0.5, "center_y": 0.749}, size_hint_max=(400, 100))
        self.list_header.global_rule = RelativeLayout()
        self.list_header.global_rule.add_widget(BannerObject(size=(120, 32), color=test_rule.global_icon_color, text="global", icon="earth-sharp.png", icon_side="left"))
        self.list_header.add_widget(self.list_header.global_rule)

        self.list_header.enabled_rule = RelativeLayout()
        self.list_header.enabled_rule.add_widget(BannerObject(size=(120, 32), color=(1, 1, 1, 1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.enabled_rule)

        self.list_header.disabled_rule = RelativeLayout()
        self.list_header.disabled_rule.add_widget(BannerObject(size=(120, 32), color=(1, 1, 1, 1), text=" ", icon="add.png"))
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

        self.controls_button = IconButton('controls', {}, (70, 110), (None, None), 'question.png', clickable=True, anchor='right', click_func=show_controls)

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

        for button in buttons: float_layout.add_widget(button)

        menu_name = f"{constants.server_manager.current_server.name}, Access Control"
        float_layout.add_widget(generate_title(f"Access Control Manager: '{constants.server_manager.current_server.name}'"))
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
            float_layout.add_widget(HintLabel(0.464, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))
            float_layout.add_widget(HintLabel(0.374, "You can ban IP ranges/whitelist:   [color=#FF6666]192.168.0.0-150[/color], [color=#66FF88]!w 192.168.1.1[/color]"))
        else:
            header_message = "Enter usernames delimited, by, commas"
            float_layout.add_widget(HintLabel(0.425, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))

        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.72}))
        float_layout.add_widget(HeaderText(header_message, '', (0, 0.8)))
        self.acl_input = AclRuleInput(pos_hint={"center_x": 0.5, "center_y": 0.64}, text="")
        float_layout.add_widget(self.acl_input)

        self.next_button = NextButton('Add Rules', (0.5, 0.24), True, show_load_icon=True)
        buttons.append(self.next_button)
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        menu_name = f"{constants.server_manager.current_server.name}, Access Control"
        list_name = "Operators" if self.current_list == "ops" else "Bans" if self.current_list == "bans" else "Whitelist"
        float_layout.add_widget(generate_title(f"Access Control Manager: Add {list_name}"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)
        self.acl_input.grab_focus()
