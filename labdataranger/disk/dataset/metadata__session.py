import yaml
import pandas as pd
import json
from collections import Counter
from labdataranger.disk.dataset.dispatcher import extract_metadata

class ImagingSessionMetadata:
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
        Otherwise, extracts metadata based on file type and stores in self.metadata.
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

    def print_summary(self):
        """
        Prints a JSON-formatted summary.
        """
        print(json.dumps(self.summarize_unique_values(), indent=4))

    def process_metadata(self, output, list_filenames=False, attribute=None, list_attributes=False,
                         summarize=False, summarize_with_counts=False, return_as="dict"):
        """
        Processes metadata by handling print, save, or return options.
        """
        # Return metadata if specified
        if output == "return":
            return json.dumps(self.metadata, indent=4) if return_as == "json" else self.metadata

        # Print metadata based on user options
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
                self.print_summary(summary)
            else:
                print(self.metadata)
        else:
            # Save metadata to YAML if output is not "print"
            self.save_metadata_to_yaml(output)
            print(f"Metadata extracted and saved to {output}")
