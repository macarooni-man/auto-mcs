import pytest
import os
import json
import requests
from unittest.mock import patch, MagicMock
from source.core.server.manager import ServerManager, ServerObject
from source.core.telepath import TelepathManager, SessionDict, RemoteServerObject
from source.core.constants import paths, telepath_download, telepath_upload

def test_session_dict_comprehensive():
    sd = SessionDict()
    
    sess1 = {
        "host": "host-a",
        "user": "user1",
        "session_id": "sess_1",
        "ip": "192.168.1.5"
    }
    sess2 = {
        "host": "host-b",
        "user": "user2",
        "session_id": "sess_2",
        "ip": "192.168.1.6"
    }
    
    sd["sess_1"] = sess1
    sd["sess_2"] = sess2

    # 1. Direct key lookups
    assert sd["sess_1"] == sess1
    assert sd["sess_2"] == sess2

    # 2. Fallback IP lookups
    assert sd["192.168.1.5"] == sess1
    assert sd["192.168.1.6"] == sess2

    # 3. Fallback Hostname lookups
    assert sd["host-a"] == sess1
    assert sd["host-b"] == sess2

    # 4. KeyError for missing keys/IPs/hosts
    with pytest.raises(KeyError):
        _ = sd["non_existent_key"]
    with pytest.raises(KeyError):
        _ = sd["192.168.1.100"]
    with pytest.raises(KeyError):
        _ = sd["host-c"]

    # 5. __contains__ (in) verification
    assert "sess_1" in sd
    assert "192.168.1.5" in sd
    assert "host-a" in sd
    assert "non_existent" not in sd

    # 6. get() method verification
    assert sd.get("sess_1") == sess1
    assert sd.get("192.168.1.5") == sess1
    assert sd.get("host-a") == sess1
    assert sd.get("non_existent") is None
    assert sd.get("non_existent", "default_val") == "default_val"

    # 7. Dictionary iteration and values
    assert len(sd) == 2
    assert list(sd.keys()) == ["sess_1", "sess_2"]
    assert list(sd.values()) == [sess1, sess2]
    assert list(sd.items()) == [("sess_1", sess1), ("sess_2", sess2)]

    # 8. Deleting and popping keys
    del sd["sess_1"]
    assert len(sd) == 1
    assert "sess_1" not in sd
    assert "192.168.1.5" not in sd
    
    popped = sd.pop("sess_2")
    assert popped == sess2
    assert len(sd) == 0

def test_session_dict_mutating_operations():
    sd = SessionDict()
    sess = {
        "host": "sys-a",
        "user": "u1",
        "session_id": "s_1",
        "ip": "10.0.0.5"
    }
    
    # Test setdefault
    res = sd.setdefault("s_1", sess)
    assert res == sess
    assert sd["s_1"] == sess
    
    # Test update
    new_sess = {
        "host": "sys-b",
        "user": "u2",
        "session_id": "s_2",
        "ip": "10.0.0.6"
    }
    sd.update({"s_2": new_sess})
    assert len(sd) == 2
    assert sd["sys-b"] == new_sess

    # Test clear
    sd.clear()
    assert len(sd) == 0
    assert not sd

def test_telepath_multi_port_registration(sandbox_paths):
    with patch('source.core.telepath.AuditLogger', create=True):
        manager = ServerManager()

        # Add Docker container 1
        inst1 = {
            "host": "127.0.0.1",
            "port": 8001,
            "nickname": "container-1",
            "hostname": "h1"
        }
        manager.add_telepath_server(inst1)

        # Add Docker container 2 on same IP, different port
        inst2 = {
            "host": "127.0.0.1",
            "port": 8002,
            "nickname": "container-2",
            "hostname": "h2"
        }
        manager.add_telepath_server(inst2)

        # 1. Assert both coexist under unique keys
        assert "127.0.0.1:8001" in manager.telepath_servers
        assert "127.0.0.1:8002" in manager.telepath_servers

        # 2. Assert nickname renaming updates correct key
        target_inst = manager.telepath_servers["127.0.0.1:8001"]
        manager.rename_telepath_server(target_inst, "renamed-1")
        assert manager.telepath_servers["127.0.0.1:8001"]["nickname"] == "renamed-1"
        assert manager.telepath_servers["127.0.0.1:8002"]["nickname"] == "container-2"

        # 3. Assert removing works for correct key
        manager.remove_telepath_server(target_inst)
        assert "127.0.0.1:8001" not in manager.telepath_servers
        assert "127.0.0.1:8002" in manager.telepath_servers

