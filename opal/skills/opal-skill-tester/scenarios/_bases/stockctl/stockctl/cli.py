"""
@header {
  "module": "cli",
  "layer": "api",
  "domain": "inventory",
  "description": "stockctl 명령행 인터페이스. add/remove/list 서브커맨드로 단일 위치 재고를 관리한다.",
  "exports": ["main"]
}
"""
import argparse
import sys

from . import store


def cmd_add(args):
    data = store.load(args.store)
    item = data["items"].setdefault(args.sku, {"name": args.name or args.sku, "qty": 0, "location": args.location})
    if args.name:
        item["name"] = args.name
    item["qty"] += args.qty
    store.save(args.store, data)
    print(f"{args.sku} qty={item['qty']}")
    return 0


def cmd_remove(args):
    data = store.load(args.store)
    item = data["items"].get(args.sku)
    if item is None:
        print(f"unknown sku: {args.sku}", file=sys.stderr)
        return 1
    if item["qty"] < args.qty:
        print(f"insufficient: {args.sku} has {item['qty']}", file=sys.stderr)
        return 2
    item["qty"] -= args.qty
    store.save(args.store, data)
    print(f"{args.sku} qty={item['qty']}")
    return 0


def cmd_list(args):
    data = store.load(args.store)
    for sku in sorted(data["items"]):
        item = data["items"][sku]
        print(f"{sku}\t{item['name']}\t{item['location']}\t{item['qty']}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="stockctl")
    p.add_argument("--store", default=None)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("add")
    a.add_argument("sku")
    a.add_argument("--qty", type=int, required=True)
    a.add_argument("--name")
    a.add_argument("--location", default="MAIN")
    a.set_defaults(func=cmd_add)
    r = sub.add_parser("remove")
    r.add_argument("sku")
    r.add_argument("--qty", type=int, required=True)
    r.set_defaults(func=cmd_remove)
    l = sub.add_parser("list")
    l.set_defaults(func=cmd_list)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.store = store.store_path(args.store)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
