---
name: v2rayn-routing-config
description: Safely configure v2rayN on Windows for Codex/OpenAI-friendly TUN routing. Use when a user asks to set up v2rayN, keep TUN enabled, apply "bypass mainland China plus speedtest direct" routing rules, make domestic/LAN/speedtest traffic direct, keep foreign/OpenAI traffic proxied, verify v2rayN runtime routing, or recover from Codex connectivity problems caused by v2rayN routing.
---

# v2rayN Routing Config

## Overview

Configure an existing Windows v2rayN installation without closing v2rayN or modifying sensitive node data. The skill writes a routing profile named `V3-绕过大陆 + 测速直连`, keeps TUN usable for Codex, and leaves service restart to the user.

## Safety Rules

- Do not close v2rayN.
- Do not kill `v2rayN.exe`, `sing-box.exe`, or `xray.exe`.
- Always back up `guiConfigs/guiNDB.db` and `guiConfigs/guiNConfig.json` before writing.
- Do not write or print nodes, subscription URLs, UUIDs, passwords, private keys, or server credentials.
- Preserve TUN when the user depends on TUN for Codex connectivity.
- After writing, ask the user to click `重启服务` in v2rayN. Do not restart processes yourself unless the user explicitly asks.

## Apply Routing

1. Ask for or discover the v2rayN root directory. Common paths contain `guiConfigs`, `binConfigs`, and `v2rayN.exe`.
2. Confirm these files exist under the root:
   - `guiConfigs/guiNDB.db`
   - `guiConfigs/guiNConfig.json`
   - `binConfigs/config.json`
3. Run `scripts/apply_v2rayn_route.py --base <v2rayN-root>`.
4. Report the backup stamp and active route ID.
5. Tell the user to click `重启服务` in v2rayN.

Example:

```powershell
python skills\v2rayn-routing-config\scripts\apply_v2rayn_route.py --base "<v2rayN-root>"
```

If the system `python` command is unavailable, use any available Python 3 runtime.

## Verify After Restart

After the user confirms they clicked `重启服务`, run:

```powershell
python skills\v2rayn-routing-config\scripts\verify_v2rayn_route.py --base "<v2rayN-root>"
```

Expected checks:

- `HasSpeedtestRule` is `True`
- `LastOutbound` is `proxy`
- `LastPort` is `0-65535`
- the active GUI route ID is `v3-whitelist-speedtest-direct`

Network spot checks are optional and may require user approval. Use domestic, speedtest, and foreign test URLs to compare routing behavior; do not treat an OpenAI root-path HTTP error as a routing failure if the host is reachable.

## Rollback

If Codex or browser traffic breaks, first ask the user to switch back to the previous v2rayN route in the UI, commonly `V3-绕过大陆(Whitelist)`.

If file rollback is required, restore the timestamped backups created by `apply_v2rayn_route.py`:

```powershell
Copy-Item -LiteralPath "<backup guiNDB.db>" -Destination "<v2rayN-root>\guiConfigs\guiNDB.db" -Force
Copy-Item -LiteralPath "<backup guiNConfig.json>" -Destination "<v2rayN-root>\guiConfigs\guiNConfig.json" -Force
```

Then ask the user to click `重启服务`.

## Resources

- `scripts/apply_v2rayn_route.py`: backs up and writes the routing profile.
- `scripts/verify_v2rayn_route.py`: verifies active GUI and runtime routing state.
- `references/v2rayn-routing-rules.json`: bundled routing rules.
