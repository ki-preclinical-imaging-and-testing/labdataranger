import json
import neo4j


def get_db_config(config_file='db_config.json'):
    with open(config_file, 'r') as file:
        config = json.load(file)
    for _i in ['uri', 'port', 'username', 'password']:
        if not config.get(_i, False):
            print(f"WARNING: '{_i}' not found in {config_file}.")
    return config


def dataframe(query, config_file='db_config.json', database='neo4j', column_map=None, verbose=False):
    config = get_db_config(config_file=config_file)
    _df = None
    with neo4j.GraphDatabase.driver(config['uri'],
                                    auth=(config['username'],
                                          config['password'])) as driver:
        _df = driver.execute_query(
            query, 
            database_=database,
            result_transformer_=neo4j.Result.to_df
        )

    _df.title = f"Results for query: {query[:100]}{'...' if len(query) > 100 else ''}"

    if column_map:
        _df.rename(columns=column_map, inplace=True)

    if verbose:
        print_dataframe(_df)
        
    return _df
    
def print_dataframe(query_result):
    print(query_result.title)
    print(query_result)    