import json


def save_json(data, output_path):
    """Save a dictionary to a JSON file."""
    with open(output_path, "w") as file:
        json.dump(data, file, indent=4)


def filter_files_by_extension(files, extensions):
    """Filter a list of files by specified extensions."""
    return [file for file in files if file.suffix in extensions]
