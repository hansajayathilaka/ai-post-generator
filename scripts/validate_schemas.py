"""Validate config.json, posts/index.json, and all posts/*/meta.json against their schemas."""

import json
import sys
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"


def _load(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(label: str, data, schema: dict) -> list[str]:
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for err in sorted(validator.iter_errors(data), key=str):
        path = " → ".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(f"  {path}: {err.message}")
    if errors:
        print(f"[FAIL] {label}")
        for e in errors:
            print(e)
    else:
        print(f"[ OK ] {label}")
    return errors


def main() -> None:
    config_schema = _load(SCHEMAS_DIR / "config.schema.json")
    meta_schema   = _load(SCHEMAS_DIR / "meta.schema.json")
    index_schema  = _load(SCHEMAS_DIR / "index.schema.json")

    all_errors: list[str] = []

    # config.json
    all_errors += _validate(
        "config.json",
        _load(REPO_ROOT / "config.json"),
        config_schema,
    )

    # posts/index.json
    all_errors += _validate(
        "posts/index.json",
        _load(REPO_ROOT / "posts" / "index.json"),
        index_schema,
    )

    # posts/*/meta.json
    for meta_path in sorted((REPO_ROOT / "posts").glob("*/meta.json")):
        rel = meta_path.relative_to(REPO_ROOT)
        data = _load(meta_path)
        # strip $schema before validating so it doesn't trip additionalProperties
        data.pop("$schema", None)
        all_errors += _validate(str(rel), data, meta_schema)

    print()
    if all_errors:
        print(f"Schema validation FAILED — {len(all_errors)} error(s).")
        sys.exit(1)
    else:
        print("All schema validations passed.")


if __name__ == "__main__":
    main()
