import tifffile


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

def _extract_page_metadata(tiff_page):
    """
    Extracts all metadata from a single TIFF page.
    Args:
        tiff_page: A single page from a TIFF file.
    Returns:
        dict: Extracted metadata as a dictionary.
    """
    metadata = {}
    for tag in tiff_page.tags.values():
        tag_name = tag.name
        tag_value = _convert_value(tag.value)
        metadata[tag_name] = tag_value
    return metadata

def extract_metadata(filepath):
    """
    Extracts metadata from a single TIFF file.
    Args:
        filepath (str): Path to the TIFF file.
    Returns:
        dict: Extracted metadata, including TIFF tags.
    """
    metadata = {}
    try:
        # Open the TIFF file and read metadata from the first page
        with tifffile.TiffFile(filepath) as tif:
            page = tif.pages[0]  # Only extract from the first page
            metadata['tiff_tags'] = _extract_page_metadata(page)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except Exception as e:
        raise ValueError(f"Error reading TIFF file {filepath}: {e}")

    return metadata
