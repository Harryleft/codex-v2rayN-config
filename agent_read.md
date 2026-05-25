# Codex v2rayN TUN 路由配置说明

本文档给 Codex 或其他 Agent AI 使用，用于在 Windows 电脑上配置 v2rayN：保留 TUN 模式，让 Codex 稳定可用，同时让局域网、国内流量和测速服务尽量直连。

## 目标效果

| 流量类型 | 出站 |
| --- | --- |
| Codex / OpenAI 未命中流量 | `proxy` 兜底 |
| 国外网站 | `proxy` |
| 国内域名 | `direct` |
| 国内 IP | `direct` |
| 局域网 | `direct` |
| Speedtest / Fast / nPerf / M-Lab | `direct` |

注意：这个方案不是“只有 Codex 进入 TUN”。v2rayN 的 TUN 开启后通常会接管全局流量，然后由路由规则决定 `proxy`、`direct` 或 `block`。

## 操作原则

1. 不要关闭 v2rayN。
2. 不要杀掉 `v2rayN.exe`、`sing-box.exe`、`xray.exe`。
3. 修改前必须备份配置。
4. 不要写入节点、订阅地址、UUID、密码、私钥等敏感信息。
5. 如果用户当前只有开启 TUN 才能使用 Codex，必须保留 TUN。

## 需要写入的规则

规则文件在本仓库：

```text
v2rayn-routing-rules.json
```

推荐规则名称：

```text
V3-绕过大陆 + 测速直连
```

## 常见配置路径

优先通过 v2rayN 快捷方式定位真实目录：

```powershell
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\v2rayN.lnk")
$shortcut.TargetPath
$shortcut.WorkingDirectory
```

常见目录示例：

```text
S:\Program Files\v2rayN
S:\Program Files\v2rayN\guiConfigs
S:\Program Files\v2rayN\binConfigs
```

关键文件：

```text
guiConfigs\guiNDB.db
guiConfigs\guiNConfig.json
binConfigs\config.json
```

## 安全写入流程

以下流程不会关闭 v2rayN。写入后需要用户在 v2rayN 里手动点一次“重启服务”才能加载新规则。

```powershell
$base = "S:\Program Files\v2rayN"
$gui = Join-Path $base "guiConfigs"
$db = Join-Path $gui "guiNDB.db"
$config = Join-Path $gui "guiNConfig.json"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"

Copy-Item -LiteralPath $db -Destination "$db.bak-$stamp" -Force
Copy-Item -LiteralPath $config -Destination "$config.bak-$stamp" -Force
```

然后用 SQLite 写入 `RoutingItem`：

| 字段 | 值 |
| --- | --- |
| `Id` | `v3-whitelist-speedtest-direct` |
| `Remarks` | `V3-绕过大陆 + 测速直连` |
| `RuleSet` | `v2rayn-routing-rules.json` 的 JSON 文本 |
| `RuleNum` | 规则数量 |
| `Enabled` | `1` |
| `IsActive` | `1` |

同时把其他 `RoutingItem.IsActive` 设为 `0`，再把 `guiNConfig.json` 中的：

```json
{
  "RoutingBasicItem": {
    "RoutingIndexId": "v3-whitelist-speedtest-direct"
  }
}
```

更新为新规则 ID。

## Python 写入示例

在仓库目录执行，或把 `$rulesPath` 改成 `v2rayn-routing-rules.json` 的绝对路径。

```powershell
$base = "S:\Program Files\v2rayN"
$rulesPath = "v2rayn-routing-rules.json"

@"
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

base = Path(r"$base")
rules_path = Path(r"$rulesPath")
gui = base / "guiConfigs"
db_path = gui / "guiNDB.db"
config_path = gui / "guiNConfig.json"
route_id = "v3-whitelist-speedtest-direct"
route_name = "V3-绕过大陆 + 测速直连"
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

for path in (db_path, config_path):
    shutil.copy2(path, path.with_name(path.name + f".bak-{stamp}"))

rules = json.loads(rules_path.read_text(encoding="utf-8"))
rule_set = json.dumps(rules, ensure_ascii=False, separators=(",", ":"))

con = sqlite3.connect(db_path, timeout=10)
cur = con.cursor()
cur.execute("update RoutingItem set IsActive = 0")
cur.execute("delete from RoutingItem where Id = ?", (route_id,))
cur.execute(
    """insert into RoutingItem
       (Id, Remarks, Url, RuleSet, RuleNum, Enabled, Locked, CustomIcon, CustomRulesetPath4Singbox,
        DomainStrategy, DomainStrategy4Singbox, Sort, IsActive)
       values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    (route_id, route_name, "", rule_set, len(rules), 1, 0, "", "", None, None, 1, 1),
)
con.commit()
con.close()

config = json.loads(config_path.read_text(encoding="utf-8-sig"))
config.setdefault("RoutingBasicItem", {})["RoutingIndexId"] = route_id
config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"backup_stamp={stamp}")
print(f"active_route={route_id}")
"@ | python -
```

## 生效方式

让用户在 v2rayN 中点击：

```text
重启服务
```

不要直接退出 v2rayN。如果用户当前依赖 TUN 使用 Codex，退出 v2rayN 可能导致 Agent 断网。

## 验证方式

```powershell
$runtime = "S:\Program Files\v2rayN\binConfigs\config.json"
$j = Get-Content -LiteralPath $runtime -Raw | ConvertFrom-Json
$rulesText = $j.routing.rules | ConvertTo-Json -Depth 30

[PSCustomObject]@{
  LastWrite = (Get-Item -LiteralPath $runtime).LastWriteTime
  RuleCount = $j.routing.rules.Count
  HasSpeedtestRule = $rulesText -match "speedtest|ookla|fast.com|nperf|measurementlab"
  LastOutbound = ($j.routing.rules | Select-Object -Last 1).outboundTag
  LastPort = ($j.routing.rules | Select-Object -Last 1).port
}
```

期望结果：

| 检查项 | 期望 |
| --- | --- |
| `HasSpeedtestRule` | `True` |
| `LastOutbound` | `proxy` |
| `LastPort` | `0-65535` |
| Codex 发消息 | 成功 |
| Speedtest 网站 | 可打开 |

## 回滚

如果 Codex 无法联网，让用户先切回原本可用的 `V3-绕过大陆(Whitelist)`。

也可以从备份恢复：

```powershell
Copy-Item -LiteralPath "S:\Program Files\v2rayN\guiConfigs\guiNDB.db.bak-YYYYMMDD-HHMMSS" -Destination "S:\Program Files\v2rayN\guiConfigs\guiNDB.db" -Force
Copy-Item -LiteralPath "S:\Program Files\v2rayN\guiConfigs\guiNConfig.json.bak-YYYYMMDD-HHMMSS" -Destination "S:\Program Files\v2rayN\guiConfigs\guiNConfig.json" -Force
```

恢复后让用户在 v2rayN 中点击“重启服务”。
