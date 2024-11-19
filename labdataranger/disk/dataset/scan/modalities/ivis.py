import datetime


def interpret_value(value):
    if ';' in value:
        items = value.split(';')
        return [interpret_single_value(item.strip()) for item in items if item.strip()]
    elif ',' in value:
        items = value.split(',')
        return [interpret_single_value(item.strip()) for item in items if item.strip()]

    return interpret_single_value(value)


def interpret_single_value(value):
    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    try:
        return datetime.datetime.strptime(value, '%A, %B %d, %Y').date()
    except ValueError:
        pass

    try:
        return datetime.datetime.strptime(value, '%H:%M:%S').time()
    except ValueError:
        pass

    return value


def parse_ivis_file(file_path):
    data = {}
    current_section = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip().replace('\t', '')  # Remove tabs and strip whitespace
            if line.startswith('***'):  # Detect new section
                # Extract section name and optional header key
                section_info = line.strip('* ').strip()
                if ':' in section_info:
                    current_section, header_value = section_info.split(':', 1)
                    current_section = current_section.strip()
                    header_value = header_value.strip()
                    data[current_section] = {current_section: interpret_value(header_value)}
                else:
                    current_section = section_info
                    data[current_section] = {}
            elif ':' in line and current_section:  # Detect key-value pairs
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if key:  # Ensure the key is not empty
                    data[current_section][key] = interpret_value(value)

    return data