def test_telepath_add_server_with_empty_nickname(sandbox_paths):
    with patch('source.core.telepath.AuditLogger', create=True):
        manager = ServerManager()

        inst = {
            "host": "10.0.0.1",
            "port": 7001,
            "nickname": "",
            "hostname": "my-cool-server-host"
        }
        # Adding server without nickname should format it from hostname
        manager.add_telepath_server(inst)
        assert "10.0.0.1:7001" in manager.telepath_servers
        assert manager.telepath_servers["10.0.0.1:7001"]["nickname"] == "my-cool-server-host"

def test_telepath_migration_on_startup(sandbox_paths):
    # Save a legacy format configuration (using IP as key) to telepath-servers.json
    legacy_config = {
        "192.168.1.200": {
            "port": 7001,
            "nickname": "LegacySvr",
            "hostname": "old-host"
        }
    }
    os.makedirs(sandbox_paths.telepath, exist_ok=True)
    with open(sandbox_paths.telepath_servers, "w") as f:
        f.write(json.dumps(legacy_config))

    with patch('source.core.telepath.AuditLogger', create=True):
        manager = ServerManager()

        # Assert manager loaded and migrated legacy key to host:port format
        assert "192.168.1.200:7001" in manager.telepath_servers
        assert "192.168.1.200" not in manager.telepath_servers
        assert manager.telepath_servers["192.168.1.200:7001"]["host"] == "192.168.1.200"

def test_create_view_list_port_extraction(sandbox_paths):
    # Create multiple remote servers mock
    remote_data = {
        "127.0.0.1:7001": {
            "port": 7001,
            "nickname": "Docker1"
        },
        "127.0.0.1:7002": {
            "port": 7002,
            "nickname": "Docker2"
        }
    }

    with patch('source.core.telepath.AuditLogger', create=True):
        manager = ServerManager()
        
        # Mock api_manager to verify host/port inputs
        mock_api_manager = MagicMock()
        mock_api_manager.request.return_value = [{"name": "remote-svr", "favorite": False, "last_modified": 12345.67}]
        with patch('source.core.constants.api_manager', mock_api_manager):
            view_list = manager.create_view_list(remote_data)
            
            # Assert api_manager was called with clean host IPs (not containing port)
            calls = mock_api_manager.request.call_args_list
            assert len(calls) == 2
            
            # First call arguments
            args1, kwargs1 = calls[0]
            assert kwargs1["host"] == "127.0.0.1"
            assert kwargs1["port"] in [7001, 7002]
            
            # Second call arguments
            args2, kwargs2 = calls[1]
            assert kwargs2["host"] == "127.0.0.1"
            assert kwargs2["port"] in [7001, 7002]

def test_jwt_tokens_multi_port_header_isolation(sandbox_paths):
    with patch('source.core.telepath.AuditLogger', create=True):
        manager = TelepathManager()

        # Add mock tokens for same IP, different ports
        manager.jwt_tokens["127.0.0.1:7001"] = "token_port_7001"
        manager.jwt_tokens["127.0.0.1:8002"] = "token_port_8002"
        manager.jwt_tokens["127.0.0.1"] = "legacy_token_port"

        # 1. Query headers with port argument (gets port-specific token)
        h7001 = manager._get_headers("127.0.0.1", port=7001)
        assert h7001["Authorization"] == "Bearer token_port_7001"

        h8002 = manager._get_headers("127.0.0.1", port=8002)
        assert h8002["Authorization"] == "Bearer token_port_8002"

        # 2. Query headers with legacy/unspecified port (falls back to legacy token)
        h_legacy = manager._get_headers("127.0.0.1")
        assert h_legacy["Authorization"] == "Bearer legacy_token_port"

