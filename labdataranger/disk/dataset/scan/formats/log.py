def parse_log_file(file_path):
    meta_dict = {}
    current_section = None
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    meta_dict[current_section] = {}
                elif '=' in line:
                    key, value = line.split('=', 1)
                    if current_section:
                        meta_dict[current_section][key.strip()] = value.strip()
                    else:
                        meta_dict[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return meta_dict


def parse_bruker_log(log_filepath, delim='='):
    """
    Parses a Bruker SkyScan log file to scan metadata.
    TODO: Replace with working code from labdataranger; this works for now
    """
    log_metadata = {}
    with open(log_filepath, 'r') as file:
        for line in file:
            # Example parsing logic: Assume key-value pairs separated by ":"
            if ":" in line:
                key, value = line.strip().split(delim, 1)
                log_metadata[key.strip()] = value.strip()
    return log_metadata
