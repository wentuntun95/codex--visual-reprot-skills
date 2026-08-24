#!/usr/bin/env python3
"""Cross-platform project housekeeping for ppt-xiaozi."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_DIRS = (
    ".ppt-agent/slides",
    "draft/archive",
    "final/pages",
    "inputs",
    "style",
    "work",
    "previews",
    "generated-assets/rejected",
)
CLEANUP_DIRS = ("work", "previews", "generated-assets")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def project_root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pptx_slide_count(path: Path) -> int:
    with zipfile.ZipFile(path) as package:
        names = package.namelist()
    return sum(
        name.startswith("ppt/slides/slide") and name.endswith(".xml")
        for name in names
    )


def init_project(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for item in PROJECT_DIRS:
        (root / item).mkdir(parents=True, exist_ok=True)

    state_path = root / ".ppt-agent/project.json"
    if state_path.exists():
        state = read_json(state_path)
        state["updated_at"] = now_iso()
    else:
        state = {
            "status": "active",
            "phase": "story",
            "current_slide": None,
            "draft": "draft/structure-draft.pptx",
            "updated_at": now_iso(),
        }
    write_json(state_path, state)

    story = root / ".ppt-agent/story-map.md"
    if not story.exists():
        story.write_text("# Story Map\n\n- Audience:\n- Objective:\n- Core message:\n\n## Sections\n\n", encoding="utf-8")
    style = root / ".ppt-agent/style.json"
    if not style.exists():
        write_json(style, {})
    print(f"Initialized: {root}")


def artifact_entry(path: Path, root: Path) -> dict:
    entry = {
        "path": relative(path, root),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    if path.suffix.lower() == ".pptx":
        entry["slides"] = pptx_slide_count(path)
    return entry


def finalize_project(root: Path) -> None:
    init_project(root)
    candidates = sorted((root / "final").glob("*.pptx"))
    candidates += sorted((root / "final/pages").glob("*.pptx"))
    draft = root / "draft/structure-draft.pptx"
    if draft.exists():
        candidates.append(draft)
    if not candidates:
        raise RuntimeError("No PPTX found in final/, final/pages/, or draft/structure-draft.pptx")

    artifacts = [artifact_entry(path, root) for path in dict.fromkeys(candidates)]
    manifest = {
        "status": "finalized",
        "finalized_at": now_iso(),
        "artifacts": artifacts,
    }
    write_json(root / ".ppt-agent/final-manifest.json", manifest)

    state_path = root / ".ppt-agent/project.json"
    state = read_json(state_path)
    state.update({"status": "finalized", "phase": "final", "updated_at": now_iso()})
    write_json(state_path, state)
    print(f"Finalized: {root} ({len(artifacts)} artifacts)")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def cleanup_ready(root: Path, grace_days: int) -> tuple[bool, str]:
    manifest_path = root / ".ppt-agent/final-manifest.json"
    if not manifest_path.exists():
        return False, "not finalized"
    manifest = read_json(manifest_path)
    finalized_at = parse_time(manifest["finalized_at"])
    if datetime.now(timezone.utc) < finalized_at.astimezone(timezone.utc) + timedelta(days=grace_days):
        return False, f"inside {grace_days}-day grace period"
    return True, "ready"


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def cleanup_project(root: Path, grace_days: int, execute: bool) -> None:
    ready, reason = cleanup_ready(root, grace_days)
    if not ready:
        print(f"Skipped: {root} ({reason})")
        return

    rows = []
    for name in CLEANUP_DIRS:
        target = (root / name).resolve()
        if target.parent != root:
            raise RuntimeError(f"Unsafe cleanup target: {target}")
        if target.exists():
            rows.append((target, directory_size(target)))

    if not rows:
        print(f"Nothing to clean: {root}")
        return
    total = sum(size for _, size in rows)
    for target, size in rows:
        print(f"{'Remove' if execute else 'Would remove'}: {target} ({size} bytes)")
    print(f"Total: {total} bytes")
    if execute:
        for target, _ in rows:
            shutil.rmtree(target)


def scan_projects(root: Path, grace_days: int, execute: bool) -> None:
    manifests = sorted(root.rglob(".ppt-agent/final-manifest.json"))
    if not manifests:
        print(f"No finalized projects found under: {root}")
        return
    for manifest in manifests:
        project = manifest.parent.parent
        try:
            cleanup_project(project, grace_days, execute)
        except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            print(f"Skipped: {project} ({exc})", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "finalize"):
        command = sub.add_parser(name)
        command.add_argument("project_root")
    for name in ("cleanup-report", "cleanup"):
        command = sub.add_parser(name)
        command.add_argument("project_root")
        command.add_argument("--grace-days", type=int, default=14)
    scan = sub.add_parser("scan")
    scan.add_argument("projects_root")
    scan.add_argument("--grace-days", type=int, default=14)
    scan.add_argument("--execute", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if getattr(args, "grace_days", 0) < 0:
        raise ValueError("--grace-days must be zero or greater")
    if args.command == "init":
        init_project(project_root(args.project_root))
    elif args.command == "finalize":
        finalize_project(project_root(args.project_root))
    elif args.command == "cleanup-report":
        cleanup_project(project_root(args.project_root), args.grace_days, False)
    elif args.command == "cleanup":
        cleanup_project(project_root(args.project_root), args.grace_days, True)
    elif args.command == "scan":
        scan_projects(project_root(args.projects_root), args.grace_days, args.execute)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
