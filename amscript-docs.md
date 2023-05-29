# Overview

The Auto-MCS scripting API (*amscript*) is available to create universal plugins for your Auto-MCS servers. It functions primarily as an asynchronous wrapper which fires events from what happens in game. Because of this mechanic, a single script will work with every Vanilla, CraftBukkit (and derivatives), Forge, and Fabric server regardless of game version. <br><br><br>




# Objects
> Note: All object attributes are read-only, but can be manipulated with their methods

## ServerScriptObject
Contains the server's running configuration from the `server.properties`, to the list of connected players.

Accessed via the global variable `server`

**Methods**: <br><br>



### server.log(*message, log_type*)

Sends a custom log event to the console. This output is displayed only while the server is running, and is not saved to the log file.

- `server.log_success()`, `server.log_warning()`, and `server.log_error()` methods can also be used, and only require the `message` parameter.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `message*` | `str` of log content |
| `log_type` | `str` can be `'info'`, `'success'`, `'warning'` or `'error'`. Defaults to `'info'` |

<br>



### server.version_check(*comparator, version*)

Compares server version to `version` with the `comparator`, returns `bool`.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `comparator*` | `str`, can be `'='`, `'<'`, `'<='`, `'>'`, or `'>='` |
| `version*` | `str`, any Minecraft version, i.e. `'1.17.1'` |

<br>



### server.get_player(*selector*) # NEEDS IMPLEMENTATION

> amscript uses a custom selector parser, and therefore tags like `@a[nbt={}]` should work in older versions

server.get_players # ALSO NEEDS IMPLEMENTATION

