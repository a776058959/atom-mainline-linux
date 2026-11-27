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

## Evidence discipline

Historical test images intentionally ended in a controlled panic so pstore
could preserve the log. A deliberate panic is not a crash caused by the
device under test.

Compiled drivers and successful probes remain separate from functional tests.
See `docs/STATUS.md` for the current gates.
