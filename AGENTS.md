# Repository instructions

## Scope

This repository contains mainline Linux support for the Redmi 10X 5G
(`atom`, `M2004J7AC`, MT6873).

- Target mainline Linux, not an Android kernel or full Android runtime.
- MT8192 is a reference platform only.
- Never treat MT8192 constants as MT6873 facts without source or hardware
  evidence.

## Working rules

1. Inspect the local source, bindings, Git history and related documents
   before changing code.
2. Prefer existing upstream MediaTek mechanisms and bindings.
3. Separate confirmed facts, inferred causes and unverified hypotheses.
4. Keep changes minimal and independently reviewable.
5. Do not invent clock IDs, reset IDs, register values, power domains, pin
   functions or compatible strings.
6. Do not treat a successful DTC/schema check as proof of boot or hardware
   operation.
7. Report compile, DTB creation, bootloader handoff, kernel boot, probe and
   hardware function as separate evidence levels.
8. Never claim an unexecuted build, boot, probe or hardware test succeeded.
9. Do not commit generated images, device logs, ROM/rootfs contents, vendor
   binary DTBs/DTBOs, caches or credentials.
10. Do not use `git reset --hard`, `git clean`, force-push or destructive
    partition operations without explicit user approval.

## Test rules

- Use the matching Linux stable version for patch and schema checks.
- Run `git diff --check`.
- Run the repository DT checker.
- Run `dt_binding_check` and focused `dtbs_check` when the workflow or a full
  Linux tree is available.
- Treat physical-device testing as a separate, explicitly authorized step.
- Restore original boot/recovery/misc/dtbo state after recovery-only tests.

## Public repository hygiene

- No device serial numbers, usernames or personal filesystem paths.
- No tokens, cookies, private keys or GitHub credentials.
- No proprietary firmware, ROMs, rootfs archives or partition dumps.
- No private repository history or release URLs.
