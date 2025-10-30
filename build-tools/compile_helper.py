from PyInstaller.building.build_main import Tree
from PyInstaller.building.datastruct import TOC
from re import findall
from glob import glob
import os


# ---------------------------------------------- Global Variables ------------------------------------------------------

tools_path:  str = os.path.dirname(__file__)
source_path: str = os.path.abspath(os.path.join(tools_path, '..', 'source'))

excluded_imports: list[str] = [
    'pandas', 'matplotlib', 'numpy', 'scipy', 'pkg_resources',
    'unittest', 'test', 'pydoc_data', 'xmlrpc', 'http.server',
    'idlelib','lib2to3', 'pydoc_data', 'turtledemo'
]

# ---------------------------------------------- Helper Methods --------------------------------------------------------

# Collect all submodules in '../source'
def collect_internal_modules() -> list:
    modules = []
    for root, dirs, scripts in os.walk(source_path):
        rel_root = os.path.relpath(root, source_path)
        parts = rel_root.split(os.sep)

        # Check whitelist
        if parts[0] not in ('', 'core', 'ui'):
            continue

        for script in scripts:
            if script.endswith('.py') and not script.startswith('__'):
                rel_file = os.path.relpath(os.path.join(root, script), os.path.abspath(os.path.join(source_path, '..')))
                module = rel_file[:-3].replace(os.sep, '.')
                parent = module.rsplit('.', 1)[0]

                if parent not in modules:
                    modules.append(parent)

                if module not in modules:
                    modules.append(module)

    print(f'Collected the following internal hidden imports in "{source_path}":\n{modules}')
    return modules


# Filter out all icons/assets that aren't actually used
def filter_datas(datas: list | tuple, excludes: list = []) -> list:
    _global_excludes = ['tzdata']
    excludes.extend(_global_excludes)

    data_list  = list(datas)
    png_list   = []


    # Scan all Python files under './ui/desktop' recursively to remove unused assets
    desktop_ui = os.path.join(source_path, 'ui', 'desktop')
    for py in glob(os.path.join(desktop_ui, '**', '*.py'), recursive=True):
        with open(py, 'r', errors='ignore') as f:
            script_contents = f.read()
            [png_list.append(x) for x in findall(r"'(.*?)'", script_contents) if '.png' in x and '{' not in x]
            [png_list.append(x) for x in findall(r'"(.*?)"', script_contents) if '.png' in x and '{' not in x]

    asset_excludes = [
        os.path.basename(file) for file in glob(os.path.join(".", "ui", "assets", "icons", "*"))
        if (os.path.basename(file) not in png_list) and ("big" not in file)
    ]


    # Filter tzdata
    data_list = [item for item in data_list if not any(f in item[0] for f in excludes)]


    # Convert modified list back to a tuple
    data_list += Tree(
        os.path.join('.', 'ui', 'assets'),
        prefix   = os.path.join('ui', 'assets'),
        excludes = asset_excludes
    )

    return data_list


# Filter out all unnecessary binaries
def filter_binaries(binaries: list | tuple, excludes: list = []) -> list:
    _global_excludes = []
    excludes.extend(_global_excludes)


    # Only keep binaries that don't contain any excluded names
    final_list = [
        binary for binary in binaries
        if not any(exclude in binary[0] for exclude in excludes)
    ]

    return TOC(final_list)
