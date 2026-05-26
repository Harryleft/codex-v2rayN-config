# Codex v2rayN Config

This repository contains a Codex Skill for safely configuring v2rayN on Windows so Codex/OpenAI traffic remains usable while domestic, LAN, and speedtest traffic goes direct.

## Ask AI To Use The Skill

Install or reference the Skill in `skills/v2rayn-routing-config`, then ask your AI agent:

```text
Use $v2rayn-routing-config to configure my v2rayN. My v2rayN path is <v2rayN-root>.
```

After the AI applies the configuration, open v2rayN and click:

```text
重启服务
```

Then ask:

```text
Use $v2rayn-routing-config to verify my v2rayN routing. My v2rayN path is <v2rayN-root>.
```

## What The Skill Does

- Keeps TUN enabled.
- Does not close v2rayN.
- Does not kill `v2rayN.exe`, `sing-box.exe`, or `xray.exe`.
- Backs up `guiConfigs\guiNDB.db` and `guiConfigs\guiNConfig.json`.
- Writes a routing profile named `V3-绕过大陆 + 测速直连`.
- Routes domestic domains, domestic IPs, LAN traffic, and speedtest services to `direct`.
- Leaves unmatched foreign traffic on `proxy`.
- Avoids writing nodes, subscription URLs, UUIDs, passwords, private keys, or server credentials.

## Skill Location

```text
skills/v2rayn-routing-config
```

The bundled rules are in:

```text
skills/v2rayn-routing-config/references/v2rayn-routing-rules.json
```

## Manual Script Use

Agents should usually call the Skill, but the scripts can also be run directly:

```powershell
python .\skills\v2rayn-routing-config\scripts\apply_v2rayn_route.py --base "<v2rayN-root>"
```

After clicking `重启服务` in v2rayN:

```powershell
python .\skills\v2rayn-routing-config\scripts\verify_v2rayn_route.py --base "<v2rayN-root>"
```

Expected verification:

- `HasSpeedtestRule`: `true`
- `LastOutbound`: `proxy`
- `LastPort`: `0-65535`
- `GuiRoutingIndexId`: `v3-whitelist-speedtest-direct`
