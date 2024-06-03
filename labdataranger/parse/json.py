import os
import glob
import json
from collections import defaultdict


def cft_study_meta_base(fp_base):
    meta = {}
    study_detail_logs = glob.glob(os.path.join(fp_base, '*.json'))
    for _sdl in study_detail_logs:
        print(_sdl)
        _meta_key = os.path.basename(_sdl)
        meta[_meta_key] = json.load(open(_sdl, 'r'))
    return meta


def print_dict_recursively(d, indent=0):
    # Create indentation string based on the current recursion depth
    indent_str = '  ' * indent
    print()
    for k, v in d.items():
        if isinstance(v, dict):
            # If the value is another dictionary, print its key and recursively call this function
            print(f"{indent_str}{k}:")
            print_dict_recursively(v, indent + 2)
        else:
            # If the value is not a dictionary, print the key and value
            print(f"{indent_str}{k}: {v}")
    print()


def cft_study_meta_recon(fp_base):
    fp_recon = os.path.join(fp_base, 'recon/study_detail.json')
    f = open(fp_recon, 'r')
    meta_recon = json.load(f)
    return meta_recon


def print_cft_study_roi(meta_recon):
    for _k, _roi in meta_recon['study_details']['rois'].items():
        _bb_dim = _roi['bounding_box']
        x0, y0, x1, y1 = tuple(_bb_dim)
        dx = x1 - x0
        dy = y1 - y0
        area = dx * dy
        print()
        print("-----------------------------")
        print()
        print(f"  ROI: {_roi['name']}")
        print()
        print(f" BBox: ")
        print()
        print(f" (x0, x1) = ({x0}, {x1})")
        print(f" (y0, y1) = ({y0}, {y1})")
        print()
        print(f"       dx = {dx:7d} pixel width")
        print(f"       dy = {dy:7d} pixel width")
        print(f"     area = {area:7d} pixel")
        print()


def find_files_by_extension(root_dir):
    # Dictionary to store the extensions and their associated file paths
    extensions_dict = defaultdict(list)

    # Walk through all directories and files in the specified root directory
    for dir_path, dir_names, filenames in os.walk(root_dir):
        for filename in filenames:
            # Get the full path of the file
            full_path = os.path.join(dir_path, filename)
            # Extract the extension from the filename
            _, ext = os.path.splitext(filename)
            # Normalize the extension to ensure consistency (optional)
            ext = ext.lower().strip('.')
            # Append the full path of the file to the list of paths for this extension
            if ext:  # Make sure there's an extension
                extensions_dict[ext].append(full_path)
    _ed = dict(extensions_dict)
    return {_k: _ed[_k] for _k in sorted(_ed)}


def summarize_directory(filetype_dict):
    print(f"Found {len(filetype_dict.keys())} extensions (filecount):")
    for _k, _v in filetype_dict.items():
        print(f"  .{_k:7s} ({len(_v)})")


def parse_cft_files(fp_base, verbose=False):
    meta = cft_study_meta_base(fp_base)
    filetype_dict = find_files_by_extension(fp_base)
    if verbose:
        print_dict_recursively(meta)
        print()
        summarize_directory(filetype_dict)
    return meta, filetype_dict
