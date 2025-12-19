import streamlit as st

from src.workflow_manager import get_workflow_manager


st.title("Gitsplain: visual diagram of a codebase")

repo_url = st.text_input(
    "Repository URL",
    placeholder="https://github.com/username/repository",
    help="Paste the URL of the repository you want to analyze",
)

if "step1_complete" not in st.session_state:
    st.session_state.step1_complete = False
if "step2_complete" not in st.session_state:
    st.session_state.step2_complete = False
if "step3_complete" not in st.session_state:
    st.session_state.step3_complete = False
if "step4_complete" not in st.session_state:
    st.session_state.step4_complete = False

# Initialize workflow manager
if "workflow_manager" not in st.session_state:
    st.session_state.workflow_manager = get_workflow_manager()

with st.expander(
    "Step 1: Reading repository",
    expanded=st.session_state.step1_complete
    or (bool(repo_url) and not st.session_state.step1_complete),
):
    if repo_url:
        st.write(f"Reading repository: {repo_url}")
        if st.button("Start reading", key="step1_btn"):
            with st.spinner("Reading repository..."):
                repository_files = st.session_state.workflow_manager.read_repository(
                    repo_url
                )
                st.session_state.repository_files = repository_files
                st.session_state.step1_complete = True
                st.rerun()

        if st.session_state.step1_complete and "repository_files" in st.session_state:
            st.success("Repository read successfully!")
            st.write("**Repository structure:**")

            def display_structure(structure, indent=0):
                """Recursively display nested folder structure"""
                prefix = "  " * indent
                for item, content in structure.items():
                    if content is None:
                        # It's a file
                        st.write(f"{prefix}📄 {item}")
                    elif isinstance(content, dict):
                        # It's a folder
                        st.write(f"{prefix}📁 {item}")
                        display_structure(content, indent + 1)

            display_structure(st.session_state.repository_files)
    else:
        st.info("Please enter a repository URL above to start.")

with st.expander(
    "Step 2: Component matching",
    expanded=bool(
        st.session_state.step2_complete
        or (st.session_state.step1_complete and not st.session_state.step2_complete)
    ),
):
    if st.session_state.step1_complete:
        st.write("Matching components...")
        if st.button("Start component matching", key="step2_btn"):
            with st.spinner("Matching components..."):
                component_matches = st.session_state.workflow_manager.match_components(
                    st.session_state.repository_files
                )
                st.session_state.component_matches = component_matches
                st.session_state.step2_complete = True
                st.rerun()

        if st.session_state.step2_complete and "component_matches" in st.session_state:
            st.success("Components matched successfully!")
            st.write("**Matched components:**")
            for component, files in st.session_state.component_matches.items():
                st.write(f"🔧 **{component}**")
                for file in files:
                    st.write(f"  └── {file}")
    else:
        st.info("Complete Step 1 first.")

with st.expander(
    "Step 3: JSON result",
    expanded=bool(
        st.session_state.step3_complete
        or (st.session_state.step2_complete and not st.session_state.step3_complete)
    ),
):
    if st.session_state.step2_complete:
        st.write("Building JSON graph...")
        if st.button("Build JSON graph", key="step3_btn"):
            with st.spinner("Building JSON graph..."):
                api_result = st.session_state.workflow_manager.build_json_graph(
                    st.session_state.repository_files,
                    st.session_state.component_matches,
                    repo_url,
                )
                st.session_state.api_result = api_result
                st.session_state.step3_complete = True
                st.rerun()
    else:
        st.info("Complete Step 2 first.")

    if st.session_state.step3_complete and "api_result" in st.session_state:
        st.success("JSON graph built successfully!")
        st.json(st.session_state.api_result)

with st.expander(
    "Step 4: HTML graph",
    expanded=bool(
        st.session_state.step4_complete
        or (st.session_state.step3_complete and not st.session_state.step4_complete)
    ),
):
    if st.session_state.step3_complete:
        st.write("Generating HTML graph...")
        if st.button("Generate graph", key="step4_btn"):
            with st.spinner("Generating graph..."):
                html_graph = st.session_state.workflow_manager.generate_html_graph(
                    st.session_state.api_result
                )
                st.session_state.html_graph = html_graph
                st.session_state.step4_complete = True
                st.rerun()
    else:
        st.info("Complete Step 3 first.")

    if st.session_state.step4_complete and "html_graph" in st.session_state:
        st.success("Graph generated successfully!")
        st.components.v1.html(st.session_state.html_graph, height=600)
