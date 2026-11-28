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
- Display Stage B panel attachment passed on hardware: the S6E8FC01 driver
  bound, acquired its VIBR regulator and GPIOs, and completed
  `mipi_dsi_attach()`.
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
  V66 completed in hardware: the panel initialization DCS traffic raised the
  DSI IRQ count to 31, while RDMA IRQ remained zero, and the framebuffer write
  still timed out waiting for vblank. The `/dev/mem` MMIO reads were blocked by
  strict devmem, so patches 0042/0043 now set the vendor-confirmed MT6873 OVL
  clock bits and add a read-only kernel-side register snapshot. V67 confirmed
  those bits and the MMSYS routes in hardware, but OVL reported abnormal SOF
  and frame underrun while RDMA reported FIFO underflow and still generated no
  IRQ. Patches 0044-0047 now port the vendor real-time OVL read thresholds,
  LARB0 WRR values, zero video-mode RDMA threshold and expanded SMI/IOMMU
  diagnostics. V68 built successfully and its recovery-only image was written
  and read back byte-for-byte. Hardware confirmed every V68 OVL/RDMA tuning
  value, but LARB0 still retained default OSTD/WRR values and the underflow
  remained. Patch 0048 now forces MT6873 LARB configuration at IOMMU component
  bind and keeps it active until unbind. V69 hardware execution still read
  the same LARB defaults, while `clk_summary` exposed the cause: the four
  MT6873 SMI clocks were registered as dummy gates, despite the vendor power
  domain clearing the corresponding MMSYS gates. Patch 0049 converts those
  four clocks to real gates. V70 then produced visible Linux console output,
  a correctly colored Linux penguin and a pure-white framebuffer on hardware.
  The vblank timeouts and primary OVL/RDMA underflow flags disappeared. V71
  kept the same kernel and completed six visible white/gray framebuffer
  updates without corrupt colors, hangs or renewed underflow. V72 then opened
  `card0` from an independent userspace client, enabled atomic/universal-plane
  capabilities and allocated/destroyed a DRM dumb buffer successfully. V73
  completed real double-buffered KMS page flips to visible red and blue frames,
  received all flip-complete events and restored the original framebuffer. V74
  completed 600 additional page flips with stable registers and no display
  errors; the user directly observed red, blue, slow red/blue block changes,
  restoration of the original framebuffer and the final white frame. Patch
  0050 now exposes the panel's vendor-confirmed 11-bit DCS brightness interface
  as a standard backlight device. Linux `v6.18.59` build run `46148455487`
  passed with zero compiler warnings/errors, and V75 was written only to
  `recovery` with matching candidate readback. V75 hardware validation passed:
  the `14010000.dsi.0` backlight exposed `0..2047`, all seven requested levels
  read back exactly, the user observed normal brightness behavior, and the
  display chain remained active without vblank timeout or display fault.

See [docs/STATUS.md](docs/STATUS.md) for completed and pending work, and
[docs/VALIDATION-HISTORY.md](docs/VALIDATION-HISTORY.md) for evidence limits.
The previously working downstream Arch/display path is documented in
[docs/VENDOR-ARCH-DISPLAY-ROUTE.md](docs/VENDOR-ARCH-DISPLAY-ROUTE.md).

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
