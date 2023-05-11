# Overview

The Auto-MCS scripting API (amscript) is available to create universal plugins for your Auto-MCS servers. It functions primarily as an asynchronous wrapper which fires events from what happens in game. Because of this mechanic, a single script will work with every Vanilla, CraftBukkit (and derivatives), Forge, and Fabric server regardless of game version.




# Events

> Note: Every parameter with a * in the table is required for assignment, but doesn't need to be used


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
### @server.alias

Used for registering custom commands and augmenting existing ones.

> Note: Commands that start with '/' don't work in Vanilla servers, instead use a different special character

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `player*` | **PlayerScriptObject** sent at execution |
| `command*` | `str` with a special character in the beginning, ie `/MyCommand` |
| `arguments` | `dict` specifying requirement for execution `{'arg1': True}` where `True` denotes a required argument. Only the last argument can be optional |
| `permission`| Can be `'anyone'`, `'op'`, or `'server'`. Defaults to `'anyone'`|
| `description` | `str` for `/help` menu. Commands will be shown to users with the minimum permission level |
| `hidden` | `bool`, defaults to `False`. Hides command from all users (they can still be executed) and disables the wrapper functionality described below. Useful for augmenting existing commands |

```
@server.alias(player, command='!test', arguments={'arg': True, 'arg2': False}, permission='op', description='Test command'):
    server.execute(f'/say {player.name} executed {command} with the following arguments: {arguments}')
```

> Note: Every alias automatically validates syntax and checks the player's permission before execution

Following the above example when a player with the `anyone` privilege executes `!test foo bar`:
- Auto-MCS will determine that the player doesn't meet the minimum permission and will fail
- Permission tree is `server` > `op` > `anyone`

Following the above example when a player with `op` or `server` privilege executes `!test foo bar`:

- `arguments` will be converted to `{'arg1': 'foo', 'arg2': 'bar'}` after execution, and can be acccessed in the function as such
- Calling `arguments['arg1']` will return the value of `'foo'`



--------------------------------------------
### @player.on_join

Fired upon player successfully connecting to the server.

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `player*` | **PlayerScriptObject** sent at execution |
| `data*` | `dict` of login data, currently `{'ip': ip address, 'date': datetime, 'logged-in': True}` |

```
@player.on_join(player, data):
    server.execute(f'/say Welcome to the server {user.name}!')
```



--------------------------------------------
### @player.on_leave

Fired upon player disconnecting from the server.

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `player*` | **PlayerScriptObject** sent at execution |
| `data*` | `dict` of logout data, currently `{'ip': ip address, 'date': datetime, 'logged-in': False}` |

```
@player.on_leave(player, data):
    server.execute(f'/say Goodbye, {user.name}!')
```



--------------------------------------------
### @player.on_message

Fired upon player disconnecting from the server.

Accepted parameters:
| Parameter | Description |
| --- | --- |
| `player*` | **PlayerScriptObject** sent at execution |
| `data*` | `dict` of login data, currently `{'ip': ip address, 'date': datetime, 'logged-in': True}` |

```
@player.on_message(player, data):
    server.execute(f'/say Goodbye, {user.name}!')
```
