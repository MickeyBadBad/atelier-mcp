"""Atelier CLI — interior design workflow without an MCP client.

For users who don't run Claude Desktop / Cursor / Codex / VS Code with
MCP. Every subcommand thin-wraps the same pure-Python modules the MCP
server tools call into, so behavior is identical.

Usage:
    atelier init <project_name> --type <project_type> [--root <path>] [--spaces a b c]
    atelier discover [--depth quick|standard|deep|adaptive] [--auto]
    atelier audit <scene_info_json> [--mode hero|exploration|construction] [--project <root>]
    atelier bom <project_root> [--format markdown|csv] [--out <path>]
    atelier moodboard <project_root> [--style <slug>] [--space <type>] [-n 4]
    atelier handbook [<chapter>] [--query <q>]
    atelier styles
    atelier --version
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional


def _cmd_version(args: argparse.Namespace) -> int:
    try:
        from importlib.metadata import version
        print(f"atelier {version('atelier-mcp')}")
    except Exception:
        print("atelier (version unknown)")
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    from ._project import (
        ProjectError, new_project_record, write_project, write_taste_profile,
    )

    root = Path(args.root or Path.cwd() / args.project_name).resolve()
    root.mkdir(parents=True, exist_ok=True)

    try:
        record = new_project_record(
            project_name=args.project_name,
            project_type=args.type,
            spaces=args.spaces or [],
            units=args.units,
        )
    except ProjectError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    write_project(root / "project.json", record)
    # Empty taste-profile placeholder
    write_taste_profile(root / "taste-profile.json", {
        "version": 1,
        "project": args.project_name,
        "depth": "",
    })
    print(f"created project at: {root}")
    print(f"  project.json + taste-profile.json written")
    print(f"  next: atelier discover  (run inside this project root)")
    return 0


def _cmd_discover(args: argparse.Namespace) -> int:
    from ._discovery import Depth, list_questions, score_answers

    try:
        depth = Depth(args.depth)
    except ValueError:
        print(f"unknown depth: {args.depth}", file=sys.stderr)
        return 2

    questions = list_questions(depth)
    print(f"=== Atelier Discovery ({depth.value}) — {len(questions)} questions ===")
    print()

    answers = {}
    for i, q in enumerate(questions, 1):
        if args.auto:
            choices = q.get("choices", [])
            if not choices:
                continue
            if q.get("multi_select"):
                answers[q["id"]] = [c["value"] for c in choices[:3]]
            else:
                answers[q["id"]] = choices[0]["value"]
            continue

        print(f"[{i}/{len(questions)}] {q.get('text_zh') or q.get('text_en') or q['id']}")
        choices = q.get("choices", [])
        for j, c in enumerate(choices, 1):
            label = c.get("text_zh") or c.get("text_en") or c.get("value")
            print(f"  {j}. {label}")
        if q.get("free_input"):
            print("  F. (free input — type the text)")
        if q.get("multi_select"):
            raw = input("  pick (comma-separated): ").strip()
            picks = [
                c["value"] for c, n in zip(choices, range(1, len(choices) + 1))
                if str(n) in raw.split(",")
            ]
            answers[q["id"]] = picks or [choices[0]["value"]]
        else:
            raw = input("  pick (number): ").strip()
            try:
                idx = int(raw) - 1
                answers[q["id"]] = choices[idx]["value"]
            except (ValueError, IndexError):
                answers[q["id"]] = (choices[0]["value"] if choices else "")
        print()

    profile = score_answers(answers)
    output = json.dumps(profile, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"taste profile written to: {args.out}")
    else:
        print("=== Taste Profile ===")
        print(output)
    print(f"\nrecommended_style: {profile.get('recommended_style')}")
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    from ._gates import StrictnessMode, run_audit
    from ._project import ProjectError, read_taste_profile

    try:
        scene_info = json.loads(Path(args.scene_info).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"error reading scene_info: {e}", file=sys.stderr)
        return 2

    try:
        mode = StrictnessMode(args.mode)
    except ValueError:
        print(f"unknown mode: {args.mode}", file=sys.stderr)
        return 2

    project_meta = None
    if args.project:
        try:
            project_meta = read_taste_profile(
                Path(args.project) / "taste-profile.json"
            )
        except ProjectError:
            project_meta = None

    report = run_audit(scene_info, mode=mode, project=project_meta)
    print(f"=== Audit ({mode.value}) — status: {report['status']} ===\n")
    for f in report.get("findings", []):
        sev = f.severity.value.upper()
        print(f"[{sev}] {f.gate}: {f.message}")
        if f.citation:
            print(f"    cite: {f.citation}")
        if f.suggested_fix:
            print(f"    fix:  {f.suggested_fix}")
        print()
    return 0 if report["status"] == "pass" else 1


def _cmd_bom(args: argparse.Namespace) -> int:
    from ._bom import bom_summary, collect_bom_rows, render_bom_csv, render_bom_markdown

    rows = collect_bom_rows(Path(args.project_root))
    if args.format == "markdown":
        out = render_bom_markdown(rows)
    elif args.format == "csv":
        out = render_bom_csv(rows)
    else:
        print(f"unknown format: {args.format}", file=sys.stderr)
        return 2

    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"BoM written to: {args.out}")
    else:
        print(out)

    summary = bom_summary(rows)
    print(
        f"\n=== Summary === items={summary['item_count']} "
        f"total=¥{summary['total_cost_rmb']:,.2f} "
        f"max_lead={summary['max_lead_time_days']}d",
        file=sys.stderr,
    )
    return 0


def _cmd_moodboard(args: argparse.Namespace) -> int:
    from ._moodboard import build_moodboard_prompts
    from ._project import ProjectError, read_taste_profile
    from ._style_vocab import StyleVocabError, parse_style_chapter

    proj = Path(args.project_root)
    try:
        profile = read_taste_profile(proj / "taste-profile.json")
    except ProjectError as e:
        print(f"error reading taste profile: {e}", file=sys.stderr)
        return 2

    slug = args.style or profile.get("recommended_style", "").replace("_", "-")
    if not slug:
        print(
            "error: no style — pass --style or run discovery first",
            file=sys.stderr,
        )
        return 2

    try:
        vocab = parse_style_chapter(slug)
    except StyleVocabError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    prompts = build_moodboard_prompts(
        profile, vocab, n=args.n, space_type=args.space,
    )
    print(f"=== {len(prompts)} moodboard prompts for {slug} / {args.space} ===\n")
    for i, p in enumerate(prompts, 1):
        print(f"[{i}] {p}\n")
    return 0


def _cmd_handbook(args: argparse.Namespace) -> int:
    from ._handbook import HandbookError, list_chapters, read_chapter, search_chapters

    if args.query:
        results = search_chapters(args.query)
        if not results:
            print(f"no matches for '{args.query}'")
            return 1
        for r in results:
            print(f"{r['chapter']:40s}  {r['matches']:3d} matches  {r['preview'][:80]}")
        return 0

    if args.chapter:
        try:
            print(read_chapter(args.chapter))
        except HandbookError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

    print("available chapters:")
    for slug in list_chapters():
        print(f"  {slug}")
    return 0


def _cmd_styles(args: argparse.Namespace) -> int:
    from ._style_vocab import available_styles, parse_style_chapter

    for slug in available_styles():
        try:
            vocab = parse_style_chapter(slug)
            kelvin_lo, kelvin_hi = vocab.kelvin_range
            n_palette = len(vocab.palette_60_30_10)
            n_refs = len(vocab.reference_projects)
            print(
                f"  {slug:30s}  Kelvin {kelvin_lo}-{kelvin_hi}K  "
                f"{n_palette} palette rows  {n_refs} ref projects"
            )
        except Exception as e:
            print(f"  {slug:30s}  (parse error: {e})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="atelier",
        description=(
            "Atelier — interior-design workflow CLI. "
            "Run without an MCP client; same handbook + skills + gates."
        ),
    )
    p.add_argument(
        "--version", action="store_true",
        help="print version and exit",
    )
    sub = p.add_subparsers(dest="command")

    # init
    pi = sub.add_parser("init", help="create a new interior design project")
    pi.add_argument("project_name")
    pi.add_argument(
        "--type", default="residential_apartment",
        help="project type (residential_apartment | residential_house | "
             "cafe_lounge | restaurant_full_service | retail_boutique | "
             "office_small)",
    )
    pi.add_argument("--root", help="project root directory (default: ./<project_name>)")
    pi.add_argument(
        "--spaces", nargs="*", default=[],
        help="space names (e.g. Living Bedroom Kitchen)",
    )
    pi.add_argument("--units", default="metric")

    # discover
    pd = sub.add_parser("discover", help="run the discovery questionnaire")
    pd.add_argument(
        "--depth", default="deep",
        help="quick | standard | deep | adaptive (default: deep)",
    )
    pd.add_argument(
        "--auto", action="store_true",
        help="auto-answer with first option (smoke test)",
    )
    pd.add_argument("--out", help="write taste profile to this file")

    # audit
    pa = sub.add_parser("audit", help="run quality gates against a scene_info JSON")
    pa.add_argument("scene_info", help="path to scene_info JSON file")
    pa.add_argument(
        "--mode", default="hero",
        help="hero | exploration | construction",
    )
    pa.add_argument("--project", help="project root (loads taste-profile if present)")

    # bom
    pb = sub.add_parser("bom", help="generate BoM from procurement.json + taste profile")
    pb.add_argument("project_root")
    pb.add_argument("--format", default="markdown", help="markdown | csv")
    pb.add_argument("--out", help="write BoM to this file")

    # moodboard
    pm = sub.add_parser("moodboard", help="build moodboard image-gen prompts")
    pm.add_argument("project_root")
    pm.add_argument("--style", help="style slug (overrides taste-profile recommended_style)")
    pm.add_argument("--space", default="living_room", help="space type")
    pm.add_argument("-n", type=int, default=4, help="number of prompts (1-8)")

    # handbook
    ph = sub.add_parser("handbook", help="read or search the design handbook")
    ph.add_argument("chapter", nargs="?", help="chapter slug (e.g. 'lighting')")
    ph.add_argument("--query", help="search across all chapters")

    # styles
    sub.add_parser("styles", help="list available style chapters with metadata")

    # version (also via --version)
    sub.add_parser("version", help="print version")

    return p


_HANDLERS = {
    "init": _cmd_init,
    "discover": _cmd_discover,
    "audit": _cmd_audit,
    "bom": _cmd_bom,
    "moodboard": _cmd_moodboard,
    "handbook": _cmd_handbook,
    "styles": _cmd_styles,
    "version": _cmd_version,
}


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        return _cmd_version(args)
    if not args.command:
        parser.print_help()
        return 0
    handler = _HANDLERS.get(args.command)
    if not handler:
        parser.print_help()
        return 2
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
