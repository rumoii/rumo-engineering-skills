# Rumo Linux Hardware Inventory

Collect Linux hardware facts without changing the target. Produce auditable raw evidence and a short Simplified Chinese configuration summary suitable for direct chat delivery.

## Connection Boundary

Before connecting, confirm the target host, port, user, environment purpose, and SSH host fingerprint. Access only an environment the user has identified and authorized. Treat production as read-only unless the user explicitly authorizes a separate state-changing task.

Choose the SSH client in this order:

1. Use the system OpenSSH client when available.
2. On Windows, fall back to an existing `plink` on `PATH` or at a path the user names.
3. If neither client is available, report the missing prerequisite and stop.

Do not install, download, bundle, or distribute Plink. The agent's interactive terminal handles the SSH session, first-use fingerprint confirmation, password prompts, optional read-only `sudo` prompts, and segmented command execution. Passwords must appear only in a visible interactive prompt. Never place credentials in command arguments, scripts, environment variables, profiles, reports, or chat.

Read [collection-commands.md](collection-commands.md) before collecting evidence. Run ordinary-permission commands first. Use only an already available `sudo` path for read-only DMI or SMART queries when the additional facts are needed and the user can complete the prompt interactively.

## Remote Safety Rules

- Execute only read-only queries.
- Do not install or upgrade packages.
- Do not edit configuration, create remote files, change passwords, operate services, reboot, or delete anything.
- Treat a missing command, denied permission, empty field, unsupported device, and invalid sensor value as distinct evidence gaps.
- Do not infer facts that the command output does not prove.

## Result Files

For each target, keep exactly these two local result files:

- `Linux硬件信息采集_<host>_原始记录.txt`
- `Linux硬件信息采集_<host>_设备配置.txt`

The raw record must preserve the command evidence needed to audit the summary and may contain sensitive asset identifiers. It must not contain passwords or terminal control sequences.

Keep the legacy file `Linux硬件信息采集_<host>_报告.txt` by default; generating the two new files does not authorize deleting it. Remove that exact path only when the user explicitly requests cleanup, and then follow `rumo-filesystem-safety`. Never use a wildcard or remove another host's file.

## Concise Summary Rules

Write Simplified Chinese plain text in this fixed field order:

1. CPU
2. CPU 主频
3. 内存
4. 硬盘
5. 主板
6. 网卡
7. 系统
8. 内核
9. Swap
10. 虚拟化
11. 未读取到

Use the last IPv4 octet in the title when the target is an IPv4 address, for example `197 设备配置如下：`.

- CPU: derive cores and threads from consistent online CPU topology. If socket or core fields conflict, report only the defensible online core/thread counts and preserve the conflict in the raw record. Normalize confirmed Phytium models to the Chinese brand name `飞腾`.
- CPU frequency: use a valid reported maximum or current frequency. Otherwise write `未读取到`.
- Memory: prefer populated DMI modules for capacity, generation, manufacturer, and speed. Fall back to rounded physical memory only when DMI is unavailable.
- Disk: write `SSD` only when SMART or equivalent device identity explicitly confirms a solid-state device. `ROTA=0` alone means `系统识别为非旋转盘`. Report SMART success only for disks whose health output explicitly passed.
- Network: count physical Ethernet interfaces separately from confirmed speed. Report speed and duplex only for an interface with a confirmed active link.
- Missing data: list unresolved asset facts without guesses, recommendations, or performance conclusions.

## Chat Handoff

Read the completed `Linux硬件信息采集_<host>_设备配置.txt` and reproduce its entire contents verbatim in the final chat response as plain text. Do not shorten it, convert it to a Markdown table, or introduce claims that differ from the file. Separately identify the two saved file paths and state that the remote collection was read-only without exposing credentials.
