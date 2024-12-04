import os
import re
from collections import defaultdict
from tqdm import tqdm
from .dicom import extract_metadata as extract_dicom
from .tiff import extract_metadata as extract_tiff
from .bruker_log import extract_metadata as extract_bruker_log
# from .json import extract_metadata as extract_json
# from .nifti import extract_metadata as extract_nifti
# from .xml import extract_metadata as extract_xml

EXTRACTION_MAP = {
    "dcm": extract_dicom,
    "tiff": extract_tiff,
    "tif":  extract_tiff,
    "log": extract_bruker_log,
    # "json": extract_json,
    # "nii": extract_nifti,
    # "xml": extract_xml,
}


def extract_metadata(filepath):
    """
    Dispatches metadata extraction to the appropriate handler based on file extension.
    Args:
        filepath (str): Path to the file.
    Returns:
        dict: Extracted metadata or None if the file type is unsupported.
    """
    ext = os.path.splitext(filepath)[1][1:].lower()  # Get file extension without the dot
    if ext in EXTRACTION_MAP:
        return EXTRACTION_MAP[ext](filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def find_file_stacks(directory, extension, pattern=None):
    """
    Identifies file stacks in a directory based on a common stem and numbering pattern.

    Args:
        directory (str): Path to the directory to scan.
        extension (str): File extension to filter by (e.g., 'tif', 'dcm').
        pattern (str, optional): Custom regex pattern for identifying stacks.
            Default matches `{stem}_???????.{extension}`.

    Returns:
        dict: A dictionary where keys are common stems and values are lists of file paths in the stack.
    """
    if not pattern:
        # Default pattern: matches {stem}_???????.{extension}
        pattern = rf"^(?P<stem>.+?)(?P<number>\d+)\.{extension}$"

    regex = re.compile(pattern)
    stacks = defaultdict(list)

    for filename in os.listdir(directory):
        match = regex.match(filename)
        if match:
            stem = match.group("stem")
            stacks[stem].append(os.path.join(directory, filename))

    # Sort file paths in each stack by their numerical order
    for stem in stacks:
        stacks[stem] = sorted(stacks[stem], key=lambda x: int(regex.match(os.path.basename(x)).group("number")))

    return stacks

def process_all_stacks(stacks, metadata_extractor):
    results = []
    for stack_key, stack_files in stacks.items(): #tqdm(stacks.items(), desc="Processing all stacks", total=len(stacks.keys())):
        result = process_stack(stack_key, stack_files, metadata_extractor)
        results.append(result)
    return results

def process_stack(stack_key, stack_files, metadata_extractor):
    """Process a single stack of files to extract metadata."""
    stack_metadata = []
    for file_path in tqdm(stack_files, desc=f"Processing files in {stack_key}", total=len(stack_files)):
        try:
            metadata = metadata_extractor(file_path)  # Your TIFF metadata extractor
            stack_metadata.append(metadata)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    return {
        "stack_key": stack_key,
        "metadata": stack_metadata
    }

import pandas as pd

def combine_metadata_to_dataframe(processed_stacks):
    all_metadata = []
    for stack in processed_stacks:
        stack_key = stack["stack_key"]
        for metadata in stack["metadata"]:
            metadata["stack_key"] = stack_key  # Add group info to each metadata record
            all_metadata.append(metadata)
    return pd.DataFrame(all_metadata)

def save_metadata(metadata_df, output_path="metadata.csv"):
    metadata_df.to_csv(output_path, index=False)
