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
checker now rejects its absence.

The original recovery was restored and revalidated as
`6a24c75e809bbae2dc062a91d922171a11cba261f6b0071bc93099ad73bd0fd6`;
`boot`, `misc` and `dtbo` retained their original hashes.

### V63: DRM bind fixed, frame completion still failed

The mutex component mapping was isolated as patch 0038. Clean-tree validation
and build both passed:

```text
DT Check run        46027955491  success
Build Mainline run  46027960323  success
Image.gz sha256     5c1b30891b30d0d3f72900a136819bdce91029ccf29181f6594748e7f9febca1
DTB sha256          81c7fe8024106e657f51bf338869d439f979f97790003744bb98b91568187b25
```

The recovery-only V63 package passed all 59 checks:

```text
image size      16050176
image sha256    8fa1d18ba959cdc6c9592a0fcc9a2d878f2f77a7581c19087180ee457444f2d6
ramdisk sha256  6c91fbaa6030cb28b2a4c92804752e03a939638b737fe4696dcd1cbb96ce3e78
dt_table sha256 744eeb82e42e84273ea4c226b01eabc153e44efda172344385b3b545ea7e6f80
```

V63 was written and booted on hardware. Patch 0038 fixed DRM binding:

```text
mediatek-drm bound OVL0, RDMA0 and DSI
drm_master_driver=mediatek-drm
drm_card_device=present
fb_node_device=present
card0-DSI-1 status=connected enabled=enabled
framebuffer_test=white_frame_written
```

No white image appeared. The display pipeline did not complete frames:

```text
[CRTC:59:crtc-0] vblank wait timed out
interrupt=311: 1 GICv3 286 Level 14005000.ovl
interrupt=312: 0 GICv3 287 Level 14006000.ovl
interrupt=313: 0 GICv3 288 Level 14007000.rdma
```

OVL0/RDMA0/DSI clocks, the 1098 MHz MIPI TX PLL, the DISP power domain and the
VIBR regulator were enabled. Vendor `ddp_mutex.c` maps OVL0 to MOD0 bit 0,
RDMA0 to bit 2 and DSI0 to bit 12; the mainline MT6873 table had the first two
but omitted DSI0. Patch 0039 adds only that missing mutex input. V64 must verify
nonzero RDMA completion interrupts and the disappearance of vblank timeout;
visible output remains a separate hardware result.

### V64: DSI0 mutex bit build prepared

V64 includes patch 0039. Clean-tree validation and build both passed:

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

The flasher dry-run passed and the restore dry-run reported
`already-restored`. V64 has not been written to the phone.

V64 was written and tested. It produced the same failure as V63: DRM/card/fb
and the connector were present, the white framebuffer write completed, but
vblank timed out three times and RDMA IRQ 313 remained zero. Patch 0039 alone
therefore did not address the blocking failure.

The Xiaomi MT6873 DRM driver uses a 35840-byte RDMA FIFO, while the formal DTS
inherited MT8192's 5120-byte value. Its MT6873 OVL start path also sets
`GCLAST_EN`, `OUTPUT_CLAMP`, and force-relay mode, none of which the current
mainline start path applies. Patches 0040 and 0041 add explicit MT6873 OVL and
RDMA data; the DTS now selects the 35840-byte FIFO. V65 must verify these
changes on hardware.

V65 then passed clean-tree build and recovery assembly:

```text
DT Check run        46042294627  success
Build Mainline run  46042299611  success
Image.gz sha256     6a0ae0af3a2910c4d661e568fbe4d4fd29390d079d5e86b8ae3020d1514c42dc
DTB sha256          f041bf87b0b7b9df72be2e00b274c184b19eb7ea4625b5f0211f7ddd2288d665
image sha256        20f1790c090965691330c3913327d3273b31c030c01b2fe24257e958b1920571
```

The image passed all 59 assembly checks and was written to recovery with a
full readback and protected-partition hash check. The device was not rebooted.

V65 hardware validation reproduced the V63/V64 failure exactly: DRM and
framebuffer state were valid, the white write completed, RDMA IRQ remained
zero and vblank timed out three times. DSI0 mutex bit 12, 35840-byte RDMA FIFO
and MT6873 OVL start settings are therefore not independently sufficient.

