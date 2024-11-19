import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
import os
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from labdataranger.disk.dataset.metadata__session import ImagingSessionMetadata

# def scan_filetree_with_metadata(base_dir, workers=4):
#     """
#     Scans a directory tree, extracts metadata for files, and builds a nested directory structure.
#     """
#     session = ImagingSessionMetadata(base_dir)  # Pass base_dir as the path argument
#     file_metadata = {}
#     folder_structure = {"_files": [], "_dirs": {}}
#
#     def process_directory(directory):
#         """Process a single directory and return its metadata."""
#         dir_metadata = {"_files": [], "_dirs": {}}
#         try:
#             with os.scandir(directory) as entries:
#                 for entry in entries:
#                     if entry.is_file():
#                         metadata = session.process_metadata(output="return")
#                         file_metadata[entry.path] = metadata
#                         dir_metadata["_files"].append(entry.name)
#                     elif entry.is_dir():
#                         # Recursively process subdirectories
#                         subdir_metadata = process_directory(entry.path)
#                         dir_metadata["_dirs"][entry.name] = subdir_metadata
#         except PermissionError:
#             print(f"Permission denied: {directory}")
#         return dir_metadata
#
#     # Collect top-level directories and files
#     top_level_files = []
#     top_level_dirs = []
#     with os.scandir(base_dir) as entries:
#         for entry in entries:
#             if entry.is_file():
#                 top_level_files.append(entry.name)
#             elif entry.is_dir():
#                 top_level_dirs.append(entry.path)
#
#     folder_structure["_files"].extend(top_level_files)
#
#     # Process subdirectories in parallel
#     with ThreadPoolExecutor(max_workers=workers) as executor:
#         futures = {executor.submit(process_directory, subdir): subdir for subdir in top_level_dirs}
#         for future in tqdm(as_completed(futures), total=len(futures), desc="Scanning directories"):
#             subdir_path = futures[future]
#             folder_structure["_dirs"][Path(subdir_path).name] = future.result()
#
#     return file_metadata, folder_structure

# from concurrent.futures import ThreadPoolExecutor, as_completed
# from tqdm import tqdm
# from pathlib import Path
# import os
# from labdataranger.disk.metadata__session import ImagingSessionMetadata
#
#
# def scan_filetree_with_metadata(base_dir, workers=4):
#     """
#     Scans a directory tree, extracts metadata for files, and builds a nested directory structure.
#     """
#     session = ImagingSessionMetadata()
#     file_metadata = {}
#     folder_structure = {"_files": [], "_dirs": {}}
#
#     def process_subdirectory(directory):
#         """
#         Processes a subdirectory recursively, gathering file metadata and subfolder structure.
#         """
#         subdir_metadata = {"_files": [], "_dirs": {}}
#         try:
#             with os.scandir(directory) as entries:
#                 for entry in entries:
#                     if entry.is_file():
#                         metadata = session.process_metadata(path=entry.path, output="return")
#                         file_metadata[entry.path] = metadata
#                         subdir_metadata["_files"].append(entry.name)
#                     elif entry.is_dir():
#                         # Recursively process the subdirectory
#                         subdir_metadata["_dirs"][entry.name] = process_subdirectory(entry.path)
#         except PermissionError:
#             print(f"Permission denied: {directory}")
#         return subdir_metadata
#
#     # Step 1: Collect top-level directories and files
#     top_level_files = []
#     top_level_dirs = []
#     with os.scandir(base_dir) as entries:
#         for entry in entries:
#             if entry.is_file():
#                 top_level_files.append(entry.name)
#             elif entry.is_dir():
#                 top_level_dirs.append(entry.path)
#
#     folder_structure["_files"].extend(top_level_files)
#
#     # Step 2: Process top-level subdirectories in parallel
#     with ThreadPoolExecutor(max_workers=workers) as executor:
#         futures = {executor.submit(process_subdirectory, subdir): subdir for subdir in top_level_dirs}
#         for future in tqdm(as_completed(futures), total=len(futures), desc="Scanning top-level directories"):
#             subdir_path = futures[future]
#             folder_structure["_dirs"][Path(subdir_path).name] = future.result()
#
#     return file_metadata, folder_structure


