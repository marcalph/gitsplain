"""Tests for diagram generator."""

from unittest.mock import MagicMock, patch

from gitsplain.diagram import DiagramGenerator, GenerationState, get_diagram_generator


class TestGenerationState:
    """Tests for GenerationState dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        state = GenerationState()
        assert state.owner == ""
        assert state.repo == ""
        assert state.instructions == ""
        assert state.repo_info == {}
        assert state.static_analysis == {}
        assert state.component_mapping == {}
        assert state.graph_structure == {}
        assert state.graph_html == ""


class TestDiagramGenerator:
    """Tests for DiagramGenerator class."""

    def test_init_creates_state(self):
        """Test initialization creates empty state."""
        with (
            patch("gitsplain.diagram.GitHubClient"),
            patch("gitsplain.diagram.LLMClient"),
        ):
            generator = DiagramGenerator()
            assert isinstance(generator.state, GenerationState)

    def test_init_with_custom_client(self):
        """Test initialization with custom GitHub client."""
        mock_github = MagicMock()
        mock_llm = MagicMock()
        generator = DiagramGenerator(github_client=mock_github, llm_client=mock_llm)
        assert generator.github == mock_github
        assert generator.llm == mock_llm

    def test_phase0_repo_info(self):
        """Test phase0 fetches and stores repo info."""
        mock_github = MagicMock()
        mock_github.get_repo_data.return_value = {
            "default_branch": "main",
            "file_tree": "src/main.py\nsrc/utils.py",
            "readme": "# Test Repo",
        }
        mock_github.get_languages.return_value = {"Python": 1000}

        generator = DiagramGenerator(github_client=mock_github, llm_client=MagicMock())
        result = generator.phase0_repo_info("owner", "repo")

        assert generator.state.owner == "owner"
        assert generator.state.repo == "repo"
        assert result["default_branch"] == "main"
        assert result["file_tree"] == ["src/main.py", "src/utils.py"]
        assert result["readme"] == "# Test Repo"
        assert result["languages"] == {"Python": 1000}

    def test_phase0_static_analysis(self):
        """Test phase0 static analysis returns AST data."""
        with (
            patch("gitsplain.diagram.GitHubClient"),
            patch("gitsplain.diagram.LLMClient"),
        ):
            generator = DiagramGenerator()
            generator.state.repo_info = {"file_tree": [], "languages": {}}
            result = generator.phase0_static_analysis()

            assert "languages" in result
            assert "files_parsed" in result
            assert "symbols" in result
            assert generator.state.static_analysis == result

    def test_phase1_component_mapping(self):
        """Test phase1 returns component mapping."""
        with (
            patch("gitsplain.diagram.GitHubClient"),
            patch("gitsplain.diagram.LLMClient") as mock_llm,
        ):
            mock_llm.return_value.call_api_structured.return_value = MagicMock(
                mappings=[]
            )
            generator = DiagramGenerator()
            generator.state.repo_info = {"file_tree": [], "readme": ""}
            generator.state.static_analysis = {"symbols": []}
            result = generator.phase1_component_mapping()

            assert isinstance(result, dict)
            assert generator.state.component_mapping == result

    def test_phase2_graph_structure(self):
        """Test phase2 returns graph structure."""
        with (
            patch("gitsplain.diagram.GitHubClient"),
            patch("gitsplain.diagram.LLMClient"),
        ):
            generator = DiagramGenerator()
            result = generator.phase2_graph_structure()

            assert "nodes" in result
            assert "edges" in result
            assert "metadata" in result
            assert generator.state.graph_structure == result

    def test_generate_html(self):
        """Test HTML generation with Mermaid."""
        with (
            patch("gitsplain.diagram.GitHubClient"),
            patch("gitsplain.diagram.LLMClient"),
        ):
            generator = DiagramGenerator()
            generator.state.graph_structure = {
                "nodes": [{"id": "test", "label": "Test", "color": "#000"}],
                "edges": [{"from": "test", "to": "test", "label": "self"}],
            }

            html = generator.generate_html()

            assert "mermaid" in html
            assert "flowchart TD" in html
            assert 'test["Test"]' in html
            assert generator.state.graph_html == html

    def test_run_all(self):
        """Test run_all executes all phases."""
        mock_github = MagicMock()
        mock_github.get_repo_data.return_value = {
            "default_branch": "main",
            "file_tree": "src/main.py",
            "readme": "# Test",
        }
        mock_github.get_languages.return_value = {"Python": 100}
        mock_github.get_files_content.return_value = {}

        mock_llm = MagicMock()
        mock_llm.call_api_structured.return_value = MagicMock(mappings=[])

        generator = DiagramGenerator(github_client=mock_github, llm_client=mock_llm)
        state = generator.run_all("owner", "repo", "custom instructions")

        assert state.owner == "owner"
        assert state.repo == "repo"
        assert state.instructions == "custom instructions"
        assert state.repo_info != {}
        assert state.static_analysis != {}
        assert state.component_mapping != {}
        assert state.graph_structure != {}
        assert state.graph_html != ""


class TestGetDiagramGenerator:
    """Tests for factory function."""

    def test_returns_generator(self):
        """Test factory returns DiagramGenerator instance."""
        with (
            patch("gitsplain.diagram.GitHubClient"),
            patch("gitsplain.diagram.LLMClient"),
        ):
            generator = get_diagram_generator()
            assert isinstance(generator, DiagramGenerator)
