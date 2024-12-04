import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
from pyvis.network import Network
import json
from io import BytesIO

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

## Fetch nodes by label
#def fetch_nodes_by_label(session, label, with_clause):
#    query = f"""
#    {with_clause}
#    MATCH (n:{label})
#    RETURN n
#    """
#    results = session.run(query)
#    nodes = [record["n"] for record in results]
#    node_data = [
#        {key: value for key, value in node.items()} for node in nodes
#    ]
#    return node_data

def fetch_nodes_by_label(session, label, with_clause):
    query = f"""
    {with_clause}
    MATCH (n:{label})
    RETURN n AS node
    UNION
    {with_clause}
    MATCH (m:{label})
    RETURN m AS node
    """
    results = session.run(query)

    # Collect unique nodes from both queries
    nodes = [dict(record["node"]) for record in results]
    return pd.DataFrame(nodes).drop_duplicates()


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
        recall_query = st.sidebar.text_area(
            "Recall Query", 
            value="MATCH (n)-[r]->(m)\nWITH DISTINCT n, r, m "
        )
        sample_size = st.sidebar.number_input("Sample Size", min_value=1, value=100, step=10)
        include_all = st.sidebar.checkbox("Include All (No Limit)", value=False)
        layout = st.sidebar.radio("Schema Layout", ["Hierarchical", "Force-Directed"], index=0)

        if st.sidebar.button("Sample Schema"):
            session = get_neo4j_session(uri, user, password, database=st.session_state.selected_db)
            limit_clause = "" if include_all else f"LIMIT {sample_size}"
            with_clause = recall_query.strip() if recall_query.strip() else ""
            query = f"""
            {with_clause}
            MATCH (n)-[r]->(m)
            RETURN labels(n)[0] AS subjectLabel, type(r) AS predicateType, labels(m)[0] AS objectLabel
            {limit_clause}
            """
            with st.spinner("Sampling schema..."):
                results = session.run(query)
                results_list = [record.data() for record in results]
                st.success(f"Sampled {len(results_list)} rows from the schema!")

                triples, nodes = extract_schema(results_list)
                st.session_state.cached_triples = triples
                st.session_state.cached_labels = sorted(nodes)  # Ensure this is updated

        # Graph Visualization
        if "cached_triples" in st.session_state:
            net = create_pyvis_graph(st.session_state.cached_triples, layout)
            net_html = net.generate_html()
            st.components.v1.html(net_html, height=800)

        # Node Data Extraction
        st.sidebar.title("Recall Nodes")
        if "cached_labels" in st.session_state:
            selected_labels = st.sidebar.multiselect("Select Node Labels", st.session_state.cached_labels)

            if st.sidebar.button("Fetch Nodes"):
                with st.spinner(f"Fetching nodes for labels: {', '.join(selected_labels)}"):
                    session = get_neo4j_session(uri, user, password, database=st.session_state.selected_db)
                    node_dataframes = {}
                    for label in selected_labels:
                        node_data = fetch_nodes_by_label(session, label, recall_query.strip())
                        node_dataframes[label] = pd.DataFrame(node_data)
                    st.session_state.node_dataframes = node_dataframes

        if "node_dataframes" in st.session_state:
            tabs = st.tabs(st.session_state.node_dataframes.keys())
            for label, tab in zip(st.session_state.node_dataframes.keys(), tabs):
                with tab:
                    st.write(f"Nodes: {label}")
                    st.dataframe(st.session_state.node_dataframes[label], use_container_width=True)

            # Option to set filename
            st.write("### Export")
            st.text("Dataframes above can be exported as a CSV - hover over top right corner of dataframe for export button.\nDownload everything as an Excel workbook using buttons below.")
            
            # Export all to Excel
            if st.button("Export All to Excel"):
                filename = st.text_input("Enter filename for Excel workbook", value="node_data.xlsx")
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    for label, df in st.session_state.node_dataframes.items():
                        df.to_excel(writer, index=False, sheet_name=label)
                output.seek(0)
                st.download_button(
                    label="Download Excel Workbook",
                    data=output,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


if __name__ == "__main__":
    main()

