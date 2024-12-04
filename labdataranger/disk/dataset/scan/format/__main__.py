from . import extract_metadata
import argparse
import json

def main():
    """
    Test the format module with example files.
    """
    parser = argparse.ArgumentParser(description="Test metadata extraction from various file format.")
    parser.add_argument("filepath", type=str, help="Path to the file for metadata extraction.")
    args = parser.parse_args()

    try:
        metadata = extract_metadata(args.filepath)
        print(json.dumps(metadata, indent=4))
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