def test_telepath_session_coexistence(sandbox_paths):
    with patch('source.core.telepath.AuditLogger', create=True):
        manager = TelepathManager()

        # Session A from System A
        sess_a = {
            "host": "my-cloned-computer",
            "user": "mathew",
            "session_id": "sess_a_id",
            "id": "hardware_id_system_a",
            "ip": "127.0.0.1"
        }
        manager._save_session(sess_a)

        # Session B from System B (shares host/user, but different hardware ID)
        sess_b = {
            "host": "my-cloned-computer",
            "user": "mathew",
            "session_id": "sess_b_id",
            "id": "hardware_id_system_b",
            "ip": "127.0.0.1"
        }
        manager._save_session(sess_b)

        # Assert BOTH sessions successfully coexist in manager
        ids = [s["id"] for s in manager.authenticated_sessions]
        assert "hardware_id_system_a" in ids
        assert "hardware_id_system_b" in ids

def test_check_telepath_servers_mixed_status(sandbox_paths):
    with patch('source.core.telepath.AuditLogger', create=True):
        manager = ServerManager()

        # Add two servers
        manager.telepath_servers = {
            "127.0.0.1:7001": {
                "port": 7001,
                "nickname": "OnlineSvr"
            },
            "127.0.0.1:7002": {
                "port": 7002,
                "nickname": "OfflineSvr"
            }
        }

        # Mock requests.get to return True for port 7001, and raise exception for 7002
        def mock_get(url, *args, **kwargs):
            mock_resp = MagicMock()
            if "7001" in url:
                mock_resp.json.return_value = True
                return mock_resp
            raise requests.exceptions.ConnectionError("Offline")

        # Mock login payload
        mock_api_manager = MagicMock()
        mock_api_manager.login.return_value = {"nickname": "OnlineSvr", "status": "online"}

        with patch('requests.get', mock_get), patch('source.core.constants.api_manager', mock_api_manager):
            online_list = manager.check_telepath_servers()
            
            # 127.0.0.1:7001 should be online and kept
            assert "127.0.0.1:7001" in online_list
            # 127.0.0.1:7002 should be offline and dropped from online list
            assert "127.0.0.1:7002" not in online_list

def test_telepath_download_upload_failures(sandbox_paths):
    # Setup mock file to upload
    temp_file = os.path.join(sandbox_paths.temp, "test_upload.txt")
    with open(temp_file, "w") as f:
        f.write("Some mock data")

    mock_api_manager = MagicMock()
    # Mock upload request failing
    mock_api_manager._retry_wrapper.return_value = None
    
    with patch('source.core.constants.api_manager', mock_api_manager):
        # 1. Upload returns None on failure
        res = telepath_upload({"host": "127.0.0.1", "port": 7001}, temp_file)
        assert res is None

        # 2. Download returns None on failure (legacy behavior)
        res_dl = telepath_download({"host": "127.0.0.1", "port": 7001}, "some/remote/path.txt", sandbox_paths.downloads)
        assert res_dl is None


def test_client_ip_cleaning():
    with patch('source.core.telepath.AuditLogger', create=True):
        manager = TelepathManager()

        # Mock public_encrypt and requests to see if clean IP is used
        manager.auth.public_encrypt = MagicMock()
        
        # Test login splits host:port
        manager.login("127.0.0.1:7001", 7001)
        from unittest.mock import ANY
        manager.auth.public_encrypt.assert_called_with("127.0.0.1", 7001, ANY)

        # Test request_pair splits host:port
        manager.request_pair("127.0.0.1:8002", 8002)
        manager.auth.public_encrypt.assert_called_with("127.0.0.1", 8002, ANY)
