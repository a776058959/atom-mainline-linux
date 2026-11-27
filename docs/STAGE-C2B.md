# Display Stage C2b: direct DRM pipeline

## Scope

Stage C2b registers MT6873 MMSYS as the DRM component master and uses the
vendor-confirmed direct primary path:

```text
OVL0 -> RDMA0 -> DSI0
```

OVL0-2L remains enabled as a probe-tested component but is intentionally not
part of this first CRTC path. The direct path uses only the four OVL0 layers.

## Source evidence

The Xiaomi MT6873 source at commit
`5339a9bd98f0a3b350855a0c23f12f6ba20eb266` defines
`DDP_SCENARIO_PRIMARY_DISP` as:

```text
OVL0 -> RDMA0 -> PWM0 -> DSI0
```

Its PQ stages, including COLOR, CCORR, AAL, GAMMA, POSTMASK and DITHER, are
inside an `#if 0` block for this path. Mainline MediaTek DRM does not model the
vendor PWM block as a DDP component, so C2b removes only that non-DDP step.

The existing MT6873 MMSYS route data already describes:

```text
OVL0  -> RDMA0
RDMA0 -> DSI0
```

The vendor OVL connection code additionally requires
`MMSYS_OVL_CON` field `CON_OVL0 = 1` for a direct OVL0-to-RDMA connection.
Patch 0037 adds that route using the vendor-defined `0xf04` register and the
same two-bit field.

## Driver data

Patch 0037 adds:

```c
static const unsigned int mt6873_mtk_ddp_main[] = {
	DDP_COMPONENT_OVL0,
	DDP_COMPONENT_RDMA0,
	DDP_COMPONENT_DSI0,
};
```

and registers it for `mediatek,mt6873-mmsys` in the DRM component-master
lookup table. The existing MT6873 MMSYS binding and clock-provider match are
unchanged.

## Why this is a separate stage

C2a proved provider probe and IOMMU consumer attachment, but no device had yet
allocated a display buffer or enabled a pixel clock. C2b is the first stage
that can:

- bind all components into one DRM device;
- allocate and map a framebuffer through OVL0/IOMMU;
- enable OVL0, RDMA0 and DSI clocks;
- program MMSYS routes and the display mutex;
- run panel prepare/display-on and DSI video output.

This makes it a much stronger hardware test and a higher-risk failure boundary.

## Expected evidence

If the path is correct, the recovery diagnostic should capture:

- `mediatek-drm` component-master bind;
- `/dev/dri/card0` and `/sys/class/drm/card0`;
- nonzero OVL0, RDMA0 and DSI clock enable counts;
- enabled DISP power domain with OVL0/RDMA0/DSI consumers;
- no display driver Oops, BUG, WARNING or deferred probe;
- DSI and RDMA interrupt activity if framebuffer setup performs a mode set;
- panel prepare and MT6359 VIBR regulator enable;
- a scripted all-white framebuffer write when `/dev/fb0` exists;
- either visible output or a later, explicitly identified blocker.

A controlled panic remains the log-collection mechanism. Screen output is not
assumed merely because the DRM device registers.

## Initial validation gate

- patch 0037 applies to clean Linux `v6.18.59`;
- source-level topology checker passes;
- existing OVL, RDMA, DSI and panel bindings still pass;
- `dt_binding_check` and focused `dtbs_check` pass;
- the kernel and DTB build without compiler warnings;
- recovery-only image and partition backups are revalidated before any flash.

Hardware testing requires a new explicit flashing authorization.

## Public CI result

`DT Check` run `46019618614` and `Build Mainline` run `46019616018` both
completed successfully on commit `e85a7ab`.

- all 37 patches applied to a clean Linux `v6.18.59` tree;
- the source-level topology checker passed;
- `dt_binding_check` and focused `dtbs_check` passed without warning/error;
- `Image.gz` and the atom DTB built without compiler warning/error;
- the DTB remained unchanged because C2b changes kernel driver data only.

Generated outputs:

```text
Image.gz size    15309885
Image.gz sha256  40257fc290f2fdf86e865b50db7b2548c681bae1093ad3f59661cb538db85c82

DTB size         59946
DTB sha256       81c7fe8024106e657f51bf338869d439f979f97790003744bb98b91568187b25
```

The V62 recovery-only diagnostic was assembled from these exact outputs and
passed 59 static checks:

```text
ramdisk sha256  2190b831bdf1095c15903d6f3c94e4f683fb8e4c50af887505fc7a7a0de3669b
image sha256    0eb1ddfebced6c4ab3dfec2ca6534e4e68d405814eb8c47b0ed20b6d751db41f
image size      16050176
```

The V62 ramdisk waits for early and settled DRM state, writes one all-white
framebuffer only when `/dev/fb0` exists, snapshots the connector/clock state,
and retains a 60-second watchdog around the write and a 15-second framebuffer
write timeout.

The flasher dry-run passed against the current Android device and the original
recovery/protected partition hashes. The image has not yet been written.
