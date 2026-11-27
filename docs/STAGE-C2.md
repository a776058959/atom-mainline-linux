# Display Stage C2a: OVL and RDMA provider probe

## Scope

Stage C2a enables only the first three memory-to-memory display providers:

```text
/soc/ovl@14005000   OVL0
/soc/ovl@14006000   OVL0-2L
/soc/rdma@14007000  RDMA0
```

The already-tested MIPI TX, DSI host, panel and display mutex providers remain
enabled. Color, CCORR, AAL, gamma, postmask, dither, OVL2-2L and RDMA4 remain
disabled.

The target MMSYS compatible is not yet registered as a DRM component master.
Consequently, enabling these three component drivers tests resource lookup,
power-domain attachment, IOMMU consumer attachment and component registration;
it must not start scanout.

## Source evidence

The primary MT6873 source is Xiaomi
`android_kernel_xiaomi_mt6875`, commit
`5339a9bd98f0a3b350855a0c23f12f6ba20eb266`.

The vendor 4.14 display source establishes:

- OVL0 has four physical layers and OVL0-2L has two;
- OVL layer/address registers match the MT8173-style layout used by upstream
  MediaTek OVL data;
- the GMC threshold fields are ten bits wide;
- `DATAPATH_CON.LAYER_SMI_ID_EN` exists and is enabled by vendor startup;
- RDMA0 uses the same IRQ/FIFO/address register offsets represented by the
  upstream MT8183 RDMA implementation.

The MT6873 5.15 DTS additionally confirms:

```text
OVL0     0x14005000  GIC SPI 254  LARB0
OVL0-2L  0x14006000  GIC SPI 255  LARB1
RDMA0    0x14007000  GIC SPI 256  LARB0
GCE      SUBSYS_1400XXXX
```

The source also confirms the IOMMU port ordering used by the inherited MT8192
resource references for these three display engines.

## Reuse boundary

The board DTS uses explicit MT6873 compatibles with narrow upstream fallbacks:

```text
mediatek,mt6873-disp-ovl
  -> mediatek,mt8192-disp-ovl

mediatek,mt6873-disp-ovl-2l
  -> mediatek,mt8192-disp-ovl-2l

mediatek,mt6873-disp-rdma
  -> mediatek,mt8183-disp-rdma
```

The fallback supplies the existing upstream driver data. This is sufficient to
compile and probe because the reviewed layer count, register layout and
SMI-ID behavior match. It is not a claim that every blend mode, pixel format,
FIFO threshold or performance tuning value is hardware-validated for MT6873.

The inherited RDMA FIFO size of 5120 bytes remains an upstream MT8192 value.
Vendor MT6873 code computes its FIFO programming dynamically, and its internal
units cannot be substituted directly into the upstream byte-based property.
The value is therefore carried only through a no-traffic provider probe and is
still pending hardware validation.

## Device-tree graph stubs

The upstream OVL and RDMA bindings require `port@0` and `port@1`. The inherited
MT8192 nodes do not contain those ports, so Stage C2a adds empty graph ports to
OVL0 and RDMA0. Empty ports contain no endpoint or `remote-endpoint`; they do
not describe a live route. OVL2-2L remains disabled, so its separate binding
does not require a graph extension.

## Expected hardware evidence

A successful recovery-only run should show:

- `14005000.ovl` bound to `mediatek-disp-ovl`;
- `14006000.ovl` bound to `mediatek-disp-ovl`;
- `14007000.rdma` bound to `mediatek-disp-rdma`;
- OVL0/2L clocks acquired through `clk-mt6873-mm`;
- RDMA0 clock acquired through `clk-mt6873-mm`;
- all three devices attached to the MT6873 DISP power domain;
- at least one IOMMU group now containing the enabled display consumers;
- no failed probe or deferred-probe list entry for these three nodes.

The RDMA driver clears its interrupt registers during probe. It does not start
the engine, and no framebuffer, mode set or DMA mapping is expected.

## Not covered

- DRM component-master registration and pipe construction;
- OVL compositing, blend modes, pixel formats or layer configuration;
- RDMA FIFO sizing, GMC thresholds, underflow behavior or DMA mapping;
- DSI packet transfer, panel prepare/display-on or visible output;
- SMI traffic, IOMMU translation, TLB invalidation or fault recovery;
- runtime suspend/resume.

## Validation gate

The C2a patch must first pass:

- the repository source-level topology checker;
- `dt_binding_check` for the OVL, OVL-2L, RDMA and DSI schemas;
- focused `dtbs_check` for the atom DTB;
- `git diff --check`;
- a warning-free `Image.gz` and DTB build.

Hardware testing is a separate recovery-only stage and requires a rebuilt
initramfs, partition hash verification and explicit flashing authorization.

## Public CI result

`DT Check` run `45990749452` on the final branch completed successfully.
The equivalent first run `45986324981` preceded a whitespace-only patch-file
cleanup:

- all 36 patches applied to a clean Linux `v6.18.59` tree;
- the source-level topology checker passed;
- the OVL, OVL-2L, RDMA and DSI schemas passed `dt_binding_check`;
- the target DTB passed focused `dtbs_check`;
- neither log contained a warning, error or schema message;
- the DTB retained `__symbols__`.

`Build Mainline` run `45986850835` completed successfully:

- `Image.gz` and the target DTB linked and packed;
- `build-mainline.log` contained no compiler warning or error;
- the resulting DTB has 343 nodes, six more than Stage C1 because OVL0 and
  RDMA0 each gained an empty graph container and two port nodes;
- the static image verifier confirmed all seven enabled display/memory
  provider nodes, their MT6873 clock IDs, DIS domain 17, reviewed IOMMU port
  IDs and disabled downstream consumers.

Generated build outputs:

```text
Image.gz size    15310559
Image.gz sha256  af8356e0209b3b367d4e19cce5a5bacbe0c11a29f6039d0a9e7d0e5270a00389

DTB size         59946
DTB sha256       81c7fe8024106e657f51bf338869d439f979f97790003744bb98b91568187b25
```

The local recovery-only V61 image, diagnostic ramdisk and complete static
verification were assembled from these exact outputs. They have not been
written to the phone:

```text
ramdisk sha256  9ca038f2b40769ab0e8de062dbc8557e6c5745f0193190176247de46fb289af6
image sha256    f7a2763726a30003499c2ceb713f8192a1ac8a012e89ee51483b358f04534a2f
image size      16050176
```

This proves compilation, patch application, DTB assembly, schema conformance
and image structure. It does not prove provider probe, IOMMU group membership,
DMA mapping, TLB behavior or any display function.
