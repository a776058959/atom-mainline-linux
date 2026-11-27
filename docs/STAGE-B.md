# Display Stage B: panel probe

## Change

This branch enables exactly one additional device-tree node relative to the
validated Stage A topology:

```text
/soc/dsi@14010000/panel@0    disabled -> okay
```

`mipi_tx0` and the DSI host remain enabled. The video/DRM consumers remain
disabled.

## Expected probe evidence

- `panel-samsung-s6e8fc01` binds to the MIPI-DSI panel device.
- The panel obtains its `power-supply`, which points to the MT6359 VIBR LDO.
- GPIO 29 (`enable`) and GPIO 42 (`reset`) are acquired.
- The panel driver sets four DSI lanes, RGB888 and 1,098,000,000 Hz HS rate.
- `mipi_dsi_attach()` reaches the MediaTek DSI host and returns success.

A bound MIPI-DSI panel driver is expected to prove that regulator/GPIO
acquisition and attach returned success, because the driver does not complete
probe otherwise.

## Not expected

The panel `prepare`/display-on sequence is not called merely by probe. This
stage does not prove:

- PLL lock;
- DSI clock/data-lane output;
- panel initialization commands;
- a first frame;
- backlight or interactive display.

Those belong to later full-DRM and panel-power tests.

## Validation gate

The `DT Check` workflow must pass on this branch before any recovery image is
assembled. Binary vendor dtbo fixtures are intentionally not present in this
public repository; source-level placeholder and symbol checks still run.

## Public CI result

`DT Check` run `45933305710` completed successfully:

- all patches applied to Linux `v6.18.59`;
- the source-level topology check passed;
- `dt_binding_check` passed;
- single-DTB `dtbs_check` passed without warning/error/schema messages;
- the resulting DTB retained `__symbols__`;
- the artifact uploaded successfully.

Generated DTB:

```text
size      59750
sha256    f0882fc50772625adfb21fd148a00b753f528a26f6bdf6d9790a304f96a73900
```

Compared with the hardware-tested Stage A DTB, the node count remains 337,
no nodes were added or removed, and `/soc/dsi@14010000/panel@0` is the only
changed node. Its non-status properties are identical; only the status
changed from `disabled` to `okay`.

The recovery-only image preparation gate also passed all 43 local assembler
checks. It has not been flashed or booted.
