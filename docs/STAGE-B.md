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

