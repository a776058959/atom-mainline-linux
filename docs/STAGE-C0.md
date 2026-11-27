# Display Stage C0: SMI provider probe

## Scope

Stage C0 enables only the MT6873 SMI common and display LARB providers:

```text
/soc/smi@14002000    okay
/soc/larb@14003000   okay
/soc/larb@14004000   okay
```

IOMMU, OVL, RDMA, MMSYS routing, the panel power sequence and all
traffic-bearing display consumers remain disabled.

## Source evidence

The vendor MT6873 DTS describes the following resources:

```text
smi common   0x14002000
larb0        0x14003000
larb1        0x14004000
power domain SCP_SYS_DIS
```

The vendor SMI common table contains six register writes plus `BUS_SEL`:

```text
SMI_L1LEN     0x0000000b
SMI_BUS_SEL   0x00001414
SMI_M4U_TH    0x0e100e10
SMI_FIFO_TH1  0x090a090a
SMI_FIFO_TH2  0x0506090a
SMI_DCM       0x000004f1
SMI_DUMMY     0x00000001
```

`0x1414` selects MMU1 for LARB 1, 2, 5 and 6. The vendor LARB0/LARB1 OSTD
tables and the `THRT_UPDATE`/`SW_FLAG` writes are represented explicitly in
patch 0033.

The vendor LARB0 path also programs WRR values for ports 2 and 3. The current
upstream `mtk-smi` interface has no generic WRR field, so Stage C0 deliberately
does not bind an IOMMU component master or enable any display traffic that
could depend on that missing programming.

## Expected probe evidence

- `mtk-smi-common` binds the node at `14002000`.
- `mtk-smi-larb` binds LARB0 at `14003000` and LARB1 at `14004000`.
- Each LARB resolves `mediatek,smi = <&smi_common>`.
- The DIS power domain remains available and no inherited MT8192 domain index
  is requested.
- No IOMMU, OVL or RDMA provider/consumer enters deferred-probe state because
  they remain disabled.

Provider probe does not prove clock output, access to SMI registers under
traffic, IOMMU translation, pixel data or display output.

## Validation gate

Both binding patches must apply to Linux `v6.18.59`, `CONFIG_MTK_SMI` must be
built in, the formal DTB must pass `dt_binding_check` and `dtbs_check`, and
the focused topology checker must pass before any recovery image is
assembled. Hardware boot and probe validation require a separate test stage
and explicit flashing authorization.
