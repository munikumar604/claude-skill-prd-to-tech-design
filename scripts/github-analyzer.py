#!/usr/bin/env python3
"""
github-analyzer.py — Analyze GitHub repository for architecture context

Usage:
    python github-analyzer.py --repo "https://github.com/org/repo" --branch main --output ./github-analysis.json
    python github-analyzer.py --repo "org/repo" --commit abc123 --output ./github-analysis.json

Environment:
    GITHUB_TOKEN (optional, for private repos)
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install: pip install requests")
    sys.exit(1)

GITHUB_API_BASE = "https://api.github.com"


def parse_repo_url(repo_input: str) -> tuple:
    repo_input = repo_input.replace("https://github.com/", "").replace("http://github.com/", "")
    repo_input = repo_input.replace("github.com/", "")
    repo_input = repo_input.rstrip("/").replace(".git", "")
    parts = repo_input.split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    raise ValueError(f"Invalid repo format: {repo_input}")


def fetch_repo_info(owner: str, repo: str, token: str = None) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    response = requests.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}", headers=headers)
    response.raise_for_status()
    return response.json()


def clone_repo(owner: str, repo: str, branch: str = None, commit: str = None, token: str = None) -> str:
    temp_dir = tempfile.mkdtemp(prefix="github-analyzer-")
    auth_prefix = ""
    if token:
        auth_prefix = f"https://{token}@"
    url = f"{auth_prefix}github.com/{owner}/{repo}.git"
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd.extend(["--branch", branch])
    cmd.extend([url, temp_dir])
    print(f"Cloning {owner}/{repo}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: Git clone failed: {result.stderr}")
        sys.exit(1)
    if commit:
        subprocess.run(["git", "fetch", "--depth=1", "origin", commit], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "checkout", commit], cwd=temp_dir, capture_output=True)
    return temp_dir


def detect_tech_stack(repo_path: str) -> dict:
    stack = {"language": None, "framework": None, "database": None, "orm": None, 
             "queue": None, "deployment": None, "testing": None, "package_manager": None}
    path = Path(repo_path)

    if (path / "package.json").exists():
        stack["package_manager"] = "npm/yarn/pnpm"
        try:
            with open(path / "package.json") as f:
                pkg = json.load(f)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps: stack["framework"] = "Next.js"
            elif "react" in deps: stack["framework"] = "React"
            elif "vue" in deps: stack["framework"] = "Vue"
            elif "express" in deps: stack["framework"] = "Express"
            elif "fastify" in deps: stack["framework"] = "Fastify"
            elif "nest" in deps: stack["framework"] = "NestJS"
            if "typescript" in deps: stack["language"] = "TypeScript"
            else: stack["language"] = "JavaScript"
            if "prisma" in deps: stack["orm"] = "Prisma"
            elif "typeorm" in deps: stack["orm"] = "TypeORM"
            elif "sequelize" in deps: stack["orm"] = "Sequelize"
            elif "mongoose" in deps: stack["orm"] = "Mongoose"
            if "bullmq" in deps or "bull" in deps: stack["queue"] = "BullMQ"
            if "jest" in deps: stack["testing"] = "Jest"
            elif "vitest" in deps: stack["testing"] = "Vitest"
            elif "mocha" in deps: stack["testing"] = "Mocha"
            if (path / "vercel.json").exists(): stack["deployment"] = "Vercel"
        except Exception as e:
            print(f"Warning: Could not parse package.json: {e}")
    elif (path / "go.mod").exists():
        stack["language"] = "Go"
        stack["package_manager"] = "Go Modules"
        if (path / "Dockerfile").exists(): stack["deployment"] = "Docker"
    elif (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
        stack["language"] = "Python"
        stack["package_manager"] = "pip/poetry"
        if any("django" in f.name for f in path.iterdir()): stack["framework"] = "Django"
        elif any("fastapi" in f.name for f in path.iterdir()): stack["framework"] = "FastAPI"
        elif any("flask" in f.name for f in path.iterdir()): stack["framework"] = "Flask"
    elif (path / "Cargo.toml").exists():
        stack["language"] = "Rust"
        stack["package_manager"] = "Cargo"

    if (path / "prisma" / "schema.prisma").exists() or any(f.suffix == ".prisma" for f in path.rglob("*.prisma")):
        stack["database"] = "PostgreSQL (inferred from Prisma)"
    elif (path / "docker-compose.yml").exists():
        try:
            with open(path / "docker-compose.yml") as f:
                content = f.read().lower()
                if "postgres" in content: stack["database"] = "PostgreSQL"
                elif "mysql" in content: stack["database"] = "MySQL"
                elif "mongodb" in content: stack["database"] = "MongoDB"
                elif "redis" in content and not stack["queue"]: stack["queue"] = "Redis"
        except: pass

    if (path / "Dockerfile").exists() and not stack["deployment"]: stack["deployment"] = "Docker"
    if (path / "kubernetes").exists() or (path / "k8s").exists(): stack["deployment"] = "Kubernetes"
    if (path / ".github" / "workflows").exists() and not stack["deployment"]: stack["deployment"] = "GitHub Actions CI/CD"

    return {k: v for k, v in stack.items() if v}


def analyze_directory_structure(repo_path: str) -> dict:
    path = Path(repo_path)
    structure = {"root_files": [f.name for f in path.iterdir() if f.is_file()], "key_directories": [], "depth": 0}
    key_patterns = ["src", "app", "lib", "components", "pages", "api", "services", "domain", 
                    "infrastructure", "application", "models", "controllers", "routes", 
                    "middleware", "tests", "test", "__tests__", "spec", "docs", "scripts", "config", "migrations"]
    for pattern in key_patterns:
        matches = list(path.rglob(pattern))
        for match in matches:
            if match.is_dir() and match.parent == path:
                structure["key_directories"].append(str(match.relative_to(path)))
    structure["key_directories"] = list(set(structure["key_directories"]))
    max_depth = 0
    for item in path.rglob("*"):
        if item.is_file():
            depth = len(item.relative_to(path).parts)
            max_depth = max(max_depth, depth)
    structure["depth"] = max_depth
    return structure


def find_integration_points(repo_path: str, prd_keywords: list = None) -> list:
    path = Path(repo_path)
    integration_points = []
    keywords = prd_keywords or ["export", "import", "auth", "user", "payment", "notification", "webhook"]
    for keyword in keywords:
        for ext in [".ts", ".js", ".tsx", ".jsx", ".py", ".go", ".rs"]:
            matches = list(path.rglob(f"*{keyword}*{ext}"))
            for match in matches[:3]:
                integration_points.append({"keyword": keyword, "file": str(match.relative_to(path)), "type": "existing_file"})
    api_dirs = list(path.rglob("api")) + list(path.rglob("routes"))
    for api_dir in api_dirs[:2]:
        if api_dir.is_dir():
            routes = [f.name for f in api_dir.iterdir() if f.is_file()][:5]
            integration_points.append({"keyword": "api_routes", "directory": str(api_dir.relative_to(path)), 
                                       "routes": routes, "type": "api_directory"})
    return integration_points


def find_constraints(repo_path: str) -> list:
    constraints = []
    path = Path(repo_path)
    if any((path / f).exists() for f in [".eslintrc", ".eslintrc.js", "eslint.config.js"]):
        constraints.append("ESLint configured — follow existing lint rules")
    if (path / "tsconfig.json").exists():
        constraints.append("TypeScript project — strict mode may be enabled")
    if (path / ".prettierrc").exists():
        constraints.append("Prettier configured — follow formatting rules")
    if any((path / f).exists() for f in ["jest.config.js", "vitest.config.ts"]):
        constraints.append("Testing framework configured — all new code must have tests")
    if (path / ".github" / "workflows").exists():
        constraints.append("CI/CD via GitHub Actions — all PRs must pass checks")
    if (path / ".gitmessage").exists() or (path / "CONTRIBUTING.md").exists():
        constraints.append("Follow commit message conventions")
    return constraints


def main():
    parser = argparse.ArgumentParser(description="Analyze GitHub repository")
    parser.add_argument("--repo", required=True, help="Repository URL or owner/repo")
    parser.add_argument("--branch", default="main", help="Branch to analyze")
    parser.add_argument("--commit", help="Specific commit to checkout")
    parser.add_argument("--output", "-o", default="github-analysis.json", help="Output JSON file")
    parser.add_argument("--keywords", nargs="+", help="PRD keywords to search for integration points")
    parser.add_argument("--keep-clone", action="store_true", help="Keep cloned repo (for debugging)")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    owner, repo = parse_repo_url(args.repo)
    print(f"Analyzing {owner}/{repo} @ {args.branch}...")

    try:
        repo_info = fetch_repo_info(owner, repo, token)
        print(f"  Repo: {repo_info.get('full_name')}")
        print(f"  Default branch: {repo_info.get('default_branch')}")
        print(f"  Language: {repo_info.get('language')}")
        print(f"  Stars: {repo_info.get('stargazers_count')}")
    except Exception as e:
        print(f"WARNING: Could not fetch repo info: {e}")
        repo_info = {}

    try:
        repo_path = clone_repo(owner, repo, args.branch, args.commit, token)
        print(f"  Cloned to: {repo_path}")
    except Exception as e:
        print(f"ERROR: Could not clone repo: {e}")
        sys.exit(1)

    tech_stack = detect_tech_stack(repo_path)
    structure = analyze_directory_structure(repo_path)
    integration_points = find_integration_points(repo_path, args.keywords)
    constraints = find_constraints(repo_path)

    output = {
        "repository": {
            "owner": owner, "repo": repo,
            "url": f"https://github.com/{owner}/{repo}",
            "branch": args.branch,
            "commit": args.commit or repo_info.get("default_branch", args.branch),
            "cloned_at": datetime.now().isoformat(),
            "clone_path": repo_path if args.keep_clone else None
        },
        "repo_metadata": {
            "description": repo_info.get("description"),
            "language": repo_info.get("language"),
            "stars": repo_info.get("stargazers_count"),
            "forks": repo_info.get("forks_count"),
            "open_issues": repo_info.get("open_issues_count"),
            "license": repo_info.get("license", {}).get("name") if repo_info.get("license") else None
        },
        "tech_stack": tech_stack,
        "directory_structure": structure,
        "integration_points": integration_points,
        "constraints": constraints,
        "risk_assessment": {"breaking_changes": [], "performance_implications": [], "security_concerns": []}
    }

    if tech_stack.get("database") == "MongoDB" and not tech_stack.get("orm"):
        output["risk_assessment"]["security_concerns"].append("No ORM detected with MongoDB — ensure query sanitization")
    if not tech_stack.get("testing"):
        output["risk_assessment"]["performance_implications"].append("No testing framework detected — consider adding tests for new features")

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Analysis complete")
    print(f"   Tech stack: {', '.join([f'{k}={v}' for k, v in tech_stack.items()])}")
    print(f"   Integration points found: {len(integration_points)}")
    print(f"   Constraints: {len(constraints)}")
    print(f"   Output: {args.output}")

    if not args.keep_clone:
        import shutil
        shutil.rmtree(repo_path, ignore_errors=True)
        print(f"   Cleaned up clone directory")


if __name__ == "__main__":
    main()
