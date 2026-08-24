import pytest
from unittest.mock import patch
from source.core.telepath import TelepathManager

def test_telepath_initialization(sandbox_paths):
    with patch('source.core.telepath.AuditLogger', create=True):
        manager = TelepathManager()
        assert manager.version == "1.2.2"
        assert manager.running is False
