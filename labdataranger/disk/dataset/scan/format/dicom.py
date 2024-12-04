import pydicom

def _convert_value(value):
    """
    Converts pydicom-specific types to standard Python types to clean up YAML output.
    """
    if isinstance(value, pydicom.multival.MultiValue):
        # Convert MultiValue (like a list) by applying _convert_value to each element
        return [_convert_value(v) for v in value]
    elif isinstance(value, pydicom.valuerep.IS):
        # Convert integer strings (IS) directly to int
        return int(value)
    elif isinstance(value, pydicom.valuerep.DSfloat):
        # Convert DSfloat (decimal string float) to float
        return float(value)
    elif isinstance(value, pydicom.uid.UID):
        # Convert UID to a string
        return str(value)
    else:
        # Convert any other unknown type to string to ensure compatibility
        return str(value) if not isinstance(value, (str, int, float, bool)) else value


def _extract_all_metadata(ds, metadata=None):
    """
    Recursively extracts all metadata from a DICOM dataset, excluding pixel data.
    """
    if metadata is None:
        metadata = {}

    for elem in ds:
        if elem.keyword == "PixelData":
            continue  # Skip pixel data

        if elem.VR == "SQ":
            sequence_data = [_extract_all_metadata(item, {}) for item in elem]
            metadata[elem.keyword or elem.tag] = sequence_data
        else:
            metadata[elem.keyword or elem.tag] = _convert_value(elem.value)
    return metadata


def extract_metadata(filepath):
    """
    Extracts all metadata from a DICOM file.
    Args:
        filepath (str): Path to the DICOM file.
    Returns:
        dict: Metadata extracted from the DICOM file.
    """
    ds = pydicom.dcmread(filepath)
    return _extract_all_metadata(ds)
