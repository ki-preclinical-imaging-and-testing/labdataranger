import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
from pyvis.network import Network
import json

# Neo4j Connection
def get_neo4j_session(uri, user, password, database=None):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    session = driver.session(database=database) if database else driver.session()
    return session

# Fetch available databases
def fetch_databases(session):
    query = "SHOW DATABASES"
    results = session.run(query)
    return [record["name"] for record in results]

# Schema Extraction Algorithm
def extract_schema(results):
    triples = set()
    for record in results:
        triples.add((record["subjectLabel"], record["predicateType"], record["objectLabel"]))
    nodes = {label for triple in triples for label in (triple[0], triple[2])}
    return triples, nodes

# Pyvis Graph Creation with Layout Options
def create_pyvis_graph(triples, layout):
    net = Network(notebook=False, height="750px", width="100%")

    # Apply selected layout
    if layout == "Hierarchical":
        net.set_options(json.dumps({
            "layout": {
                "hierarchical": {
                    "enabled": True,
                    "levelSeparation": 150,
                    "nodeSpacing": 100,
                    "treeSpacing": 200,
                    "direction": "UD",  # UD = Up-Down
                    "sortMethod": "hubsize"
                }
            }
        }))
    else:
        net.barnes_hut()  # Force-directed layout

    for subject, predicate, object_ in triples:
        net.add_node(subject, label=subject)
        net.add_node(object_, label=object_)
        net.add_edge(subject, object_, label=predicate, arrows="to")  # Add directionality
    return net

# Streamlit App
def main():
    st.sidebar.title("Neo4j Connection")

    # Connection Details in Sidebar
    uri = st.sidebar.text_input("Neo4j URI", "bolt://localhost:7687")
    user = st.sidebar.text_input("Username", "neo4j")
    password = st.sidebar.text_input("Password", type="password")

    if "connected" not in st.session_state:
        st.session_state.connected = False

    if "selected_db" not in st.session_state:
        st.session_state.selected_db = None

    if st.sidebar.button("Connect"):
        with st.spinner("Connecting to Neo4j..."):
            try:
                session = get_neo4j_session(uri, user, password)
                st.session_state.session = session
                st.session_state.connected = True
                st.success("Connected!")
            except Exception as e:
                st.sidebar.error(f"Connection failed: {e}")
                st.session_state.connected = False

    if st.session_state.connected:
        with st.spinner("Fetching available databases..."):
            databases = fetch_databases(st.session_state.session)
            st.sidebar.title("Database Selection")
            selected_db = st.sidebar.selectbox(
                "Select Database",
                databases,
                index=databases.index(st.session_state.selected_db) if st.session_state.selected_db else 0
            )
            st.session_state.selected_db = selected_db

        # Schema Sampling Section
        st.sidebar.title("Schema Sampling")
        sample_size = st.sidebar.number_input("Sample Size", min_value=1, value=100, step=10)
        include_all = st.sidebar.checkbox("Include All (No Limit)", value=False)
        layout = st.sidebar.radio("Schema Layout", ["Force-Directed", "Hierarchical"], index=0)

        if st.sidebar.button("Sample Schema"):
            session = get_neo4j_session(uri, user, password, database=st.session_state.selected_db)

            # Construct the query dynamically
            limit_clause = "" if include_all else f"LIMIT {sample_size}"
            query = f"""
            MATCH (n)-[r]->(m)
            RETURN labels(n)[0] AS subjectLabel, type(r) AS predicateType, labels(m)[0] AS objectLabel
            {limit_clause}
            """
            with st.spinner("Sampling schema..."):
                results = session.run(query)
                results_list = [record.data() for record in results]
                st.success(f"Sampled {len(results_list)} rows from the schema!")

                # Extract Schema and Cache Results
                triples, nodes = extract_schema(results_list)
                st.session_state.cached_triples = triples
                st.write(f"Extracted {len(triples)} unique triples and {len(nodes)} unique nodes.")

        # Graph Visualization
        if "cached_triples" in st.session_state:
            net = create_pyvis_graph(st.session_state.cached_triples, layout)
            net_html = net.generate_html()
            st.components.v1.html(net_html, height=800)

            # Display Results Table
            st.write("Resulting Data Table")
            st.dataframe(pd.DataFrame(st.session_state.cached_triples, columns=["Subject", "Predicate", "Object"]))


if __name__ == "__main__":
    main()

