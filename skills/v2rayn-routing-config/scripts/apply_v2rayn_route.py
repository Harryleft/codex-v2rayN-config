import argparse
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


ROUTE_ID = "v3-whitelist-speedtest-direct"
ROUTE_NAME = "V3-绕过大陆 + 测速直连"


def default_rules_path() -> Path:
    return Path(__file__).resolve().parents[1] / "references" / "v2rayn-routing-rules.json"


def load_rules(path: Path) -> list[dict]:
    rules = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rules, list) or not rules:
        raise ValueError("routing rules must be a non-empty JSON array")
    return rules


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"required file not found: {path}")


def backup(path: Path, stamp: str) -> Path:
    target = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, target)
    return target


def apply_route(base: Path, rules_path: Path) -> dict:
    gui = base / "guiConfigs"
    db_path = gui / "guiNDB.db"
    config_path = gui / "guiNConfig.json"
    runtime_path = base / "binConfigs" / "config.json"

    for path in (db_path, config_path, runtime_path):
        require_file(path)

    rules = load_rules(rules_path)
    rule_set = json.dumps(rules, ensure_ascii=False, separators=(",", ":"))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    backups = [backup(db_path, stamp), backup(config_path, stamp)]

    con = sqlite3.connect(db_path, timeout=10)
    try:
        cur = con.cursor()
        cur.execute("update RoutingItem set IsActive = 0")
        cur.execute("delete from RoutingItem where Id = ?", (ROUTE_ID,))
        cur.execute(
            """insert into RoutingItem
               (Id, Remarks, Url, RuleSet, RuleNum, Enabled, Locked, CustomIcon, CustomRulesetPath4Singbox,
                DomainStrategy, DomainStrategy4Singbox, Sort, IsActive)
               values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ROUTE_ID, ROUTE_NAME, "", rule_set, len(rules), 1, 0, "", "", None, None, 1, 1),
        )
        con.commit()
    finally:
        con.close()

    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    config.setdefault("RoutingBasicItem", {})["RoutingIndexId"] = ROUTE_ID
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "backup_stamp": stamp,
        "backups": [str(path) for path in backups],
        "active_route": ROUTE_ID,
        "route_name": ROUTE_NAME,
        "rule_count": len(rules),
        "restart_required": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely apply Codex-ready v2rayN routing rules.")
    parser.add_argument("--base", required=True, help="v2rayN root directory, e.g. D:\\v2rayN\\v2rayN")
    parser.add_argument("--rules", default=str(default_rules_path()), help="routing rules JSON path")
    args = parser.parse_args()

    result = apply_route(Path(args.base), Path(args.rules))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
