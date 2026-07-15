import pytest
import os
from source.core.server.manager import ServerObject
from unittest.mock import MagicMock

def test_mock_server_launch(sandbox_paths):
    mock_manager = MagicMock()
    mock_manager.update_list = {}
    
    server_name = "TestSvr"
    server_dir = os.path.join(sandbox_paths.servers, server_name)
    os.makedirs(server_dir, exist_ok=True)
    
    config_file = os.path.join(server_dir, "auto-mcs.ini")
    with open(config_file, "w") as f:
        f.write(f"[general]\nserverName = {server_name}\nisFavorite = false\nallocatedMemory = 2\nserverType = vanilla\nserverVersion = 1.20.1\n")
        
    properties_file = os.path.join(server_dir, "server.properties")
    with open(properties_file, "w") as f:
        f.write("level-name=world\nwhite-list=false\n")
        
    server = ServerObject(mock_manager, server_name)
    
    assert server.name == server_name
    assert server.favorite is False
    assert server.dedicated_ram == "2"
    assert server.type == "vanilla"
    assert server.version == "1.20.1"
