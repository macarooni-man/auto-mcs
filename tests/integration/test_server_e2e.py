import pytest
import os
from source.core.server.manager import ServerObject
from unittest.mock import MagicMock

@pytest.mark.slow
def test_server_dir_resolution(sandbox_paths):
    mock_manager = MagicMock()
    mock_manager.update_list = {}
    
    server_name = "E2EIntegrationServer"
    server_dir = os.path.join(sandbox_paths.servers, server_name)
    os.makedirs(server_dir, exist_ok=True)
    
    config_file = os.path.join(server_dir, "auto-mcs.ini")
    with open(config_file, "w") as f:
        f.write(f"[general]\nserverName = {server_name}\nisFavorite = true\nallocatedMemory = 4\nserverType = fabric\nserverVersion = 1.20.1\n")
        
    properties_file = os.path.join(server_dir, "server.properties")
    with open(properties_file, "w") as f:
        f.write("level-name=world\nwhite-list=false\n")
        
    server = ServerObject(mock_manager, server_name)
    
    assert server.name == server_name
    assert server.favorite is True
    assert server.dedicated_ram == "4"
    assert server.type == "fabric"
    assert server.version == "1.20.1"
