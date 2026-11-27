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

## Public CI result

`DT Check` run `45947473666` completed successfully:

- all 35 patches applied to a clean Linux `v6.18.59` tree;
- the focused topology checker passed;
- `dt_binding_check` passed;
- the single-DTB `dtbs_check` passed;
- both logs contained no warning, error or schema message;
- `__symbols__` remained in the generated DTB.

`Build Mainline` run `45947477132` also completed successfully:

- `CONFIG_MTK_IOMMU=y` survived `olddefconfig`;
- `drivers/iommu/mtk_iommu.o` was compiled;
- `vmlinux`, `Image.gz` and the atom DTB linked and packed successfully;
- `build-mainline.log` contained no compiler warning or error.

Generated outputs:

```text
Image.gz size    15298656
Image.gz sha256  84c5d3f222a3aa0c02c6ce903799824d9689bdea84db7188a624016772ad7dd6

DTB size         59682
DTB sha256       59e62d69a097639567b9902aa506c53d27d1c6ae282309409a39702d1e300e2e
```

The DTB still has 337 nodes. Its only semantic board change relative to C0 is
the `/soc/m4u@1401d000` properties. DTC renumbered phandles throughout the
tree because the IOMMU node now references two LARBs; those phandle-only
changes do not alter the referenced nodes.

This proves compilation, DTB assembly and schema conformance. It does not
prove that the IOMMU probed on the phone.

## Recovery diagnostics correction

The first C0/C1 recovery tests reached the longer black-screen kernel phase
but produced no new pstore console record. An embedded-config comparison found
that `olddefconfig` had changed diagnostics-only options:

```text
Stage B kernel:
  CONFIG_PSTORE_CONSOLE=y
  CONFIG_PSTORE_PMSG=y
  CONFIG_PSTORE_RAM=y

first C0/C1 kernels:
  CONFIG_PSTORE_CONSOLE=n
  CONFIG_PSTORE_PMSG=n
  CONFIG_PSTORE_RAM=m
```

The config fragment now pins all three to `y`, and the build workflow rejects
the kernel if they regress. A Stage B kernel with the same V60 initramfs
reached init at 1.036 seconds, took both snapshots, cancelled its watchdog and
completed the controlled panic. This proves the V60 user-space diagnostic
itself; C0/C1 probe evidence still requires a pstore-enabled rebuild.
