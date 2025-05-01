# Overview

The auto-mcs scripting API (*amscript*) is available to quickly create universal plugins for your auto-mcs servers. It functions primarily as an asynchronous wrapper which fires events from what happens in-game and uses standard Python 3.9 syntax. Because of this mechanic, a single script will work with every Vanilla, CraftBukkit (and derivatives), Forge, and Fabric server regardless of the game version. This functionality can be accessed via the amscript button in the Server Manager. Create a new script to open the built-in IDE and get started!

To see more examples of the library in action, [visit our repository of amscripts](https://github.com/macarooni-man/auto-mcs/tree/main/amscript-library) to see how the objects and events work together!

> Note: All of these scripts are available to download and edit directly inside the amscript manager

<br><br><br>




# Objects
> Note: All object attributes are read-only, but can be manipulated with their methods

## ServerScriptObject
Contains the server's running configuration from the `server.properties`, to the list of connected players.

Accessed via the global variable `server`

**Methods**: <br><br>



### server.launch()

Immediately starts the server if it's not running.


<br>



### server.stop()

Immediately stops the server.


<br>



### server.restart()

Immediately stops and restarts the server.


<br>



### server.log(*message, log_type*)

Sends a custom log event to the console. This output is displayed only while the server is running, and is not saved to `latest.log`.

- `server.log_success()`, `server.log_warning()`, and `server.log_error()` methods can also be used, and only require the `message` parameter.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `message*` | `str` of log content |
| `log_type` | `str` can be `'info'`, `'success'`, `'warning'` or `'error'`. Defaults to `'info'` |

<br>



### server.broadcast(*message, color, style*)

Sends a custom chat message to all players and the console. This output is displayed only while the server is running, and is not saved to `latest.log`.

- `server.broadcast_success()`, `server.broadcast_warning()`, and `server.broadcast_error()` methods can also be used, and only require the `message` parameter.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `message*` | `str` of content to broadcast |
| `color` | `str` of Minecraft color ID, all values for `/tellraw` are accepted. List of IDs can be found [here](https://minecraft.fandom.com/wiki/Formatting_codes#Color_codes) |
| `style` | `str`, can be `'normal'`, `'italic'`, `'bold'`, `'strikethrough'`, `'underlined'`, and `'obfuscated'`. Defaults to `'italic'` |

<br>


### server.operator_broadcast(*message, color, style*)

Sends a custom chat message to all operators and the console. This output is displayed only while the server is running, and is not saved to `latest.log`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `message*` | `str` of content to broadcast |
| `color` | `str` of Minecraft color ID, all values for `/tellraw` are accepted. List of IDs can be found [here](https://minecraft.fandom.com/wiki/Formatting_codes#Color_codes) |
| `style` | `str`, can be `'normal'`, `'italic'`, `'bold'`, `'strikethrough'`, `'underlined'`, and `'obfuscated'`. Defaults to `'italic'` |

<br>



### server.execute(*command*)

Executes any Minecraft command in the server console.

> Note: Some commands are version dependent and you may need to implement a switch to execute different commands for different versions.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `command*` | `str`, any Minecraft command |
| `log` | `bool`, show execution in the console, `False` by default to prevent lag or clutter in the console with fast loops |

<br>



### server.after(*delay, function, params*)

Runs a delayed background (non-blocking) task. Exits before execution if the server stops, or if scripts are reloaded. Returns `ServerScriptObject.AmsTimer()` of the background task, which has a method `AmsTimer.cancel()` to end prematurely.

**Accepted parameters**:
| Parameter | Description | 
| --- | --- |
| `delay*` | `int`, delay in seconds |
| `function*` | `callable`, any Python callable function or method |
| `params` | accepts `*args` and `**kwargs` which are passed to `function` |

<br>



### server.get_player(*selector, reverse, offline*)

Returns [**PlayerScriptObject**](#PlayerScriptObject) on match, else `None`. Only returns the first match.

> Note: In versions prior to 1.13, `selector` can only be a username

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `selector*` | `str` of username, or a valid Minecraft selector that returns a single value (like @p, @s, @r). Only players will be matched |
| `offline` | `bool` retrieves playerdata from `.dat` file if the target player isn't connected to the server. Defaults to `False` |

<br>



### server.get_players()

Returns a generator of [**PlayerScriptObject**](#PlayerScriptObject) for each online player.

<br>



**Attributes**:
> Note: All attributes are read-only, and thus will not change the server data when modified


#### server.name
 - `str`, server's current filename

#### server.version
 - `AmsVersion`, Minecraft version of the server, i.e. `'1.16.3'`
 - When used in a string, it will be formatted as `'1.16.3'`
 - Can be used in mathematical comparisons with another version string, returns `bool`.
```python
if server.version >= '1.8':
    server.log("Server is 1.8 or newer")
```

#### server.build
 - `str`, Only applicable for Paper/Forge, contains build number. Else will be `None`

#### server.type
 - `str`, type of server, i.e. `'craftbukkit'` or `'vanilla'`
 - Can be `'vanilla'`, `'craftbukkit'`, `'spigot'`, `'paper'`, `'forge'`, or `'fabric'`

#### server.world
 - `str`, filename of `level-name` from `server.properties`

#### server.directory
 - `str`, full path of the directory in which the server is stored

#### server.network
 - `dict`, contains the listening IP and port
 - Structured as `{'ip': ip address, 'port': port}`

#### server.properties
 - `dict`, current keys in the `server.properties` file
 - A boolean value for example can be accessed with `server.properties['enable-command-block']`

#### server.player_list
 - `dict`, contains a key and a sub-dictionary for each connected player
 - The current format is `{'username': {'uuid': uuid, 'ip': ip address, 'date': datetime, 'logged-in': True}}`

#### server.usercache
 - `dict`, contains a dictionary for each player who has ever joined the server
 - The current format is `{'username': 'uuid'}`

#### server.persistent
 - `dict`, persistent variable storage for saving information between server restarts, or script reloads
 - Assigning or updating a key in the `server.persistent` dictionary will automatically save it, and can be accessed via the same key persistently until it is changed again, or deleted. Data will only be saved for the server referenced in the object.

> Warning: persistent data is only saved properly when the server shuts down gracefully, if the computer crashes or the server process is terminated forcefully, the persistent data will likely revert to previous values

#### server.ams_version
- `str`, contains the current amscript version to account for API changes

#### server.output
- `list`, contains a formatted list of dictionaries organizing the items visible in the auto-mcs console from oldest to newest (limit of 850)

<br><br>



## PlayerScriptObject
Contains current player configuration from their username, UUID, to all their NBT data

Accessed by an applicable event, or by the `server.get_player()` method

**Methods**: <br><br>



### player.set_permission(*permission, enabled*)

Sets a custom permission for [**@player.on_alias**](#playeron_alias) events.

- The `player.check_permission()` method can also be used with only the `permission` argument to return a `bool` if the player has the specified permission. Note that the server console has all custom permissions. Note that these are arbitrary permissions for moderating auto-mcs commands, and have no relation to Bukkit.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `permission*` | `str` of the permission name |
| `enabled` | `bool` to enable or disable the permission. Defaults to `True` |

<br>



### player.log(*message, color, style*)

Sends a private message to the chat of the player with formatting support.
Useful for command feedback with a [**@player.on_alias**](#playeron_alias) event

- `player.log_success()`, `player.log_warning()`, and `player.log_error()` methods can also be used, and only require the `message` parameter.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `message*` | `str` of content to log to the player |
| `color` | `str` of Minecraft color ID, all values for `/tellraw` are accepted. List of IDs can be found [here](https://minecraft.fandom.com/wiki/Formatting_codes#Color_codes) |
| `style` | `str`, can be `'normal'`, `'italic'`, `'bold'`, `'strikethrough'`, `'underlined'`, and `'obfuscated'`. Defaults to `'italic'` |

<br>



**Attributes**:
> Note: Most attributes are read-only, and thus will not change playerdata when modified.

> Note: Versions prior to 1.13 load NBT from playerdata.dat, which is only updated every couple of minutes or so. Any version between 1.8-1.13 will execute `save-all` to force updated data. 1.13 and later retrieves *all* of the most recent NBT data.


#### player.name
 - `str`, player's current username

#### player.uuid
 - `str`, player's Universally Unique IDentifier *(`None` pre-1.8)*

#### player.ip_address
 - `str`, currently connected IP address

#### player.is_server
 - `bool`, if current object was created from the console
 - This will be `True` if the console sends a command to a [**@player.on_alias**](#playeron_alias) event, for example

#### player.is_online
 - `bool`, if current object is connected to the server
 - This will be `False` if the console sends a command to a [**@player.on_alias**](#playeron_alias) event, for example

#### player.is_operator
 - `bool`, if current object has operator permissions
 - This will be `True` if the console sends a command to a [**@player.on_alias**](#playeron_alias) event, for example

#### player.position
 - `CoordinateObject`, player's current position in X, Y, and Z coordinates
 - When assigned to a variable or persistence, it will stay a `CoordinateObject`
 - Can be referenced in a string (such as a command) with `player.position` or `player.position.x`, `player.position.y`, and `player.position.z`

#### player.rotation
 - `CoordinateObject`, player's current rotation in X, and Y values
 - When assigned to a variable or persistence, it will stay a `CoordinateObject`
 - Can be referenced in a string (such as a command) with `player.rotation` or `player.rotation.x` and `player.rotation.y`

#### player.motion
 - `CoordinateObject`, player's current motion in X, Y, and Z values
 - When assigned to a variable or persistence, it will stay a `CoordinateObject`
 - Can be referenced in a string (such as a command) with `player.motion` or `player.motion.x`, `player.motion.y`, and `player.motion.z`

#### player.spawn_position
 - `CoordinateObject`, player's spawn position in X, Y, and Z coordinates
 - When assigned to a variable or persistence, it will stay a `CoordinateObject`
 - Can be referenced in a string (such as a command) with `player.spawn_position` or `player.spawn_position.x`, `player.spawn_position.y`, and `player.spawn_position.z`

#### player.health
 - `int`, player's current health
 - Value of `0-20`, but can be higher depending on attributes

#### player.hunger_level
 - `int`, player's current hunger level
 - Value of `0-20`

#### player.gamemode
 - `str`, player's current gamemode
 - Settable with `player.gamemode = 'survival'`
 - Value of `'survival'`, `'creative'`, `'adventure'`, or `'spectator'`

#### player.xp
 - `float`, player's current xp level

#### player.on_fire
 - `bool`, is `True` if player is on fire

#### player.is_flying
 - `bool`, is `True` if player is flying

#### player.is_sleeping
 - `bool`, is `True` if player is sleeping

#### player.is_drowning
 - `bool`, is `True` if player is drowning

#### player.hurt_time
 - `int`, determines if player was hurt recently *(in ticks)*
 - Any value above `0` yields invincibilty until it reaches `0` again

#### player.death_time
 - `int`, how long since the player died *(in ticks)*
 
#### player.dimension
 - `str`, the dimension that the player is currently in
 - Settable with `player.dimension = 'overworld'`
 - Value of `'overworld'`, `'the_nether'`, or `'the_end'`

#### player.active_effects
 - `dict` of `EffectObject`, player's current effects
 - Speed, for example can be accessed with `player.active_effects['speed'].duration`

#### player.inventory
 - `InventoryObject`, organized list of all items in the player's inventory
 - Each list is full of `ItemObject`, which can be accessed via lowercase NBT attributes like in game, and with Pythonic logic: `player.inventory.selected_item.tag.display.name` or `if "diamond_sword" in player.inventory` or `player.inventory.hotbar.count("cobblestone")`
 - An `InventoryObject` is structured in the following format:
```python
class InventoryObject():
    # The attributes below are supported and abracted in a consistent way via amscript, regardless of the game version

    # The selected item in the inventory
    self.selected_item <ItemObject>

    # The item in the offhand slot
    self.offhand <ItemObject>

    # Items in the hotbar slots with index 0-8
    self.hotbar <list of ItemObject>

    # The items in the main inventory with index 0-26
    self.inventory <list of ItemObject>

    # The items in the armor slot
    # Keys: "head", "chest", "legs", "feet"
    self.armor <dict of ItemObject>
```

> Note: all methods below can also be used on `player.inventory.hotbar`, `player.inventory.armor`, and `player.inventory.inventory` as well

   - #### inventory.items()
     - Returns a `list` of every `ItemObject` in the inventory

   - #### inventory.find(*item_id*)
     - Returns a `list` of every `ItemObject` which matches `item_id`

   - #### inventory.count(*item_id*)
     - Returns a total count in `int` of all `item_id` in the inventory.
     - If `item_id` is a list, it will return the count of all items in the list.
     - If `item_id` is not provided, it will return the count of all items in the inventory.

   - #### inventory.give(*ItemObject, preserve_slot*)
     - Gives the player the specified `ItemObject`. This can be helpful for transferring items between players, even with NBT data like enchantments, names, etc.
     - If `preserve_slot` is `True`, the item will be given to the player in the same slot it originated from. Defaults to `False`. This parameter is only compatible with Minecraft 1.8 and later.
     > Note: This method is compatible with every version of Minecraft
     - Compliments `ItemObject.take()`

   - #### inventory.clear()
     - Clears the player's inventory of all items.


 - An `ItemObject` is structured in the following format:
```python
class ItemObject():
    # The attributes below (except for self.nbt) are supported and abstracted in a consistent way via amscript, regardless of the game version

    # The slot in the inventory that contains the item
    # Follows the standard Minecraft slot format, e.g. "slot.hotbar.0", "slot.armor.head", "slot.inventory.0", etc.
    self.slot <str>

    # ID of the item
    self.id <str>

    # Quantity of the item
    self.count <int>

    # e.g. durability of a tool
    self.damage <int>

    # Custom name of the item, or None
    self.custom_name <str or None>

    # List of strings, each string is a line of lore
    self.lore <list>

    # Dictionary of dictionaries, each dictionary is an enchantment
    self.enchantments <dict>

    # List of dictionaries, each dictionary is an attribute modifier
    self.attribute_modifiers <list>

    # Many items have extra attributes such as a book (normal NBT format: self.pages).
    # This is the raw NBT data, and is formatted differently depending on the game version
    self.nbt <dict>
```
   - #### ItemObject.take()
     - Takes the specified `ItemObject` from the player it originated from, and returns the `ItemObject` that was taken. This can be helpful for transferring items between players, even with NBT data like enchantments, names, etc.
     > Note: This method is only compatible with Minecraft 1.4.2 and later

```python
# Example of transferring all items from one player to another
player1 = server.get_player("player1")
player2 = server.get_player("player2")

for item in player1.inventory:
    player2.inventory.give(item.take())
```

#### player.persistent
 - `dict`, persistent variable storage for saving information between server restarts, or script reloads
 - Assigning or updating a key in the `player.persistent` dictionary will automatically save it, and can be accessed via the same key persistently until it is changed again, or deleted. Data will be saved only for the player referenced by the object, and only for the server. Data will not persist between different servers.

> Warning: persistent data is only saved properly when the server shuts down gracefully, if the computer crashes or the server process is terminated forcefully, the persistent data will likely revert to previous values

<br><br>



## BackupManager
Contains the server's back-up configuration and allows you to save, restore, or configure the UI settings.

Accessed via the global variable `backup`

**Methods**: <br><br>



### backup.save()

Immediately saves the state of the server to a back-up file.

<br>



### backup.restore(*backup_obj*)

Restores a back-up from a `BackupObject`. Use the `backup.latest` or `backup.list` attribute to retrieve a `BackupObject`.

- If the server is currently running, this function will do nothing. Schedule the restore in a [**@server.on_stop**](#serveron_stop)

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `backup_obj*` | `BackupObject`, retrieve from `backup.latest` or `backup.list` |

<br>



### backup.set_directory(*new_directory*)

Migrates all the back-up files from the previous directory to the specified `new_directory`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `new_directory*` | `str` of a folder on the filesystem, and will create it if it doesn't exist |

<br>



### backup.set_amount(*amount*)

Configures the maximum amount of back-ups that can be saved to `backup.directory` before overwriting.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `amount*` | `int` or `'unlimited'` |

<br>



### backup.enable_auto_backup(*enabled*)

Enables or disables automatic server back-ups.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `enabled*` | `bool` to enable automatic back-ups. Defaults to `True`. |

<br>



**Attributes**:
> Note: All attributes are read-only, and thus will not change the server data when modified


#### backup.directory
 - `str`, default filesystem directory to save and restore back-ups from

#### backup.maximum
 - `int` or `'unlimited'`, shows the maximum amount of back-ups allowed in `backup.directory`

#### backup.auto_backup
 - `bool`, shows whether automatic server back-ups are enabled or not

#### backup.total_size
 - `int`, contains storage utilization in bytes of all back-ups in `backup.directory`

#### backup.latest
 - `BackupObject`, file details of the most recent back-up
 - Available attributes are `BackupObject.path`, `BackupObject.size`, and `BackupObject.date`

#### backup.list
 - `list` of `BackupObject`, file details of all back-ups sorted from most recent in descending order at `backup.list[0]`
 - Available attributes are `BackupObject.path`, `BackupObject.size`, and `BackupObject.date`

<br><br>




## AclManager
Contains the server's access control configuration and manages the whitelist, bans, and operators programmatically.

Accessed via the global variable `acl`

The `AclManager` conceptualizes both users and IP addresses as `AclRule` objects in their respective lists in the `acl.rules` attribute. A majority of the methods include and modify the `'bans'`, `'ops'`, `'wl'`, and `'subnets'` keys in this attribute.

- An `AclRule` is structured in the following format:
```python
class AclRule():

    # ID/name of the rule
    self.rule <str>

    # 'player' or 'ip'
    self.rule_type <str>

    # 'local' or 'global'
    self.rule_scope <str>

    # 'ops', 'bans', 'wl', or 'subnets'
    self.acl_group <str>

    # Extra content (ban reason, IP geolocation, etc.)
    self.extra_data <dict>

    # To be added when rule is displayed from AclManager
    self.display_data <dict>
```



<br>


**Methods**: <br><br>



### acl.get_uuid(*username*)

Returns a `dict` of a player's connection data given their username and other rules. Use `acl.get_uuid('User')['uuid']` to get their UUID.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `username*` | `str` of username |

<br>



### acl.kick_player(*rule_list, reason*)

Kicks a player or list of players, optionally with a reason.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `rule_list*` | [**PlayerScriptObject**](#PlayerScriptObject), `str` of username, or a `list` of either |
| `reason` | `str`, reason for the kick displayed in the menu, and log |

<br>



### acl.ban_player(*rule_list, remove, reason*)

Bans/pardons a player, IP, list of players, or list of IP's, optionally with a reason. A subnet range such as `192.168.0.0/24` is also acceptable. You can whitelist an IP or subnet with `!w192.168.0.5`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `rule_list*` | [**PlayerScriptObject**](#PlayerScriptObject), `str` of username/IP, or a `list` of either |
| `remove` | `bool`, removes rule from effect. Defaults to `False` |
| `reason` | `str`, reason for the ban displayed in the menu, and log |

<br>



### acl.op_player(*rule_list, remove*)

Ops/de-ops a player or list of players.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `rule_list*` | [**PlayerScriptObject**](#PlayerScriptObject), `str` of username, or a `list` of either |
| `remove` | `bool`, removes rule from effect. Defaults to `False` |

<br>



### acl.whitelist_player(*rule_list, remove*)

Adds/removes a player or list of players to/from the whitelist.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `rule_list*` | [**PlayerScriptObject**](#PlayerScriptObject), `str` of username, or a `list` of either |
| `remove` | `bool`, removes rule from effect. Defaults to `False` |

<br>



### acl.enable_whitelist(*enabled*)

Enables or disables the server whitelist.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `enabled*` | `bool`, to enable or disable the whitelist. Defaults to `True` |

<br>



### acl.add_global_rule(*rule_list, list_type, remove*)

Adds a player or list of players to a specified list type for every server.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `rule_list*` | [**PlayerScriptObject**](#PlayerScriptObject), `str` of username, or a `list` of either |
| `list_type*` | `str`, can be `'ops'`, `'bans'`, or `'wl'` |
| `remove` | `bool`, removes rule from effect. Defaults to `False` |

<br>



### acl.reload_list(*list_type*)

Reloads the list type from the server `.json` files and refreshes `acl.rules`. If `list_type` is unspecified, all data is reloaded.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `list_type` | `str`, can be `'ops'`, `'bans'`, or `'wl'` |

<br>



### acl.edit_list(*rule_list, list_type, remove*)

Similar to the `acl.*_player` methods, but only edits `acl.rules` in memory without writing to disk.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `rule_list*` | [**PlayerScriptObject**](#PlayerScriptObject), `str` of username, or a `list` of either |
| `list_type*` | `str`, can be `'ops'`, `'bans'`, or `'wl'` |
| `remove` | `bool`, removes rule from effect. Defaults to `False` |

<br>



### acl.write_rules()

Writes data from `acl.rules` to disk in their respective format. Works pre-1.8 for `.txt` files, and post-1.8 for `.json` files.

<br>



### acl.rule_in_acl(*rule, list_type*)

Checks if a player or IP is in a specified list type. Returns `bool`

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `rule*` | [**PlayerScriptObject**](#PlayerScriptObject) or `str` of username or IP |
| `list_type*` | `str`, can be `'ops'`, `'bans'`, `'wl'`, or `'subnets'` |

<br>



### acl.count_rules(*list_type*)

Counts rules in the specified list type, or all rules if unspecified. Returns the total amount as `int`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `list_type` | `str`, can be `'ops'`, `'bans'`, or `'wl'` |

<br>



### acl.get_rule(*rule_name*)

Retrieves all the access control data associated with a rule. Returns a new `AclRule` with additional data in the `AclRule.extra_data` dictionary.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `rule_name*` | `str` of username, IP, or subnet |

<br>



**Attributes**:
> Note: All attributes are read-only, and thus will not change the server data when modified


#### acl.rules
 - `dict`, contains lists of `AclRule` objects with the following structure:
 ```python
acl.rules = {
    'ops': [AclRule, AclRule, ...],
    'bans': [AclRule, AclRule, ...],
    'wl': [AclRule, AclRule, ...],
    'subnets': [AclRule, AclRule, ...]
}
```

#### acl.playerdata
 - `list`, contains an `AclRule` for every player who has joined the server in the `usercache.json`, or who has player data in the world

#### acl.list_items
 - `dict`, structured similarly to `acl.rules`, but contains an organized list of disabled and enabled items for each list type. Used for the UI

#### acl.displayed_rule
 - `AclRule`, contains the rule returned from the `acl.get_rule()` method

#### acl.whitelist_enabled
 - `bool`, whether or not the server whitelist is enforced

<br><br>




## AddonManager
Contains the server's add-on configuration. Manages both plugins and mods depending on the server distribution.

Accessed via the global variable `addon`

> Note: Vanilla servers don't support addons, but the `AddonManager` is still included for compatibility with certain scripts. Because of this, the following methods and attributes will return `None`, and empty `list` or `False` with certain checks. Eventually, the empty `AddonManager` for Vanilla servers will be replaced with datapack functionality.

The `AddonManager` conceptualizes add-ons in a few different formats:

- For all functionality relating to data stored locally, add-ons are abstracted as an `AddonFileObject`. The attributes are as follows:
```python
class AddonFileObject():
    self.addon_object_type = "file"

    # The name defined in the '.jar' file 
    self.name <str>

    # Type of add-on: 'forge', 'fabric', or 'bukkit'
    self.type <str>

    # The author defined in the '.jar' file
    self.author <str>

    # A short description defined in the '.jar' file
    self.subtitle <str>

    # A short, unique identifier of the add-on
    self.id <str>

    # The full file path of the '.jar' file
    self.path <str>

    # Add-on version defined in the '.jar' file
    self.addon_version <str>

    # Whether or not the add-on is enabled in auto-mcs
    self.enabled <bool>
```

<br>

- For all functionality relating to data stored on the internet, add-ons are abstracted as an `AddonWebObject`. The attributes are as follows:
```python
class AddonWebObject():
    self.addon_object_type = "web"

    # The name defined on the internet
    self.name <str>

    # Type of add-on: 'forge', 'fabric', or 'bukkit'
    self.type <str>

    # The author defined on the internet
    self.author <str>

    # A short description defined on the internet
    self.subtitle <str>

    # A short, unique identifier of the add-on (the URL slug)
    self.id <str>

    # The full URL of the website hosting the project
    self.url <str>

    # Add-on version defined on the download page
    self.addon_version <str>

    # Whether or not the add-on has a version available for your server
    self.supported <bool>

    # Constains all supported Minecraft versions
    self.versions <str>

    # A long-form description of the project defined on the internet
    self.description <str>

    # A direct download link to the appropriate version for the server
    self.download_url <str>

    # Download version of 'self.download_url'
    self.download_version <str>
```


<br>


**Methods**: <br><br>



### addon.search_addons(*query*)

Returns a `list` of `AddonWebObject` that match your query, sorted in descending order from `index[0]`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `query*` | `str`, partial search term or full add-on name |

<br>



### addon.download_addon(*addon*)

Downloads an add-on from a string of the add-on name, ID, or an `AddonWebObject` provided by `addon.search_addons()`. The file is saved in `addon.addon_path`.

> Note: This method will automatically determine the most compatible version for your server.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `addon*` | `str` or `AddonWebObject` to download |

<br>



### addon.import_addon(*addon_path*)

Imports a `.jar` file to `addon.addon_path`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `addon_path*` | `str`, full system path to the `.jar` file |

<br>



### addon.addon_state(*addon, enabled*)

Enables/disables an installed add-on. Retrieve an `AddonFileObject` with `addon.get_addon()` or from `addon.installed_addons`.

> Note: The server requires a restart for changes to take effect

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `addon*` | `AddonFileObject`, from `addon.get_addon()` or `addon.installed_addons` |  
| `enabled*` | `bool`, to enable or disable the add-on. Defaults to `True` |

<br>



### addon.delete_addon(*addon*)

Permanently deletes an installed add-on. Retrieve an `AddonFileObject` with `addon.get_addon()` or from `addon.installed_addons`.

> Note: The server requires a restart for changes to take effect

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `addon*` | `AddonFileObject`, from `addon.get_addon()` or `addon.installed_addons` |

<br>



### addon.get_addon(*addon_name, online*)

Retrieves an `AddonFileObject` from the installed server add-ons, or `AddonWebObject` from the online repository if `online` is `True`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `addon_name*` | `str`, add-on name |
| `online` | `bool`, retrieves online data instead if `True`. Defaults to `False` |

<br>



### addon.return_single_list()

Returns a single `list` of both enabled and disabled `AddonFileObject` from `addon.installed_addons`.

<br>



### addon.check_for_updates()

Checks the `AddonFileObject.addon_version` for all the installed add-ons against the internet to see if an update is available. Returns `True` if one or more plugins require an update, and the value is stored in the `addon.update_required` attribute.

> Note: Currently, the only way to update add-ons is through the UI

<br>



### addon.check_geyser()

Inspects installed add-ons to determine if Geyser and Floodgate are installed. Returns `True` if they are available, and the value is stored in the `addon.geyser_support` attribute.

<br>



**Attributes**:
> Note: All attributes are read-only, and thus will not change the server data when modified


#### addon.installed_addons
 - `dict`, contains lists of `AddonFileObject` with the following structure:
 ```python
addon.installed_addons = {
    'enabled': [AddonFileObject, AddonFileObject, ...],
    'disabled': [AddonFileObject, AddonFileObject, ...]
}
```

#### addon.addon_path
- `str`, full filesystem path to the server's add-ons directory

#### addon.disabled_addon_path
- `str`, full filesystem path to the server's disabled add-ons directory

#### addon.update_required
 - `bool`, `True` if one or more add-ons can be updated

#### addon.geyser_support
 - `bool`, `True` if Geyser and Floodgate are installed

<br><br>




## ScriptManager
Contains the server's amscript configuration.

Accessed via the global variable `amscript`

The `ScriptManager` conceptualizes scripts in a few different formats:

- For all functionality relating to data stored locally, scripts are abstracted as an `AmsFileObject`. The attributes are as follows:
```python
class AmsFileObject():
    self.addon_object_type = "file"

    # The title defined in the script
    self.title <str>

    # The author defined in the script
    self.author <str>

    # The description defined in the script
    self.description <str>

    # The file name of the script
    self.file_name <str>

    # The full file path of the script
    self.path <str>

    # Add-on version defined in the script
    self.version <str>

    # Whether or not the script is enabled in auto-mcs
    self.enabled <bool>
```

<br>

- For all functionality relating to data stored on the internet, scripts are abstracted as an `AmsWebObject`. The attributes are as follows:
```python
class AmsWebObject():
    self.addon_object_type = "web"

    # The title defined on the internet
    self.title <str>

    # The author defined on the internet
    self.author <str>

    # The description defined on the internet
    self.description <str>

    # The file name defined of the internet
    self.file_name <str>

    # The full URL of the project on the internet
    self.url <str>

    # A direct download link to the appropriate version for the server
    self.download_url <str>

    # The script version defined on the internet
    self.version <str>

    # Whether or not the script is installed
    self.installed <bool>

    # A direct download link to required dependencies, or None
    self.libs <str>
```


<br>


**Methods**: <br><br>



### amscript.search_scripts(*query*)

Returns a `list` of `AmsWebObject` that match your query, sorted in descending order from `index[0]`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `query*` | `str`, partial search term or full script name |

<br>



### amscript.download_script(*script*)

Downloads a script from a string of the script name, or an `AddonWebObject` provided by `addon.search_addons()`. The file is saved in `amscript.script_path`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `script*` | `str` or `AmsWebObject` to download |

<br>



### amscript.import_script(*script_path*)

Imports an `.ams` file to `amscript.script_path`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `script_path*` | `str`, full system path to the `.ams` file |

<br>



### amscript.script_state(*script, enabled*)

Enables/disables an installed script. Retrieve an `AmsFileObject` with `amscript.get_script()` or from `amscript.installed_scripts`.

> Note: The amscript engine requires a restart for changes to take effect

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `script*` | `AmsFileObject`, from `amscript.get_script()` or `amscript.installed_scripts` |  
| `enabled*` | `bool`, to enable or disable the script. Defaults to `True` |

<br>



### amscript.delete_script(*script*)

Permanently deletes an installed script. Retrieve an `AmsFileObject` with `amscript.get_script()` or from `amscript.installed_scripts`.

> Note: The amscript engine requires a restart for changes to take effect

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `script*` | `AmsFileObject`, from `amscript.get_script()` or `amscript.installed_scripts` |

<br>



### amscript.get_script(*script_name, online*)

Retrieves an `AmsFileObject` from the installed server scripts, or `AmsWebObject` from the online repository if `online` is `True`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `script_name*` | `str`, script name |
| `online` | `bool`, retrieves online data instead if `True`. Defaults to `False` |

<br>



### amscript.return_single_list()

Returns a single `list` of both enabled and disabled `AmsFileObject` from `amscript.installed_scripts`.

<br>



**Attributes**:
> Note: All attributes are read-only, and thus will not change the server data when modified


#### amscript.installed_scripts
 - `dict`, contains lists of `AmsFileObject` with the following structure:
 ```python
amscript.installed_scripts = {
    'enabled': [AmsFileObject, AmsFileObject, ...],
    'disabled': [AmsFileObject, AmsFileObject, ...]
}
```

#### amscript.script_path
- `str`, full filesystem path to the global auto-mcs script folder

#### amscript.json_path
- `str`, full filesystem path to the server's amscript `.json` configuration file

<br><br>




# Events

> Note: Every parameter with a * in the table is required for assignment, but doesn't need to be used

> Note: If you're using delay, the `delay=<int>` keyword must be specified 

<br>

## @server events

### @server.on_start

Fired upon process execution by auto-mcs, not when a player can connect.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `data*` | `dict` of startup data, currently `{'date': datetime}` |
| `delay` | `int` or `float`, waits a specified amount of time in seconds before running |

```
@server.on_start(data, delay=0):
    server.log("Server has started!")
```

<br>



### @server.on_stop

Fired upon process termination by auto-mcs, not when `/stop` or a crash is logged.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `data*` | `dict` of shutdown data, currently `{'date': datetime, 'crash': str}` |
| `delay` | `int` or `float`, waits a specified amount of time in seconds before running |

```
@server.on_stop(data, delay=0):
    server.log("Server has stopped!")
```

This event is also fired when the amscript engine is restarted, either through the UI or `!ams reload`.

Since engine restarts create a new memory space, this is useful when an asyncronous task such as a GUI window or another server is running in the background and that process needs to be closed when scripts are reloaded or the server is stopped. There are no parameters for this event.

This example demonstrates how to implement a Tkinter UI that will close and re-open when the engine is restarted:

```
import tkinter as tk
window = tk.Tk()

@server.on_start(data, delay=0):
    window.mainloop()

@server.on_stop():
    window.destroy()
```

<br>



### @server.on_loop

Fired after every `interval`. Loops until the server is closed, or manually cancelled by using `return`.

> Note: The fastest loop supported by this event is 1 tick (50 milliseconds)

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `interval` | `int`, defaults to `1` |
| `unit` | `str`, specifies `interval` scale, can be `'tick'`, `'second'`, `'minute'`, or `'hour'`. Defaults to `'second'` |

```
@server.on_loop(interval=1, unit='minute'):
    server.execute("/kill @e[type=item]")
    server.log_success("Cleaned up items!")
```

<br><br>



## @player events

### @player.on_join

Fired upon player successfully connecting to the server.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `player*` | [**PlayerScriptObject**](#PlayerScriptObject) sent at execution |
| `data*` | `dict` of login data, currently `{'uuid': uuid, 'ip': ip address, 'date': datetime, 'logged-in': True}` |
| `delay` | `int` or `float`, waits a specified amount of time in seconds before running |

```
@player.on_join(player, data):
    player.log(f'Welcome to the server {player}!')
```

<br>



### @player.on_leave

Fired upon player disconnecting from the server.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `player*` | [**PlayerScriptObject**](#PlayerScriptObject) sent at execution |
| `data*` | `dict` of logout data, currently `{'uuid': uuid, 'ip': ip address, 'date': datetime, 'logged-in': False}` |
| `delay` | `int` or `float`, waits a specified amount of time in seconds before running |

```
@player.on_leave(player, data):
    server.execute(f'/say Goodbye, {player}!')
```

<br>



### @player.on_message

Fired upon player sending a message in the chat, excluding commands.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `player*` | [**PlayerScriptObject**](#PlayerScriptObject) sent at execution |
| `message*` | `str` of the message |
| `delay` | `int` or `float`, waits a specified amount of time in seconds before running |

```
@player.on_message(player, message):
    if "can i have op" in message.lower():
        acl.ban_player(player)
```

<br>



### @player.on_death

Fired upon player dying to the environment or another player.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `player*` | [**PlayerScriptObject**](#PlayerScriptObject) sent at execution of the victim |
| `enemy*` | [**PlayerScriptObject**](#PlayerScriptObject) sent at execution of the attacker (`None` if player was killed by the environment) |
| `message*` | `str` of the message |
| `delay` | `int` or `float`, waits a specified amount of time in seconds before running |

```
@player.on_death(player, enemy, message):
    if enemy:
        enemy.log(f"Did you know: murder is a crime {enemy}?")
        acl.ban_player(enemy)
    else:
        player.log(f"You should really be more careful {player}!")
```

<br>



### @player.on_achieve

Fired upon a player earning an advancement.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `player*` | [**PlayerScriptObject**](#PlayerScriptObject) sent at execution |
| `advancement*` | `str` of the advancement title. List of all advancement titles can be found [here](https://minecraft.fandom.com/wiki/Advancement#List_of_advancements) |
| `delay` | `int` or `float`, waits a specified amount of time in seconds before running |

```
@player.on_achieve(player, advancement):
    if advancement == 'Stone Age':
        player.log_success(f'Seriously {player}?? Pick on someone your own size!')
```

<br>



### @player.on_alias

Used for registering custom commands and augmenting existing ones.

> Note: Commands will start with `!` therefore making them visible when executed by a player from the in-game chat, though the feedback is hidden when using the `server.log()` and `player.log()` methods. They are completely hidden if executed from the server console.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `player*` | [**PlayerScriptObject**](#PlayerScriptObject) sent at execution |
| `command*` | `str` to specify the command verb |
| `arguments` | `dict` specifying requirement for execution `{'arg1': True}` where `True` denotes a required argument. Only the last arguments can be optional |
| `permission`| `str`, used to restrict execution to privileged users. Can be `'anyone'`, `'op'`, `'server'`, or a [**custom player permission**](#playerset_permissionpermission-enabled). Defaults to `'anyone'`|
| `description` | `str` for `!help` menu. Command will be shown to users which meet the minimum permission level |
| `hidden` | `bool`, defaults to `False`. Hides command from all users (they can still be executed) and disables the wrapper functionality described below. Useful for augmenting existing commands |

```
@player.on_alias(player, command='test', arguments={'arg1': True, 'arg2': False}, permission='op'):
    server.log(f'{player.name} executed {command} with the following arguments: {arguments}')
```

> Note: Every alias automatically validates syntax and checks the player's permission level before execution

Following the above example when a player with the `anyone` privilege executes `!test foo bar`:
- amscript will determine that the player doesn't meet the minimum permission and will fail
- Permission tree is `server` > `op` > `anyone`

Following the above example when a player with the `op` or `server` privilege executes `!test foo bar`:

- `arguments` will be converted to `{'arg1': 'foo', 'arg2': 'bar'}` after execution, and can be acccessed in the function as such
- Calling `arguments['arg1']` will return the value of `'foo'`