A diagnostic-only V66 image reused the exact V65 kernel/DTB and expanded the
initramfs to capture DSI interrupt state, DRM debugfs state and read-only MMIO
values. V66 passed all 59 assembly checks, was written to recovery, and ran on
hardware. Its marker, early/settled/post-framebuffer snapshots and controlled
`sysrq` panic were all present.

V66 directly proved that the DSI controller handled panel initialization:
IRQ 309 was `31`, while OVL IRQ 311 was `1`, OVL-2L IRQ 312 was `0`, RDMA IRQ
313 was `0`, and `vblank wait timed out` appeared three times. The DRM plane
and CRTC state showed the expected active 1080x2400 XR24 framebuffer, but no
frame completion or visible output occurred. All attempted `/dev/mem` reads
returned `raw=unavailable` because strict devmem rejected them.

Vendor MT6873 `ddp_ovl.c` was rechecked from source SHA `5339a9bd...`.
`ovl_start()` sets `HF_FOVL_CK_ON` bit 10, and `ovl_clock_on()` sets
`OVL_READ_WRK` bit 20 and `OVL_BYPASS_SHADOW` bit 22. Patch 0042 preserves
those bits when starting MT6873 OVL. Patch 0043 adds a one-shot, read-only
kernel-side delayed snapshot for MMSYS, OVL, RDMA, DSI and mutex registers so
V67 does not depend on `/dev/mem`.

V67 then passed a clean `v6.18.59` build:

```text
Build Mainline run  46122277644  success
Image.gz sha256     1e091bfccdc20f1e39d8114e761d5b1b1effe41d869580b6b7487cff04fbab92
DTB sha256          f041bf87b0b7b9df72be2e00b274c184b19eb7ea4625b5f0211f7ddd2288d665
```

The build log compiled `mtk_mt6873_diag.o` and contained no compiler
warning/error gate failure. The recovery-only image passed all 59 assembly
checks. It was written to the recovery partition and read back with matching
size and SHA-256:

```text
image sha256             2bd407c97bb8c3a872fed2b12c51b49f2ac01d1e9f250a34240eefc2b828eb11
recovery readback sha256 2bd407c97bb8c3a872fed2b12c51b49f2ac01d1e9f250a34240eefc2b828eb11
```

The phone remained in Android and was not rebooted. Hardware execution and
register interpretation are still pending.

V67 then ran successfully on hardware. The direct register evidence showed:

```text
mmsys[0x0f04]=0x00000001
ovl0[0x000c]=0x00500401
ovl0[0x0038]=0x09600438
ovl0[0x0044]=0x100010e0
ovl0[0x0f40]=0xfe000000
ovl0[0x0008]=0x00006025
rdma0[0x0004]=0x0000002f
mutex0[0x0030]=0x00000005
```

The MMSYS route, OVL enable bits, 1080x2400 layer geometry, pitch, address and
mutex module bits were programmed. OVL status still set `ABNORMAL_SOF`,
`RDMA0_EOF_ABNORMAL` and `FME_UND`; RDMA status set frame/EOF/underflow flags,
while RDMA IRQ 313 remained zero and DSI IRQ 309 remained at 31.

The target Xiaomi Android 11 source shows that upstream lacks several
MT6873 real-time read-path settings. V68 adds the vendor OVL GMC/FIFO/GREQ and
buffer values, LARB0 WRR values `0x7` for ports 2 and 3, LARB throttle
`0x370256`, zero video-mode RDMA output threshold, and additional SMI/IOMMU
register diagnostics.

V68 passed clean Linux `v6.18.59` build run `46127177683`:

```text
Image.gz sha256  5b402b001e74c738ae3d123802ca9f7b3f999f228b423a60f75feee79a2c01dd
DTB sha256       f041bf87b0b7b9df72be2e00b274c184b19eb7ea4625b5f0211f7ddd2288d665
image sha256     bb2b8c42787ee42afb8897454a46c0ebdbc0a7e98754aceff056ebfeb74716e8
```

