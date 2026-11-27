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

### Stage B: prepared, not hardware-verified

The panel probe stage changes only `panel@0` to `okay`. It is intended to
verify:

- driver binding for `panel-samsung-s6e8fc01`;
- acquisition of the `ldo_vibr` regulator;
- acquisition of GPIO 29 and GPIO 42;
- successful `mipi_dsi_attach()`.

Probe does not run panel prepare/display-on. Screen output remains Stage C.

The public `DT Check` workflow run `45933305710` on
`display/stage-b-panel` completed successfully. The generated 59,750-byte DTB
has SHA-256
`f0882fc50772625adfb21fd148a00b753f528a26f6bdf6d9790a304f96a73900`.
It differs from the hardware-tested Stage A DTB only by the panel status
property. A recovery-only image passed 43 local assembly checks, but has not
been flashed or booted.

## Pending

- full DRM/OVL/RDMA chain;
- SMI/LARB and MT6873 IOMMU;
- GPU/Panfrost;
- camera, audio, video codec and other multimedia blocks;
- full pinmux/eINT lifecycle validation;
- suspend/resume and error recovery across storage, USB, PMIC and display.
