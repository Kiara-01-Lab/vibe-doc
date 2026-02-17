#!/usr/bin/env python3
"""
AutoDoc - Self-Documenting Repos
Your project documents itself every time you push.

Copyright (c) 2026 Kiara Inc. | MIT License
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

import anthropic

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_DIR = os.environ.get("AUTODOC_OUTPUT_DIR", "docs/autodoc")
LANGUAGE = os.environ.get("AUTODOC_LANGUAGE", "en")
INCLUDE_API = os.environ.get("AUTODOC_INCLUDE_API", "true") == "true"
INCLUDE_ARCH = os.environ.get("AUTODOC_INCLUDE_ARCH", "true") == "true"
INCLUDE_ONBOARD = os.environ.get("AUTODOC_INCLUDE_ONBOARD", "true") == "true"
INCLUDE_DECISIONS = os.environ.get("AUTODOC_INCLUDE_DECISIONS", "true") == "true"
MAX_FILES = int(os.environ.get("AUTODOC_MAX_FILES", "50"))
FILE_EXTENSIONS = os.environ.get(
    "AUTODOC_FILE_EXTENSIONS", ".py,.ts,.tsx,.js,.jsx,.go,.rs,.java,.rb,.php"
).split(",")

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096

# ---------------------------------------------------------------------------
# Repo Scanner
# ---------------------------------------------------------------------------


def get_repo_root() -> Path:
    """Find the git repository root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: Not a git repository.")
        sys.exit(1)
    return Path(result.stdout.strip())


def scan_source_files(repo_root: Path) -> list[dict]:
    """Scan repo for source files, return list of {path, content, size}."""
    files = []
    skip_dirs = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", ".autodoc", "docs/autodoc",
        ".tox", ".mypy_cache", ".pytest_cache", "vendor",
    }

    for root, dirs, filenames in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in filenames:
            if not any(fname.endswith(ext) for ext in FILE_EXTENSIONS):
                continue
            fpath = Path(root) / fname
            rel_path = fpath.relative_to(repo_root)
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if len(content) > 50_000:
                    content = content[:50_000] + "\n... [truncated]"
                files.append({
                    "path": str(rel_path),
                    "content": content,
                    "size": fpath.stat().st_size,
                })
            except Exception as e:
                print(f"  Skipping {rel_path}: {e}")

            if len(files) >= MAX_FILES:
                return files
    return files


def scan_config_files(repo_root: Path) -> list[dict]:
    """Scan for config/metadata files that help understand the project."""
    config_names = [
        "package.json", "pyproject.toml", "setup.py", "setup.cfg",
        "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
        "Makefile", "Dockerfile", "docker-compose.yml",
        "README.md", "README.rst", ".env.example",
    ]
    configs = []
    for name in config_names:
        fpath = repo_root / name
        if fpath.exists():
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if len(content) > 10_000:
                    content = content[:10_000] + "\n... [truncated]"
                configs.append({"path": name, "content": content})
            except Exception:
                pass
    return configs


