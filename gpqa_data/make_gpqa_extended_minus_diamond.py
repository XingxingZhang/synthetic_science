from __future__ import annotations

import json
from pathlib import Path

import fire


def build_extended_minus_diamond(
    extended_path: str = "gpqa_jsonls/gpqa_extended.jsonl",
    diamond_path: str = "gpqa_jsonls/gpqa_diamond.jsonl",
    output_path: str = "gpqa_jsonls/gpqa_extended-diamond.jsonl",
) -> None:
    extended_file = Path(extended_path)
    diamond_file = Path(diamond_path)
    output_file = Path(output_path)

    diamond_ids: set[str] = set()
    diamond_count = 0

    with diamond_file.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            record_id = record["Record ID"]

            if record_id in diamond_ids:
                raise ValueError(f"duplicate Record ID in diamond set: {record_id}")

            diamond_ids.add(record_id)
            diamond_count += 1

    output_file.parent.mkdir(parents=True, exist_ok=True)

    extended_ids: set[str] = set()
    matched_diamond_ids: set[str] = set()
    extended_count = 0
    kept_count = 0

    with (
        extended_file.open(encoding="utf-8") as source,
        output_file.open("w", encoding="utf-8") as destination,
    ):
        for line in source:
            record = json.loads(line)
            record_id = record["Record ID"]

            if record_id in extended_ids:
                raise ValueError(f"duplicate Record ID in extended set: {record_id}")

            extended_ids.add(record_id)
            extended_count += 1

            if record_id in diamond_ids:
                matched_diamond_ids.add(record_id)
                continue

            destination.write(json.dumps(record, ensure_ascii=False))
            destination.write("\n")
            kept_count += 1

    missing_ids = diamond_ids - matched_diamond_ids
    if missing_ids:
        raise ValueError(
            f"{len(missing_ids)} diamond Record IDs were not found in the extended set"
        )

    print(f"loaded {extended_count} extended rows")
    print(f"loaded {diamond_count} diamond rows")
    print(f"wrote {kept_count} rows to {output_file}")


if __name__ == "__main__":
    fire.Fire(build_extended_minus_diamond)
