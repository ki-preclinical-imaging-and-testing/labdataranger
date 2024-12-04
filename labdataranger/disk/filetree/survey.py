import os
import logging
import networkx as nx
from pathlib import Path
import time
import pandas as pd
import glob
from PIL import Image
from PIL.TiffTags import TAGS
import pickle
import os
import re
import networkx as nx


def get_base_dirs(base_path):
    base_dirs = {}
    for _dir in glob.glob(f"{base_path}/*"):
        if Path(_dir).is_dir():
            base_dirs[Path(_dir).name] = _dir
    return base_dirs


def format_property_key(key):
    return to_lower_camel_case(convert_chars_for_neo4j(key))


def to_lower_camel_case(s):
    s = re.sub(r"([_\-])+", " ", s).title().replace(" ", "")
    return s[0].lower() + s[1:]


def convert_chars_for_neo4j(s):
    s = s.replace('/', '')
    s = s.replace('(', '_')
    s = s.replace(')', '_')
    s = s.replace('+', 'plus')
    return s


def process_directory(
    base_directory_path,
    skips=['System Volume Information','$RECYCLE.BIN'],
    checkpoint_fstr='.labdataranger.pkl',
    log_fstr='.labdataranger.out',
    verbose=False):
    
    checkpoint_file = os.path.join(base_directory_path, checkpoint_fstr)
    log_file = os.path.join(base_directory_path, log_fstr)
    
    if verbose:
        print()
        print(f"      Base: {base_directory_path}")
        print(f"Checkpoint: {checkpoint_fstr}")
        print(f"       Log: {checkpoint_fstr}")
        print()

    ft = FileTree(
        base_directory_path,
        skips, 
        log_file=log_file, 
        checkpoint_file=checkpoint_file        
    )
    ft.collect_file_tree()
    ft.save_state(checkpoint_file)

    return ft


def process_parallel(base_path, 
                     max_workers=56, 
                     verbose=False):

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    
        futures = {
            executor.submit(process_directory, base_dir): {
                'base': base_dir, 'name': dir_name
            } for dir_name, base_dir 
            in get_base_dirs(base_path).items()
        }
        
    
        for future in concurrent.futures.as_completed(futures):
        
            _dir = futures[future]
            
            try:
                result = future.result()
                if verbose:
                    print(f"Processing completed for: {result.base_directory}")
                    print(f"                          {_dir['name']}")
                    
            except Exception as exc:
                print(f"Error processing {_dir['base']}: {exc}")


