# Redmi 10X 5G mainline Linux

Mainline Linux bring-up work for the Xiaomi Redmi 10X 5G (`atom`,
`M2004J7AC`, MediaTek MT6873 / Dimensity 820).

This is a hardware-porting and validation repository. It is not an Android
kernel port. Android data and executables, when discussed, are used only as
read-only hardware-test fixtures.

## Current status

- Baseline: Linux stable `v6.18.59`.
- UFS host/PHY, partition discovery, repeated reads, ext4 read-only mounts and
  file access have been validated on hardware.
- USB2 MTU3/CDC ACM bidirectional data transfer and xHCI controller/root-hub
  initialization have been validated on hardware.
- UART clocks, MT6359/PWRAP, I2C5/MT6360 and the minimal MT6873 power-domain
  providers have hardware evidence.
- Display Stage A passed: MIPI TX PHY and DSI host bind, the DSI IRQ is
  registered, MMSYS DSI clocks are acquired and the DISP power domain is
  attached.
- Display Stage B panel attachment is prepared but has not yet been validated
  against a freshly compiled DTB.
- Display Stage C0/C1 SMI, LARB and main IOMMU providers passed on hardware.
- Display Stage C2a OVL/RDMA providers bind on hardware, attach to the expected
  LARBs and a shared IOMMU group, and remain behind the no-DRM-card boundary.
- Display Stage C2b V62 reached all OVL/RDMA/DSI/panel providers but exposed a
  missing MT6873 disp-mutex component mapping before DRM bind. Patch 0038
  fixed that mapping and V63 bound DRM, `/dev/dri/card0` and `/dev/fb0`.
  V63 then exposed a missing DSI0 mutex module bit: white framebuffer writes
  completed, but vblank timed out and RDMA generated no frame interrupts.
  Patch 0039 added the vendor-confirmed DSI0 mutex input, but V64 showed the
  same failure. Patches 0040/0041 now add vendor-backed MT6873 OVL start
  settings and the correct 35840-byte RDMA FIFO. V65 passed CI and static
  checks, but hardware validation reproduced the same vblank/RDMA failure.
  A diagnostic-only V66 register-dump image is prepared for the next test.

See [docs/STATUS.md](docs/STATUS.md) for completed and pending work, and
[docs/VALIDATION-HISTORY.md](docs/VALIDATION-HISTORY.md) for evidence limits.

## Repository contents

```text
mainline/mt6873-atom-usb.dts       formal atom board DTS
mainline/patches/                  MT6873 kernel and binding patches
mainline/configs/                  focused driver configuration
tools/check_mt6873_usb_dts.py      source-level topology/evidence check
.github/workflows/                  focused DT check and kernel build
docs/                               public project and validation notes
```

The default branch deliberately keeps the display host and panel disabled.
Staged display work is maintained on dedicated branches.

## Build and DT validation

The GitHub workflows are authoritative because they use a clean Linux
`v6.18.59` checkout:

- `DT Check` applies all patches, compiles `mt6873-atom-usb.dtb`, runs
  `dt_binding_check`, runs a single-DTB `dtbs_check`, and checks that
  `__symbols__` survives.
- `Build Mainline` compiles `Image.gz` and the atom DTB, with warning/error
  log gates, and uploads the outputs.

For local Linux builds, keep the source and build output on a Linux-native
filesystem. The sparse Windows reference checkout is not a Kbuild tree.

## Evidence policy

Compilation, DTB generation, bootloader handoff, kernel boot, driver probe,
hardware functionality, and suspend/resume are distinct evidence levels.
None of them implies the next.

Do not claim:

- UFS writes, encrypted userdata, or UFS suspend/resume are working;
- external USB devices enumerate through xHCI;
- USB3 gadget, hotplug or role switching is working;
- the panel attaches or the screen works before Stage B is actually tested;
- IOMMU, GPU, camera, audio or multimedia work because their nodes compile.

## Deliberately excluded

This repository does not contain:

- device serial numbers or personal device logs;
- ROM/rootfs images, boot images, recovery images or partition dumps;
- vendor `vendor-base.dtb` or vendor overlay binary fixtures;
- private repository history;
- Android/P2 build output, cached artifacts or credentials.

The text symbol manifest needed for source-level vendor-overlay compatibility
checks remains included. Binary overlay execution must be performed in the
private validation environment.

## License

Files retain their upstream SPDX identifiers where present. New porting code
and documentation are provided under GPL-2.0-only; see [LICENSE](LICENSE).
