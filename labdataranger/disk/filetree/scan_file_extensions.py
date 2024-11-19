import os
import argparse
import pickle
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tqdm import tqdm

def scan_subdirectory(subdirectory):
    """Recursively scans a subdirectory and returns a nested dictionary structure."""
    structure = {"_files": [], "_dirs": {}}
    stack = [subdirectory]

    while stack:
        current_dir = stack.pop()
        try:
            with os.scandir(current_dir) as it:
                for entry in it:
                    relative_path = os.path.relpath(entry.path, subdirectory)
                    if entry.is_file():
                        structure["_files"].append(relative_path)
                    elif entry.is_dir():
                        structure["_dirs"][relative_path] = {"_files": [], "_dirs": {}}
                        stack.append(entry.path)
        except PermissionError:
            pass  # Skip directories without permission

    return structure

def merge_structures(main_structure, sub_structure, subdir_name):
    """Merges a scanned subdirectory structure into the main directory structure."""
    main_structure["_dirs"][subdir_name] = sub_structure

def scan_directory(directory, num_workers):
    # Initialize main directory structure
    dir_structure = {"_files": [], "_dirs": {}}

    # Collect top-level subdirectories
    with os.scandir(directory) as it:
        subdirs = [entry.path for entry in it if entry.is_dir()]
        files = [entry.path for entry in it if entry.is_file()]

    # Add top-level files to the main structure
    dir_structure["_files"].extend([os.path.basename(file) for file in files])

    # Parallel processing of each top-level subdirectory
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        with tqdm(total=len(subdirs), desc="Scanning subdirectories", unit="subdir") as pbar:
            futures = {executor.submit(scan_subdirectory, subdir): subdir for subdir in subdirs}
            for future in as_completed(futures):
                subdir_name = os.path.basename(futures[future])
                sub_structure = future.result()
                merge_structures(dir_structure, sub_structure, subdir_name)
                pbar.update(1)

    return dir_structure

def save_as_pickle(data, output_path):
    with open(output_path, 'wb') as f:
        pickle.dump(data, f)

def save_as_csvs(data, output_dir):
    all_files = []
    
    # Recursively gather all files with their paths
    def gather_files(structure, base_path=""):
        for file in structure["_files"]:
            all_files.append((base_path, file))
        for subdir, substructure in structure["_dirs"].items():
            gather_files(substructure, os.path.join(base_path, subdir))

    gather_files(data)
    df = pd.DataFrame(all_files, columns=["Directory", "Filename"])
    df.to_csv(os.path.join(output_dir, "directory_structure.csv"), index=False)

def save_as_xlsx(data, output_path):
    all_files = []
    
    # Recursively gather all files with their paths
    def gather_files(structure, base_path=""):
        for file in structure["_files"]:
            all_files.append((base_path, file))
        for subdir, substructure in structure["_dirs"].items():
            gather_files(substructure, os.path.join(base_path, subdir))

    gather_files(data)
    df = pd.DataFrame(all_files, columns=["Directory", "Filename"])
    with pd.ExcelWriter(output_path) as writer:
        df.to_excel(writer, sheet_name="DirectoryStructure", index=False)

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Scan a directory and save the filesystem structure.")
    parser.add_argument("directory", type=str, help="The directory to scan")
    parser.add_argument("--output", type=str, default="directory_structure.pkl", help="Output file name (Pickle or XLSX)")
    parser.add_argument("--output-format", type=str, choices=["pickle", "csv", "xlsx"], default="pickle",
                        help="Output format: 'pickle' (default), 'csv', or 'xlsx'")
    parser.add_argument("-w", "--workers", type=int, default=4, help="The number of worker threads to use (default: 4)")

    args = parser.parse_args()

    # Scan directory and build nested dictionary structure
    dir_structure = scan_directory(args.directory, args.workers)

    # Save to specified format
    if args.output_format == "pickle":
        save_as_pickle(dir_structure, args.output)
        print(f"Data saved as Pickle at {args.output}")
    elif args.output_format == "csv":
        os.makedirs(args.output, exist_ok=True)
        save_as_csvs(dir_structure, args.output)
        print(f"Data saved as CSV in {args.output}")
    elif args.output_format == "xlsx":
        save_as_xlsx(dir_structure, args.output)
        print(f"Data saved as XLSX at {args.output}")

if __name__ == "__main__":
    main()

