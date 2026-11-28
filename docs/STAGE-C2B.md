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

## V62 hardware result

V62 was written to the recovery partition and booted. The directly observed
state was:

- OVL0, OVL0-2L, RDMA0, DSI, DSI PHY and the panel driver bound;
- SMI, LARB and IOMMU providers stayed bound;
- OVL0, OVL0-2L and RDMA0 remained in IOMMU group 0 with type `DMA`;
- no display driver Oops, BUG, warning, probe failure or deferred probe;
- the DRM master did not bind and no DRM card or framebuffer device appeared.

The decisive log lines were:

```text
mediatek-drm mediatek-drm.7.auto: Adding component match for /soc/ovl@14005000
mediatek-drm mediatek-drm.7.auto: Adding component match for /soc/rdma@14007000
mediatek-drm mediatek-drm.7.auto: Adding component match for /soc/dsi@14010000
mediatek-drm mediatek-drm.7.auto: Failed to find disp-mutex node
```

`mtk_drm_probe()` classifies sibling nodes through `mtk_ddp_comp_dt_ids[]`.
Patch 0023 added the MT6873 mutex compatible to the mutex driver and binding,
but the DRM-local table had no corresponding `MTK_DISP_MUTEX` entry. The mutex
node therefore could not become `private->mutex_node`, and probe returned
`-ENODEV`. Patch 0038 adds only that mapping.

The absence of a white frame is explained by the failed DRM bind and is not
evidence about panel timing, DSI PLL lock or RDMA traffic. The original recovery
was restored and hash-verified after log collection.

Evidence:

```text
D:\820Linux\dumps\drm-pipeline-v62-20261127\20261127-233135\
console-ramoops-2 sha256 eab0343daf7af3d804f896c45e1ac9f7bc7c67570e892430e924d4340c961539
```

## V63 build

Patch 0038 was validated against a clean Linux `v6.18.59` tree:

```text
DT Check run        46027955491  success
Build Mainline run  46027960323  success
Image.gz sha256     5c1b30891b30d0d3f72900a136819bdce91029ccf29181f6594748e7f9febca1
DTB sha256          81c7fe8024106e657f51bf338869d439f979f97790003744bb98b91568187b25
```

The V63 recovery-only image reuses the validated first-frame diagnostic and
changes only the version marker plus the kernel:

```text
image size      16050176
image sha256    8fa1d18ba959cdc6c9592a0fcc9a2d878f2f77a7581c19087180ee457444f2d6
ramdisk sha256  6c91fbaa6030cb28b2a4c92804752e03a939638b737fe4696dcd1cbb96ce3e78
dt_table sha256 744eeb82e42e84273ea4c226b01eabc153e44efda172344385b3b545ea7e6f80
```

All 59 assembly checks passed, the flasher dry-run passed, and the recovery
restore dry-run reported `already-restored`.

## V63 hardware result

V63 was written and booted. Patch 0038 fixed the previous DRM master failure:
DRM bound OVL0, RDMA0 and DSI, `/dev/dri/card0` and `/dev/fb0` appeared, the
DSI connector was connected and enabled, and the diagnostic wrote its white
framebuffer.

The screen remained black. Three atomic commits timed out:

```text
[CRTC:59:crtc-0] vblank wait timed out
```

At the settled snapshot, OVL0 IRQ 311 had fired once while RDMA0 IRQ 313 had
never fired. OVL0, RDMA0, DSI, the MIPI TX PLL, the DISP power domain and the
VIBR regulator were enabled. This locates the failure after DRM bind but before
completed scanout.

## V64 mutex fix

Vendor `ddp_mutex.c` maps the primary path modules as:

```text
DISP_MODULE_OVL0   -> MUTEX MOD0 bit 0
DISP_MODULE_RDMA0  -> MUTEX MOD0 bit 2
DISP_MODULE_DSI0   -> MUTEX MOD0 bit 12
```

Patch 0023 added the first two MT6873 bits but omitted DSI0. Patch 0039 adds
the vendor-confirmed DSI0 bit and the topology checker now requires it.

Expected V64 evidence is a nonzero RDMA frame-end interrupt count and no
`vblank wait timed out` warning. A visible white frame remains a separate
functional result.

## V64 build

Patch 0039 passed clean-tree validation and compilation:

```text
DT Check run        46036375152  success
Build Mainline run  46036381292  success
Image.gz sha256     411e07241dc9ea0634ad40a8e230005d4e0467abaf73b53e25da635df329bfc1
DTB sha256          81c7fe8024106e657f51bf338869d439f979f97790003744bb98b91568187b25
```

The V64 recovery-only image passed all 59 assembly checks:

```text
image size      16050176
image sha256    6194f12b7fa5ea4e671a505067a663af4b0ea44fd84492bfc377165dfc6a7953
ramdisk sha256  1d36629bf44997352b6b98c1fb24e3636d640aab86dfb5e075861617b2c49d6e
dt_table sha256 744eeb82e42e84273ea4c226b01eabc153e44efda172344385b3b545ea7e6f80
```

The flasher and restore dry-runs passed against the connected
`M2004J7AC / mt6873` device. No partition has been modified.

## V64 hardware result

V64 was written and tested. Patch 0039 did not change the failure:
DRM/card/fb and the DSI connector were present, the white framebuffer write
succeeded, but vblank timed out three times and RDMA IRQ 313 stayed at zero.
The original recovery was restored and hash-verified after log collection.

## V65 OVL and RDMA data

The Xiaomi MT6873 DRM driver provides two concrete differences on the active
path:

- MT6873 RDMA FIFO is 3 KiB + 32 KiB = 35840 bytes, not MT8192's 5120 bytes;
- MT6873 OVL start sets `GCLAST_EN`, `OUTPUT_CLAMP`, and force-relay mode.

Patch 0040 adds explicit MT6873 OVL/OVL-2L driver data and start settings.
Patch 0041 adds explicit MT6873 RDMA driver data with the correct FIFO size.
The board DTS overrides `mediatek,rdma-fifo-size` with 35840.

Expected V65 evidence is again a nonzero RDMA frame-end interrupt and no
vblank timeout. Visible output remains independent.

## V65 build and flash

V65 passed CI and assembly:

```text
DT Check run        46042294627  success
Build Mainline run  46042299611  success
Image.gz sha256     6a0ae0af3a2910c4d661e568fbe4d4fd29390d079d5e86b8ae3020d1514c42dc
DTB sha256          f041bf87b0b7b9df72be2e00b274c184b19eb7ea4625b5f0211f7ddd2288d665
image size          16052224
image sha256        20f1790c090965691330c3913327d3273b31c030c01b2fe24257e958b1920571
```

All 59 assembly checks and the flash dry-run passed. The image was written to
recovery and read back byte-for-byte. `boot`, `misc` and `dtbo` retained their
original hashes. The device was not rebooted.

## V65 hardware result

V65 reproduced the same failure. RDMA IRQ remained zero, vblank timed out
three times and no white frame appeared. DSI0 mutex bit 12, the 35840-byte
RDMA FIFO and MT6873 OVL start settings did not independently unblock output.

## V66 register diagnostics

V66 keeps the exact V65 kernel and DTB and changes only the initramfs. It
captures:

- DSI and display interrupt state;
- DRM debugfs summary and atomic state;
- MMSYS route registers;
- OVL0, RDMA0, DSI and mutex0 registers;
- read-only `/dev/mem` MMIO values when available.

V66 passed all 59 assembly checks and the flash dry-run. Hardware diagnostics
have not yet run.