def is_imaging_session(directory):
    """
    Determines if a directory qualifies as a single imaging session (Leaf).
    Criteria can be based on file extensions, patterns, or custom logic.
    """
    supported_extensions = {".dcm", ".nii", ".nii.gz", ".tif", ".tiff"}
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    return any(f.lower().endswith(tuple(supported_extensions)) for f in files)


def process_leaf(directory):
    """
    Processes a directory as a single Leaf node using ImagingSessionMetadata.
    """
    try:
        session = ImagingSessionMetadata(directory)
        return session.process_metadata(path=directory, output="return")
    except Exception as e:
        print(f"Error processing Leaf node at {directory}: {e}")
        return None


def process_subdirectory(directory):
    """
    Processes a subdirectory. If it qualifies as a Leaf, process it as one.
    Otherwise, recurse into its structure and process files individually.
    """
    subdir_metadata = {"_files": [], "_dirs": {}}
    try:
        # Check if the directory qualifies as a Leaf node
        if is_imaging_session(directory):
            metadata = process_leaf(directory)
            if metadata:
                subdir_metadata["leaf_metadata"] = metadata
            return subdir_metadata  # Treat as Leaf; skip deeper processing

        # Otherwise, process contents
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file():
                    metadata = process_file(entry.path)
                    file_metadata[entry.path] = metadata
                    subdir_metadata["_files"].append(entry.name)
                elif entry.is_dir():
                    # Recursively process subdirectories
                    subdir_metadata["_dirs"][entry.name] = process_subdirectory(entry.path)
    except PermissionError:
        print(f"Permission denied: {directory}")
    return subdir_metadata


def scan_filetree_with_metadata(base_dir, workers=4):
    """
    Scans a directory tree, extracts metadata for files, and builds a nested directory structure.
    """
    file_metadata = {}
    folder_structure = {"_files": [], "_dirs": {}}

    # Step 1: Process top-level files and subdirectories
    top_level_files = []
    top_level_dirs = []
    with os.scandir(base_dir) as entries:
        for entry in entries:
            if entry.is_file():
                top_level_files.append(entry.name)
            elif entry.is_dir():
                top_level_dirs.append(entry.path)

    folder_structure["_files"].extend(top_level_files)

    # Step 2: Parallelize processing of subdirectories
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_subdirectory, subdir): subdir for subdir in top_level_dirs}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Scanning top-level directories"):
            subdir_path = futures[future]
            folder_structure["_dirs"][Path(subdir_path).name] = future.result()

    return file_metadata, folder_structure


def save_results(file_metadata, folder_structure, output_dir):
    """Saves file metadata and directory structure to output files."""
    os.makedirs(output_dir, exist_ok=True)
    metadata_file = os.path.join(output_dir, "file_metadata.json")
    structure_file = os.path.join(output_dir, "directory_structure.json")

    with open(metadata_file, "w") as meta_out:
        json.dump(file_metadata, meta_out, indent=4)

    with open(structure_file, "w") as struct_out:
        json.dump(folder_structure, struct_out, indent=4)

    print(f"Metadata saved to {metadata_file}")
    print(f"Directory structure saved to {structure_file}")

def main():
    parser = argparse.ArgumentParser(description="Scan a filetree and scan metadata.")
    parser.add_argument("directory", type=str, help="Base directory to scan.")
    parser.add_argument("--output", type=str, default="output", help="Directory to save results.")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker threads.")
    args = parser.parse_args()

    file_metadata, folder_structure = scan_filetree_with_metadata(args.directory, args.workers)
    save_results(file_metadata, folder_structure, args.output)

if __name__ == "__main__":
    main()
