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
    return df.pivot(index="ScanID", columns="PropertyName", values="Value").reset_index(drop=True)

# Modular Connection Section
def connection_section():
    """Modular connection section always visible in the sidebar."""
    st.title("Neo4j Connection")
    
    if "connected" not in st.session_state:
        st.session_state.connected = False

    if "selected_db" not in st.session_state:
        st.session_state.selected_db = None

    uri = st.text_input("Neo4j URI", "bolt://localhost:7687", key="neo4j_uri")
    user = st.text_input("Username", "neo4j", key="neo4j_user")
    password = st.text_input("Password", type="password", key="neo4j_password")

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
            try:
                session = st.session_state.session
                databases = fetch_databases(session)

                # Store the selected database and refresh the connection
                selected_db = st.selectbox(
                    "Select Database",
                    databases,
                    index=databases.index(st.session_state.selected_db) if st.session_state.selected_db else 0,
                )
                
                # Refresh connection if database changes
                if selected_db != st.session_state.selected_db:
                    st.session_state.selected_db = selected_db
                    st.session_state.session = get_neo4j_session(
                        uri, user, password, database=selected_db
                    )
                    st.success(f"Database changed to {selected_db}!")
            except Exception as e:
                st.error(f"Error fetching databases: {e}")
                st.session_state.connected = False

# Main App with Page Navigation
def main():

    with st.sidebar.expander("Neo4j Connection", expanded=True):
        connection_section()  # Always show connection section at the top of the sidebar
   
    if st.session_state.connected:
        page = st.sidebar.selectbox(
                "Toolkit", 
                ["Pull Dataset", "Extract Metadata", "Disambiguated Dataset", "Ambiguous Dataset"]
                )

        if page == "Pull Dataset":
            pull_dataset_page()
        elif page == "Extract Metadata":
            metadata_extraction_page()
        elif page == "Disambiguated Dataset":
            disambiguated_page()
        elif page == "Ambiguous Dataset":
            ambiguous_page()



# Pull Dataset Page
def pull_dataset_page():
    st.title("Pull Dataset")
    st.write("Connect to the Neo4j database and fetch Scan data.")

    if st.session_state.connected:
        st.write("Write a Cypher query to fetch the scans. You can use the template below.")
        default_query = """MATCH (s:Scan)
WITH s, keys(s) AS keys
UNWIND keys AS key
RETURN s[key] AS Value, key AS PropertyName, ID(s) AS ScanID"""
        query = st.text_area("Cypher Query Editor", value=default_query, height=200)

        if st.button("Run Query"):
            session = st.session_state.session
            with st.spinner("Running query..."):
                try:
                    scans_df = fetch_scans(session, query)
                    st.success(f"Query executed successfully! Retrieved {len(scans_df)} rows.")
                    st.session_state.scans_df = scans_df
                except Exception as e:
                    st.error(f"Failed to execute query: {e}")

        if "scans_df" in st.session_state:
            scans_df = st.session_state.scans_df
            st.write("### Query Results")
            st.dataframe(scans_df, use_container_width=True)

            st.write("### Save Results")
            csv = scans_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="scans.csv",
                mime="text/csv",
            )

# Metadata Extraction Page
def metadata_extraction_page():
    st.title("Metadata Extraction and Organization")
    st.write("Add hierarchical fields to organize Scan data.")

    if "scans_df" in st.session_state:
        scans_df = st.session_state.scans_df.copy()
        st.write("### Current Dataset")
        st.dataframe(scans_df, use_container_width=True)

        st.write("### Add Metadata Fields")
        metadata_fields = st.multiselect(
            "Select Fields to Add", 
            ["Study", "Group", "Individual", "Date"], 
            default=["Study", "Group"]
        )
        
        for field in metadata_fields:
            if field == "Date":
                scans_df[field] = st.date_input(f"{field}:")
            else:
                scans_df[field] = st.text_input(f"{field}:", value="")
        
        if st.button("Update Dataset with Metadata"):
            # TODO: Attempt to parse filepath using lambda functions in each line above
            #
            # scans_df
            # st.success("Metadata fields updated!")
            st.success("Nothing happened! This feature remains to be built :D")

        # Provide an interactive editor for metadata fields
        st.write("### Edit Metadata")
        editable_df = st.data_editor(scans_df, use_container_width=True)

        if st.button("Commit Edited Metadata"):
            st.session_state.scans_df = editable_df
            st.success("Metadata updated!")


        st.write("### Updated Dataset")
        st.dataframe(st.session_state.scans_df, use_container_width=True)

        st.write("### Save Results")
        csv = scans_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="updated_scans.csv",
            mime="text/csv",
        )
    else:
        st.warning("No dataset loaded. Please use the Pull Dataset page first.")

# Utility function to check disambiguation
def check_disambiguation(df):
    """Splits the DataFrame into disambiguated and ambiguous rows."""
    if {"Study", "Group", "Individual", "Date"}.issubset(df.columns):
        # Create a unique identifier for disambiguation
        df["_unique_id"] = (
            df["Study"].astype(str)
            + df["Group"].astype(str)
            + df["Individual"].astype(str)
            + df["Date"].astype(str)
        )
        # Find duplicates
        disambiguated = df.drop_duplicates(subset="_unique_id")
        ambiguous = df[df.duplicated(subset="_unique_id", keep=False)]
        return disambiguated.drop(columns=["_unique_id"]), ambiguous.drop(columns=["_unique_id"])
    else:
        st.warning("Dataset must contain 'Study', 'Group', 'Individual', and 'Date' columns.")
        return df, pd.DataFrame()  # Default to the full dataset as ambiguous
        

# Disambiguated Page
def disambiguated_page():
    st.title("Disambiguated Dataset")
    st.write("View rows that have unique combinations of Study, Group, Individual, and Date.")

    if "scans_df" in st.session_state:
        scans_df = st.session_state.scans_df.copy()
        disambiguated, _ = check_disambiguation(scans_df)

        st.write("### Disambiguated Rows")
        st.dataframe(disambiguated, use_container_width=True)

        st.write("### Save Results")
        csv = disambiguated.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Disambiguated CSV",
            data=csv,
            file_name="disambiguated_scans.csv",
            mime="text/csv",
        )
    else:
        st.warning("No dataset loaded. Please use the Pull Dataset page first.")

# Ambiguous Page
def ambiguous_page():
    st.title("Ambiguous Dataset")
    st.write("Edit rows that do not have unique combinations of Study, Group, Individual, and Date.")

    if "scans_df" in st.session_state:
        scans_df = st.session_state.scans_df.copy()
        _, ambiguous = check_disambiguation(scans_df)

        st.write("### Ambiguous Rows")
        if ambiguous.empty:
            st.success("No ambiguous rows found!")
        else:
            editable_df = st.data_editor(ambiguous, use_container_width=True)

            if st.button("Save Changes to Ambiguous Rows"):
                # Save the changes back to session state
                st.session_state.scans_df.update(editable_df)
                st.success("Changes saved!")

            st.write("### Save Results")
            csv = editable_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Ambiguous CSV",
                data=csv,
                file_name="ambiguous_scans.csv",
                mime="text/csv",
            )
    else:
        st.warning("No dataset loaded. Please use the Pull Dataset page first.")


if __name__ == "__main__":
    main()