The build compiled `mtk_disp_ovl.o`, `mtk_disp_rdma.o`, `mtk-smi.o` and
`mtk_mt6873_diag.o`. The recovery-only image passed all 59 assembly checks and
was written only to recovery. Readback matched the image hash; the V68 recovery
partition hash is
`627629d69b6d6c7c9e3910a568ed7aeafc6fb1fbe4f781c937473cb127491019`.
The phone remained in Android and was not rebooted.

V68 ran on hardware. Its OVL and RDMA tuning values were all present:

```text
ovl0[0x00c8]=0x03ff03ff
ovl0[0x00d0]=0x01800000
ovl0[0x01e0]=0x207f00ff
ovl0[0x01f8]=0xf1ff7777
ovl0[0x020c]=0x00008040
rdma0[0x0040]=0x88c00000
```

The failure remained: OVL status was still `0x6025`, RDMA status was `0x77`
with FIFO underflow/empty flags, RDMA IRQ 313 stayed zero and three vblank
waits timed out. LARB0 did not retain the intended configuration:

```text
larb0[0x0024]=0x00370246
larb0[0x0108]=0x00000000
larb0[0x010c]=0x00000000
larb0[0x0208]=0x00003f3f
```

The expected values are `0x370256`, WRR `0x7` for ports 2/3 and OSTD
`0x28` for port 2. Patch 0048 forces MT6873 LARB configuration during IOMMU
component bind, holds runtime PM until unbind, and logs immediate readback.

V69 passed clean Linux `v6.18.59` build run `46131176338`:

```text
Image.gz sha256  4fa93f9ad287da91b35417f42979b2635fa9656a8b875d51032b923e2597b2ed
DTB sha256       f041bf87b0b7b9df72be2e00b274c184b19eb7ea4625b5f0211f7ddd2288d665
image sha256     d9caef909f6ed9e61d7df499cb781ecfdca9e2d33bbe21103dae8b330434f6d5
```

The image passed all 59 assembly checks. A 1 MiB-block write changed only the
unused gap after the candidate inside the last padded block; the candidate
prefix read back exactly, and every recovery byte from offset 16 MiB onward
matched the backup. The V69 script now uses 4 KiB writes.

V69 then ran in recovery. Its bind-time diagnostic readback was still
`0x370246 / 0x0 / 0x0 / 0x3f3f`, proving that even the forced component-bind
configuration did not remain in LARB0. The deferred diagnostic snapshot was
unchanged: OVL status stayed `0x6025`, RDMA status stayed `0x77`, RDMA IRQ 313
remained zero and all observed vblank waits timed out.

The V69 initramfs clock dump identified the next concrete blocker. It read the
following live `clk_summary` entries:

```text
mm_smi_common  2 2 0 0 0 0 ... ?  14002000.smi
mm_smi_infra   2 2 0 0 0 0 ... ?  14002000.smi
mm_smi_gals    3 3 0 0 0 0 ... ?  14002000.smi
mm_smi_iommu   2 2 0 0 0 0 ... ?  1401d000.m4u
```

The nonzero prepare/enable counts prove that consumers requested the clocks;
the `?` hardware state is the direct evidence that the clock provider has no
gate backend. Patch 0020 had declared all four as `GATE_DUMMY`. Vendor CCF also
marks them dummy, but vendor power-domain code separately clears MMSYS CG0
bits 11/17/27 and CG1 bit 0. Patch 0049 now represents those four clocks as
real MMSYS gates in upstream `mtk_clk_register_gates()`. V70 is not built or
hardware-tested yet.

## Pending

- V70 build and hardware validation of the four real SMI gates;
- V70 confirmation that bind-time LARB throttle/WRR/OSTD values persist;
- Stage C2b first-frame completion and visible-output validation;
- full DRM component chain and routing;
- MT6873 SMI traffic validation, LARB0 WRR handling and legacy IOMMU bank
  fault-reporting;
- IOMMU DMA mapping, TLB fault/recovery and suspend/resume;
- GPU/Panfrost;
- camera, audio, video codec and other multimedia blocks;
- full pinmux/eINT lifecycle validation;
- suspend/resume and error recovery across storage, USB, PMIC and display.
