import os
import argparse
from labdataranger.disk.dataset.scan.format import (
    find_file_stacks,
    process_all_stacks,
    extract_dicom,
)
import yaml


def combine_mri_metadata(dcm_metadata, log_metadata=None):
    """
    Combines metadata from DICOM files and an optional metadata log file.

    Args:
        dcm_metadata (list): List of metadata dictionaries from DICOM files.
        log_metadata (dict, optional): Metadata from a log file (if provided).

    Returns:
        dict: Combined metadata for the MRI scan.
    """
    combined_metadata = {
        "dicom_metadata": dcm_metadata
    }

    if log_metadata:
        combined_metadata["log_metadata"] = log_metadata

    return combined_metadata


def parse_metadata_log(log_file_path):
    """
    Parses a custom metadata log file if provided.

    Args:
        log_file_path (str): Path to the metadata log file.

    Returns:
        dict: Parsed metadata from the log file.
    """
    log_metadata = {}
    try:
        with open(log_file_path, "r") as file:
            for line in file:
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    log_metadata[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Log file not found: {log_file_path}")
    except Exception as e:
        print(f"Error reading log file {log_file_path}: {e}")
    return log_metadata


def process_mri_directory(scan_directory, dcm_extension, log_file=None):
    """
    Processes an MRI dataset directory to extract DICOM metadata and optionally parse a log file.

    Args:
        scan_directory (str): Path to the directory containing the MRI dataset.
        dcm_extension (str): Extension for the DICOM files.
        log_file (str, optional): Path to a metadata log file.

    Returns:
        dict: Combined metadata for the MRI scan.
    """
    # Process DICOM stacks
    dicom_stacks = find_file_stacks(scan_directory, dcm_extension)
    processed_dicom_metadata = process_all_stacks(dicom_stacks, extract_dicom)

    # Parse optional log file
    log_metadata = None
    if log_file:
        log_metadata = parse_metadata_log(log_file)

    # Combine metadata
    return combine_mri_metadata(processed_dicom_metadata, log_metadata)


def main():
    parser = argparse.ArgumentParser(description="Process MRI datasets with DICOM files and an optional metadata log.")
    parser.add_argument("scan_directory", type=str, help="Path to the MRI dataset directory.")
    parser.add_argument("--dcm_ext", type=str, default="dcm", help="Extension for DICOM files (default: dcm).")
    parser.add_argument("--log_file", type=str, help="Path to an optional metadata log file.")
    parser.add_argument("--output", type=str, help="Path to save the combined metadata as a YAML file.")

    args = parser.parse_args()

    # Process the MRI directory
    combined_metadata = process_mri_directory(args.scan_directory, args.dcm_ext, args.log_file)

    # Save or display the metadata
    if args.output:
        with open(args.output, "w") as yaml_file:
            yaml.dump(combined_metadata, yaml_file, default_flow_style=False)
        print(f"Metadata saved to {args.output}")
    else:
        print(yaml.dump(combined_metadata, default_flow_style=False))


if __name__ == "__main__":
    main()
