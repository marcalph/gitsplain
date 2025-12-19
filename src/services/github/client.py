import base64
import requests
from typing import Any, Dict, Optional, List
from urllib.parse import urlparse
from dataclasses import dataclass


@dataclass
class GitHubRepository:
    files: List[str]
    tree_structure: Dict[str, str]
    readMe: str


class GitHubFileTree:
    """Client pour récupérer et afficher l'arborescence d'un repo GitHub"""

    def __init__(self, github_token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

    def parse_github_url(self, url: str) -> tuple[str, str, Optional[str]]:
        """
        Parse une URL GitHub pour extraire owner, repo et branch
            input: URL du repository GitHub
            output: Tuple (owner, repo, branch)
        """

        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]

        if len(path_parts) < 2:
            raise ValueError(
                "URL GitHub invalide. Format attendu: https://github.com/owner/repo"
            )

        owner = path_parts[0]
        repo = path_parts[1]
        branch = None

        # Si l'URL contient /tree/branch
        if len(path_parts) >= 4 and path_parts[2] == "tree":
            branch = path_parts[3]

        return owner, repo, branch

    def get_default_branch(self, owner: str, repo: str) -> str:
        """Récupère la branche par défaut du repository"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["default_branch"]

    def get_tree(self, owner: str, repo: str, branch: str = None) -> Dict:
        """
        Récupère l'arbre complet du repository via l'API GitHub
        """
        if branch is None:
            branch = self.get_default_branch(owner, repo)

        # Récupère le SHA du commit de la branche
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}"
        response = requests.get(url, headers=self.headers, params={"recursive": "1"})
        response.raise_for_status()

        return response.json()

    def build_tree_structure(self, tree_data: Dict) -> Dict:
        """
        Construit une structure arborescente à partir des données de l'API
        """
        root = {}

        for item in tree_data.get("tree", []):
            path = item["path"]
            item_type = item["type"]

            parts = path.split("/")
            current = root

            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # Dernier élément
                    current[part] = {"type": item_type, "path": path}
                else:
                    # Dossier intermédiaire
                    if part not in current:
                        current[part] = {"type": "tree", "children": {}}
                    if "children" not in current[part]:
                        current[part]["children"] = {}
                    current = current[part]["children"]

        return root

    def generate_filetree(self, github_url: str, show_types: bool = False) -> Dict:
        """
        Génère et affiche l'arbre de fichiers à partir d'une URL GitHub

        Args:
            github_url: URL du repository GitHub
            show_types: Afficher les types (blob/tree)

        Returns:
            Structure arborescente du repository
        """
        print(f"📥 Récupération du repository: {github_url}\n")

        # Parse l'URL
        owner, repo, branch = self.parse_github_url(github_url)
        print(f"👤 Owner: {owner}")
        print(f"📦 Repo: {repo}")

        # Récupère l'arbre
        tree_data = self.get_tree(owner, repo, branch)
        branch_used = branch or self.get_default_branch(owner, repo)
        print(f"🌿 Branch: {branch_used}")
        print(f"📊 Total items: {len(tree_data.get('tree', []))}\n")

        # Construit la structure
        tree_structure = self.build_tree_structure(tree_data)

        return tree_structure

    def get_file_content_from_url(self, github_url: str, file_path: str) -> str:
        """
        Récupère le contenu d'un fichier à partir d'une URL GitHub
        """
        owner, repo, branch = self.parse_github_url(github_url)
        return self.get_file_content(owner, repo, file_path, branch)

    def get_file_content(
        self, owner: str, repo: str, file_path: str, branch: str = None
    ) -> str:
        """
        Récupère le contenu d'un fichier spécifique

        Args:
            owner: Propriétaire du repository
            repo: Nom du repository
            file_path: Chemin du fichier dans le repo (ex: "README.md", "src/main.py")
            branch: Branche (si None, utilise la branche par défaut)

        Returns:
            Contenu du fichier en texte
        """
        if branch is None:
            branch = self.get_default_branch(owner, repo)

        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
        response = requests.get(url, headers=self.headers, params={"ref": branch})
        response.raise_for_status()

        data = response.json()

        # Le contenu est encodé en base64
        content = base64.b64decode(data["content"]).decode("utf-8")

        return content

    def build_simple_tree_structure(self, tree_data) -> Dict[str, Any]:
        # Construire la structure simplifiée
        result: Dict[str, Any] = {}

        for item in tree_data.get("tree", []):
            path = item["path"]
            item_type = item["type"]

            parts = path.split("/")
            current = result

            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # Dernier élément
                    if item_type == "tree":
                        # C'est un dossier
                        folder_name = part + "/"
                        if folder_name not in current:
                            current[folder_name] = {}
                    else:
                        # C'est un fichier
                        current[part] = None
                else:
                    # Dossier intermédiaire
                    folder_name = part + "/"
                    if folder_name not in current:
                        current[folder_name] = {}
                    current = current[folder_name]

        return result

    def get_simple_tree_structure(self, github_url: str) -> GitHubRepository:
        """
        Récupère l'arbre de fichiers à partir d'une URL GitHub
        """
        owner, repo, branch = self.parse_github_url(github_url)
        branch = self.get_default_branch(owner, repo)
        tree_data = self.get_tree(owner, repo, branch)
        files = [_["path"] for _ in tree_data["tree"] if _["type"] == "blob"]
        tree_structure = self.build_simple_tree_structure(tree_data)
        readMe = self.get_file_content(owner, repo, "README.md", branch)

        return GitHubRepository(
            files=files, tree_structure=tree_structure, readMe=readMe
        )
