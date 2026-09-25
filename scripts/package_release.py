"""Package source and required assets, never local notes or credentials."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {"README.md", ".gitignore", "package.json", "package-lock.json",
              "index.html", "jsconfig.json", "vite.config.js"}
DIRS = {"src", "public", "tests", "scripts", "server", "database", "compute_wi"}
EXCLUDED = {"__pycache__", "node_modules", ".venv", "uploads", "output", "data"}


def included(path):
    relative = path.relative_to(ROOT)
    if len(relative.parts) == 1:
        return relative.name in ROOT_FILES
    if relative.parts[0] not in DIRS or any(p in EXCLUDED or p.startswith("cmake-build") for p in relative.parts):
        return False
    if relative.parts[:2] == ("server", "config"):
        return relative.name == "app_config.example.json"
    return path.suffix.lower() in {".py", ".ps1", ".js", ".mjs", ".vue", ".json", ".css",
        ".scss", ".sass", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".ico", ".woff", ".woff2",
        ".ttf", ".otf", ".glb", ".gltf", ".bin", ".csv", ".xls", ".cpp", ".h", ".txt"}


def main():
    destination = ROOT / "release" / "rockburst-platform.zip"
    destination.parent.mkdir(exist_ok=True)
    candidates = [ROOT / name for name in ROOT_FILES]
    for directory in DIRS:
        candidates.extend((ROOT / directory).rglob("*"))
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in sorted(candidates):
            if path.is_file() and not path.is_symlink() and included(path):
                archive.write(path, path.relative_to(ROOT).as_posix())
    print(destination)


if __name__ == "__main__":
    main()
