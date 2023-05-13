# Overview

The Auto-MCS scripting API (amscript) is available to create universal plugins for your Auto-MCS servers. It functions primarily as an asynchronous wrapper which fires events from what happens in game. Because of this mechanic, a single script will work with every Vanilla, CraftBukkit (and derivatives), Forge, and Fabric server regardless of game version.


# Objects
> Note: All object attributes are read-only, but can be manipulated with their methods


## ServerScriptObject
Contains the server's running configuration from the `server.properties` to the list of connected players.

Accessed via the global variable `server`

Methods:

### server.get_player(*selector*)

Returns **PlayerScriptObject** on match, else `None`. Only returns the first match.



## PlayerScriptObject
Contains current player configuration, from their username, UUID, and all their NBT data

Accessed by an applicable event, or by the `server.get_player()` method

Methods:

### player.log(*message, style*)

Returns **PlayerScriptObject** on match, else `None`

change the formatting to an arg table later: `style` can be 'standard', `'error'`, `'success'`





# Events

> Note: Every parameter with a * in the table is required for assignment, but doesn't need to be used

> Note: If you're using delay, the `delay=<int>` keyword must be specified 


## @server events

### @server.on_start

Fired upon process execution by Auto-MCS, not when a player can connect.

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `data*` | `dict` of startup data, currently `{'date': datetime}` |
| `delay` | Waits a specified amount of time in seconds before running |

```
@server.on_start(data, delay=0):
    server.execute("/say Server has started!")
```



--------------------------------------------
### @server.on_stop

Fired upon process termination by Auto-MCS, not when `/stop` or a crash is logged.

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `data*` | `dict` of shutdown data, currently `{'date': datetime, 'crash': str}` |
| `delay` | Waits a specified amount of time in seconds before running |

```
@server.on_stop(data, delay=0):
    server.execute("/say Server has stopped!")
```



--------------------------------------------
### @server.on_loop

Fired after every `interval`. Loops until the server is closed, or manually cancelled with `return`.

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `interval` | `int`, defaults to `1` |
| `unit` | Specifies `interval` scale, can be `'tick'`, `'second'`, `'minute'`, or `'hour'`. Defaults to `'second'` |

```
@server.on_loop(interval=1, unit='minute'):
    server.execute("/kill @e[type=item]")
    server.execute("/say Cleaned up items!")
```



--------------------------------------------
### @server.alias

Used for registering custom commands and augmenting existing ones.

> Note: Commands will start with `!` therefore making them visible when executed from the in-game chat, though the feedback is hidden

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `player*` | **PlayerScriptObject** sent at execution |
| `command*` | `str` to specify the command verb |
| `arguments` | `dict` specifying requirement for execution `{'arg1': True}` where `True` denotes a required argument. Only the last argument can be optional |
| `permission`| Used to restrict execution to privileged users. Can be `'anyone'`, `'op'`, or `'server'`. Defaults to `'anyone'`|
| `description` | `str` for `!help` menu. Commands will be shown to users with the minimum permission level |
| `hidden` | `bool`, defaults to `False`. Hides command from all users (they can still be executed) and disables the wrapper functionality described below. Useful for augmenting existing commands |

```
@server.alias(player, command='test', arguments={'arg': True, 'arg2': False}, permission='op', description='Test command'):
    server.execute(f'/say {player.name} executed {command} with the following arguments: {arguments}')
```

> Note: Every alias automatically validates syntax and checks the player's permission level before execution

Following the above example when a player with the `anyone` privilege executes `!test foo bar`:
- Auto-MCS will determine that the player doesn't meet the minimum permission and will fail
- Permission tree is `server` > `op` > `anyone`

Following the above example when a player with the `op` or `server` privilege executes `!test foo bar`:

- `arguments` will be converted to `{'arg1': 'foo', 'arg2': 'bar'}` after execution, and can be acccessed in the function as such
- Calling `arguments['arg1']` will return the value of `'foo'`



## @player events

### @player.on_join

Fired upon player successfully connecting to the server.

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `player*` | **PlayerScriptObject** sent at execution |
| `data*` | `dict` of login data, currently `{'ip': ip address, 'date': datetime, 'logged-in': True}` |
| `delay` | Waits a specified amount of time in seconds before running |

```
@player.on_join(player, data):
    server.execute(f'/say Welcome to the server {player.name}!')
```



--------------------------------------------
### @player.on_leave

Fired upon player disconnecting from the server.

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `player*` | **PlayerScriptObject** sent at execution |
| `data*` | `dict` of logout data, currently `{'ip': ip address, 'date': datetime, 'logged-in': False}` |
| `delay` | Waits a specified amount of time in seconds before running |

```
@player.on_leave(player, data):
    server.execute(f'/say Goodbye, {player.name}!')
```



--------------------------------------------
### @player.on_message

Fired upon player sending a message in the chat, excluding commands.

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `player*` | **PlayerScriptObject** sent at execution |
| `message*` | `str` of the message |
| `delay` | Waits a specified amount of time in seconds before running |

```
@player.on_message(player, message):
    if "can i have op" in message.lower():
        acl.ban_player(player)
```
