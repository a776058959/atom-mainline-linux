# Validation history

This file summarizes hardware evidence from the private development
repository. Raw logs and serial numbers are intentionally not published.

## UFS

The v6.18.59 mainline kernel successfully:

1. bound the MediaTek UFS host and PHY;
2. enumerated three UFS LUNs;
3. exposed 60 GPT partition names matching Android's by-name mapping;
4. performed repeated 4 KiB reads;
5. mounted four known `super` ext4 extents read-only and read representative
   `build.prop` files whose hashes matched Android's copies;
6. unmounted and detached all test loops before a controlled panic.

These results do not cover UFS writes, encrypted userdata, journal replay or
suspend/resume.

## USB host

The xHCI controller and generic MTK T-PHY bind. USB2 and USB3 root hubs are
created and the USB clocks are enabled by their consumers.

This does not prove external device enumeration or host-mode transfer.

## USB device

MTU3 reaches configured high-speed peripheral mode after:

- selecting USB2/USB3 PHY types from the upstream binding;
- programming verified MT6873 U2 analog values;
- enabling the MT6873 VUSB10 setting;
- forcing the U2 session-select signals indicated by vendor source.

Windows enumerated a CDC ACM device and three random PING/ACK pairs completed
in both directions. The same result was reproduced with the cable connected
continuously from Android through preloader/LK/Linux.

This does not prove USB3 gadget, host/device role switching, hotplug or
suspend/resume.

## PMIC, I2C5 and MT6360

The MT6359 regulator chain probes. I2C5 is backed by MT6873 clock and pinctrl
resources. MT6360 exposes its regmap, regulators, charger and TCPC, and live
I2C/TCPC interrupt counters advance.

The stock vendor overlay originally injected duplicate Android-only I2C
clients into the mainline bus. The formal DTS now routes those fixups to
disabled placeholders; the corrected topology was verified on hardware.

## Display Stage A

Direct hardware evidence from the Stage A image:

```text
11e50000.dsi-phy -> mediatek-mipi-tx
14010000.dsi     -> mtk-dsi
DSI IRQ           registered
MMSYS gates       mm_dsi0 and mm_dsi_dsi0 acquired by the DSI device
DISP domain       on, containing 14010000.dsi
panel             disabled
```

The MIPI PLL remained off because no panel/DRM mode was enabled.

## Display Stage B

The panel device bound `panel-samsung-s6e8fc01`. Its probe acquired GPIO29,
GPIO42 and the MT6359 VIBR regulator without enabling the rail, then completed
`mipi_dsi_attach()`. No panel probe or deferred-probe failure was logged.

This does not cover panel prepare/display-on, PLL lock, DSI packet transfer or
screen output.

## Display Stage C0

Public `DT Check` run `45943655920` passed binding and single-DTB schema
checks. Public `Build Mainline` run `45944032565` compiled `mtk-smi.o` and
generated `Image.gz` plus the target DTB without compiler warnings.

The DTB changed only the SMI common and LARB0/LARB1 nodes relative to Stage B.
IOMMU, OVL, RDMA and traffic-bearing display consumers remain disabled.

The subsequent Stage C1 hardware diagnostic directly observed the SMI common
at `14002000` bound to `mtk-smi-common`, and both reviewed LARBs bound to
`mtk-smi-larb`, without a deferred-probe entry.

## Display Stage C1

Public `DT Check` run `45947473666` passed binding and single-DTB schema
checks. Public `Build Mainline` run `45947477132` compiled `mtk_iommu.o` and
generated `Image.gz` plus the target DTB without compiler warnings.

The provider uses the single main MT6873 display IOMMU at `0x1401d000`, one
IRQ, one bank and the two reviewed SMI LARBs. No device consumes its
`#iommu-cells` yet.

The first recovery run exposed a fatal null shared-page-table list access in
`mtk_iommu_probe`. The single-provider data incorrectly retained architecture
for two IOMMUs sharing a page table. Removing that flag fixed the probe.

The rebuilt recovery-only image was then run on hardware. SMI common, LARB0,
LARB1 and the main IOMMU all bound their intended drivers; the IOMMU bound both
LARBs as components and no deferred-probe entry appeared. The devices remained
runtime-suspended with no traffic consumer.

This proves provider probe and component links only. DMA mapping, TLB
invalidation, fault recovery, SMI traffic, suspend/resume and screen output
remain unverified.

## Display Stage C2a

The recovery-only V61 image enabled OVL0, OVL0-2L and RDMA0 without registering
MMSYS as a DRM component master. The kernel was `v6.18.59`, and the console
snapshots showed:

```text
14005000.ovl   -> mediatek-disp-ovl -> LARB0
14006000.ovl   -> mediatek-disp-ovl -> LARB1
14007000.rdma  -> mediatek-disp-rdma -> LARB0
```

All three consumers joined IOMMU group 0 with type `DMA`. IRQ 311, 312 and
313 were registered and remained at zero occurrences. The DISP power domain
was on; idle providers stayed runtime-suspended with their display clocks
disabled. No OVL/RDMA probe failure or deferred-probe entry was observed.

