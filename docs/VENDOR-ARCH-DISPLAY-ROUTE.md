# Vendor 4.14 Arch Linux boot and display route

This note records how the previously working downstream 4.14 Linux setup ran
Arch Linux ARM and drove the Redmi 10X 5G panel. It is a reference for the
mainline port, not a claim that the downstream binaries or ABI can be reused
unchanged.

## Boot route

The working route did not boot Arch directly as an Android `boot` replacement:

1. A downstream 4.14 `Image.gz` was packed with a custom initramfs into a
   recovery-sized Android boot image.
2. The image was written to `recovery`, and LK was directed there with a
   `boot-recovery` BCB in `misc`.
3. The kernel used the device's vendor DTB/DTBO and initialized the downstream
   drivers.
4. The initramfs found the Arch Linux ARM root filesystem on `cust`, mounted it
   and performed `switch_root`.
5. The initramfs cleared the BCB so a failed Linux boot fell back to Android on
   the next reset.

This LK rejected the normal `fastboot boot` workflow in practice: the command
returned OKAY but did not hand off the supplied image. The Android `boot`
partition was kept as the recovery path.

The successful userspace used a downstream 4.14.336 kernel built from the
`mt6873-dev/android_kernel_xiaomi_mt6875` family, not upstream Linux. Replacing
that kernel with the exact factory binary did not complete the same initramfs
route because the factory kernel's tty/init semantics differed. The exact
factory binary and the working self-built 4.14 binary therefore must not be
treated as interchangeable evidence.

## Display stack

The downstream kernel provided the complete MediaTek display driver stack:

- `CONFIG_DRM=y` and `CONFIG_DRM_MEDIATEK=y`;
- the MT6873 MMSYS, mutex, SMI, IOMMU/LARB, OVL, RDMA, DSI, MIPI TX and PWM
  devices from the vendor DTB/DTBO;
- the vendor LCM/panel data and initialization table from the device display
  overlay;
- runtime PM, clock, power-domain and IOMMU handling specific to the downstream
  ABI.

Source review of the matching MT6873 downstream family at
`Can186/Redmi10X-android11-kernel@058d3f7f74c5b0fb9a5442f7f42b8cc6a16fed98`
shows the primary DDP component list as:

```text
OVL0_2L -> OVL0 -> RDMA0 -> COLOR0 -> CCORR0 -> AAL0
        -> GAMMA0 -> POSTMASK0 -> DITHER0 -> DSI0 -> PWM0
```

The panel timing and initialization data are selected through the vendor
`disp_lcm_probe()` path, then programmed through the vendor DDP/DSI code. This
is not an upstream `simple-framebuffer` or an Arch-provided hardware driver.

The vendor power-domain code clears MMSYS CG0 bits 11, 17 and 27 plus CG1 bit 0
for `SMI_INFRA`, `SMI_COMMON`, `SMI_GALS` and `SMI_IOMMU` before LARB traffic.
The same vendor display power-on sequence also enables the display module
clocks. Those top-level SMI gates are therefore part of the minimum display
initialization, not optional tuning.

The gate offsets, bits and set/clear/status register layout are directly
confirmed by the vendor clock driver and power-on callback. The provisional
mainline gate descriptors use `disp_sel` as their parent because the current
minimal MT6873 clock tree has no separate SMI parent. This affects rate
reporting and is still a hypothesis to verify; it does not change the confirmed
gate-enable bits.

## What Arch Linux actually used

The kernel first exposed the panel as a DRM DSI connector and used DRM fbdev
emulation plus `FRAMEBUFFER_CONSOLE` for the text console. The downstream
kernel reported a 1080x2400 `DSI-1` connector and a 4.14 `/dev/fb0`.

Later Weston testing used the standard DRM ioctls with `--renderer=pixman`.
`modetest -M mediatek -s 28:1080x2400` successfully enabled visible output.
Weston could display a framebuffer and terminal, but the vendor primary plane
rejected XRGB8888 for the EGL/GBM path, so GPU rendering was not usable.

Writing directly to the downstream `/dev/fb0` was not a reliable scanout test:
that framebuffer advertised unusual dimensions (`1088x7200` in the observed
system), while the active display was controlled by the DRM CRTC. The useful
functional evidence is the enabled DSI connector, successful modeset and
visible Weston output, not whether the fbdev memory appeared to change.

The current Android factory kernel provides a direct hardware cross-check:

```text
/sys/class/drm/card0/device/driver -> mediatek-drm
card0-DSI-1 status                 -> connected
card0-DSI-1 enabled                -> enabled
fb0 mode                          -> U:1080x2400p-0
/proc/version                      -> 4.14.186-perf
```

## Relationship to the mainline port

The downstream success came from having the entire MT6873 platform glue and
vendor DDP data, not from Arch Linux itself. The mainline port must reproduce
the required order explicitly:

1. DIS power domain;
2. `SMI_INFRA`, `SMI_COMMON`, `SMI_GALS` and `SMI_IOMMU` gates;
3. SMI common/LARB programming;
4. IOMMU and LARB attachment;
5. OVL/RDMA/MMSYS resources and routes;
6. DSI host and MIPI PHY/panel.

The mainline Stage C2b path currently tests the smaller direct route
`OVL0 -> RDMA0 -> DSI0`. That reduction can be valid only after its MMSYS route
and memory path are proven on MT6873. It does not inherit the downstream full
PQ path or the downstream power/clock sequence automatically.

At the time of this note, V69 proved that the SMI clocks were registered as
dummy gates even though consumers requested them. Patch 0049 maps the four
IDs to real MMSYS gates. V70 validated that change on hardware: all four gates
reported `Y`, LARB0 retained its vendor configuration, vblank timeouts
disappeared and the physical panel showed colored Linux console output plus a
white framebuffer. V71 then displayed six timed white/gray framebuffer updates
without visual or logged display faults. V72/V73 then opened the mainline DRM
node as an independent KMS client and completed real double-buffered page
flips to visible red and blue framebuffers.
