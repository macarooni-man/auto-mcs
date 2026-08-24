import pytest
import os
import shutil
import tempfile

@pytest.fixture(scope="function", autouse=True)
def sandbox_paths():
    temp_dir = tempfile.mkdtemp(prefix="automcs_test_")
    from source.core.constants import paths
    
    orig_values = {}
    orig_app_folder = paths.app_folder
    
    for folder in ['Servers', 'Config', 'Tools', 'Logs', 'Backups', 'Downloads', 'Uploads', 'Temp', 'Cache']:
        os.makedirs(os.path.join(temp_dir, folder), exist_ok=True)
        
    for attr in dir(paths):
        if attr.startswith('__'):
            continue
        val = getattr(paths, attr)
        if isinstance(val, str):
            orig_values[attr] = val
            if orig_app_folder in val:
                setattr(paths, attr, val.replace(orig_app_folder, temp_dir))
            elif attr in ['app_folder', 'servers', 'config', 'tools', 'logs', 'backups', 'downloads', 'uploads', 'temp', 'cache']:
                new_val = os.path.join(temp_dir, attr.capitalize() if attr != 'app_folder' else '')
                setattr(paths, attr, new_val)

    os.makedirs(paths.telepath, exist_ok=True)
    os.makedirs(paths.scripts, exist_ok=True)
    
    yield paths
    
    for attr, val in orig_values.items():
        setattr(paths, attr, val)
        
    shutil.rmtree(temp_dir, ignore_errors=True)