The no-scanout gate also held: `/sys/class/drm/card0` and `/dev/dri/card0`
were absent. The expected controlled panic produced the pstore record, and
the original recovery plus protected partition hashes were restored and
verified afterward.

This does not prove DMA mapping, TLB invalidation, RDMA/OVL traffic, a DRM
modeset or visible output.

## Display Stage C2b V62

V62 registered MT6873 MMSYS as a DRM component master and enabled the direct
`OVL0 -> RDMA0 -> DSI0` path. The kernel bound OVL0, OVL0-2L, RDMA0, DSI, DSI
PHY and the panel, and kept the three memory consumers in IOMMU group 0. It
reported no display probe failure, deferred probe or kernel fault.

DRM bind nevertheless failed:

```text
mediatek-drm mediatek-drm.7.auto: Failed to find disp-mutex node
```

No DRM card, DRM node, framebuffer node or visible white frame followed. The
source audit found that patch 0023 registered the MT6873 mutex with its own
driver but did not add the compatible to `mtk_ddp_comp_dt_ids[]` in
`mtk_drm_drv.c`. Patch 0038 adds that single DRM component mapping.

V62 therefore proves the provider, panel-attachment and IOMMU topology at the
point before DRM bind. It does not prove mutex programming, modeset, DMA
mapping, RDMA/OVL traffic, DSI PLL lock or panel output.

## Display Stage C2b V63

V63 included the mutex component mapping from patch 0038. DRM then bound OVL0,
RDMA0 and DSI; the DRM master, card node, framebuffer node and enabled DSI
connector all appeared. The diagnostic completed its white framebuffer write.

No white image was visible. DRM atomic commits timed out three times waiting
for vblank. In the settled snapshot, OVL0 IRQ 311 had one occurrence while
RDMA0 IRQ 313 had zero. Display clocks, the 1098 MHz MIPI TX PLL, the DISP
power domain and the VIBR regulator were enabled.

The vendor MT6873 mutex map assigns OVL0, RDMA0 and DSI0 to MOD0 bits 0, 2 and
12. The existing mainline MT6873 table omitted DSI0. Patch 0039 adds that bit.
V63 proves DRM registration, connector setup, framebuffer allocation/write and
clock/provider state, but not completed scanout or visible output.

## Display Stage C2b V64

V64 included DSI0 mutex MOD0 bit 12. It booted with the same DRM, framebuffer
and connector state as V63, and the white framebuffer write completed.

The hardware result was unchanged: three vblank waits timed out, OVL0 IRQ 311
remained at one and RDMA0 IRQ 313 remained at zero. No white image appeared.
The DSI0 mutex bit is therefore not the blocking defect.

The vendor MT6873 DRM source exposes two additional active-path differences:
the RDMA FIFO is 35840 bytes rather than MT8192's 5120 bytes, and OVL start
programs `GCLAST_EN`, `OUTPUT_CLAMP` and force-relay mode. Patches 0040/0041
will be tested next in V65.

## Display Stage C2b V65

V65 included the DSI0 mutex bit, MT6873 RDMA FIFO data and MT6873 OVL start
settings. It booted and produced the same DRM/framebuffer/connector state as
V63/V64. The white framebuffer write completed, but RDMA0 IRQ remained zero,
vblank timed out three times and no image appeared.

Those three changes are not independently sufficient. V66 is a
diagnostic-only initramfs using the exact V65 kernel/DTB. It adds DSI/display
IRQ evidence, DRM debugfs state, display-controller register dumps and optional
read-only `/dev/mem` MMIO values.

## Display Stage C2b V66

V66 ran successfully on hardware with the exact V65 kernel and DTB. The
diagnostic marker and all three snapshots completed, followed by the expected
controlled panic. Direct log evidence showed 31 DSI interrupts and zero RDMA
interrupts. The DRM framebuffer and CRTC state were active, but the white
framebuffer update still produced three vblank timeouts and no visible frame.

The initramfs could not read the display registers because strict devmem
rejected `/dev/mem`; every reported MMIO value was `unavailable`. A source
audit of vendor MT6873 `ddp_ovl.c` found that the mainline start path still
clears `HF_FOVL_CK_ON` bit 10 and the `OVL_READ_WRK`/`OVL_BYPASS_SHADOW` bits
20/22. Patch 0042 fixes that register update. Patch 0043 adds a temporary,
read-only kernel-side register snapshot through `of_iomap()` so V67 can
identify which part of the OVL -> RDMA -> DSI path stops progressing.

## Display Stage C2b V67 build and flash

V67 passed clean Linux v6.18.59 build run `46122277644`. The new diagnostic
translation unit and the updated MT6873 OVL path compiled under the workflow's
warning/error gate. The resulting `Image.gz` SHA-256 is
`1e091bfccdc20f1e39d8114e761d5b1b1effe41d869580b6b7487cff04fbab92`;
the DTB is unchanged.

