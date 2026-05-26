import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path


ROUTE_ID = "v3-whitelist-speedtest-direct"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verify(base: Path) -> dict:
    db_path = base / "guiConfigs" / "guiNDB.db"
    config_path = base / "guiConfigs" / "guiNConfig.json"
    runtime_path = base / "binConfigs" / "config.json"

    gui_config = read_json(config_path)
    runtime = read_json(runtime_path)
    rules = runtime.get("routing", {}).get("rules", [])
    rules_text = json.dumps(rules, ensure_ascii=False).lower()
    last_rule = rules[-1] if rules else {}

    con = sqlite3.connect(db_path, timeout=10)
    try:
        cur = con.cursor()
        active_rows = cur.execute(
            "select Id, Remarks, RuleNum, Enabled, IsActive from RoutingItem where IsActive = 1"
        ).fetchall()
    finally:
        con.close()

    return {
        "RuntimeConfig": str(runtime_path),
        "RuntimeLastWrite": datetime.fromtimestamp(runtime_path.stat().st_mtime).isoformat(timespec="seconds"),
        "RuntimeRuleCount": len(rules),
        "HasSpeedtestRule": any(
            token in rules_text for token in ("speedtest", "ookla", "fast.com", "nperf", "measurementlab")
        ),
        "LastOutbound": last_rule.get("outboundTag") or last_rule.get("outbound"),
        "LastPort": last_rule.get("port"),
        "GuiRoutingIndexId": gui_config.get("RoutingBasicItem", {}).get("RoutingIndexId"),
        "ExpectedRouteId": ROUTE_ID,
        "ActiveGuiRoutes": active_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify v2rayN routing profile and runtime rules.")
    parser.add_argument("--base", required=True, help="v2rayN root directory, e.g. C:\\path\\to\\v2rayN")
    args = parser.parse_args()
    print(json.dumps(verify(Path(args.base)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
