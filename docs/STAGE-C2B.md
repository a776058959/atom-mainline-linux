# Display Stage C2b: direct DRM pipeline

## Scope

Stage C2b registers MT6873 MMSYS as the DRM component master and uses the
vendor-confirmed direct primary path:

```text
OVL0 -> RDMA0 -> DSI0
```

OVL0-2L remains enabled as a probe-tested component but is intentionally not
part of this first CRTC path. The direct path uses only the four OVL0 layers.

## Source evidence

The Xiaomi MT6873 source at commit
`5339a9bd98f0a3b350855a0c23f12f6ba20eb266` defines
`DDP_SCENARIO_PRIMARY_DISP` as:

```text
OVL0 -> RDMA0 -> PWM0 -> DSI0
```

Its PQ stages, including COLOR, CCORR, AAL, GAMMA, POSTMASK and DITHER, are
inside an `#if 0` block for this path. Mainline MediaTek DRM does not model the
vendor PWM block as a DDP component, so C2b removes only that non-DDP step.

The existing MT6873 MMSYS route data already describes:

```text
OVL0  -> RDMA0
RDMA0 -> DSI0
```

No additional register-value inference is needed for this direct route.

## Driver data

Patch 0037 adds:

```c
static const unsigned int mt6873_mtk_ddp_main[] = {
	DDP_COMPONENT_OVL0,
	DDP_COMPONENT_RDMA0,
	DDP_COMPONENT_DSI0,
};
```

and registers it for `mediatek,mt6873-mmsys` in the DRM component-master
lookup table. The existing MT6873 MMSYS binding and clock-provider match are
unchanged.

## Why this is a separate stage

C2a proved provider probe and IOMMU consumer attachment, but no device had yet
allocated a display buffer or enabled a pixel clock. C2b is the first stage
that can:

- bind all components into one DRM device;
- allocate and map a framebuffer through OVL0/IOMMU;
- enable OVL0, RDMA0 and DSI clocks;
- program MMSYS routes and the display mutex;
- run panel prepare/display-on and DSI video output.

This makes it a much stronger hardware test and a higher-risk failure boundary.

## Expected evidence

If the path is correct, the recovery diagnostic should capture:

- `mediatek-drm` component-master bind;
- `/dev/dri/card0` and `/sys/class/drm/card0`;
- nonzero OVL0, RDMA0 and DSI clock enable counts;
- enabled DISP power domain with OVL0/RDMA0/DSI consumers;
- no display driver Oops, BUG, WARNING or deferred probe;
- DSI and RDMA interrupt activity if framebuffer setup performs a mode set;
- panel prepare and MT6359 VIBR regulator enable;
- either visible output or a later, explicitly identified blocker.

A controlled panic remains the log-collection mechanism. Screen output is not
assumed merely because the DRM device registers.

## Initial validation gate

- patch 0037 applies to clean Linux `v6.18.59`;
- source-level topology checker passes;
- existing OVL, RDMA, DSI and panel bindings still pass;
- `dt_binding_check` and focused `dtbs_check` pass;
- the kernel and DTB build without compiler warnings;
- recovery-only image and partition backups are revalidated before any flash.

Hardware testing requires a new explicit flashing authorization.
