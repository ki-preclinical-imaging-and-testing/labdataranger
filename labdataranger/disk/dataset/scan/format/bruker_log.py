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


def _convert_value(value):
    """
    Attempts to convert a value into an appropriate Python type.
    Supports numbers, lists, strings, and binary data.
    Args:
        value: The original value from the TIFF metadata.
    Returns:
        The converted Python value, or the original value if conversion fails.
    """
    # Try converting to integer
    try:
        return int(value)
    except (ValueError, TypeError):
        pass

    # Try converting to float
    try:
        return float(value)
    except (ValueError, TypeError):
        pass

    # Check if the value is a list or iterable
    if isinstance(value, (list, tuple)):
        return [_convert_value(v) for v in value]  # Recursively convert each element

    # Check for binary data (convert to string if safe, or return as-is)
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')  # Decode to string
        except UnicodeDecodeError:
            return value  # Return as raw bytes if decoding fails

    # If none of the above, return the value as a string (fallback)
    return str(value)

def _extract_all_metadata(file_path):
    """
    Parses a Bruker log file into a nested dictionary of sections and key-value pairs.

    Args:
        file_path (str): Path to the Bruker log file.

    Returns:
        dict: Parsed metadata from the log file.
    """
    meta_dict = {}
    current_section = None

    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                # Check for section headers [SectionName]
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    meta_dict[current_section] = {}
                # Parse key-value pairs (key=value)
                elif '=' in line:
                    key, value = line.split('=', 1)
                    if current_section:
                        meta_dict[current_section][key.strip()] = _convert_value(value.strip())
                    else:
                        meta_dict[key.strip()] = _convert_value(value.strip())
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading file {file_path}: {e}")

    return meta_dict




def extract_metadata(filepath):
    """
    Extracts metadata from a Bruker log file.

    Args:
        filepath (str): Path to the Bruker log file.

    Returns:
        dict: Metadata extracted from the log file.
    """
    return _extract_all_metadata(filepath)
