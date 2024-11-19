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


import pydicom as dcm
import pandas as pd


def dicom_dict(dcm_file, verbose=False):
    d = {}
    for element in dcm_file:
        _k = element.keyword
        if verbose:
            print(_k)
        _v = element.value
        if element.is_empty:
            if verbose:
                print("    Found empty value")
        elif element.is_undefined_length:
            if verbose:
                print(f"   Value: {type(_v)}")
        else:
            if verbose:
                print(f"   Value: {type(_v)}, Length: {len(str(_v))}")
        if verbose:
            print()
        d[_k] = _v
    return d

## Code from original labdataranger is below... leaving until it can be removed

def describe_dicom_dict(element_dict):
    print("--------------------")
    print("Elements")
    print()
    for _k, _v in element_dict.items():
        print(f"{str(type(_v)):>40s}  {_k:15s} ")
    print()


def sort_elements_by_type(element_dict):
    element_type_d = {}
    for _k, _v in element_dict.items():
        element_type = str(type(_v)).split("'")[1]
        if element_type in element_type_d.keys():
            element_type_d[element_type][_k] = _v
        else:
            element_type_d[element_type] = {_k: _v}
    return element_type_d


def describe_elements_by_type(element_dict):
    d = sort_elements_by_type(element_dict)
    print("--------------------")
    print("Element Types")
    print()
    for _k, _v in d.items():
        print(f" - {len(_v.keys()):3d} {_k}")
    print()


def summarize_elements_by_type(element_dict):
    d = sort_elements_by_type(element_dict)
    _l = []
    for _k, _v in d.items():
        _l.append([len(_v), _k])
    df = pd.DataFrame(_l, columns=['Count', 'Type'])
    return df.sort_values('Count', ascending=False).reset_index(drop=True)


def parse_dicom_file(dicom_filename, verbose=False):
    dicom_file = dcm.read_file(dicom_filename)
    element_dict = dicom_dict(dicom_file)
    element_by_type = sort_elements_by_type(element_dict)
    if verbose:
        describe_elements_by_type(element_dict)
        describe_dicom_dict(element_dict)
    return element_dict, element_by_type
