import argparse
import yaml
import pandas as pd
import json
from collections import Counter
from labdataranger.disk.dataset.scan.router import extract_metadata


class ImagingSessionMetadata:
    """
    Handles metadata extraction, loading, and processing for imaging sessions.
    """

    def __init__(self, path):
        """
        Initializes an ImagingSessionMetadata instance with a specified path.
        The path can be an image file, a directory, or a YAML file.
        """
        self.metadata = None
        self.path = path
        self.load_or_extract_metadata(path)

    def load_metadata_from_yaml(self, input_path):
        """
        Loads metadata from a YAML file and stores it in self.metadata.
        """
        with open(input_path, 'r') as yaml_file:
            self.metadata = yaml.load(yaml_file, Loader=yaml.FullLoader)

    def save_metadata_to_yaml(self, output_path):
        """
        Saves self.metadata to a YAML file.
        """
        with open(output_path, 'w') as yaml_file:
            yaml.dump(self.metadata, yaml_file, default_flow_style=False, sort_keys=False)

    def load_or_extract_metadata(self, path):
        """
        Loads metadata from YAML if the path is a YAML file.
        Otherwise, extracts metadata based on file type and stores it in self.metadata.
        """
        if path.endswith(".yaml"):
            self.load_metadata_from_yaml(path)
        else:
            try:
                self.metadata = extract_metadata(path)
            except ValueError as e:
                print(e)
                self.metadata = {}

    def get_all_attributes(self):
        """
        Retrieves all unique metadata attributes across files in self.metadata.
        """
        attributes = set()
        for data in self.metadata.values():
            attributes.update(data.keys())
        return sorted(attributes)

    def metadata_to_dataframe(self):
        """
        Converts self.metadata to a pandas DataFrame.
        """
        df = pd.DataFrame.from_dict(self.metadata, orient='index')
        df.index.name = 'Filename'
        return df

    def summarize_unique_values(self, with_counts=False):
        """
        Summarizes unique values in each column of the DataFrame.
        """
        df = self.metadata_to_dataframe()
        summary = {}
        for col in df.columns:
            value_counts = Counter()
            unique_values = set()
            contains_unhashable = False
            for val in df[col].dropna():
                if isinstance(val, dict):
                    contains_unhashable = True
                    break
                elif isinstance(val, list):
                    try:
                        hashable_val = tuple(self.make_hashable(v) for v in val)
                        if with_counts:
                            value_counts[str(hashable_val)] += 1
                        else:
                            unique_values.add(hashable_val)
                    except TypeError:
                        contains_unhashable = True
                        break
                else:
                    try:
                        hashable_val = str(val) if isinstance(val, tuple) else val
                        if with_counts:
                            value_counts[hashable_val] += 1
                        else:
                            unique_values.add(hashable_val)
                    except TypeError:
                        contains_unhashable = True
                        break
            if contains_unhashable:
                summary[col] = "Contains complex unhashable types (e.g., dictionaries), please investigate manually."
            else:
                summary[col] = dict(value_counts) if with_counts else list(unique_values)
        return summary

    def make_hashable(self, item):
        """
        Recursively makes items hashable for use in sets or dictionaries.
        """
        if isinstance(item, dict):
            return tuple(sorted(item.items()))
        elif isinstance(item, list):
            return tuple(self.make_hashable(subitem) for subitem in item)
        return item

    def process_metadata(self, output, list_filenames=False, attribute=None, list_attributes=False,
                         summarize=False, summarize_with_counts=False, return_as="dict"):
        """
        Processes metadata by handling print, save, or return options.
        """
        if output == "return":
            return json.dumps(self.metadata, indent=4) if return_as == "json" else self.metadata

        if output == "print":
            if list_filenames:
                print("Filenames:")
                print("\n".join(self.metadata.keys()))
            elif attribute:
                for filename, data in self.metadata.items():
                    attr_value = data.get(attribute, "Attribute not found")
                    print(f"{filename}: {attr_value}")
            elif list_attributes:
                attributes = self.get_all_attributes()
                print("All unique attributes across files:")
                print("\n".join(attributes))
            elif summarize or summarize_with_counts:
                summary = self.summarize_unique_values(with_counts=summarize_with_counts)
                print(json.dumps(summary, indent=4))
            else:
                print(self.metadata)
        else:
            self.save_metadata_to_yaml(output)
            print(f"Metadata extracted and saved to {output}")


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

    session = ImagingSessionMetadata(path=args.path)

    result = session.process_metadata(
        output=args.output,
        list_filenames=args.list_filenames,
        attribute=args.attribute,
        list_attributes=args.list_attributes,
        summarize=args.summarize,
        summarize_with_counts=args.summarize_with_counts,
        return_as=args.return_as
    )

    if args.output == "return" and args.return_as == "json":
        print(result)


if __name__ == "__main__":
    main()
