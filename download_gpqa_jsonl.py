from __future__ import annotations

import json
from pathlib import Path

import fire
from datasets import load_dataset


DATASET_NAME = "Idavidrein/gpqa"
CONFIG_NAMES = (
    "gpqa_diamond",
    "gpqa_experts",
    "gpqa_extended",
    "gpqa_main",
)


def export_gpqa_jsonl(
    output_dir: str = "gpqa_jsonls",
    dataset_name: str = DATASET_NAME,
    dataset_split: str = "train",
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for config_name in CONFIG_NAMES:
        dataset = load_dataset(dataset_name, config_name, split=dataset_split)
        destination = output_path / f"{config_name}.jsonl"

        with destination.open("w", encoding="utf-8") as handle:
            for record in dataset:
                handle.write(json.dumps(record, ensure_ascii=False))
                handle.write("\n")

        print(f"wrote {len(dataset)} rows to {destination}")


if __name__ == "__main__":
    fire.Fire(export_gpqa_jsonl)
