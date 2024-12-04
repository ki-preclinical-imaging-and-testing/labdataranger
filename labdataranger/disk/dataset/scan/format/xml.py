import os
import tqdm
import glob
import xml.etree.ElementTree as ET


# def parse_xml_file(fn):
#     xml_file = ET.parse(fn)
#     root = xml_file.getroot()
#
#     data_dict = {
#         'root': {
#             'tag': root.tag,
#             'attributes': root.attrib
#         },
#         'children': []
#     }
#
#     for child in root:
#         child_data = {
#             'tag': child.tag,
#             'attributes': child.attrib
#         }
#         data_dict['children'].append(child_data)
#
#     return data_dict


def parse_xml_file(fn):
    try:
        xml_file = ET.parse(fn)
        root = xml_file.getroot()

        data_dict = {
            'root': {
                'tag': root.tag,
                'attributes': root.attrib
            },
            'children': []
        }

        for child in root:
            child_data = {
                'tag': child.tag,
                'attributes': child.attrib
            }
            data_dict['children'].append(child_data)

        return data_dict

    except ET.ParseError as e:
        print(f"Error parsing XML file {fn}: {e}")
        return None  # or return an empty dict or any other appropriate value

    except Exception as e:
        print(f"An error occurred when processing the file {fn}: {e}")
        return None  # or return an empty dict or any other appropriate value


def build_meta_dict(fp):
    meta_dict = {}
    _files = find_files(fp, ['*.*xml*', '*.*xml*.*bak'])
    for _fn in tqdm.tqdm(_files, total=len(_files)):
        _, _ext = os.path.splitext(_fn)
        if _ext not in meta_dict.keys():
            meta_dict[_ext] = {}
        meta_dict[_ext][_fn] = parse_xml_file(_fn)
    return meta_dict


def find_files(base_folder, patterns, recursive=True):
    all_files = []
    for pattern in patterns:
        if recursive:
            path_pattern = os.path.join(base_folder, '**', pattern)
        else:
            path_pattern = os.path.join(base_folder, pattern)
        files = glob.glob(path_pattern, recursive=recursive)
        all_files.extend(files)
    return all_files


def summarize_meta_dict(meta_dict):
    for _ext, _entries in meta_dict.items():
        print(len(_entries), _ext)


def parse_ultrasound_files(fp_base, verbose=False):
    meta_dict = build_meta_dict(fp_base)
    if verbose:
        summarize_meta_dict(meta_dict)
    _fn = os.path.join(fp_base, 'MeasurementInfo.vxml')
    measurement_info = parse_xml_file(_fn)
    _fn = os.path.join(fp_base, 'Study.vxml')
    study = parse_xml_file(_fn)
    return meta_dict, measurement_info, study
