import streamlit as st
from neo4j import GraphDatabase
import pandas as pd

# Neo4j Connection
def get_neo4j_session(uri, user, password, database=None):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    session = driver.session(database=database) if database else driver.session()
    return session

def fetch_databases(session):
    query = "SHOW DATABASES"
    results = session.run(query)
    return [record["name"] for record in results]

def fetch_scans(session, query):
    results = session.run(query)
    rows = [record.data() for record in results]
    df = pd.DataFrame(rows)
    return df.pivot(
            index="ScanID", 
            columns="PropertyName", 
            values="Value").reset_index(drop=True)


# Streamlit App
def main():
    # Session State Initialization
    if "connected" not in st.session_state:
        st.session_state.connected = False

    if "selected_db" not in st.session_state:
        st.session_state.selected_db = None

    with st.sidebar.expander("Neo4j Connection", expanded=True):
        st.title("Neo4j Connection")
        uri = st.text_input("Neo4j URI", "bolt://localhost:7687")
        user = st.text_input("Username", "neo4j")
        password = st.text_input("Password", type="password")


        if st.button("Connect"):
            try:
                session = get_neo4j_session(uri, user, password)
                st.session_state.session = session
                st.session_state.connected = True
                st.success("Connected!")
            except Exception as e:
                st.error(f"Connection failed: {e}")
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

        # Query Editor and Execution
        st.title("Extract Scans")
        st.write("Write a Cypher query to fetch the scans. You can use the template below.")
        default_query = """MATCH (s:Scan)
WITH s, keys(s) AS keys
UNWIND keys AS key
RETURN s[key] AS Value, key AS PropertyName, ID(s) AS ScanID"""
        query = st.text_area("Cypher Query Editor", value=default_query, height=200)

        if st.button("Run Query"):
            session = get_neo4j_session(uri, user, password, database=st.session_state.selected_db)
            with st.spinner("Running query..."):
                try:
                    scans_df = fetch_scans(session, query)
                    st.success(f"Query executed successfully! Retrieved {len(scans_df)} rows.")
                    st.session_state.scans_df = scans_df
                except Exception as e:
                    st.error(f"Failed to execute query: {e}")

        # Display Query Results
        if "scans_df" in st.session_state:
            scans_df = st.session_state.scans_df
            st.write("### Query Results")
            st.dataframe(scans_df, use_container_width=True)

            # Save Results
            st.write("### Save Results")
            csv = scans_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="scans.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    main()