def get_git_log(repo_root: Path, max_commits: int = 50) -> str:
    """Get recent git history with commit messages."""
    result = subprocess.run(
        [
            "git", "log",
            f"--max-count={max_commits}",
            "--pretty=format:%h | %ad | %s",
            "--date=short",
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    return result.stdout if result.returncode == 0 else ""


def get_directory_tree(repo_root: Path, max_depth: int = 3) -> str:
    """Generate a directory tree string."""
    skip_dirs = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        "dist", "build", ".next",
    }
    lines = []

    def _walk(path: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        dirs = [e for e in entries if e.is_dir() and e.name not in skip_dirs]
        files = [e for e in entries if e.is_file()]
        items = dirs + files
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{item.name}")
            if item.is_dir():
                extension = "    " if is_last else "│   "
                _walk(item, prefix + extension, depth + 1)

    lines.append(repo_root.name + "/")
    _walk(repo_root, "", 1)
    return "\n".join(lines[:200])  # cap output


# ---------------------------------------------------------------------------
# Claude API
# ---------------------------------------------------------------------------

client = anthropic.Anthropic()


def call_claude(system_prompt: str, user_prompt: str) -> str:
    """Call Claude API and return text response."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
    except Exception as e:
        print(f"  API error: {e}")
        return f"*Documentation generation failed: {e}*"


# ---------------------------------------------------------------------------
# Document Generators
# ---------------------------------------------------------------------------

LANG_INSTRUCTION = {
    "en": "Write all documentation in English.",
    "ja": "Write all documentation in Japanese (日本語).",
    "both": (
        "Write documentation in BOTH English and Japanese. "
        "Use English first, then add a Japanese section (日本語版) below with "
        "a horizontal rule separator."
    ),
}


def generate_architecture(
    tree: str, configs: list[dict], sources: list[dict]
) -> str:
    """Generate ARCHITECTURE.md"""
    lang = LANG_INSTRUCTION.get(LANGUAGE, LANG_INSTRUCTION["en"])

    system = f"""You are a senior software architect writing clear documentation.
{lang}
Write in Markdown. Be concise but thorough. Use diagrams (Mermaid syntax) where helpful.
Target audience: a new developer joining the project with no context."""

    source_summary = "\n\n".join(
        f"### {s['path']}\n```\n{s['content'][:3000]}\n```"
        for s in sources[:20]
    )
    config_summary = "\n\n".join(
        f"### {c['path']}\n```\n{c['content']}\n```" for c in configs
    )

    user = f"""Analyze this codebase and generate an ARCHITECTURE.md document.

## Directory Structure
```
{tree}
```

## Config Files
{config_summary}

## Source Files (samples)
{source_summary}

## Required Sections
1. **Project Overview** - What this project does (1-2 sentences a non-technical person can understand)
2. **Tech Stack** - Languages, frameworks, key dependencies (table format)
3. **Architecture Overview** - High-level system design with Mermaid diagram
4. **Directory Structure** - What each top-level directory contains
5. **Key Components** - The most important files/modules and what they do
6. **Data Flow** - How data moves through the system
7. **Configuration** - Key config files and environment variables
"""
    return call_claude(system, user)


def generate_api_docs(sources: list[dict], configs: list[dict]) -> str:
    """Generate API.md"""
    lang = LANG_INSTRUCTION.get(LANGUAGE, LANG_INSTRUCTION["en"])

    system = f"""You are a technical writer creating API documentation.
{lang}
Write in Markdown. Include code examples for every endpoint/function.
Target audience: a developer who wants to integrate with or use this project."""

    source_text = "\n\n".join(
        f"### {s['path']}\n```\n{s['content'][:4000]}\n```"
        for s in sources[:30]
    )
    config_text = "\n\n".join(
        f"### {c['path']}\n```\n{c['content']}\n```" for c in configs
    )

    user = f"""Analyze these source files and generate API documentation.

## Config Files
{config_text}

## Source Files
{source_text}

## Required Sections
1. **API Overview** - What this API/library does
2. **Installation / Setup** - How to install and configure
3. **Authentication** (if applicable)
4. **Endpoints / Public Functions** - For each:
   - Method signature or HTTP method + path
   - Parameters (table: name, type, required, description)
   - Response format
   - Code example (request + response)
5. **Error Handling** - Common errors and how to handle them
6. **Rate Limits / Constraints** (if applicable)

If this is a library (not a web API), document the public interface:
exported functions, classes, and their methods with usage examples.
If no clear API is found, document the main entry points and public interfaces.
"""
    return call_claude(system, user)


def generate_onboarding(
    tree: str, configs: list[dict], sources: list[dict]
) -> str:
    """Generate ONBOARDING.md"""
    lang = LANG_INSTRUCTION.get(LANGUAGE, LANG_INSTRUCTION["en"])

    system = f"""You are writing an onboarding guide for new developers.
{lang}
Write in Markdown. Be extremely friendly and assume zero context.
Use numbered steps. Include exact commands to copy-paste.
Target audience: someone who just cloned this repo and has never seen it before."""

    config_text = "\n\n".join(
        f"### {c['path']}\n```\n{c['content']}\n```" for c in configs
    )
    source_paths = "\n".join(f"- {s['path']}" for s in sources)

    user = f"""Create an onboarding guide for this project.

## Directory Structure
```
{tree}
```

## Config Files
{config_text}

## Source Files Present
{source_paths}

## Required Sections
1. **Welcome** - 1 sentence: what this project does
2. **Prerequisites** - What you need installed (with version numbers if detectable)
3. **Quick Start** - Numbered steps from `git clone` to running the project
4. **Project Structure** - Brief tour of important directories/files
5. **Common Tasks** - How to:
   - Run the project locally
   - Run tests
   - Add a new feature
   - Deploy (if applicable)
6. **Troubleshooting** - Common issues and fixes
7. **Where to Get Help** - Links, contacts, channels
"""
    return call_claude(system, user)


def generate_decisions(git_log: str, configs: list[dict], sources: list[dict]) -> str:
    """Generate DECISIONS.md from git history."""
    lang = LANG_INSTRUCTION.get(LANGUAGE, LANG_INSTRUCTION["en"])

    system = f"""You are a software historian reconstructing project decisions from git history.
{lang}
Write in Markdown. Use a table format for the decision log.
Be factual — only infer decisions that are clearly supported by the evidence."""

    config_text = "\n\n".join(
        f"### {c['path']}\n```\n{c['content'][:2000]}\n```" for c in configs
    )

    user = f"""Analyze this git history and project files to reconstruct key decisions.

## Git Log (recent commits)
```
{git_log}
```

## Config Files
{config_text}

## Required Output
Generate a DECISIONS.md with:

1. **Decision Log** - Table with columns:
   | Date | Decision | Reasoning (inferred) | Evidence |
   
   Include decisions about:
   - Technology choices (why this language/framework?)
   - Architecture patterns (why this structure?)
   - Dependency additions (why this library?)
   - Major refactors or migrations
   - Configuration changes

2. **Technology Choices Summary** - Why the current stack was likely chosen

3. **Open Questions** - Things that are unclear from the history and should be documented

Only include decisions you can reasonably infer. Mark uncertain inferences with ⚠️.
"""
    return call_claude(system, user)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("  AutoDoc - Self-Documenting Repos")
    print("  Your project documents itself every time you push.")
    print("=" * 60)

    repo_root = get_repo_root()
    output_path = repo_root / OUTPUT_DIR
    output_path.mkdir(parents=True, exist_ok=True)

    # Scan
    print("\n📂 Scanning repository...")
    tree = get_directory_tree(repo_root)
    configs = scan_config_files(repo_root)
    sources = scan_source_files(repo_root)
    git_log = get_git_log(repo_root)

    print(f"  Found {len(sources)} source files, {len(configs)} config files")
    print(f"  Git history: {len(git_log.splitlines())} recent commits")

    files_generated = []

    # Generate docs
    if INCLUDE_ARCH:
        print("\n🏗️  Generating ARCHITECTURE.md ...")
        arch = generate_architecture(tree, configs, sources)
        (output_path / "ARCHITECTURE.md").write_text(arch, encoding="utf-8")
        files_generated.append("ARCHITECTURE.md")
        print("  ✅ Done")

    if INCLUDE_API:
        print("\n📡 Generating API.md ...")
        api = generate_api_docs(sources, configs)
        (output_path / "API.md").write_text(api, encoding="utf-8")
        files_generated.append("API.md")
        print("  ✅ Done")

    if INCLUDE_ONBOARD:
        print("\n👋 Generating ONBOARDING.md ...")
        onboard = generate_onboarding(tree, configs, sources)
        (output_path / "ONBOARDING.md").write_text(onboard, encoding="utf-8")
        files_generated.append("ONBOARDING.md")
        print("  ✅ Done")

    if INCLUDE_DECISIONS:
        print("\n🧠 Generating DECISIONS.md ...")
        decisions = generate_decisions(git_log, configs, sources)
        (output_path / "DECISIONS.md").write_text(decisions, encoding="utf-8")
        files_generated.append("DECISIONS.md")
        print("  ✅ Done")

    # GitHub Actions outputs
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"docs_generated={','.join(files_generated)}\n")
            f.write(f"files_analyzed={len(sources)}\n")

    print(f"\n🎉 Generated {len(files_generated)} docs in {OUTPUT_DIR}/")
    print(f"   Files: {', '.join(files_generated)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
