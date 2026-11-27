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

## Public CI result

`DT Check` run `45943655920` completed successfully:

- all 33 patches applied to a clean Linux `v6.18.59` tree;
- the source-level topology checker passed;
- `dt_binding_check` passed;
- the focused single-DTB `dtbs_check` passed;
- both logs contained no warning, error or schema message;
- the resulting DTB retained `__symbols__`.

`Build Mainline` run `45944032565` also completed successfully:

- `CONFIG_MTK_SMI=y` survived `olddefconfig`;
- `drivers/memory/mtk-smi.o` was compiled;
- `vmlinux`, `Image.gz` and the atom DTB linked and packed successfully;
- `build-mainline.log` contained no compiler warning or error.

Generated outputs:

```text
Image.gz size    15298410
Image.gz sha256  2a814bb32bc78a4e7330fc2ab18399ba2ef163e22fcc9b7a507088f43a914e19

DTB size         59738
DTB sha256       b333db80ed5bf9a46a62c1a61658df3fb0e4df879c349ceb87e85782db94a7d9
```

Compared with the hardware-tested Stage B DTB, both trees contain 337 nodes
and no node was added or removed. Only these nodes changed:

```text
/soc/smi@14002000   clocks, compatible, power-domains, status
/soc/larb@14003000  compatible, power-domains, status
/soc/larb@14004000  compatible, power-domains, status
```

This proves source application, kernel compilation, DTB generation and schema
conformance. It does not prove that any SMI provider probed on the phone.
