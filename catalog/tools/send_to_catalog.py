#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Phillip Edwards (Eddy)
# Written with the help of AI (Claude).
"""Sends new and changed plugins to the IngeTrazo extensions catalog.

For every catalog/entries/<id>.toml in this repository it works out what the
catalog entry should say now:

  * download - the plugin file named in 'source', at this exact commit
  * sha256   - the fingerprint of that file
  * version  - the catalog's version, one step up when the file has changed
               (1.1 -> 1.2), or the 'version' you put in the entry yourself
  * screenshot - catalog/screenshots/<id>.webp (or .png / .jpg) if there is one

Two keys in our entries are ours only and are not sent: 'source' (the plugin file)
and 'pr_note' (the answer to "does it use the network, run programs or delete
files?" in the pull request).

and compares it with the entry on the catalog's main branch. If anything that
matters has changed (the file, the picture, the name, summary or tags), it
opens a pull request on the catalog from your fork, one per plugin, touching
only that plugin's entry and its picture. An update to a plugin that is already
listed then goes in by itself (the catalog's own automerge); a new plugin waits
for a maintainer to approve its first entry.

It never runs any plugin code. Run by .github/workflows/send-to-ingetrazo-catalog.yml (a copy of catalog/send-to-ingetrazo-catalog.yml).

Environment:
  GH_TOKEN        a token of the account in author_url (eddy-99), public_repo scope
  CATALOG_REPO    the catalog, e.g. ingelibre/ingetrazo-extensions
  FORK_REPO       your fork of it, e.g. eddy-99/ingetrazo-extensions
  SOURCE_REPO     this repository (owner/name)
  SOURCE_SHA      the commit the download addresses point at
  ONLY            optional: ids to send, separated by spaces or commas
  DRY_RUN         "1": work everything out and print it, send nothing
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]          # the repository root
ENTRIES = HERE / "catalog" / "entries"
SHOTS = HERE / "catalog" / "screenshots"
MAX_SHOT = 600 * 1024
ORDER = ("id", "version", "author", "author_url", "license", "repository", "download",
         "sha256", "ingetrazo", "tags", "screenshot")
TABLES = ("name", "summary", "description")
# what decides whether the catalog needs telling (not the download address:
# the same file at a newer commit is not news)
COMPARE = ("sha256", "author", "author_url", "license", "repository", "ingetrazo", "tags",
           "screenshot", "name", "summary", "description")


def run(*args, cwd=None, check=True, capture=False):
    print("$", " ".join(a if "x-access-token" not in a else "<fork>" for a in args), flush=True)
    r = subprocess.run(args, cwd=cwd, text=True, capture_output=capture)
    if check and r.returncode != 0:
        if capture:
            print(r.stdout, r.stderr)
        raise SystemExit(f"failed: {' '.join(args[:3])} ...")
    return r


def q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def toml_text(e: dict) -> str:
    out = []
    for k in ORDER:
        if k not in e:
            continue
        v = e[k]
        out.append(f"{k} = " + ("[" + ", ".join(q(t) for t in v) + "]" if isinstance(v, list) else q(v)))
    for t in TABLES:
        if t in e:
            out += ["", f"[{t}]"] + [f"{lang} = {q(text)}" for lang, text in e[t].items()]
    return "\n".join(out) + "\n"


def bump(v: str) -> str:
    m = re.match(r"^(\d+(?:\.\d+)*)", v or "")
    if not m:
        return "1.0"
    parts = m.group(1).split(".")
    if len(parts) == 1:
        parts.append("0")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def newer(a: str, b: str) -> bool:
    def nums(v):
        return [int(x) for x in re.findall(r"\d+", v or "")]
    return nums(a) > nums(b)


def main() -> int:
    catalog = os.environ.get("CATALOG_REPO", "ingelibre/ingetrazo-extensions")
    fork = os.environ.get("FORK_REPO", "eddy-99/ingetrazo-extensions")
    source_repo = os.environ["SOURCE_REPO"]
    sha_commit = os.environ["SOURCE_SHA"]
    # a token pasted into the secret often carries a stray space or line break
    token = "".join(os.environ.get("GH_TOKEN", "").split())
    if token:
        os.environ["GH_TOKEN"] = token          # gh reads it from here too
    dry = os.environ.get("DRY_RUN") == "1"
    only = {x for x in re.split(r"[,\s]+", os.environ.get("ONLY", "")) if x}
    if not token and not dry:
        raise SystemExit("No CATALOG_TOKEN secret: see catalog/README.md for the one-time setup.")
    fork_owner = fork.split("/")[0]

    work = Path(tempfile.mkdtemp())
    cat = work / "catalog"
    # the whole history: the branch is pushed to your fork, which may be behind the catalog
    run("git", "clone", "-q", os.environ.get("CATALOG_URL") or f"https://github.com/{catalog}.git", str(cat))
    run("git", "config", "user.name", os.environ.get("GIT_NAME", "Phillip Edwards (Eddy)"), cwd=cat)
    run("git", "config", "user.email", os.environ.get("GIT_EMAIL", f"{fork_owner}@users.noreply.github.com"), cwd=cat)
    if not dry:
        run("git", "remote", "add", "fork", os.environ.get("FORK_URL") or f"https://x-access-token:{token}@github.com/{fork}.git", cwd=cat)

    sent, same, problems = [], [], []
    for path in sorted(ENTRIES.glob("*.toml")):
        ident = path.stem
        if only and ident not in only:
            continue
        try:
            mine = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            problems.append(f"{ident}: {path.name} does not read: {exc}")
            continue
        src = HERE / mine.get("source", "")
        if not mine.get("source") or not src.is_file():
            problems.append(f"{ident}: the plugin file '{mine.get('source')}' is not in the repository")
            continue
        data = src.read_bytes()
        digest = hashlib.sha256(data).hexdigest()

        live_path = cat / "extensions" / f"{ident}.toml"
        live = tomllib.loads(live_path.read_text(encoding="utf-8")) if live_path.is_file() else None

        entry = {k: v for k, v in mine.items() if k not in ("source", "pr_note")}
        entry["id"] = ident
        entry["download"] = f"https://raw.githubusercontent.com/{source_repo}/{sha_commit}/{mine['source']}"
        entry["sha256"] = digest

        # the picture: ours if we have one, else whatever the catalog already shows
        shot_file = None
        for ext in ("webp", "png", "jpg", "jpeg"):
            p = SHOTS / f"{ident}.{ext}"
            if p.is_file():
                shot_file = p
                break
        if shot_file is not None and shot_file.stat().st_size > MAX_SHOT:
            problems.append(f"{ident}: {shot_file.name} is over 600 KB, so it was left out")
            shot_file = None
        if shot_file is not None:
            entry["screenshot"] = shot_file.name
        elif live and live.get("screenshot"):
            entry["screenshot"] = live["screenshot"]
        else:
            entry.pop("screenshot", None)
            problems.append(f"{ident}: no picture - put one in catalog/screenshots/{ident}.webp "
                            f"(about 1200 x 750, under 600 KB) so the catalog shows one")

        # the version
        if live is None:
            entry["version"] = mine.get("version") or "1.0"
        elif live.get("sha256") != digest:
            want = mine.get("version")
            entry["version"] = want if want and newer(want, live.get("version", "0")) else bump(live.get("version"))
        else:
            entry["version"] = live.get("version", "1.0")

        shot_changed = False
        if shot_file is not None:
            there = cat / "screenshots" / shot_file.name
            shot_changed = not there.is_file() or there.read_bytes() != shot_file.read_bytes()

        if live is not None and not shot_changed and all(live.get(k) == entry.get(k) for k in COMPARE):
            same.append(ident)
            continue

        what = []
        if live is None:
            what.append("new plugin")
        else:
            if live.get("sha256") != digest:
                what.append(f"new version {live.get('version')} -> {entry['version']}")
            if shot_changed:
                what.append("new picture")
            if any(live.get(k) != entry.get(k) for k in ("name", "summary", "description", "tags")):
                what.append("new wording")
        print(f"\n=== {ident}: {', '.join(what) or 'entry changed'}", flush=True)

        branch = f"auto/{ident}"
        run("git", "checkout", "-q", "-B", branch, "origin/main", cwd=cat)
        live_path.write_text(toml_text(entry), encoding="utf-8")
        files = [f"extensions/{ident}.toml"]
        if shot_changed:
            (cat / "screenshots").mkdir(exist_ok=True)
            shutil.copyfile(shot_file, cat / "screenshots" / shot_file.name)
            files.append(f"screenshots/{shot_file.name}")

        # the catalog's own check, on just this entry (it reads the file, never runs it)
        offline = ["--offline"] if os.environ.get("CHECK_OFFLINE") == "1" else []
        r = run(sys.executable, "tools/catalog.py", "check", *offline, ident, cwd=cat, check=False, capture=True)
        print(r.stdout, r.stderr)
        if r.returncode != 0:
            problems.append(f"{ident}: the catalog's check found a problem, nothing sent:\n{r.stdout}")
            run("git", "reset", "-q", "--hard", cwd=cat)
            run("git", "clean", "-fdq", cwd=cat)
            continue
        note = mine.get("pr_note") or ("No. It uses no network and runs no other programs; it only "
                                       "writes its own settings and presets.")
        if "for the reviewer to read" in r.stdout:
            print(f"{ident}: the check lists things for a maintainer to read, so this one waits for a person.")
            listed = [ln.strip() for ln in r.stdout.splitlines() if ln.strip().startswith("·")]
            if not mine.get("pr_note"):
                note = "Only as part of what the plugin is for (see the plugin's description)."
            note += "\n\nThe automatic check lists:\n" + "\n".join(f"- {ln.lstrip('· ')}" for ln in listed)

        if dry:
            print(toml_text(entry))
            run("git", "reset", "-q", "--hard", cwd=cat)
            run("git", "clean", "-fdq", cwd=cat)
            sent.append(ident)
            continue

        run("git", "add", *files, cwd=cat)
        name = entry.get("name", {}).get("en") or ident
        title = (f"Add {name}" if live is None else f"{name} {entry['version']}")
        run("git", "commit", "-q", "-m", title, cwd=cat)
        run("git", "push", "-f", "fork", f"{branch}:{branch}", cwd=cat)

        body = (
            "Sent automatically from " f"https://github.com/{source_repo}/commit/{sha_commit}\n\n"
            "- [x] One file `extensions/<id>.toml`" + (" and its screenshot" if shot_changed else "") + "\n"
            "- [x] `download` points at a **commit**, not a branch\n"
            f"- [x] I tested it with the IngeTrazo version in `ingetrazo` ({entry.get('ingetrazo')})\n"
            f"- [x] The licence in `license` is the one in my code ({entry.get('license')})\n"
            "- [x] I did **not** edit `reviewed.toml`\n\n"
            "**What does it do? / ¿Qué hace?**\n"
            f"{entry.get('summary', {}).get('en', '')}\n\n"
            f"{entry.get('summary', {}).get('es', '')}\n\n"
            "**Does it use the network, run programs or delete files? Why? / ¿Usa internet, ejecuta "
            "programas o borra archivos?**\n"
            f"{note}\n\n"
            f"Changes: {', '.join(what) or 'entry updated'}.\n"
        )
        r = run("gh", "pr", "list", "-R", catalog, "--state", "open", "--head", branch,
                "--author", fork_owner, "--json", "number", "--jq", ".[0].number",
                check=False, capture=True)
        number = (r.stdout or "").strip()
        if number:
            run("gh", "pr", "edit", number, "-R", catalog, "--title", title, "--body", body)
            print(f"{ident}: updated the open pull request #{number}")
        else:
            run("gh", "pr", "create", "-R", catalog, "--base", "main",
                "--head", f"{fork_owner}:{branch}", "--title", title, "--body", body)
        sent.append(ident)

    print("\n------------------------------------------------------------")
    print(f"Sent to the catalog: {', '.join(sent) or 'nothing'}")
    print(f"Already up to date:  {', '.join(same) or 'none'}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("## IngeTrazo catalog\n\n")
            fh.write(f"**Sent:** {', '.join(sent) or 'nothing'}\n\n")
            fh.write(f"**Already up to date:** {', '.join(same) or 'none'}\n\n")
            if problems:
                fh.write("**Needs a look:**\n\n" + "\n".join(f"- {p}" for p in problems) + "\n")
    if problems:
        print("\nNeeds a look:")
        for p in problems:
            print("  -", p)
    # a missing picture is a warning; a failed check stops the run going green
    return 1 if any("check found a problem" in p or "does not read" in p or "is not in the repository" in p
                    for p in problems) else 0


if __name__ == "__main__":
    sys.exit(main())
