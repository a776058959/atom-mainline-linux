# Project status

Baseline: Linux stable `v6.18.59`.

The default branch is a safe, all-disabled display topology. Hardware that was
validated during staged development is not automatically enabled here.

## Completed with hardware evidence

### Boot and recovery flow

- Mainline v6.18.59 boots to an initramfs using a recovery-only image.
- Diagnostic logs can be collected through pstore/expdb.
- Original recovery is restored and hash-checked after tests; protected
  partitions remain unchanged.

### UART and clocks

- MT6873 topckgen, infracfg and apmixed clock providers bind.
- UART0/UART1 bind to `mt6577-uart`; the ttyS0 console registers.

### UFS

- `ufshcd-mtk` and `ufs_mtk_phy` probe successfully.
- Three Micron UFS LUNs enumerate.
- The mainline GPT view matches all 60 Android partition names.
- Repeated 4 KiB reads are stable.
- Four `super` ext4 extents can be mounted read-only, read and unmounted
  cleanly.

Not verified: writes, journal replay, encrypted userdata, suspend/resume,
error recovery and the residual UIC `PA_TXHSADAPTTYPE` behavior.

### USB host

- `xhci-mtk` probes and creates USB2 and USB3 root hubs.
- USB PLL and SSUSB gate clocks are acquired.

Not verified: external device enumeration, real host transfers, hotplug,
role switching or suspend/resume.

### USB device

- MTU3 peripheral-only high-speed mode works.
- Type-C/PHY session and analog tuning are applied.
- Windows enumerates the CDC ACM gadget.
- Bidirectional host/device data transfer succeeds.

Not verified: USB3 gadget, other gadget functions, hotplug, role switching or
suspend/resume.

### PMIC, I2C5 and MT6360

- MT6359 regulator/MFD infrastructure probes.
- I2C5 and MT6360 MFD, charger and TCPC probe.
- Type-C port/partner registration and live I2C IRQ activity were observed.

Not verified: complete power-delivery negotiation, role reversal, VBUS
sourcing, charger current control and suspend/resume.

## Display staging

### Stage A: complete on hardware

Only these nodes are enabled in the Stage A DTB:

```text
mipi_tx0   okay
DSI host   okay
panel@0    disabled
```

Observed:

- `11e50000.dsi-phy` binds `mediatek-mipi-tx`.
- `14010000.dsi` binds `mtk-dsi`.
- DSI IRQ registration succeeds.
- MMSYS `mm_dsi0` and `mm_dsi_dsi0` are acquired.
- The DISP power domain is on and contains the DSI device.

This is not proof of PLL lock, DSI packet transfer or screen output.

### Stage B: complete on hardware

The panel probe stage changes only `panel@0` to `okay`. It is intended to
verify:

- driver binding for `panel-samsung-s6e8fc01`;
- acquisition of the `ldo_vibr` regulator;
- acquisition of GPIO 29 and GPIO 42;
- successful `mipi_dsi_attach()`.

Observed:

- `14010000.dsi.0` bound `panel-samsung-s6e8fc01`;
- the panel acquired the MT6359 VIBR regulator without enabling it;
- GPIO29 and GPIO42 were acquired and remained low;
- successful probe proves `mipi_dsi_attach()` returned zero;
- no panel probe or deferred-probe error was logged.

Probe does not run panel prepare/display-on. Screen output remains a later
stage.

### Stage C0: SMI provider probe complete on hardware

The inherited MT8192 SMI common and LARB0/LARB1 nodes are replaced with
MT6873-specific providers at the same addresses. MT6873 register defaults,
bus selection, LARB OSTD data and threshold/SW-flag settings come from the
vendor source.

IOMMU, OVL, RDMA and all display traffic remain disabled. Vendor LARB0 has an
additional WRR setup that upstream `mtk-smi` does not yet model; traffic must
not be enabled until that is resolved.

Public `DT Check` run `45943655920` and `Build Mainline` run `45944032565`
completed successfully. The latter compiled `mtk-smi.o` and generated:

```text
Image.gz sha256  2a814bb32bc78a4e7330fc2ab18399ba2ef163e22fcc9b7a507088f43a914e19
DTB sha256       b333db80ed5bf9a46a62c1a61658df3fb0e4df879c349ceb87e85782db94a7d9
```

The DTB still has 337 nodes; only the reviewed SMI common/LARB0/LARB1 nodes
changed relative to Stage B. Later Stage C1 hardware diagnostics directly
observed `14002000.smi` bound to `mtk-smi-common` and both reviewed LARBs bound
to `mtk-smi-larb`, with no deferred-probe entry.

### Stage C1: main IOMMU provider probe complete on hardware

The inherited MT8192 IOMMU node is replaced with `mediatek,mt6873-m4u` at the
vendor-confirmed main address. This stage intentionally uses one bank and one
IRQ, matching current MT6873 vendor kernels; the legacy bank1-3 nodes are not
reinterpreted as independent page-table engines.

Only LARB0 and LARB1 are connected to the provider. No device has an `iommus`
consumer, and OVL/RDMA remain disabled.

Public `DT Check` run `45947473666` and `Build Mainline` run `45947477132`
completed successfully. The latter compiled `mtk_iommu.o` and generated:

```text
Image.gz sha256  84c5d3f222a3aa0c02c6ce903799824d9689bdea84db7188a624016772ad7dd6
DTB sha256       59e62d69a097639567b9902aa506c53d27d1c6ae282309409a39702d1e300e2e
```

The DTB still has 337 nodes. Hardware IOMMU probe, DMA mapping, TLB behavior
and traffic behavior were initially not tested.

