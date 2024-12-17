import re, json, json_repair

# Fix relaxed JSON to standard JSON
def json_regex(match):
    if match.group(2):  # Match unquoted strings or numbers
        value = match.group(2)
        if re.match(r'^-?\d+\.?\d*(f|L|b|d)?$', value):  # Handle numbers
            if "." in value:
                final_str = str(round(float(re.sub(r'[^0-9.-]', '', value)), 4))
            else:
                final_str = re.sub(r'[^0-9-]', '', value)
        else:
            # Quote strings
            final_str = f'"{value}"'
    else:  # Keys (e.g., unquoted strings before a colon)
        final_str = match.group(1).replace('minecraft:', '')

    return final_str



# "Fake" a player event to debug NBT data
with open('/Users/kaleb/debug.log') as f:
    log_data = f.read()

nbt_data = log_data.split("following entity data: ")[1].strip()

# Remove color escape codes if they exist
try:
    # Remove ANSI escape codes
    ansi_escape = re.compile(r'''
        \x1B  # ESC character
        \[    # literal [
        [0-?]*  # zero or more chars between 0 and ?
        [ -/]*  # zero or more chars between space and /
        [@-~]   # one char between @ and ~
    ''', re.VERBOSE)
    nbt_data = ansi_escape.sub('', nbt_data)

    # Handle unquoted keys and values
    nbt_data = re.sub(
        r'(:?"[^"]*")|([A-Za-z_\-\d.?\d]\w*\.*\d*\w*)',
        lambda x: json_regex(x),
        nbt_data
    )

    # Replace semicolons with commas, fix brackets
    nbt_data = nbt_data.replace(";", ",").replace("'{", '"{').replace("}'", '}"')

    # Escape internal JSON quotes
    new_nbt = re.sub(r'(?<="{)(.*?)(?=}")', lambda x: x.group(1).replace('"', '\\"'), nbt_data)

    new_nbt = json_repair.loads(re.sub(r'(?<="{)(.*?)(?=}")', lambda x: x.group(1).replace('"', '\\"'), new_nbt))
    print(new_nbt)
except json.decoder.JSONDecodeError:
    print('Failed to process NBT data')