class FileTree:

    def __init__(self, base_directory, skips=None, verbose=False, log_file=None, checkpoint_file=None):

        self.graph = None
        self.base_directory = Path(base_directory)
        self.skips = skips if skips is not None else []
        self.verbose = verbose
        self.log_file = log_file
        self.file_tree = None
        self.file_types = (
            '.log',
            '.json',
            '.xml',
            '.xml.bak',
            '.vxml',
            '.vxml.bak',
            '.mxml',
            '.mxml.bak',
            '.txt',
            '.dcm',
            '.dicom',
            '.tif',
            '.tiff'
        )

        if log_file:
            self.setup_logging(log_file, verbose)

        if checkpoint_file and Path(checkpoint_file).is_file():
            self.load_state(checkpoint_file)
            self.build_file_path_index()
            self.build_graph()

        elif verbose:
                print(f"No checkpoint available at {checkpoint_file}")
                print(f"To create, run `manager.collect_file_tree()`")

    def is_folder_metadata(self, parent_folder_path, file_path):
        if '.log' in file_path:
            return True
        else:
            return False

    def is_file_metadata(self, file_path):
        pass

    def build_graph(self):
        self.graph = nx.DiGraph()

        def process_folder(folder_path, folder_meta, parent_id=None):

            folder_id = f"folder_{folder_path}"
            folder_absolute_path = os.path.abspath(folder_path)

            self.graph.add_node(
                folder_id,
                label='Folder',
                name=Path(folder_path).name,
                filepath=folder_absolute_path
            )

            if parent_id:
                self.graph.add_edge(
                    parent_id,
                    folder_id,
                    relationship='contains_folder'
                )

            process_files(
                folder_meta.get('contents', {}),
                folder_id,
                folder_path
            )

            process_metadata(
                folder_meta.get('metadata', {}),
                folder_id,
                folder_absolute_path
            )

            for subfolder_name, subfolder_meta in folder_meta.get('contents', {}).items():
                if isinstance(subfolder_meta, dict) and subfolder_meta.get('type') == 'folder':
                    subfolder_path = os.path.join(folder_path, subfolder_name)
                    process_folder(subfolder_path, subfolder_meta, folder_id)

        def process_files(files_dict, parent_folder_id, parent_folder_path):

            for file_name, file_info in files_dict.items():

                if isinstance(file_info, dict) and file_info.get('type') != 'folder':

                    file_path = os.path.join(
                        parent_folder_path,
                        file_name
                    )

                    file_info['filepath'] = os.path.abspath(file_path)

                    file_id = f"file_{file_info['filepath']}"

                    _properties = file_info.copy()
                    _meta = _properties.pop('metadata', {})
                    _properties.update(_meta)

                    self.graph.add_node(
                        file_id,
                        label='File',
                        **_properties)

                    self.graph.add_edge(
                        parent_folder_id,
                        file_id,
                        relationship='contains_file')

                    if self.is_folder_metadata(parent_folder_path, file_info['filepath']):

                        # process_metadata(
                        #     file_info.get('metadata', {}),
                        #     file_id,
                        #     file_path
                        # )
                        process_metadata(
                            file_info.get('metadata', {}),
                            parent_folder_id,
                            parent_folder_path
                        )

                else:
                    pass

        def process_metadata(meta_dict, parent_id, parent_path):

            if meta_dict:

                for section, attrs in meta_dict.items():

                    # TODO: Generalize; currently handles only MicroCT
                    if isinstance(attrs, dict):

                        section = section.replace(' ', '_')
                        section_id = f"{section}_{parent_path}"

                        _properties = {
                            format_property_key(_k): _v
                            for _k, _v in attrs.items()
                        }

                        self.graph.add_node(
                            section_id,
                            label=section,
                            **_properties
                        )

                        scan_id = f"scan_{parent_path}"

                        self.graph.add_node(
                            scan_id,
                            label='Scan',
                            filepath=parent_path
                        )

                        self.graph.add_edge(
                            scan_id,
                            section_id,
                            relationship='involved'
                        )

                        self.graph.add_edge(
                            scan_id,
                            parent_id,
                            relationship='stored_in'
                        )

                    else:
                        pass

                        # metadata_id = f"meta_{parent_path}"
                        #
                        # if not self.graph.has_node(metadata_id):
                        #     _properties = {
                        #         format_property_key(_k): _v
                        #         for _k, _v in meta_dict.items()
                        #     }
                        #
                        #     self.graph.add_node(
                        #         metadata_id,
                        #         label='Metadata',
                        #         **_properties
                        #     )
                        #
                        #     self.graph.add_edge(
                        #         parent_id,
                        #         metadata_id,
                        #         relationship='has_metadata'
                        #     )

        process_folder(
            self.base_directory,
            self.file_tree['base']
        )

        print("File tree graph built.")

    def setup_logging(self, log_file, verbose):
        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(message)s')
        if verbose:
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s %(message)s')
            console.setFormatter(formatter)
            logging.getLogger().addHandler(console)

    def log_message(self, message):
        logging.info(message)

    def remove_contents_key(self, meta):
        if isinstance(meta, dict) and 'contents' in meta:
            meta_copy = meta.copy()  # Create a shallow copy of the dictionary
            del meta_copy['contents']  # Remove the 'contents' key
            return meta_copy
        return meta

    def parse_metadata_file(self, file_path):
        parsers = {
            '.log': self.parse_log_file,
            '.json': self.parse_json_file,
            '.xml': self.parse_xml_file,
            '.dcm': self.parse_dicom_file,
            '.dicom': self.parse_dicom_file,
            '.tif': self.parse_tif_file,
            '.tiff': self.parse_tif_file,
            # Add other specific file type parsers here
        }
        _, ext = os.path.splitext(file_path)
        parser = parsers.get(ext)
        if parser:
            return parser(file_path)
        else:
            self.log_message(f"No parser available for file with extension {ext}")
            return {}

    def parse_log_file(self, file_path):
        meta_dict = {}
        current_section = None
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        meta_dict[current_section] = {}
                    elif '=' in line:
                        key, value = line.split('=', 1)
                        if current_section:
                            meta_dict[current_section][key.strip()] = value.strip()
                        else:
                            meta_dict[key.strip()] = value.strip()
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
        return meta_dict

    def parse_json_file(self, file_path):
        return {'format': 'json'}

    def parse_xml_file(self, file_path):
        return {'format': 'xml'}

    def parse_dicom_file(self, file_path):
        return {'format': 'dicom'}

    def parse_tif_file(self, file_path):
        try:
            img = Image.open(file_path)
            meta = {}
            for key in img.tag_v2:
                if key in TAGS:
                    meta[TAGS[key]] = img.tag[key]
                else:
                    meta[f"TAG_{key}"] = img.tag[key]
            return meta
        except Exception as e:
            self.log_message(f"Error processing TIFF file {file_path}: {e}")
            return {}

    def update_folder_sizes(self, parts, file_size, tree):
        current_tree = tree
        for part in parts:
            if part not in current_tree:
                current_tree[part] = {'type': 'folder', 'size': 0, 'created': None, 'modified': None, 'contents': {}}
            current_tree = current_tree[part]['contents']
            if 'size' in current_tree:
                current_tree['size'] += file_size
            else:
                current_tree['size'] = file_size

    def collect_file_tree(self):
        def add_to_tree(path, tree):
            parts = path.relative_to(self.base_directory).parts
            current_tree = tree
            for part in parts[:-1]:
                if part not in current_tree:
                    current_tree[part] = {'type': 'folder', 'size': 0, 'created': None, 'modified': None,
                                          'contents': {}}
                current_tree = current_tree[part]['contents']
            if path.is_dir():
                stats = path.stat()
                current_tree[parts[-1]] = {
                    'type': 'folder',
                    'size': 0,  # Placeholder size for folders
                    'created': time.ctime(stats.st_ctime),
                    'modified': time.ctime(stats.st_mtime),
                    'contents': {}
                }
                self.log_message(f"Added directory: {path}")
            elif path.is_file():
                stats = path.stat()
                meta_data = {}
                if path.suffix in self.file_types:
                    meta_data = self.parse_metadata_file(path)
                current_tree[parts[-1]] = {
                    'type': f'{path.suffix}',
                    'size': stats.st_size,
                    'created': time.ctime(stats.st_ctime),
                    'modified': time.ctime(stats.st_mtime),
                    'contents': None,
                    'metadata': meta_data
                }
                self.log_message(f"Added file: {path}")
                # Update the size of all parent directories
                self.update_folder_sizes(parts[:-1], stats.st_size, tree)

        # Ensure the base directory itself is included
        file_tree = {
            'base': {
                'type': 'folder',
                'size': 0,  # Placeholder size for base directory
                'created': time.ctime(self.base_directory.stat().st_ctime),
                'modified': time.ctime(self.base_directory.stat().st_mtime),
                'contents': {}
            }
        }

        for item in self.base_directory.rglob('*'):
            if not any(skip in str(item) for skip in self.skips):
                add_to_tree(item, file_tree['base']['contents'])
                if item.is_dir():
                    self.log_message(f"Processing directory: {item}")
                elif item.is_file():
                    self.log_message(f"Processing file: {item}")

        self.file_tree = file_tree
        return file_tree

    def build_file_path_index(self):
        """ Build an index of all file paths for autocompletion. """
        self.file_path_index = []

        def recurse_tree(tree, current_path):
            for name, meta in tree.items():
                if isinstance(meta, dict) and 'type' in meta:
                    new_path = f"{current_path}/{name}" if current_path else name
                    self.file_path_index.append(new_path)
                    if meta['type'] == 'folder' and 'contents' in meta:
                        recurse_tree(meta['contents'], new_path)

        if self.file_tree:
            recurse_tree(self.file_tree['base']['contents'], 'base')

        print("File path index built.")

    def autocomplete_path(self, prefix):
        """ Autocomplete potential directory paths based on the index. """
        return [path for path in self.file_path_index if path.startswith(prefix)]

    def get_directory_contents(self, path=''):
        # parts = path.split('/')[1:]
        parts = [_i for _i in path.split('/') if len(_i) > 0]
        current_tree = self.file_tree['base']['contents']
        for part in parts:
            if part in current_tree:
                current_tree = current_tree[part]['contents']
            else:
                raise ValueError(f"Path '{path}' not found in the directory structure.")
        return current_tree

    def list_files(self, directory=''):
        _l = []

        def process_files(tree):
            for _k, _v in tree.items():
                if isinstance(_v, dict) and _v.get('type') != 'folder':
                    _d = _v.copy()
                    del _d['contents']
                    _d['name'] = _k
                    _l.append(_d)

        directory_contents = self.get_directory_contents(directory)
        process_files(directory_contents)
        return pd.DataFrame(_l)

    def list_folders(self, directory=''):
        _l = []

        def folder_size_sum(tree):
            _sum_size = 0
            for _i, _contents in tree.items():
                if isinstance(_contents, dict):
                    if _contents['type'] == 'folder':
                        _sum_size += folder_size_sum(_contents['contents'])
                    else:
                        _sum_size += _contents['size']
            return _sum_size

        def process_folders(tree):
            for _k, _v in tree.items():
                if isinstance(_v, dict) and _v.get('type') == 'folder':
                    _d = {
                        'type': _v['type'],
                        'size': folder_size_sum(_v['contents']),
                        'created': _v['created'],
                        'modified': _v['modified'],
                        'name': _k
                    }
                    _l.append(_d)

        directory_contents = self.get_directory_contents(directory)
        process_folders(directory_contents)
        return pd.DataFrame(_l)

    def list_all(self, directory=''):
        files_df = self.list_files(directory)
        folders_df = self.list_folders(directory)
        return pd.concat([files_df, folders_df], ignore_index=True)

    def extract_tiff_tags(self, img):
        for _k in img.tag_v2:
            if _k in TAGS.keys():
                print(TAGS[_k], img.tag[_k])
            else:
                print(f"CUSTOM TAG[{_k}]", img.tag[_k])

    def save_state(self, file_name, save_graph=False):
        """ Save the necessary data structures of the ForestSurveyor to a file. """
        state = {
            'base_directory': self.base_directory,
            'file_tree': self.file_tree
        }
        with open(file_name, 'wb') as f:
            pickle.dump(state, f)
        print(f"State saved to {file_name}.")

        if self.graph is not None and save_graph:
            graphml_file_name = str(file_name).replace('.pkl', '.graphml')
            temp_graph = self.translate_for_graphml(self.graph)
            nx.write_graphml(temp_graph, graphml_file_name)
            print(f"Graph saved to {graphml_file_name}.")

    def load_state(self, file_name, load_graph=False):
        """ Load the necessary data structures of the ForestSurveyor from a file. """
        with open(file_name, 'rb') as f:
            state = pickle.load(f)
            self.base_directory = state['base_directory']
            self.file_tree = state['file_tree']
        print(f"State loaded from {file_name}.")

        graphml_file_name = str(file_name).replace('.pkl', '.graphml')
        if os.path.exists(graphml_file_name):
            if load_graph:
                temp_graph = nx.read_graphml(graphml_file_name)
                self.graph = self.translate_from_graphml(temp_graph)
                print(f"Graph loaded from {graphml_file_name}.")
            else:
                print(f"Graph found but not loaded ({graphml_file_name}).")
        else:
            self.graph = None
            print(f"No graph file found at {graphml_file_name}.")

    def translate_for_graphml(self, graph):
        """ Convert unsupported types in the graph to GraphML-friendly format. """
        temp_graph = graph.copy()
        for node, data in temp_graph.nodes(data=True):
            for key, value in list(data.items()):
                if value is None:
                    data[key] = "NoneType"
                elif isinstance(value, list):
                    data[key] = ",".join(map(str, value))
                elif isinstance(value, dict):
                    data[key] = str(value)
                elif isinstance(value, tuple):
                    data[key] = ",".join(map(str, value))
        for u, v, data in temp_graph.edges(data=True):
            for key, value in list(data.items()):
                if value is None:
                    data[key] = "NoneType"
                elif isinstance(value, list):
                    data[key] = ",".join(map(str, value))
                elif isinstance(value, dict):
                    data[key] = str(value)
                elif isinstance(value, tuple):
                    data[key] = ",".join(map(str, value))
        return temp_graph

    def translate_from_graphml(self, graph):
        """ Convert GraphML-friendly format back to original types in the graph. """
        for node, data in graph.nodes(data=True):
            for key, value in list(data.items()):
                if value == "NoneType":
                    data[key] = None
                elif isinstance(value, str) and ',' in value:
                    data[key] = value.split(',')
                elif isinstance(value, str) and (value.startswith('{') and value.endswith('}')):
                    try:
                        data[key] = eval(value)
                    except:
                        pass
        for u, v, data in graph.edges(data=True):
            for key, value in list(data.items()):
                if value == "NoneType":
                    data[key] = None
                elif isinstance(value, str) and ',' in value:
                    data[key] = value.split(',')
                elif isinstance(value, str) and (value.startswith('{') and value.endswith('}')):
                    try:
                        data[key] = eval(value)
                    except:
                        pass
        return graph