Returns [**PlayerScriptObject**](#PlayerScriptObject) on match, else `None`. Only returns the first match.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `selector*` | `str` of username, or a valid Minecraft selector. Only players will be matched |
| `reverse` | `bool` selects last match on `True`. Defaults to `False` |


<br>



**Attributes**:
> Note: All attributes are read-only, and thus will not change the server data when modified


#### server.name
 - `str`, server's current filename

#### server.version
 - `str`, Minecraft version of the server, i.e. `'1.16.3'`

#### sever.build
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

#### server.persistent
 - `dict`, persistent variable storage for saving information between server restarts, or script reloads
 - Assigning or updating a key in the `server.persistent` dictionary will automatically save it, and can be accessed via the same key persistently until it is changed again, or deleted. Data will only be saved for the server referenced in the object.

> Warning: persistent data is only saved properly when the server shuts down gracefully, if the computer crashes or the server process is terminated forcefully, the persistent data will likely revert to previous values

<br><br>



## PlayerScriptObject
Contains current player configuration from their username, UUID, to all their NBT data

Accessed by an applicable event, or by the `server.get_player()` method

**Methods**: <br><br>




### player.log(*message, color, style*)

Sends a private message to the chat of the player with formatting support.
Useful for command feedback with a [**@server.alias**](#serveralias) event

- `player.log_success()`, `player.log_warning()`, and `player.log_error()` methods can also be used, and only require the `message` parameter.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `message*` | `str` of username, or selector. Only players will be matched |
| `color` | `str` of Minecraft color ID, all values for `/tellraw` are accepted. List of IDs can be found [here](https://minecraft.fandom.com/wiki/Formatting_codes#Color_codes) |
| `style` | `str`, can be `'normal'`, `'italic'`, `'bold'`, `'strikethrough'`, `'underlined'`, and `'obfuscated'`. Defaults to `'italic'` |

<br>



**Attributes**:
> Note: All attributes are read-only, and thus will not change playerdata when modified

> Note: Versions prior to 1.13 load NBT from playerdata.dat, which is only updated every couple of minutes or so. Any version between 1.8-1.13, though, will have updated position data. 1.13 and later retrieves *all* of the most recent NBT data.


#### player.name
 - `str`, player's current username

#### player.uuid
 - `str`, player's Universally Unique IDentifier *(`None` pre-1.8)*

#### player.ip_address
 - `str`, currently connected IP address

#### player.is_server
 - `bool`, if current object was created from the console
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
 - Value of `'overworld'`, `'the_nether'`, or `'the_end'`

#### player.active_effects
 - `dict` of `EffectObject`, player's current effects
 - Speed, for example can be accessed with `player.active_effects['speed'].duration`

#### player.inventory
 - `InventoryObject`, organized list of all items in the player's inventory
 - Attributes are `player.inventory.selected_item`, `player.inventory.offhand`, `player.inventory.hotbar`, `player.inventory.armor`, `player.inventory.inventory`
 - Each list is full of `ItemObject`, which can be accessed via lowercase NBT attributes like in game, and with Pythonic logic: `player.inventory.selected_item.tag.display.name` or `if "diamond_sword" in player.inventory`

#### player.persistent
 - `dict`, persistent variable storage for saving information between server restarts, or script reloads
 - Assigning or updating a key in the `player.persistent` dictionary will automatically save it, and can be accessed via the same key persistently until it is changed again, or deleted. Data will be saved only for the player referenced by the object, and only for the server. Data will not persist between different servers.

> Warning: persistent data is only saved properly when the server shuts down gracefully, if the computer crashes or the server process is terminated forcefully, the persistent data will likely revert to previous values

<br><br>



# Events

> Note: Every parameter with a * in the table is required for assignment, but doesn't need to be used

> Note: If you're using delay, the `delay=<int>` keyword must be specified 

<br>

## @server events

### @server.on_start

Fired upon process execution by Auto-MCS, not when a player can connect.

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

Fired upon process termination by Auto-MCS, not when `/stop` or a crash is logged.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `data*` | `dict` of shutdown data, currently `{'date': datetime, 'crash': str}` |
| `delay` | `int` or `float`, waits a specified amount of time in seconds before running |

```
@server.on_stop(data, delay=0):
    server.log("Server has stopped!")
```

<br>



### @server.on_loop

Fired after every `interval`. Loops until the server is closed, or manually cancelled with `return`.

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
    player.log(f'Welcome to the server {player.name}!')
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
    server.execute(f'/say Goodbye, {player.name}!')
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



### @player.on_alias

Used for registering custom commands and augmenting existing ones.

> Note: Commands will start with `!` therefore making them visible when executed by a player from the in-game chat, though the feedback is hidden when using the `server.log()` and `player.log()` methods. They are completely hidden if executed from the server console.

**Accepted parameters**:
| Parameter | Description |
| --- | --- |
| `player*` | [**PlayerScriptObject**](#PlayerScriptObject) sent at execution |
| `command*` | `str` to specify the command verb |
| `arguments` | `dict` specifying requirement for execution `{'arg1': True}` where `True` denotes a required argument. Only the last argument can be optional |
| `permission`| `str`, used to restrict execution to privileged users. Can be `'anyone'`, `'op'`, or `'server'`. Defaults to `'anyone'`|
| `description` | `str` for `!help` menu. Command will be shown to users which meet the minimum permission level |
| `hidden` | `bool`, defaults to `False`. Hides command from all users (they can still be executed) and disables the wrapper functionality described below. Useful for augmenting existing commands |

```
@player.on_alias(player, command='test', arguments={'arg': True, 'arg2': False}, permission='op', description='Test command'):
    server.log(f'{player.name} executed {command} with the following arguments: {arguments}')
```

> Note: Every alias automatically validates syntax and checks the player's permission level before execution

Following the above example when a player with the `anyone` privilege executes `!test foo bar`:
- Auto-MCS will determine that the player doesn't meet the minimum permission and will fail
- Permission tree is `server` > `op` > `anyone`

Following the above example when a player with the `op` or `server` privilege executes `!test foo bar`:

- `arguments` will be converted to `{'arg1': 'foo', 'arg2': 'bar'}` after execution, and can be acccessed in the function as such
- Calling `arguments['arg1']` will return the value of `'foo'`
