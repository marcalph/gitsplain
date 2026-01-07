import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from github import GithubException

from gitsplain.diagram import get_diagram_generator
from gitsplain.services.github import GitHubClient
from gitsplain.utils import parse_github_url

load_dotenv()


# Page configuration
st.set_page_config(
    page_title="Gitsplain",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "graph_html": None,
        "repo_info": None,
        "static_analysis": None,
        "component_mapping": None,
        "graph_structure": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()
st.title("Gitsplain")
st.markdown("Visualize any codebase in seconds.")
col1, col2 = st.columns([2, 3])

with col1:
    repo_input = st.text_input(
        "Repository",
        placeholder="owner/repo or https://github.com/owner/repo",
        help="Enter owner/repo or full GitHub URL",
    )

with col2:
    instructions = st.text_input(
        "Custom Instructions (optional)",
        placeholder="e.g., Focus on the API layer",
        help="Add custom instructions for diagram generation",
    )


owner = None
repo = None

if repo_input:
    try:
        owner, repo = parse_github_url(repo_input)
        st.caption(f"Repository: **{owner}/{repo}**")
    except GithubException as e:
        st.error(f"Invalid input: {e.data}")

# Generate button
if owner and repo:
    if st.button("Generate Diagram", type="primary"):
        github_client = GitHubClient()
        if not github_client.check_repository_exists(owner, repo):
            st.error(f"Repository **{owner}/{repo}** not found or is private.")
        else:
            with st.spinner("Generating architecture diagram..."):
                generator = get_diagram_generator()
                state = generator.run_all(owner, repo, instructions)
                st.session_state.graph_html = state.graph_html
                st.session_state.repo_info = state.repo_info
                st.session_state.static_analysis = state.static_analysis
                st.session_state.component_mapping = state.component_mapping
                st.session_state.graph_structure = state.graph_structure


# Tabs for graph and phase outputs
tab_graph, tab_repo_analysis, tab_mapping, tab_graph_struct = st.tabs(
    [
        "Graph",
        "Phase 0: repository analysis",
        "Phase 1: component mapping",
        "Phase 2: Graph representation",
    ]
)


with tab_graph:
    if st.session_state.graph_html:
        components.html(st.session_state.graph_html, height=600, scrolling=True)
    else:
        st.info("Enter a repository and click 'Generate Diagram' to visualize.")


with tab_repo_analysis:
    if st.session_state.repo_info:
        file_tree = "\n".join(st.session_state.repo_info.get("file_tree", []))
        readme = st.session_state.repo_info.get("readme", "")
        symbols = ""
        if st.session_state.static_analysis:
            symbol_list = st.session_state.static_analysis.get("symbols", [])
            symbols = "\n".join(str(s) for s in symbol_list)
        llm_input = (
            f"<filetree>\n{file_tree}\n</filetree>\n\n"
            f"<symbols>\n{symbols}\n</symbols>\n\n"
            f"<readme>\n{readme}\n</readme>"
        )
        st.code(llm_input, language=None)
    else:
        st.caption("No repository data yet.")

with tab_mapping:
    if st.session_state.repo_info and st.session_state.static_analysis:
        file_tree = "\n".join(st.session_state.repo_info.get("file_tree", []))
        readme = st.session_state.repo_info.get("readme", "")
        symbol_list = st.session_state.static_analysis.get("symbols", [])
        symbols = "\n".join(str(s) for s in symbol_list)
        llm_input = (
            f"<explanation>\n{readme}\n</explanation>\n\n"
            f"<file_tree>\n{file_tree}\n</file_tree>\n\n"
            f"<symbols>\n{symbols}\n</symbols>"
        )
        st.code(llm_input, language=None)
        if st.session_state.component_mapping:
            st.subheader("LLM Output")
            mappings = st.session_state.component_mapping.get("mappings", [])
            llm_output = "\n".join(str(m) for m in mappings)
            st.code(llm_output, language=None)
    else:
        st.caption("No component mapping data yet.")


with tab_graph_struct:
    if st.session_state.repo_info and st.session_state.component_mapping:
        readme = st.session_state.repo_info.get("readme", "")
        mappings = st.session_state.component_mapping.get("mappings", [])
        component_mapping_str = "\n".join(str(m) for m in mappings)
        llm_input = (
            f"<explanation>\n{readme}\n</explanation>\n\n"
            f"<component_mapping>\n{component_mapping_str}\n</component_mapping>"
        )
        st.code(llm_input, language=None)
        if st.session_state.graph_structure:
            st.subheader("LLM Output")
            nodes = st.session_state.graph_structure.get("nodes", [])
            edges = st.session_state.graph_structure.get("edges", [])
            nodes_str = "\n".join(str(n) for n in nodes)
            edges_str = "\n".join(str(e) for e in edges)
            llm_output = f"NODES:\n{nodes_str}\n\nEDGES:\n{edges_str}"
            st.code(llm_output, language=None)
    else:
        st.caption("No graph structure data yet.")
