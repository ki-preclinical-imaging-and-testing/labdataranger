import logging
from tqdm import tqdm
from pathlib import Path
from neomodel import db, config
from .query import get_db_config
from labdataranger.disk.filetree.survey import format_property_key, get_base_dirs, FileTree
from .model import build_classes


def neomodel_db_config(config_file='db_config.json', database=None):
    _config_file = get_db_config(config_file)
    protocol = _config_file['uri'].split(':')[0]
    hostname = _config_file['uri'].split(':')[1].split('/')[0]
    port = _config_file['port']
    username = _config_file['username']
    password = _config_file['password']
    try:
        if database:
            config.DATABASE_URL = f'{protocol}://{username}:{password}@{hostname}:{port}/{database}'
        else:
            config.DATABASE_URL = f'{protocol}://{username}:{password}@{hostname}:{port}'
    except Exception as e:
        print(f"ERROR: Database config failed with Exception {e}")


def push_to_neo4j(nx_graph, class_map, log_file='push.out'):

    logging.basicConfig(filename=log_file, level=logging.ERROR, format='%(asctime)s %(message)s')

    node_map = {}
    with db.transaction:
        for node, data in tqdm(nx_graph.nodes(data=True), desc="Nodes"):
            label = data['label']
            properties = {
                k: v
                for k, v in data.items() if k not in ['label', 'relationship']
            }

            NodeClass = class_map.get(label, None)
            if NodeClass:
                try:
                    node_instance = NodeClass(**properties).save()
                    node_map[node] = node_instance
                except Exception as e:
                    error_message = f"Error saving node {node} of type {label}: {e}"
                    logging.error(error_message)
            else:
                label_mod = format_property_key(label)
                NodeClass = class_map.get(label_mod, None)
                if NodeClass:
                    try:
                        node_instance = NodeClass(**properties).save()
                        node_map[node] = node_instance
                    except Exception as e:
                        error_message = f"Error saving node {node} of type {label_mod}: {e}"
                        logging.error(error_message)
                else:
                    warning_message = f"WARNING: Node {node} has no label match:\n{data}"
                    logging.warning(warning_message)

        for source, target, data in tqdm(nx_graph.edges(data=True), desc="Edges"):
            relationship_type = data.get('relationship')
            source_node = node_map.get(source)
            target_node = node_map.get(target)

            if source_node and target_node and relationship_type:
                source_type = nx_graph.nodes[source]['label']
                source_type_camel_case = format_property_key(source_type)
                relationship = getattr(class_map[source_type], relationship_type, None)
                if not relationship:
                    print("Source:", source_node)
                    print("Target:", target_node)
                    print("Source Type:", source_type)
                    print("Relationship Type", relationship_type)
                    relationship = getattr(class_map[source_type_camel_case], relationship_type, None)
                if relationship:
                    try:
                        getattr(source_node, relationship_type).connect(target_node)
                    except ValueError as ve:
                        error_message = f"Error connecting {source_node} to {target_node}: {ve}"
                        logging.error(error_message)
                    except Exception as e:
                        error_message = f"Unexpected error connecting {source_node} to {target_node}: {e}"
                        logging.error(error_message)
                else:
                    warning_message = f"Relationship type '{relationship_type}' not found between {source} and {target}"
                    logging.warning(warning_message)

    print("Graph loading complete!")
    return node_map


def push_tree_to_db(base_path, checkpoint_fstr='.labdataranger.pkl'):
    base_path = Path(base_path)
    print(base_path)
    ft = FileTree(
        base_path, 
        checkpoint_file=base_path.joinpath(checkpoint_fstr)
    )    
    class_map, class_dict = build_classes(ft.graph)
    try:
        node_map = push_to_neo4j(ft.graph, class_map)
    except: 
        print(f"ERROR: {base_path.name} filetree could not be loaded")


def push_forest_to_db(base_path, 
                      checkpoint_fstr='.labdataranger.pkl'):
    
    for dir_name, base_dir in get_base_dirs(base_path).items():
        push_tree_to_db(base_dir, checkpoint_fstr=checkpoint_fstr)
        # ft = FileTree(base_dir, checkpoint_file=checkpoint)    
        # class_map, class_dict = build_classes(ft.graph)
        # try:
        #     node_map = push_to_neo4j(ft.graph, class_map)
        # except: 
        #     print(f"ERROR: {dir_name} filetree could not be loaded")



def create_and_connect_folders(parent_folder_path, 
                               database=None,
                               config_file='db_config.json'):

    db_config = get_db_config(config_file=config_file)
    uri = f"{db_config['uri']}:{db_config['port']}"
    username = db_config['username']
    password = db_config['password']
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    parent_folder_name = os.path.basename(parent_folder_path.rstrip('/'))    

    query = """
        MERGE (parent:Folder {filepath: $parentFolderPath, name: $parentFolderName})
        WITH parent
        MATCH (subfolder:Folder)
        WHERE subfolder.filepath STARTS WITH $parentFolderPath + '/'
          AND NOT (subfolder)<-[:CONTAINS_FOLDER]-(:Folder)
          AND subfolder.filepath <> $parentFolderPath
        MERGE (parent)-[:CONTAINS_FOLDER]->(subfolder)
        RETURN parent, subfolder
    """
    
    with driver.session(database=database) as session:
        
        result = session.run(query, 
                             parentFolderPath=parent_folder_path,
                             parentFolderName=parent_folder_name)
        
        print("Related Subfolders to Base Folder")
        for record in result:
            print()
            print(f"  Parent Folder: {record['parent']['filepath']}")
            print(f"      Subfolder: {record['subfolder']['filepath']}")
            print()
            
    driver.close()
