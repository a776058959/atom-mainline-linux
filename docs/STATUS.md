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

### Stage C0: SMI provider probe compile/schema-verified, not hardware-verified

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
changed relative to Stage B. Hardware provider probe has not been run.

### Stage C1: main IOMMU provider prepared, not validated

The inherited MT8192 IOMMU node is replaced with `mediatek,mt6873-m4u` at the
vendor-confirmed main address. This stage intentionally uses one bank and one
IRQ, matching current MT6873 vendor kernels; the legacy bank1-3 nodes are not
reinterpreted as independent page-table engines.

Only LARB0 and LARB1 are connected to the provider. No device has an `iommus`
consumer, and OVL/RDMA remain disabled. Public DT and kernel-build gates still
need to run for this stage.

## Pending

- full DRM/OVL/RDMA chain;
- MT6873 SMI traffic validation, LARB0 WRR handling and legacy IOMMU bank
  fault-reporting;
- IOMMU bank selection, DMA mapping, TLB fault/recovery and suspend/resume;
- GPU/Panfrost;
- camera, audio, video codec and other multimedia blocks;
- full pinmux/eINT lifecycle validation;
- suspend/resume and error recovery across storage, USB, PMIC and display.
