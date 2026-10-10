"""Build deterministic codebone context for one isolated benchmark copy."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


QUERIES = [
    "VAT invoice credit note finance export standard rate",
    "customer phone persistence create get event payload",
    "password reset token TTL minutes timestamp",
    "payment succeeded webhook retry idempotent ledger event",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="codebone source root containing src/")
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--work", required=True)
    args = parser.parse_args()

    source = Path(args.source).resolve()
    project = Path(args.project).resolve()
    output = Path(args.output).resolve()
    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(source))

    from src import codesearch, context_format
    from src.config import Config
    from src.providers import FastFallbackProvider
    from src.service import CodeBoneService

    config = Config(config_file=work / "config.json")
    config.set("project_path", str(project))
    service = CodeBoneService(config)
    service.provider = FastFallbackProvider()
    started = time.monotonic()
    try:
        service.rescan_all()
        elapsed = time.monotonic() - started
        files, index = service.storage.view()
        texts = codesearch.read_texts(str(project), files)
        facts = service.storage.source_facts()
        sections = [
            "# codebone benchmark context",
            "",
            "This file was generated from this exact isolated project copy immediately before the agent run.",
            "",
            context_format.overview(project.name, files, index),
        ]
        for query in QUERIES:
            sections += ["", "---", "", context_format.search(
                project.name, files, index, query=query, texts=texts, facts=facts
            )]
        output.write_text("\n".join(sections) + "\n", encoding="utf-8")
        meta = {
            "index_s": round(elapsed, 3),
            "indexed_files": len(files),
            "context_chars": output.stat().st_size,
            "analysis": "codebone deterministic architecture graph",
        }
        print(json.dumps(meta, sort_keys=True))
        return 0
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
