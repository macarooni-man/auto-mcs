# Initialize amscript engine for static testing
def init_ams_engine():
    import amscript
    import telepath
    import constants
    import svrmgr
    import time

    constants.server_manager = svrmgr.ServerManager()
    constants.server_manager.open_server(server_name)
    while not constants.server_manager.current_server.script_manager:
        time.sleep(0.1)

    constants.server_manager.current_server.run_data = {
        'log': [], 'network': {'address': None}, 'player-list': {},
        'process-hooks': [],
        'performance': {'ram': 0, 'cpu': 0, 'uptime': '00:00:00:00',
        'current-players': []}
    }
    so = amscript.ScriptObject(constants.server_manager.current_server)
    so.construct()
    return so.server_script_obj


# Server to test
server_name = 'Shop Test'
server = init_ams_engine()


# Test amscript code below
print(server.get_player('KChicken', offline=True).position)
