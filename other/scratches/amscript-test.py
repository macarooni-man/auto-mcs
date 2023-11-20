import time
from datetime import datetime
from amscript import ScriptObject, PlayerScriptObject
import functools
from svrmgr import ServerObject


server_obj = ServerObject('bedrock-test')
server_obj.run_data = {
    'log': [],
    'performance': [],
    'player-list': {'KChicken': {'uuid': None, 'ip': '127.0.0.1:1234', 'date': None, 'logged-in': True}},
    'network': {'address': '1.1.1.1'},
    'process-hooks': []
}
while not server_obj.script_manager:
    time.sleep(0.1)

so = ScriptObject(server_obj)
# print(so.scripts)
so.construct()

# # int(so.aliases)
# print(so.server_script_obj.aliases)
# player = PlayerScriptObject(so.server_script_obj, 'KChicken')
# player.inventory.hotbar[1].item = 'twwdwd'



# print(so.function_dict)
# so.call_event('@player.on_message', (PlayerScriptObject(so.server_script_obj, 'KChicken'), 'test'))



# so.deconstruct()
