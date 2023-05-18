import time
from datetime import datetime
from amscript import ScriptObject, PlayerScriptObject
import functools
from svrmgr import ServerObject


so = ScriptObject(ServerObject('test'))
time.sleep(1)
# print(so.scripts)
so.construct()

# int(so.aliases)
print(so.server_script_obj.aliases)



# print(so.function_dict)
so.call_event('@player.on_message', (PlayerScriptObject(so.server_script_obj, 'KChicken'), 'test'))



so.deconstruct()
