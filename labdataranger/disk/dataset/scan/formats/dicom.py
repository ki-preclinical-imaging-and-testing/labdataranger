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
