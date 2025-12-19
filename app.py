import streamlit as st
import time


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

with st.expander(
    "Step 1: Reading repository",
    expanded=st.session_state.step1_complete
    or (bool(repo_url) and not st.session_state.step1_complete),
):
    if repo_url:
        st.write(f"Reading repository: {repo_url}")
        if st.button("Start reading", key="step1_btn"):
            with st.spinner("Reading repository..."):
                time.sleep(1)
                # Nested folder structure: dict for folders, list for files, None for single files
                fake_files = {
                    "src/": {
                        "main.py": None,
                        "utils.py": None,
                        "config.py": None,
                        "services/": {
                            "api.py": None,
                            "db.py": None,
                            "auth/": {
                                "login.py": None,
                                "token.py": None,
                            },
                        },
                    },
                    "tests/": {
                        "test_main.py": None,
                        "test_utils.py": None,
                        "integration/": {
                            "test_api.py": None,
                        },
                    },
                    "docs/": {
                        "README.md": None,
                        "API.md": None,
                    },
                    "app.py": None,
                    "requirements.txt": None,
                }
                st.session_state.repository_files = fake_files
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
                time.sleep(1)
                fake_matches = {
                    "Database": ["src/config.py", "src/utils.py"],
                    "API Handler": ["src/main.py", "app.py"],
                    "Test Suite": ["tests/test_main.py", "tests/test_utils.py"],
                    "Documentation": ["docs/README.md", "docs/API.md"],
                }
                st.session_state.component_matches = fake_matches
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
                time.sleep(1)
                api_result = {
                    "repository": repo_url,
                    "components": [
                        {
                            "name": "Database",
                            "files": ["src/config.py", "src/utils.py"],
                            "dependencies": ["API Handler"],
                        },
                        {
                            "name": "API Handler",
                            "files": ["src/main.py", "app.py"],
                            "dependencies": ["Database", "Test Suite"],
                        },
                        {
                            "name": "Test Suite",
                            "files": ["tests/test_main.py", "tests/test_utils.py"],
                            "dependencies": ["API Handler"],
                        },
                        {
                            "name": "Documentation",
                            "files": ["docs/README.md", "docs/API.md"],
                            "dependencies": [],
                        },
                    ],
                    "total_files": 8,
                    "total_components": 4,
                }
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
                time.sleep(1)
                html_graph = """
                <!DOCTYPE html>
                <html>
                <head>
                </head>
                <body>
                    MY GRAPH HERE
                </body>
                </html>
                """
                st.session_state.html_graph = html_graph
                st.session_state.step4_complete = True
                st.rerun()
    else:
        st.info("Complete Step 3 first.")

    if st.session_state.step4_complete and "html_graph" in st.session_state:
        st.success("Graph generated successfully!")
        st.components.v1.html(st.session_state.html_graph, height=600)
