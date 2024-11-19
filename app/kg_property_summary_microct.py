import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import .labdataranger as ldr

db_config = ldr.query.get_db_config()
uri = f"{db_config['uri']}:{db_config['port']}"
username = db_config['username']
password = db_config['password']
database = "instruments"


def fetch_properties_by_label(label):
    query = f"MATCH (n:{label}) RETURN properties(n) AS properties"
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session(database=database) as session:
        result = session.run(query)
        data = [record["properties"] for record in result]
    driver.close()
    return pd.DataFrame(data)

def summarize_property_analysis(df):
    summary_data = []
    for prop in df.columns:
        counts = df[prop].value_counts(dropna=False)
        summary = {
            'property': prop,
            'total_value_count': counts.sum(),
            'unique_value_count': counts.index.nunique(dropna=False),
            'unique_values': list(counts.index)
        }
        summary_data.append(summary)
    return pd.DataFrame(summary_data).sort_values(by='unique_value_count', ascending=False).reset_index(drop=True)

def app():
    st.title('MicroCT Metadata Viewer [Demo]')

    label = st.sidebar.selectbox("Label", ['User', 'System', 'Acquisition', 'Reconstruction'])
    if st.sidebar.button('Display'):
        meta_dict = {label: fetch_properties_by_label(label)}
        summary_dict = {label: summarize_property_analysis(meta_dict[label])}
        st.session_state['summary_dict'] = summary_dict
        st.session_state['meta_dict'] = meta_dict
        show_data(summary_dict, meta_dict, label)

    if st.sidebar.button('Refresh'):
        meta_dict = {label: fetch_properties_by_label(label)}
        summary_dict = {label: summarize_property_analysis(meta_dict[label])}
        st.session_state['summary_dict'] = summary_dict
        st.session_state['meta_dict'] = meta_dict
        show_data(summary_dict, meta_dict, label)

    manage_filters(label)
    manage_column_selection_sidebar()

def show_data(summary_dict, meta_dict, label):
    st.write("### Property Summary", summary_dict[label])
    st.write("### All Properties", meta_dict[label])

def manage_filters(label):
    if 'filters' not in st.session_state:
        st.session_state['filters'] = []

    if st.sidebar.button('Add Filter'):
        st.session_state['filters'].append({'property': None, 'values': []})

    for i, _filter in enumerate(st.session_state['filters']):
        options = st.session_state['summary_dict'][label]['property'] if 'summary_dict' in st.session_state else []
        _filter['property'] = st.sidebar.selectbox(f"Property {i+1}", options, key=f'prop_{i}')
        if _filter['property']:
            possible_values = st.session_state['summary_dict'][label][st.session_state['summary_dict'][label]['property'] == _filter['property']].iloc[0]['unique_values']
            _filter['values'] = st.sidebar.multiselect(f"Values for {_filter['property']} {i+1}", possible_values, key=f'val_{i}')

    if st.sidebar.button("Filter Data"):
        query, parameters = generate_cypher_query(label, st.session_state['filters'])
        results = execute_cypher_query(query, parameters)
        st.session_state['query_results'] = results
        show_data(st.session_state['summary_dict'], st.session_state['meta_dict'], label)

def manage_column_selection_sidebar():
    if 'query_results' in st.session_state and not st.session_state['query_results'].empty:
        column_container = st.sidebar.container()
        with column_container:
            st.write("## Column Selector")
            available_columns = st.session_state['query_results'].columns.tolist()
            selected_columns = st.multiselect('Select columns to display:', available_columns, key='column_selector')
            if selected_columns:
                filtered_results = st.session_state['query_results'][selected_columns]
                st.write("### Selected Data", filtered_results)
                csv = filtered_results.to_csv(index=False)
                st.download_button("Download selected data as CSV", csv, "filtered_data.csv", "text/csv", key='download-csv')




def generate_cypher_query(label, filters):
    where_clauses = []
    parameters = {}
    for i, f in enumerate(filters):
        if f['property'] and f['values']:
            param_name = f"values{i}"
            where_clauses.append(f"n.{f['property']} IN ${param_name}")
            parameters[param_name] = f['values']

    query = f"MATCH (n:{label})" + (" WHERE " + " AND ".join(where_clauses) if where_clauses else "") + " RETURN n"
    return query, parameters
    

def execute_cypher_query(query, parameters):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session(database=database) as session:
        result = session.run(query, parameters)
        data = [record["n"] for record in result]
    driver.close()
    return pd.DataFrame(data)




if __name__ == "__main__":
    app()
