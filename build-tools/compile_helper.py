import os


tools_path = os.path.dirname(__file__)
source_path = os.path.abspath(os.path.join(tools_path, '..', 'source'))


# # Filter out all datas to remove un-needed software
# def filter_datas(datas: list) -> list:
#     return [data for data in datas if str(os.path.join('site-packages', '<package-name>')) not in data[0]]


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
