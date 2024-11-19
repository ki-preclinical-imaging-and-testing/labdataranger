import tifffile


def convert_tiff_value(value):
    """
    Converts tifffile-specific types to standard Python types for cleaner output.
    """
    # Currently, this is a placeholder. Add conversions as needed.
    return value


def extract_all_tiff_metadata(tiff_page):
    """
    Extracts all metadata from a single TIFF page.
    """
    metadata = {}
    for tag in tiff_page.tags.values():
        tag_name = tag.name
        tag_value = convert_tiff_value(tag.value)
        metadata[tag_name] = tag_value
    return metadata


def extract_tiff_metadata(filepath):
    """
    Extracts metadata from a single TIFF file.
    """
    metadata = {}

    # Open the TIFF file and read metadata from the first page
    with tifffile.TiffFile(filepath) as tif:
        page = tif.pages[0]
        metadata['tiff_tags'] = extract_all_tiff_metadata(page)

    return metadata
