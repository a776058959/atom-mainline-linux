# Display Stage C1: main IOMMU provider

## Scope

Stage C1 enables only the main MT6873 display IOMMU at `0x1401d000`:

```text
compatible   mediatek,mt6873-m4u
interrupt    GIC SPI 277
clock        mm_smi_iommu
power domain DIS
larbs        larb0, larb1
translation  one bank / shared page table
```

OVL, RDMA, MMSYS routing, panel power-on and every `iommus` consumer remain
disabled.

## Why this starts with one bank

The original vendor 4.14 DTS exposes a main M4U followed by `bank1_m4u0`,
`bank2_m4u0`, `bank3_m4u0` and a secure M4U. The old vendor driver uses the
main base for translation and retains the extra bank bases primarily for
additional IRQ registration, interrupt masks and protect-PA programming. Its
multi-bank implementation does not assign a separate page table to each of
those bank nodes.

Current MT6873 vendor kernels provide clearer evidence:

- vendor 5.10/5.15/6.1 MT6873 IOMMU data uses one main display IOMMU with
  `SHARE_PGTABLE`;
- their MT6873 DTS has one `iommu@1401d000` node, one IRQ and one `bclk`;
- the LARB remap matches the MT8192/MT6893 mapping already represented in
  upstream;
- the display IOVA region starts at 0 for 4 GiB.

Linux v6.18.59 also models this provider as one memory region and one IRQ.
Adding four independent upstream banks would therefore be an unsupported
reinterpretation of the old fault-reporting nodes.

## Sources checked

- Xiaomi `android_kernel_xiaomi_mt6875`, commit
  `5339a9bd98f0a3b350855a0c23f12f6ba20eb266`:
  `arch/arm64/boot/dts/mediatek/mt6873.dts`,
  `drivers/iommu/mtk_iommu_v2.c` and
  `drivers/misc/mediatek/include/mt-plat/mt6873/include/mach/mt_iommu_plat.h`.
- `NothingOSS/android_kernel_5.15_nothing_mt6886`:
  `drivers/iommu/mtk_iommu.c` blob
  `346398ff953e61f05d486bf949a913ef181c55b3` and
  `arch/arm64/boot/dts/mediatek/mt6873.dtsi` blob
  `3e14a12ebc8ea9f17207f93f48e20f07ac8458d6`.
- Linux `v6.18.59`:
  `drivers/iommu/mtk_iommu.c` and
  `Documentation/devicetree/bindings/iommu/mediatek,iommu.yaml`.

## Driver data

Patch 0035 defines separate `mediatek,mt6873-m4u` match data instead of
silently aliasing the compatible to MT8192. The data uses the generation-two
MT8192 hardware operations and the following vendor-confirmed properties:

- block clock (`HAS_BCLK`);
- two-bit sub-common LARB ID mapping;
- output-order write and write-throttle controls;
- 34-bit IOVA mode and shared page table;
- one enabled bank;
- MT8192/MT6893 LARB remap and display/video/camera IOVA regions.

## Not covered

- translation-fault reporting from legacy bank1-3;
- the separate VPU/APU IOMMU;
- SMI LARB bank-selection programming under real traffic;
- DMA mapping, TLB invalidation, fault recovery or suspend/resume;
- any OVL/RDMA transfer or display output.

Successful probe and compilation remain separate from those functional tests.
Hardware verification requires a separately authorized recovery-only image.
