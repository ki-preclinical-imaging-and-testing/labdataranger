import argparse
import os
from labdataranger.disk.dataset.scan.format import (
    find_file_stacks,
    process_all_stacks,
    extract_tiff,
    extract_metadata as extract_log_metadata,
)
import yaml


def combine_log_and_stack(log_file, processed_stacks, reconstruction_stacks=None):
    """
    Combines metadata from a Bruker log file, raw TIFF stack, and optional reconstructed TIFF stack.

    Args:
        log_file (str): Path to the Bruker log file.
        processed_stacks (list): List of dictionaries containing raw TIFF stack metadata.
        reconstruction_stacks (list, optional): List of dictionaries containing reconstructed TIFF stack metadata.

    Returns:
        dict: Combined metadata for the scan.
    """
    combined_metadata = {}

    # Extract metadata from the log file
    try:
        log_metadata = extract_log_metadata(log_file)
        combined_metadata["log_metadata"] = log_metadata
    except Exception as e:
        print(f"Error extracting metadata from log file {log_file}: {e}")
        combined_metadata["log_metadata"] = {}

    # Add raw TIFF stack metadata
    combined_metadata["raw_stack_metadata"] = processed_stacks

    # Add reconstructed TIFF stack metadata if available
    if reconstruction_stacks:
        combined_metadata["reconstruction_stack_metadata"] = reconstruction_stacks

    return combined_metadata


def process_reconstruction_subfolder(parent_dir, tiff_extension):
    """
    Checks for a '_Rec' subfolder and processes reconstructed TIFF stacks if present.

    Args:
        parent_dir (str): Path to the parent directory.
        tiff_extension (str): Extension for the TIFF files.

    Returns:
        list: Processed metadata for reconstructed TIFF stacks, or None if no '_Rec' folder exists.
    """
    rec_dir = os.path.join(parent_dir, f"{os.path.basename(parent_dir)}_Rec")

    if os.path.exists(rec_dir) and os.path.isdir(rec_dir):
        print(f"Found reconstruction folder: {rec_dir}")
        rec_stacks = find_file_stacks(rec_dir, tiff_extension)
        return process_all_stacks(rec_stacks, extract_tiff)

    return None


def main():
    parser = argparse.ArgumentParser(description="Process Bruker scans with log files and TIFF stacks.")
    parser.add_argument(
        "scan_directory", type=str, help="Path to the directory containing the TIFF stacks and log file."
    )
    parser.add_argument("--log_ext", type=str, default="log", help="Extension for the Bruker log file (default: log).")
    parser.add_argument("--tiff_ext", type=str, default="tif", help="Extension for the TIFF files (default: tif).")
    parser.add_argument("--output", type=str, help="Path to save the combined metadata as a YAML file.")

    args = parser.parse_args()

    scan_directory = args.scan_directory
    log_extension = args.log_ext
    tiff_extension = args.tiff_ext

    # Find the log file in the scan directory
    log_file = None
    for file in os.listdir(scan_directory):
        if file.endswith(f".{log_extension}"):
            log_file = os.path.join(scan_directory, file)
            break

    if not log_file:
        print(f"No log file with extension {log_extension} found in {scan_directory}")
        return

    # Process raw TIFF stacks in the directory
    raw_stacks = find_file_stacks(scan_directory, tiff_extension)
    processed_raw_stacks = process_all_stacks(raw_stacks, extract_tiff)

    # Check for and process reconstructed TIFF stacks
    processed_rec_stacks = process_reconstruction_subfolder(scan_directory, tiff_extension)

    # Combine metadata
    combined_metadata = combine_log_and_stack(log_file, processed_raw_stacks, processed_rec_stacks)

    # Save or display the metadata
    if args.output:
        with open(args.output, "w") as yaml_file:
            yaml.dump(combined_metadata, yaml_file, default_flow_style=False)
        print(f"Metadata saved to {args.output}")
    else:
        print(yaml.dump(combined_metadata, default_flow_style=False))


if __name__ == "__main__":
    main()
