from neomodel import StructuredNode, StringProperty, RelationshipTo, RelationshipFrom, IntegerProperty


class Folder(StructuredNode):
    name = StringProperty()
    filepath = StringProperty(index=True)
    contains_folder = RelationshipTo('Folder', 'CONTAINS_FOLDER')
    contained_by = RelationshipFrom('Folder', 'CONTAINS_FOLDER')
    contains_file = RelationshipTo('File', 'CONTAINS_FILE')
    has_metadata = RelationshipTo('Metadata', 'HAS_METADATA')


class File(StructuredNode):
    name = StringProperty()
    filepath = StringProperty(index=True)
    extension = StringProperty()
    size = IntegerProperty()
    contained_by = RelationshipFrom('Folder', 'CONTAINS_FILE')
    has_metadata = RelationshipTo('Metadata', 'HAS_METADATA')


class Scan(StructuredNode):
    filepath = StringProperty(index=True)
    stored_in = RelationshipTo('Folder', 'STORED_IN')
    involved = RelationshipTo('Section', 'INVOLVED')


class Section(StructuredNode):
    name = StringProperty(unique_index=True)
    involved_in = RelationshipFrom('Scan', 'INVOLVED')


class Metadata(StructuredNode):
    key = StringProperty()
    value = StringProperty()
    belongs_to_folder = RelationshipFrom('Folder', 'HAS_METADATA')
    belongs_to_file = RelationshipFrom('File', 'HAS_METADATA')


def build_classes(g):
    (meta_section_properties,
     meta_section_labels,
     schema_labels) = collect_properties_by_meta_section(g)

    class_map = initialize_class_map_from_graph(
        meta_section_properties
    )

    class_dict = {}
    for _k in class_map.keys():
        class_dict[_k] = collect_class_attributes(
            class_map[_k])

    return class_map, class_dict


def find_nodes_by_label(g, label):
    for node, data in g.nodes(data=True):
        if data['label'] == label:
            print(node)
            print(data)
            print()


def collect_properties_by_meta_section(nx_graph):
    schema_labels = ['Folder', 'File', 'Scan']
    meta_section_labels = []
    for node, data in nx_graph.nodes(data=True):
        label = data['label']
        if label not in schema_labels and label not in meta_section_labels:
            meta_section_labels.append(label)

    props_by_section = {}
    for section in meta_section_labels:
        props_by_section[section] = set()
        for node, data in nx_graph.nodes(data=True):
            label = data['label']
            if label == section:
                for _k, _v in data.items():
                    if _k != 'label':
                        props_by_section[section].add(_k)

    return {_s: list(_p)
            for _s, _p in props_by_section.items()}, meta_section_labels, schema_labels


def initialize_class_map_from_graph(meta_section_properties,
                                    class_map={'Folder': Folder,
                                               'File': File,
                                               'Scan': Scan,
                                               'Section': Section}):
    # Create Neomodel classes for each unique section label found
    for section_name in meta_section_properties.keys():
        class_key = section_name.replace(' ', '_')
        if class_key not in class_map:
            class_map[class_key] = type(class_key, (Section,), {
                _p: StringProperty(unique_index=True)
                for _p in meta_section_properties[section_name]
            })

    return class_map


def collect_class_attributes(model_class, verbose=False):
    _d = {
        'properties': {},
        'relationships': {}
    }
    for attr in dir(model_class):
        if not attr.startswith("__") and not callable(getattr(model_class, attr)):
            _fstr = str(getattr(model_class, attr))
            _fstr = _fstr.strip('<').split(' ')[0]
            if 'property' in _fstr or 'properties' in _fstr:
                _d['properties'][attr] = _fstr
            if 'relationship' in _fstr:
                _d['relationships'][attr] = _fstr
    if verbose:
        print("Attributes:")
        for _i in ['relationships', 'properties']:
            print(_i.capitalize())
            for _attr, _fstr in _d[_i].items():
                print(f"  {_attr:>35s}: {_fstr}")
            print()

    return _d
