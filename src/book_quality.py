"""File-based Agent pipeline: prepare -> triage -> book -> audit.

No provider dependency or hidden model calls. Semantic reviews are supplied by the
Agent; this module checks evidence, completeness, freshness and reading cost.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READING_UNITS_PER_MINUTE = 400
READING_SENSITIVITY = (300, 500)
KEY_TERM_ORIGINS = {"editor", "speaker"}
SEMANTIC_REVIEW_MODES = {"agent_assisted", "human", "hybrid"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seconds(stamp):
    if isinstance(stamp, (int, float)):
        return float(stamp)
    parts = str(stamp).split(":")
    if len(parts) not in (2, 3):
        raise ValueError(f"Invalid timestamp: {stamp}")
    result = 0.0
    for p in parts:
        result = result * 60 + float(p)
    return result


def stamp(value):
    value = int(value)
    return f"{value // 3600:02}:{value % 3600 // 60:02}:{value % 60:02}"


def key_terms(item):
    """Return the deliberately small list of terms needing a first-use gloss.

    ``terms`` remains a free-form source vocabulary for backwards readability;
    only the explicit ``key_terms`` field is a beginner-readability contract.
    A string is accepted as shorthand for an editor gloss requirement.  The
    normalized shape is used by both triage validation and audit validation.
    """
    if "key_terms" not in item:
        return None
    raw = item.get("key_terms") or []
    if not isinstance(raw, list):
        return None
    result = []
    for value in raw:
        if isinstance(value, str):
            term = value.strip()
            if term:
                result.append({"term": term, "aliases": [term], "origin": "editor", "requires_definition": True})
            continue
        if not isinstance(value, dict):
            continue
        term = str(value.get("term") or value.get("name") or "").strip()
        if not term:
            continue
        aliases = value.get("aliases", [])
        if not isinstance(aliases, list):
            aliases = [aliases]
        aliases = [str(x).strip() for x in [term, *aliases] if str(x).strip()]
        unique_aliases = list(dict.fromkeys(aliases))
        result.append({
            "term": term,
            "aliases": unique_aliases,
            "origin": str(value.get("origin", "editor")).strip().lower(),
            "definition": str(value.get("definition") or "").strip(),
            "requires_definition": bool(value.get("requires_definition", True)),
        })
    return result


def _definition_like(term, evidence):
    """Conservative structural check for a short first-use glossary quote."""
    if not term or not evidence or term not in evidence:
        return False
    # Parenthetical gloss: TERM（作用……） / TERM (作用……)
    parenthetical = re.search(re.escape(term) + r"\s*[（(]([^）)]{2,160})[）)]", evidence, re.I)
    if parenthetical and len(parenthetical.group(1).strip()) <= 160:
        return True
    # Short prose gloss: TERM 是/指/用于/让/用来……; this permits a speaker's
    # natural explanation while rejecting a bare keyword hit.
    prose = re.search(
        re.escape(term) + r"[^。！？!?\n]{0,60}(?:是|指|表示|用于|用来|让|意味着|指的是)",
        evidence,
        re.I,
    )
    return bool(prose)


def read_source(directory):
    """Corrected text is primary when available, raw stays independently readable."""
    corrected = directory / "transcript.corrected.txt"
    raw = directory / "transcript.json"
    meta = load(directory / "meta.json") if (directory / "meta.json").exists() else {}
    data = load(raw) if raw.exists() else {}
    if corrected.exists():
        lines = corrected.read_text(encoding="utf-8").splitlines()
        matches = [re.match(r"^\[(\d+(?::\d+){1,2}(?:\.\d+)?)\]\s*(.*)$", x) for x in lines if x.strip()]
        if not matches or any(m is None for m in matches):
            raise ValueError("Corrected transcript must contain timestamped lines")
        segments = [(seconds(m[1]), m[2]) for m in matches]
        source = corrected.name
    elif data.get("segments"):
        segments = [(seconds(s["start"]), s["text"]) for s in data["segments"]]
        source = raw.name
    else:
        raise ValueError("No usable transcript")
    if any(b[0] < a[0] for a, b in zip(segments, segments[1:])):
        raise ValueError("Transcript timestamps are not ordered")
    duration = float(data.get("duration") or meta.get("duration") or segments[-1][0])
    estimated = bool(meta.get("duration_is_estimate", not data.get("duration") and not meta.get("duration")))
    return segments, source, duration, estimated, raw.exists()


def prepare(directory, window=600):
    if window <= 0:
        raise ValueError("Window must be positive")
    segments, source, duration, estimated, has_raw = read_source(directory)
    groups = {}
    for time, text in segments:
        groups.setdefault(int(time // window), []).append((time, text))
    ordered_groups = sorted(groups.items())
    chunks = []
    duplicate_pairs = 0
    for i, (_, rows) in enumerate(ordered_groups, 1):
        # The end of a source window is the next observed timestamp (or the
        # video duration), rather than the start of its final subtitle.  This
        # keeps source spans useful when a knowledge item crosses a boundary.
        next_start = ordered_groups[i][1][0][0] if i < len(ordered_groups) else duration
        end = max(rows[-1][0], next_start or rows[-1][0])
        duplicate_pairs += sum(
            1 for (_, left), (_, right) in zip(rows, rows[1:])
            if re.sub(r"\s+", "", left) and re.sub(r"\s+", "", left) == re.sub(r"\s+", "", right)
        )
        chunks.append({"id": f"S{i:02}", "start": stamp(rows[0][0]), "end": stamp(end),
                       "segment_count": len(rows),
                       "text": "\n".join(f"[{stamp(t)}] {s}" for t, s in rows)})
    source_data = {"source": source, "raw_available": has_raw, "duration": duration,
                   "duration_is_estimate": estimated, "window_seconds": window,
                   "chunks": chunks, "adjacent_duplicate_pairs": duplicate_pairs,
                   "dedupe_policy": "source text retains all segments; duplicate candidates are counted for editorial review, never silently removed"}
    save(directory / "quality/source.json", source_data)
    header = (f"# Source review\n\nPrimary: {source}; raw available: {has_raw}.\n"
              "Read every complete window and adjacent windows together where a knowledge chain crosses a boundary.\n"
              "Source text is not truncated or silently deduplicated; repeated adjacent lines are only counted as candidates.\n"
              "If transcript.json exists, compare suspected corrections against it.\n\n")
    (directory / "quality/source.md").write_text(header + "\n\n".join(
        f"## {c['id']} {c['start']}–{c['end']}\n\n{c['text']}" for c in chunks) + "\n", encoding="utf-8")
    return source_data


def metrics(book, duration):
    # Strip markup/URLs, retain visible captions, prose, code and Mermaid labels.
    # Everything is counted once as approximate reading units; Mermaid syntax
    # and code tokens are included because they still impose reading cost, but
    # there is no extra code-line penalty and no claim of stopwatch accuracy.
    text = re.sub(r"<!--.*?-->", "", book, flags=re.S)
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    units = len(re.findall(r"[\u3400-\u9fff]|[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text))
    minutes = units / READING_UNITS_PER_MINUTE
    video = duration / 60 if duration else None
    return {"markdown_characters": len(book), "reading_units": units,
            "reading_units_definition": "每个汉字或英文/数字词计 1 个阅读单位；Markdown 语法、链接 URL 和 HTML 标签移除；代码与 Mermaid 标签按文本近似计数。",
            "reading_formula": "reading_units / 400",
            "reading_minutes_400": round(minutes, 2),
            "reading_minutes_300_500": [round(units / READING_SENSITIVITY[1], 2), round(units / READING_SENSITIVITY[0], 2)],
            "video_minutes": round(video, 2) if video else None,
            "time_saved_percent_400": round(100 * (1 - minutes / video), 1) if video else None,
            "reading_ratio": round(minutes / video, 4) if video else None,
            "note": "统一估算公式，不是对实际阅读时长的测量；300/500 为敏感性范围。"}


def triage_errors(triage, source):
    errors = []
    chunks = {c["id"]: c for c in source["chunks"]}
    reviewed = triage.get("reviewed_chunks", [])
    if set(reviewed) != set(chunks) or len(reviewed) != len(chunks):
        errors.append("Triage must review every source chunk exactly once")
    if triage.get("status", "reviewed") != "reviewed":
        errors.append("Triage is not marked status=reviewed")
    seen, sourced = set(), set()
    items = triage.get("items") or []
    if not items:
        errors.append("Empty triage")
    if not any(i.get("priority") == "A" for i in items if isinstance(i, dict)):
        if not triage.get("no_learning_content"):
            errors.append("No A knowledge item; use an explicit no_learning_content outcome only when the source was actually reviewed")
        elif not triage.get("no_learning_reason"):
            errors.append("no_learning_content requires no_learning_reason")
    for item in triage.get("items", []):
        if not isinstance(item, dict):
            errors.append("Knowledge item must be an object")
            continue
        key = item.get("id")
        if not key or key in seen:
            errors.append(f"Duplicate/missing knowledge id: {key}")
        seen.add(key)
        if item.get("priority") not in ("A", "B", "C"):
            errors.append(f"{key}: invalid priority")
        if item.get("kind") not in ("observation", "opinion", "prediction", "speculation"):
            errors.append(f"{key}: invalid claim kind")
        if not item.get("why") or not item.get("topic"):
            errors.append(f"{key}: missing value judgment")
        if item.get("priority") in ("A", "B") and not item.get("must_preserve"):
            errors.append(f"{key}: missing knowledge requirements")
        # C is a category summary: it must not become a line-by-line dump of
        # filler.  A/B require exact source quotes; C may omit quotes and rely
        # on reviewed_chunks plus its category/reason.
        if item.get("priority") in ("A", "B") and not item.get("sources"):
            errors.append(f"{key}: missing source evidence")
        if item.get("priority") == "C" and item.get("must_preserve"):
            errors.append(f"{key}: C item must not carry must_preserve requirements")
        if item.get("priority") == "A" and "key_terms" not in item:
            errors.append(f"{key}: A item must declare key_terms (use [] when no specialist term needs a gloss)")
        declared_key_terms = key_terms(item)
        if "key_terms" in item and declared_key_terms is None:
            errors.append(f"{key}: key_terms must be a list")
        for term in declared_key_terms or []:
            if term["origin"] not in KEY_TERM_ORIGINS:
                errors.append(f"{key}: invalid key term origin for {term['term']}")
            if term["requires_definition"] and not term.get("definition"):
                # The definition can be supplied in the book, but an internal
                # hint keeps the editor from silently inventing mechanisms.
                errors.append(f"{key}: key term {term['term']} needs a short definition hint")
        for ref in item.get("sources", []):
            if not isinstance(ref, dict):
                errors.append(f"{key}: source evidence must be objects")
                continue
            cid, quote = ref.get("chunk"), ref.get("quote")
            if cid not in chunks or not quote or quote not in chunks[cid]["text"]:
                errors.append(f"{key}: source quote not found in {cid}")
            else:
                if item.get("priority") in ("A", "B"):
                    sourced.add(cid)
    # reviewed_chunks proves that every window was read.  A/B source quotes
    # prove where retained knowledge came from; C summaries intentionally do
    # not need a quote for every deleted line.
    if not sourced and any(i.get("priority") in ("A", "B") for i in items if isinstance(i, dict)):
        errors.append("No A/B source evidence was validated")
    return errors


def audit_errors(triage, review, book, source):
    errors = triage_errors(triage, source)
    expected = {
        i.get("id"): i
        for i in (triage.get("items") or [])
        if isinstance(i, dict) and i.get("id") and i.get("priority") in ("A", "B")
    }
    semantic = review.get("semantic_review", {})
    if not isinstance(semantic, dict):
        semantic = {}
    if semantic.get("performed") is not True:
        errors.append("Semantic review provenance is missing or performed is not true; audit cannot pass automatically")
    if semantic.get("mode") not in SEMANTIC_REVIEW_MODES:
        errors.append("Semantic review mode must be agent_assisted, human or hybrid")
    if not semantic.get("method"):
        errors.append("Semantic review method is required; state how the source and book were read")
    if not expected:
        if not (triage.get("no_learning_content") and review.get("outcome") == "no_learning_content"):
            errors.append("No A/B learning item was audited; use explicit outcome=no_learning_content only after a complete source sweep")
    rows = review.get("items", [])
    if not isinstance(rows, list):
        rows = []
        errors.append("Audit items must be a list")
    ids = [r.get("id") for r in rows if isinstance(r, dict)]
    if set(ids) != set(expected) or len(ids) != len(expected):
        errors.append("Audit must review each A/B item exactly once")
    for row in rows:
        if not isinstance(row, dict):
            errors.append("Audit item must be an object")
            continue
        key = row.get("id")
        if key not in expected:
            continue
        if row.get("status") != "covered":
            errors.append(f"{key}: {row.get('status', 'missing')}")
        evidence = row.get("evidence", [])
        if not evidence or any(not q or q not in book for q in evidence):
            errors.append(f"{key}: book evidence not found")
        checks = row.get("checks", [])
        requirements = expected[key].get("must_preserve") or expected[key].get("must_explain") or []
        if sorted(c.get("requirement", "") for c in checks) != sorted(requirements):
            errors.append(f"{key}: every knowledge requirement needs a check")
        for c in checks:
            if not c.get("evidence") or c["evidence"] not in book:
                errors.append(f"{key}: requirement evidence not found")
        if not row.get("note"):
            errors.append(f"{key}: missing semantic review note")
        # A term can only be counted as beginner-readable when the review
        # records the first-use evidence.  This remains an Agent/editor
        # judgment; the validator only prevents an unsubstantiated pass.
        terms = key_terms(expected[key]) or []
        term_checks = row.get("term_checks", [])
        if not isinstance(term_checks, list):
            term_checks = []
            errors.append(f"{key}: term_checks must be a list")
        expected_names = [str(term["term"]) for term in terms]
        check_names = [str(t.get("term")) for t in term_checks if isinstance(t, dict) and t.get("term")]
        malformed_checks = [
            index for index, value in enumerate(term_checks)
            if not isinstance(value, dict) or not str(value.get("term") or "").strip()
        ]
        if malformed_checks:
            errors.append(f"{key}: term_checks entries need a non-empty term ({malformed_checks})")
        duplicate_names = sorted({name for name in check_names if check_names.count(name) > 1})
        if duplicate_names:
            errors.append(f"{key}: duplicate term_checks: {', '.join(duplicate_names)}")
        if set(check_names) != set(expected_names) or len(check_names) != len(expected_names):
            missing_names = sorted(set(expected_names) - set(check_names))
            unexpected_names = sorted(set(check_names) - set(expected_names))
            detail = []
            if missing_names:
                detail.append("missing=" + ",".join(missing_names))
            if unexpected_names:
                detail.append("unexpected=" + ",".join(unexpected_names))
            errors.append(f"{key}: term_checks must match key_terms exactly ({'; '.join(detail) or 'count mismatch'})")
        term_by_name = {str(t.get("term")): t for t in term_checks if isinstance(t, dict)}
        for term in terms:
            check = term_by_name.get(term["term"])
            if not check:
                errors.append(f"{key}: missing term_check for {term['term']}")
                continue
            expected_statuses = {"defined"} if term.get("requires_definition", True) else {"defined", "not_needed"}
            if check.get("status") not in expected_statuses:
                errors.append(f"{key}: key term {term['term']} is not marked defined")
                continue
            if check.get("status") == "not_needed":
                continue
            evidence = str(check.get("evidence") or "")
            if not evidence or evidence not in book:
                errors.append(f"{key}: key term {term['term']} first-use evidence not found in book")
            elif not _definition_like(term["term"], evidence):
                errors.append(f"{key}: key term {term['term']} evidence is a bare hit, not a short gloss")
            if not check.get("first_use"):
                errors.append(f"{key}: key term {term['term']} needs a first_use quote")
            elif check["first_use"] not in book:
                errors.append(f"{key}: key term {term['term']} first_use quote not found in book")
        # Causal and attribution checks are semantic work products.  The script
        # requires their explicit status but does not pretend to derive it from
        # a keyword or concatenate distant paragraphs.
        if expected[key]["priority"] == "A":
            causal = row.get("causal_check")
            if not isinstance(causal, dict) or causal.get("status") not in ("pass", "not_applicable") or not causal.get("note"):
                errors.append(f"{key}: missing semantic causal_check")
            elif causal.get("evidence"):
                evidence_rows = causal["evidence"] if isinstance(causal["evidence"], list) else [causal["evidence"]]
                if any(str(e) not in book for e in evidence_rows):
                    errors.append(f"{key}: causal_check evidence not found in book")
        needs_attribution = expected[key].get("kind", expected[key].get("claim_type")) in ("opinion", "prediction", "speculation")
        needs_attribution = needs_attribution or any(t.get("origin") == "speaker" for t in (key_terms(expected[key]) or []))
        if needs_attribution:
            attribution = row.get("attribution_check")
            if not isinstance(attribution, dict) or attribution.get("status") != "pass" or not attribution.get("note"):
                errors.append(f"{key}: missing semantic attribution_check")
            elif attribution.get("evidence") and str(attribution["evidence"]) not in book:
                errors.append(f"{key}: attribution_check evidence not found in book")
    sweep = review.get("source_sweep", {})
    chunks = [c["id"] for c in source["chunks"]]
    if sorted(sweep.get("chunks", [])) != sorted(chunks) or not sweep.get("note"):
        errors.append("Missing complete source sweep")
    for section in ("fidelity", "redundancy", "accessibility"):
        value = review.get(section, {})
        if not isinstance(value, dict) or value.get("status") != "pass" or not value.get("note"):
            errors.append(f"{section}: needs review")
    if not review.get("reviewer"):
        errors.append("Missing reviewer/provenance")
    return errors


def fingerprints(directory):
    names = ["book.md", "book.html", "knowledge.triage.json", "coverage.audit.json", "transcript.corrected.txt", "transcript.json", "meta.json"]
    return {n: hashlib.sha256((directory / n).read_bytes()).hexdigest() for n in names if (directory / n).exists()}


def audit(directory):
    source = prepare(directory)  # Never validate against an obsolete transcript snapshot.
    triage = load(directory / "knowledge.triage.json")
    review = load(directory / "coverage.audit.json")
    book = (directory / "book.md").read_text(encoding="utf-8")
    errors = audit_errors(triage, review, book, source)
    if not (directory / "book.html").is_file():
        errors.append("Missing rendered book.html; run post_process.py after the final book/capture pass before audit")
    stats = metrics(book, source["duration"])
    warnings = []
    ratio = stats["reading_ratio"]
    if ratio is not None and ratio > .30:
        warnings.append("Above 30% soft reading budget; review compression without deleting A knowledge")
        if not review.get("budget_note"):
            errors.append("Above budget without editorial explanation")
    if not source["raw_available"]:
        warnings.append("Raw transcript unavailable; corrected-source review only")
    if source["duration_is_estimate"]:
        warnings.append("Video duration is estimated")
    source_completeness = "raw_and_corrected" if source["raw_available"] and source["source"] == "transcript.corrected.txt" else (
        "raw_only" if source["raw_available"] else "corrected_only"
    )
    report = {"passed": not errors, "status": "passed" if not errors else "needs_review",
              "errors": errors, "warnings": warnings,
              "metrics": stats, "fingerprints": fingerprints(directory),
              "source_completeness": source_completeness,
              "limits": "Structural checks plus Agent semantic self-review; not independent factual verification."}
    save(directory / "quality/report.json", report)
    return report


def check_ready(directory):
    """Legacy books remain publishable; triaged books must pass a fresh audit."""
    if not (directory / "knowledge.triage.json").exists():
        return
    path = directory / "quality/report.json"
    if not path.exists():
        raise ValueError("Run book_quality.py audit before publishing")
    report = load(path)
    if not report.get("passed") or report.get("fingerprints") != fingerprints(directory):
        raise ValueError("Quality audit failed or is stale; rerun after review")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["prepare", "check-triage", "audit", "metrics"])
    ap.add_argument("directory", type=Path, help="output/<id> or a regression fixture directory")
    args = ap.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.directory)
            print(f"Prepared {len(result['chunks'])} source chunks in {args.directory}/quality")
        elif args.command == "check-triage":
            errors = triage_errors(load(args.directory / "knowledge.triage.json"), prepare(args.directory))
            print(json.dumps(errors, ensure_ascii=False, indent=2))
            raise SystemExit(bool(errors))
        elif args.command == "audit":
            report = audit(args.directory)
            print(json.dumps({k: v for k, v in report.items() if k != "fingerprints"}, ensure_ascii=False, indent=2))
            raise SystemExit(not report["passed"])
        else:
            _, _, duration, _, _ = read_source(args.directory)
            print(json.dumps(metrics((args.directory / "book.md").read_text(encoding="utf-8"), duration), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        ap.exit(2, f"Quality input error: {exc}\n")


if __name__ == "__main__":
    main()