The recovery-only image passed all 59 assembly checks and has SHA-256
`2bd407c97bb8c3a872fed2b12c51b49f2ac01d1e9f250a34240eefc2b828eb11`.
The flash tool wrote only the recovery partition, read the image back with the
same hash, and then matched the full recovery partition hash
`6d1a73bc6d682df53e9cd4bd94a00fe024bd306a658e7bc56744240c6e07696d`.
No reboot was performed. The next evidence must come from the V67 hardware run,
not from this build or write-back result.

## Display Stage C2b V67 hardware result

V67 executed successfully and preserved a complete register log. MMSYS routing
and the patch-0042 OVL enable bits were present:

```text
mmsys[0x0f04]=0x00000001
ovl0[0x000c]=0x00500401
ovl0[0x0038]=0x09600438
ovl0[0x0044]=0x100010e0
ovl0[0x0f40]=0xfe000000
```

The pipeline still did not complete. OVL `INTSTA=0x6025` reported abnormal SOF,
RDMA0 EOF abnormal and frame underrun. RDMA `INT_STATUS=0x2f` reported frame,
EOF, FIFO-underflow and target-line events, while RDMA IRQ 313 remained zero
and DSI IRQ 309 remained 31. The mutex enabled the path with MOD0 bits 0 and 2.

The exact Redmi 10X Android 11 source exposes missing real-time controls for
OVL RDMA thresholds/FIFO/GREQ/buffers, LARB0 WRR ports 2 and 3, LARB throttle
`0x370256`, and video-mode RDMA output threshold. Patches 0044-0047 implement
those values and expand the next register snapshot. No visible output existed
in V67, and IOMMU/SMI read completion remains unproven.

## Display Stage C2b V68 build and flash

V68 passed Linux v6.18.59 build run `46127177683`. It compiled the modified
OVL, RDMA and SMI drivers plus the expanded MT6873 diagnostic unit. The
resulting kernel SHA-256 is
`5b402b001e74c738ae3d123802ca9f7b3f999f228b423a60f75feee79a2c01dd`;
the DTB remained unchanged.

The recovery-only image passed all 59 assembly checks with SHA-256
`bb2b8c42787ee42afb8897454a46c0ebdbc0a7e98754aceff056ebfeb74716e8`.
Only recovery was written. Readback matched the image, and the full partition
hash after writing is
`627629d69b6d6c7c9e3910a568ed7aeafc6fb1fbe4f781c937473cb127491019`.
No reboot was performed. Functional effect remains unverified until the V68
recovery run completes.

## Display Stage C2b V68 hardware result

V68 executed successfully. All intended OVL GMC/FIFO/GREQ/buffer and RDMA
video-threshold writes were present in the kernel-side snapshot. DSI remained
active, but RDMA IRQ 313 remained zero and the initial three vblank waits timed
out.

OVL status remained `0x6025`, and RDMA status `0x77` retained FIFO-underflow
and FIFO-empty flags. LARB0 was not configured as vendor source requires:
throttle read `0x370246`, WRR ports 2/3 were zero, and OSTD ports read
`0x3f3f`.

Patch 0048 configures MT6873 LARBs during IOMMU component bind, holds their
runtime-PM reference for the component lifetime, and logs immediate register
readback. The next hardware run must verify both the LARB readback and whether
the OVL/RDMA underflow clears.

## Display Stage C2b V69 build and flash

V69 passed build run `46131176338` with kernel SHA-256
`4fa93f9ad287da91b35417f42979b2635fa9656a8b875d51032b923e2597b2ed`.
Its recovery image passed all 59 assembly checks and has SHA-256
`d9caef909f6ed9e61d7df499cb781ecfdca9e2d33bbe21103dae8b330434f6d5`.

The candidate prefix read back exactly. The original flash command used a
1 MiB write block and altered only the unused post-image gap in the final
padded block; recovery bytes from 16 MiB onward matched the backup. The write
scripts now use 4 KiB blocks.

## Display Stage C2b V69 hardware result

V69 booted in recovery and forced LARB configuration during IOMMU component
bind. The immediate readback nevertheless remained the hardware default:

```text
larb0 thrt=0x370246 wrr2=0x0 wrr3=0x0 ostd2=0x3f3f
larb1 thrt=0x370246 wrr2=0x0 wrr3=0x0 ostd2=0x3f3f
```

The delayed snapshot matched V68: OVL status `0x6025`, RDMA status `0x77`,
RDMA IRQ 313 zero, and DSI IRQ 309 at 31. Three vblank waits timed out.

The clock summary showed nonzero prepare/enable counts but `?` hardware state
for all four SMI clocks. This is consistent with their upstream and vendor CCF
definitions as dummy clocks, while the vendor power-domain callback clears
MMSYS gate bits directly. Patch 0049 maps the same clock IDs to real MM0/MM1
gates. V70 build and hardware execution have not occurred.

## Evidence discipline

Historical test images intentionally ended in a controlled panic so pstore
could preserve the log. A deliberate panic is not a crash caused by the
device under test.

Compiled drivers and successful probes remain separate from functional tests.
See `docs/STATUS.md` for the current gates.
