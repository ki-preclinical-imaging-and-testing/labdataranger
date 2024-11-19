import argparse
from metadata__session import ImagingSessionMetadata

def main():
    parser = argparse.ArgumentParser(description="Extract or load metadata from image files or a YAML file.")
    parser.add_argument("path", type=str, help="Path to the image file, directory of image files, or YAML file.")
    parser.add_argument("output", type=str, help="Path for the output YAML file, 'print' to display metadata, or 'return' to return metadata.")
    parser.add_argument("--list-filenames", action="store_true", help="Print all filenames in the metadata.")
    parser.add_argument("--attribute", type=str, help="Print all filenames and a specific attribute if available.")
    parser.add_argument("--list-attributes", action="store_true", help="Print all unique attributes across files.")
    parser.add_argument("--summarize", action="store_true", help="Print a summary of unique values for each attribute.")
    parser.add_argument("--summarize-with-counts", action="store_true", help="Print a summary with counts of unique values for each attribute.")
    parser.add_argument("--return-as", choices=["json", "dict"], default="dict", help="Specify return format if output is 'return'.")

    args = parser.parse_args()

    # Initialize ImagingSessionMetadata with the given path
    session = ImagingSessionMetadata(path=args.path)

    # Process metadata based on arguments
    result = session.process_metadata(
        output=args.output,
        list_filenames=args.list_filenames,
        attribute=args.attribute,
        list_attributes=args.list_attributes,
        summarize=args.summarize,
        summarize_with_counts=args.summarize_with_counts,
        return_as=args.return_as
    )

    # If 'return' option is specified and JSON output was requested, print the JSON result
    if args.output == "return" and args.return_as == "json":
        print(result)

if __name__ == "__main__":
    main()
