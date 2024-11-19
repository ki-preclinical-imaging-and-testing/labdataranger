import os
from tqdm import tqdm
from labdataranger.disk.dataset.scan.formats.dicom_extractor import extract_dicom_metadata
from labdataranger.disk.dataset.scan.formats.nifti_extractor import extract_nifti_metadata
from labdataranger.disk.dataset.scan.formats.tiff_extractor import extract_tiff_metadata
from labdataranger.disk.dataset.scan.formats.bruker_log_extractor import parse_bruker_log

# Mapping of file extensions to extractor functions for easy extensibility
EXTRACTOR_FUNCTIONS = {
    ".dcm": extract_dicom_metadata,
    ".nii": extract_nifti_metadata,
    ".nii.gz": extract_nifti_metadata,
    ".tif": extract_tiff_metadata,
    ".tiff": extract_tiff_metadata,
    # Future additions can go here, e.g., ".jpg": extract_jpg_metadata
}

def get_extractor_function(file_extension):
    """
    Returns the appropriate extraction function based on file extension.
    """
    return EXTRACTOR_FUNCTIONS.get(file_extension.lower(), None)


def extract_metadata(filepath):
    """
    Extracts metadata from a single file or directory.
    - If a directory, determines if it contains Bruker files, generic TIFF files, or other formats.
    - If a single file, applies the correct extraction function based on file type.
    """
    if os.path.isdir(filepath):
        return extract_metadata_from_directory(filepath)

    # Extract metadata from a single file
    file_extension = os.path.splitext(filepath)[1].lower()
    extractor = get_extractor_function(file_extension)
    if extractor:
        return {os.path.basename(filepath): extractor(filepath)}
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")


def extract_metadata_from_directory(directory):
    """
    Extracts metadata from a directory.
    - Checks if it contains Bruker TIFF series or generic TIFF files.
    - If neither, scans all files in the directory and applies available extractors by extension.
    """
    # Check for the presence of TIFF and log files
    tiff_files = [f for f in os.listdir(directory) if f.lower().endswith(('.tif', '.tiff'))]
    log_files = [f for f in os.listdir(directory) if f.lower().endswith('.log')]

    # If TIFF and log files are found, assume Bruker series
    if tiff_files and log_files:
        print("Detected Bruker series with TIFF and log files.")
        return extract_bruker_metadata(directory)
    else:
        # Scan all files in the directory and scan metadata for supported formats
        print("Scanning directory for supported file types.")
        return extract_metadata_from_directory_generic(directory)


def extract_metadata_from_directory_generic(directory):
    """
    Extracts metadata from all supported files in a directory, skipping empty or unsupported files.
    """
    directory_metadata = {}
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_extension = os.path.splitext(filename)[1].lower()
            extractor = get_extractor_function(file_extension)
            if extractor:
                if os.path.getsize(filepath) == 0:  # Skip empty files
                    print(f"Skipping empty file: {filepath}")
                    continue
                try:
                    directory_metadata[filename] = extractor(filepath)
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
            else:
                print(f"Unsupported file format: {filename}")
    return directory_metadata



def extract_bruker_metadata(directory, extension='.log'):
    """
    Extracts metadata from all Bruker TIFF files and their associated log file in a directory.
    Assumes TIFF files in the series share a filename stem with the log file.
    """
    bruker_metadata = {}

    # Detect log file (assuming only one Bruker log file per directory)
    log_files = [f for f in os.listdir(directory) if f.endswith(extension)]
    if not log_files:
        print("No Bruker log file found.")
        return bruker_metadata
    log_filepath = os.path.join(directory, log_files[0])

    # Parse the log file for Bruker metadata
    bruker_metadata['bruker_log'] = parse_bruker_log(log_filepath)

    # Extract metadata for each TIFF file in the series
    tiff_files = [f for f in os.listdir(directory) if f.lower().endswith(('.tif', '.tiff'))]
    for filename in tqdm(tiff_files,
                         desc="Processing TIFF files",
                         total=len(tiff_files)):
        filepath = os.path.join(directory, filename)
        bruker_metadata[filename] = extract_tiff_metadata(filepath)

    return bruker_metadata
