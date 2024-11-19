import pydicom

def convert_value(value):
    """
    Converts pydicom-specific types to standard Python types to clean up YAML output.
    """
    if isinstance(value, pydicom.multival.MultiValue):
        # Convert MultiValue (like a list) by applying convert_value to each element
        return [convert_value(v) for v in value]
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


def extract_all_metadata(ds, metadata=None):
    """
    Recursively extracts all metadata from a DICOM dataset, excluding pixel data.
    """
    if metadata is None:
        metadata = {}

    for elem in ds:
        if elem.keyword == "PixelData":
            continue  # Skip pixel data

        if elem.VR == "SQ":
            sequence_data = [extract_all_metadata(item, {}) for item in elem]
            metadata[elem.keyword or elem.tag] = sequence_data
        else:
            metadata[elem.keyword or elem.tag] = convert_value(elem.value)
    return metadata

def extract_dicom_metadata(filepath):
    """
    Extracts all metadata from a DICOM file.
    """
    ds = pydicom.dcmread(filepath)
    return extract_all_metadata(ds)