The initial recovery diagnostics had `CONFIG_PSTORE_CONSOLE=n`,
`CONFIG_PSTORE_PMSG=n` and `CONFIG_PSTORE_RAM=m`, so a successful run could
not preserve its log. The config fragment and build gate now force all three
to `y`; the next hardware run uses this rebuilt kernel.

The first pstore-enabled run then caught the IOMMU probe bug directly:
`mtk_iommu_probe+0x248` dereferenced a null shared page-table list because the
MT6873 data inherited `SHARE_PGTABLE` without `.hw_list`. The single main
IOMMU no longer enables that flag.

The rebuilt recovery-only image then completed the provider probe:

- `14002000.smi` bound `mtk-smi-common`;
- `14003000.larb` and `14004000.larb` bound `mtk-smi-larb`;
- `1401d000.m4u` bound `mtk-iommu`;
- both LARBs bound as IOMMU components;
- no SMI/IOMMU deferred-probe entry was captured.

The providers remained runtime-suspended because no device consumes
`#iommu-cells` yet. This does not prove DMA mapping, TLB operations, fault
recovery, SMI traffic or display output.

### Stage C2a: OVL/RDMA provider probe complete on hardware

Stage C2a enables only OVL0, OVL0-2L and RDMA0. The nodes use explicit MT6873
compatibles with narrow MT8192/MT8183 driver-data fallbacks, verified MT6873
clock IDs, DIS power domain 17 and the reviewed IOMMU port IDs.

Empty graph ports satisfy the upstream bindings without declaring a live
display route. Color, CCORR, AAL, gamma, postmask, dither, OVL2-2L, RDMA4 and
the DRM component master remain disabled.

Public final-branch `DT Check` run `45990749452` and `Build Mainline` run
`45986850835` completed successfully. The earlier DT run `45986324981`
produced the same Build Mainline input tree before a whitespace-only cleanup
of the binding patch file:

```text
Image.gz sha256  af8356e0209b3b367d4e19cce5a5bacbe0c11a29f6039d0a9e7d0e5270a00389
DTB sha256       81c7fe8024106e657f51bf338869d439f979f97790003744bb98b91568187b25
```

The recovery-only V61 image passed 57 static assembly checks and has SHA-256
`f7a2763726a30003499c2ceb713f8192a1ac8a012e89ee51483b358f04534a2f`.
It was then run once on the phone and restored afterward.

Direct hardware observations:

- OVL0 and OVL0-2L bound `mediatek-disp-ovl`;
- RDMA0 bound `mediatek-disp-rdma`;
- OVL0/RDMA0 linked to LARB0 and OVL0-2L linked to LARB1;
- all three consumers joined IOMMU group 0 with type `DMA`;
- the three display IRQs were registered and had zero occurrences;
- the DISP power domain was on; idle providers remained runtime-suspended;
- no DRM card was created, enforcing the no-scanout boundary.

The log and analyzer passed all V61 gates. The original recovery was restored
and every protected partition hash was revalidated.

DMA mapping, TLB invalidation, OVL/RDMA traffic, DRM component binding and
scanout remain unverified.

### Stage C2b: V62 found a missing mutex component mapping

Stage C2b adds an MT6873 DRM component master with the vendor-confirmed direct
primary path `OVL0 -> RDMA0 -> DSI0`. It also adds the vendor-defined
`MMSYS_OVL_CON.CON_OVL0 = 1` route required for the direct OVL-to-RDMA
selection.

Public `DT Check` run `46019618614` and `Build Mainline` run `46019616018`
completed successfully on the final C2b branch:

```text
Image.gz sha256  40257fc290f2fdf86e865b50db7b2548c681bae1093ad3f59661cb538db85c82
DTB sha256       81c7fe8024106e657f51bf338869d439f979f97790003744bb98b91568187b25
```

The recovery-only V62 image passed 59 static checks and has SHA-256
`0eb1ddfebced6c4ab3dfec2ca6534e4e68d405814eb8c47b0ed20b6d751db41f`.
It writes a white frame through `/dev/fb0` under both a write timeout and an
independent 60-second watchdog.

V62 was written and tested on hardware. OVL0, OVL0-2L, RDMA0, DSI, DSI PHY and
the panel all bound, and all three memory consumers remained in IOMMU group 0.
The DRM master did not bind:

```text
mediatek-drm mediatek-drm.7.auto: Adding component match for /soc/ovl@14005000
mediatek-drm mediatek-drm.7.auto: Adding component match for /soc/rdma@14007000
mediatek-drm mediatek-drm.7.auto: Adding component match for /soc/dsi@14010000
mediatek-drm mediatek-drm.7.auto: Failed to find disp-mutex node
```

Consequently `drm_master_driver=unbound`, `drm_card_device=absent` and no white
frame was written. The directly observed failure matches a missing
`mediatek,mt6873-disp-mutex` entry in `mtk_ddp_comp_dt_ids[]`: patch 0023 made
the mutex driver match the node, but the DRM master could not classify that node
as `MTK_DISP_MUTEX`. Patch 0038 adds the missing mapping and the topology
checker now rejects its absence. This is a source-level root-cause fix until a
new image is built and tested.

The original recovery was restored and revalidated as
`6a24c75e809bbae2dc062a91d922171a11cba261f6b0071bc93099ad73bd0fd6`;
`boot`, `misc` and `dtbo` retained their original hashes.

## Pending

- build and validate a new recovery-only image with patch 0038;
- Stage C2b DRM master bind and first-frame hardware validation;
- full DRM component chain and routing;
- MT6873 SMI traffic validation, LARB0 WRR handling and legacy IOMMU bank
  fault-reporting;
- IOMMU DMA mapping, TLB fault/recovery and suspend/resume;
- GPU/Panfrost;
- camera, audio, video codec and other multimedia blocks;
- full pinmux/eINT lifecycle validation;
- suspend/resume and error recovery across storage, USB, PMIC and display.
