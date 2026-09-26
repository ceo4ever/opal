"""
@header {
  "module": "store",
  "layer": "data",
  "domain": "inventory",
  "description": "JSON 파일 기반 재고 저장소. 품목은 sku → {name, qty, location} 단일 위치 구조로 저장한다.",
  "exports": ["load", "save", "store_path"]
}
"""
import json
import os
from pathlib import Path


def store_path(explicit=None):
    return Path(explicit or os.environ.get("STOCKCTL_STORE", "stock.json"))


def load(path):
    p = Path(path)
    if not p.exists():
        return {"items": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def save(path, data):
    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, p)
