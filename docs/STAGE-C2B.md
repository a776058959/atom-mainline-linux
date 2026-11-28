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

The vendor OVL connection code additionally requires
`MMSYS_OVL_CON` field `CON_OVL0 = 1` for a direct OVL0-to-RDMA connection.
Patch 0037 adds that route using the vendor-defined `0xf04` register and the
same two-bit field.

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
- a scripted all-white framebuffer write when `/dev/fb0` exists;
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

## Public CI result

`DT Check` run `46019618614` and `Build Mainline` run `46019616018` both
completed successfully on commit `e85a7ab`.

- all 37 patches applied to a clean Linux `v6.18.59` tree;
- the source-level topology checker passed;
- `dt_binding_check` and focused `dtbs_check` passed without warning/error;
- `Image.gz` and the atom DTB built without compiler warning/error;
- the DTB remained unchanged because C2b changes kernel driver data only.

Generated outputs:

```text
Image.gz size    15309885
Image.gz sha256  40257fc290f2fdf86e865b50db7b2548c681bae1093ad3f59661cb538db85c82

DTB size         59946
DTB sha256       81c7fe8024106e657f51bf338869d439f979f97790003744bb98b91568187b25
```

The V62 recovery-only diagnostic was assembled from these exact outputs and
passed 59 static checks:

```text
ramdisk sha256  2190b831bdf1095c15903d6f3c94e4f683fb8e4c50af887505fc7a7a0de3669b
image sha256    0eb1ddfebced6c4ab3dfec2ca6534e4e68d405814eb8c47b0ed20b6d751db41f
image size      16050176
```

The V62 ramdisk waits for early and settled DRM state, writes one all-white
framebuffer only when `/dev/fb0` exists, snapshots the connector/clock state,
and retains a 60-second watchdog around the write and a 15-second framebuffer
write timeout.

## V62 hardware result

V62 was written to the recovery partition and booted. The directly observed
state was:

- OVL0, OVL0-2L, RDMA0, DSI, DSI PHY and the panel driver bound;
- SMI, LARB and IOMMU providers stayed bound;
- OVL0, OVL0-2L and RDMA0 remained in IOMMU group 0 with type `DMA`;
- no display driver Oops, BUG, warning, probe failure or deferred probe;
- the DRM master did not bind and no DRM card or framebuffer device appeared.

The decisive log lines were:

```text
mediatek-drm mediatek-drm.7.auto: Adding component match for /soc/ovl@14005000
mediatek-drm mediatek-drm.7.auto: Adding component match for /soc/rdma@14007000
mediatek-drm mediatek-drm.7.auto: Adding component match for /soc/dsi@14010000
mediatek-drm mediatek-drm.7.auto: Failed to find disp-mutex node
```

`mtk_drm_probe()` classifies sibling nodes through `mtk_ddp_comp_dt_ids[]`.
Patch 0023 added the MT6873 mutex compatible to the mutex driver and binding,
but the DRM-local table had no corresponding `MTK_DISP_MUTEX` entry. The mutex
node therefore could not become `private->mutex_node`, and probe returned
`-ENODEV`. Patch 0038 adds only that mapping.

The absence of a white frame is explained by the failed DRM bind and is not
evidence about panel timing, DSI PLL lock or RDMA traffic. The original recovery
was restored and hash-verified after log collection.

Evidence:

```text
D:\820Linux\dumps\drm-pipeline-v62-20261127\20261127-233135\
console-ramoops-2 sha256 eab0343daf7af3d804f896c45e1ac9f7bc7c67570e892430e924d4340c961539
```

## V63 build

Patch 0038 was validated against a clean Linux `v6.18.59` tree:

```text
DT Check run        46027955491  success
Build Mainline run  46027960323  success
Image.gz sha256     5c1b30891b30d0d3f72900a136819bdce91029ccf29181f6594748e7f9febca1
DTB sha256          81c7fe8024106e657f51bf338869d439f979f97790003744bb98b91568187b25
```

The V63 recovery-only image reuses the validated first-frame diagnostic and
changes only the version marker plus the kernel:

```text
image size      16050176
image sha256    8fa1d18ba959cdc6c9592a0fcc9a2d878f2f77a7581c19087180ee457444f2d6
ramdisk sha256  6c91fbaa6030cb28b2a4c92804752e03a939638b737fe4696dcd1cbb96ce3e78
dt_table sha256 744eeb82e42e84273ea4c226b01eabc153e44efda172344385b3b545ea7e6f80
```

All 59 assembly checks passed, the flasher dry-run passed, and the recovery
restore dry-run reported `already-restored`.

## V63 hardware result

V63 was written and booted. Patch 0038 fixed the previous DRM master failure:
DRM bound OVL0, RDMA0 and DSI, `/dev/dri/card0` and `/dev/fb0` appeared, the
DSI connector was connected and enabled, and the diagnostic wrote its white
framebuffer.

The screen remained black. Three atomic commits timed out:

```text
[CRTC:59:crtc-0] vblank wait timed out
```

At the settled snapshot, OVL0 IRQ 311 had fired once while RDMA0 IRQ 313 had
never fired. OVL0, RDMA0, DSI, the MIPI TX PLL, the DISP power domain and the
VIBR regulator were enabled. This locates the failure after DRM bind but before
completed scanout.

## V64 mutex fix

Vendor `ddp_mutex.c` maps the primary path modules as:

```text
DISP_MODULE_OVL0   -> MUTEX MOD0 bit 0
DISP_MODULE_RDMA0  -> MUTEX MOD0 bit 2
DISP_MODULE_DSI0   -> MUTEX MOD0 bit 12
```

Patch 0023 added the first two MT6873 bits but omitted DSI0. Patch 0039 adds
the vendor-confirmed DSI0 bit and the topology checker now requires it.

Expected V64 evidence is a nonzero RDMA frame-end interrupt count and no
`vblank wait timed out` warning. A visible white frame remains a separate
functional result.

## V64 build

Patch 0039 passed clean-tree validation and compilation:

```text
DT Check run        46036375152  success
Build Mainline run  46036381292  success
Image.gz sha256     411e07241dc9ea0634ad40a8e230005d4e0467abaf73b53e25da635df329bfc1
DTB sha256          81c7fe8024106e657f51bf338869d439f979f97790003744bb98b91568187b25
```

The V64 recovery-only image passed all 59 assembly checks:

```text
image size      16050176
image sha256    6194f12b7fa5ea4e671a505067a663af4b0ea44fd84492bfc377165dfc6a7953
ramdisk sha256  1d36629bf44997352b6b98c1fb24e3636d640aab86dfb5e075861617b2c49d6e
dt_table sha256 744eeb82e42e84273ea4c226b01eabc153e44efda172344385b3b545ea7e6f80
```

The flasher and restore dry-runs passed against the connected
`M2004J7AC / mt6873` device. No partition has been modified.

## V64 hardware result

V64 was written and tested. Patch 0039 did not change the failure:
DRM/card/fb and the DSI connector were present, the white framebuffer write
succeeded, but vblank timed out three times and RDMA IRQ 313 stayed at zero.
The original recovery was restored and hash-verified after log collection.

## V65 OVL and RDMA data

The Xiaomi MT6873 DRM driver provides two concrete differences on the active
path:

- MT6873 RDMA FIFO is 3 KiB + 32 KiB = 35840 bytes, not MT8192's 5120 bytes;
- MT6873 OVL start sets `GCLAST_EN`, `OUTPUT_CLAMP`, and force-relay mode.

Patch 0040 adds explicit MT6873 OVL/OVL-2L driver data and start settings.
Patch 0041 adds explicit MT6873 RDMA driver data with the correct FIFO size.
The board DTS overrides `mediatek,rdma-fifo-size` with 35840.

Expected V65 evidence is again a nonzero RDMA frame-end interrupt and no
vblank timeout. Visible output remains independent.

## V65 build and flash

V65 passed CI and assembly:

```text
DT Check run        46042294627  success
Build Mainline run  46042299611  success
Image.gz sha256     6a0ae0af3a2910c4d661e568fbe4d4fd29390d079d5e86b8ae3020d1514c42dc
DTB sha256          f041bf87b0b7b9df72be2e00b274c184b19eb7ea4625b5f0211f7ddd2288d665
image size          16052224
image sha256        20f1790c090965691330c3913327d3273b31c030c01b2fe24257e958b1920571
```

All 59 assembly checks and the flash dry-run passed. The image was written to
recovery and read back byte-for-byte. `boot`, `misc` and `dtbo` retained their
original hashes. The device was not rebooted.

## V65 hardware result

V65 reproduced the same failure. RDMA IRQ remained zero, vblank timed out
three times and no white frame appeared. DSI0 mutex bit 12, the 35840-byte
RDMA FIFO and MT6873 OVL start settings did not independently unblock output.

## V66 register diagnostics

V66 keeps the exact V65 kernel and DTB and changes only the initramfs. It
captures:

- DSI and display interrupt state;
- DRM debugfs summary and atomic state;
- MMSYS route registers;
- OVL0, RDMA0, DSI and mutex0 registers;
- read-only `/dev/mem` MMIO values when available.

V66 passed all 59 assembly checks and the flash dry-run. Hardware diagnostics
then ran successfully with a complete `ATOM-DIAG-V66` marker, three diagnostic
snapshots and the expected controlled `sysrq` panic. The log directly showed:

```text
interrupt=309: 31 GICv3 297 Level 14010000.dsi
interrupt=311: 1  GICv3 286 Level 14005000.ovl
interrupt=312: 0  GICv3 287 Level 14006000.ovl
interrupt=313: 0  GICv3 288 Level 14007000.rdma
```

DSI therefore transmitted the panel-initialization command traffic, while
RDMA never reported frame completion. The DRM state contained an active
1080x2400 XR24 framebuffer on plane 0 and an enabled/active CRTC, but three
`vblank wait timed out` warnings occurred and no white output appeared.
Strict devmem blocked every `/dev/mem` read, so V66 could not recover the
controller register values.

Vendor `ddp_ovl.c` from the MT6873 source snapshot shows two additional writes
that the mainline path was clearing: `ovl_clock_on()` sets OVL `EN` bits 20
and 22, while `ovl_start()` sets bit 10. Patch 0042 switches the MT6873 start
write to read-modify-write and preserves those vendor-confirmed bits. Patch
0043 adds a one-shot kernel-side snapshot after ten seconds, reading MMSYS,
OVL0, RDMA0, DSI0 and mutex0 MMIO directly through `of_iomap()` without
depending on `/dev/mem`. V67 must compile and run before either the bit change
or the snapshot can be treated as validated.

## V67 build and flash

V67 passed clean-tree build run `46122277644`. The compiler built
`mtk_mt6873_diag.o`, and the workflow's warning/error gate passed. The kernel
hash is
`1e091bfccdc20f1e39d8114e761d5b1b1effe41d869580b6b7487cff04fbab92`;
the DTB remains unchanged at
`f041bf87b0b7b9df72be2e00b274c184b19eb7ea4625b5f0211f7ddd2288d665`.

The V67 recovery-only image passed all 59 assembly checks with SHA-256
`2bd407c97bb8c3a872fed2b12c51b49f2ac01d1e9f250a34240eefc2b828eb11`.
Only the recovery partition was written. A bounded readback matched the image
byte-for-byte, and the full recovery partition hash after the write was
`6d1a73bc6d682df53e9cd4bd94a00fe024bd306a658e7bc56744240c6e07696d`.
The device remained in Android and was not rebooted. The OVL bits and kernel
register snapshot were validated next by running V67 on hardware.

## V67 hardware result

V67 proved that the MMSYS OVL-to-RDMA routes, OVL enable bits, layer geometry,
pitch, framebuffer IOVA and mutex modules reached hardware. `ovl0[0x0c]` was
`0x00500401`, so the previously missing bits 10, 20 and 22 were preserved.

The data path still failed before completed output. OVL interrupt status
`0x6025` set `ABNORMAL_SOF`, `RDMA0_EOF_ABNORMAL` and `FME_UND`. RDMA status
`0x2f` set frame, abnormal EOF, FIFO-underflow and target-line flags. RDMA IRQ
313 remained zero, and DSI IRQ 309 remained at 31 after the video-mode setup.

Source comparison against the exact Redmi 10X Android 11 kernel identified
unported real-time settings:

- OVL RDMA GMC threshold, 384-entry FIFO, issue thresholds, GREQ counts, buffer
  thresholds and DCM registers;
- LARB0 WRR port 2/3 values of `0x7`;
- LARB throttle value `0x370256`;
- zero output-valid FIFO threshold for video-mode RDMA.

Patches 0044-0047 add those settings and extend the kernel register dump to
cover the OVL read path, SMI common, LARB0 and IOMMU. V68 tests this combined
change set without altering DSI timing or panel power sequences.

## V68 build and flash

V68 passed Build Mainline run `46127177683`. The compiled objects include
`mtk_disp_ovl.o`, `mtk_disp_rdma.o`, `mtk-smi.o` and
`mtk_mt6873_diag.o`, with no compiler warning/error gate failure.

```text
Image.gz sha256  5b402b001e74c738ae3d123802ca9f7b3f999f228b423a60f75feee79a2c01dd
DTB sha256       f041bf87b0b7b9df72be2e00b274c184b19eb7ea4625b5f0211f7ddd2288d665
image sha256     bb2b8c42787ee42afb8897454a46c0ebdbc0a7e98754aceff056ebfeb74716e8
```

The image passed all 59 assembly checks. Only the recovery partition was
written; readback matched `bb2b8c...16e8`, and the full partition hash is
`627629d69b6d6c7c9e3910a568ed7aeafc6fb1fbe4f781c937473cb127491019`.
The device remained in Android. The new real-time settings and underflow
behavior have not yet been observed in a V68 hardware run.

## V68 hardware result

V68's OVL real-time controls reached hardware exactly, including
`GMC=0x03ff03ff`, FIFO size `0x01800000`, issue threshold `0x207f00ff`,
GREQ `0xf1ff7777`, urgent GREQ `0x7777`, and RDMA video threshold
`0x88c00000`.

Output remained broken. OVL status stayed `0x6025`; RDMA status changed to
`0x77`, retaining FIFO-underflow and FIFO-empty flags. RDMA IRQ 313 remained
zero and three vblank waits timed out.

LARB0 diagnostics exposed the next blocker: throttle was `0x370246` rather
than `0x370256`, both WRR port registers were zero, and OSTD ports read
`0x3f3f` instead of the vendor values. The LARB MMU enable bits were already
set, indicating that the full MT6873 configuration had not remained applied.

Patch 0048 forces the MT6873 LARB configuration during component bind,
holds a runtime-PM reference until unbind, and logs the immediate register
readback. V69 tests this state without changing the V68 OVL/RDMA values.

## V69 build and flash

V69 passed Build Mainline run `46131176338` with kernel SHA-256
`4fa93f9ad287da91b35417f42979b2635fa9656a8b875d51032b923e2597b2ed`.
The recovery image passed all 59 assembly checks and has SHA-256
`d9caef909f6ed9e61d7df499cb781ecfdca9e2d33bbe21103dae8b330434f6d5`.

Candidate-prefix readback matched exactly. The original 1 MiB-block `dd`
changed only the unused gap after the candidate in the final padded block;
all recovery bytes at or after offset 16 MiB still matched the backup. The
flash scripts were corrected to use 4 KiB writes. The device was not rebooted.
The LARB bind readback and underflow behavior remained to be observed.

## V69 hardware result

V69 booted and produced the new bind-time readback, but the forced
configuration still did not stick:

```text
ATOM-DIAG-V69 larb0 thrt=0x370246 wrr2=0x0 wrr3=0x0 ostd2=0x3f3f
ATOM-DIAG-V69 larb1 thrt=0x370246 wrr2=0x0 wrr3=0x0 ostd2=0x3f3f
```

The later snapshot remained unchanged: OVL status was `0x6025`, RDMA status
was `0x77`, RDMA IRQ 313 was zero and three vblank waits timed out. DSI IRQ
309 still held 31 events, so the failure remained downstream of DSI command
traffic.

The clock dump supplied the next direct evidence. `mm_smi_common`,
`mm_smi_infra`, `mm_smi_gals` and `mm_smi_iommu` all had nonzero prepare/enable
counts, but their hardware state was `?` because patch 0020 registered them as
`GATE_DUMMY`. The vendor clock driver has the same dummy entries, while the
vendor power-domain callback explicitly clears CG0 bits 11/17/27 and CG1 bit 0.

Patch 0049 changes only those four clock descriptors to the corresponding
`GATE_MM0`/`GATE_MM1` entries. No register value, clock ID, DTS property or
display tuning value changes. V70 must first show `Y` for all four gates and
then show the expected LARB values at component bind.

## V70 build and preflight

V70 passed Build Mainline run `46135235963`. The kernel changed to SHA-256
`27813ac1cebeb85cc89ac3bf59446ce57b6830df39974e6b94a9435412b6de3e`;
the DTB remained `f041bf87b0b7b9df72be2e00b274c184b19eb7ea4625b5f0211f7ddd2288d665`.
The build log is free of compiler warning/error lines and explicitly compiled
`drivers/clk/mediatek/clk-mt6873-mm.o`.

The recovery image is 16,054,272 bytes with SHA-256
`90918d3f8db33888fa3f58ddd016cf94ae2161fb3cbd1a945c2eeffec10c998c`
and passed all 59 assembly checks. The non-writing flash preflight found the
expected current recovery hash
`3bcdb7329697cb200d3faae3aeeb8241b25c11cb15281338f4a0e4287c973468`.
V70 was then written only to recovery and manually booted.

## V70 hardware result

All four SMI clocks reported hardware-enabled at 546 MHz:

```text
mm_smi_common  Y
mm_smi_infra   Y
mm_smi_gals    Y
mm_smi_iommu   Y
```

LARB0 retained the vendor values in the delayed snapshot:

```text
0x0024 = 0x00370256
0x0108 = 0x00000007
0x010c = 0x00000007
0x0200 = 0x00000202
0x0204 = 0x00000202
0x0208 = 0x00002828
0x020c = 0x00000a0a
0x0210 = 0x00000c0c
0x0214 = 0x00002828
```

The vendor writes one byte per port (`02, 02, 28, 0a, 0c, 28`); hardware
readback expands each active field into the repeated 16-bit form.

The physical panel displayed the Linux boot text, a correctly colored Linux
penguin and a pure-white framebuffer. The log independently recorded an
enabled 1080x2400 DSI connector, no vblank timeout, OVL IRQ progress from 38
to 292 and a completed white-framebuffer write.

OVL status changed from the failing `0x6025` to `0x007fc003`; FME underflow,
RDMA0 abnormal EOF, RDMA0 SMI underflow and abnormal SOF are clear. RDMA status
changed from `0x77` to `0x67`; FIFO underflow and abnormal EOF are clear while
FIFO-empty remains latched.

RDMA IRQ 313 read zero because `mtk_crtc_enable_vblank()` enables vblank only
on component zero. In this path that is OVL0, whose IRQ advanced from 38 to
292; RDMA0's frame-end interrupt was never enabled. This is current upstream
behavior, not a scanout failure. The run proves basic visible scanout, not
animation, long-running stability, independent panel power-up or the full PQ
chain.

## V71 dynamic framebuffer

V71 reused the V70 kernel and DTB and changed only the initramfs. It wrote an
initial white framebuffer followed by six timed white/gray updates:

```text
dynamic_frame=1 pattern=gray
dynamic_frame=2 pattern=white
dynamic_frame=3 pattern=gray
dynamic_frame=4 pattern=white
dynamic_frame=5 pattern=gray
dynamic_frame=6 pattern=white
dynamic_test=frames_completed count=6
```

The physical panel showed the intended approximately two-second cadence with
no freeze, corruption, wrong color or reboot. The delayed snapshot retained
LARB0 configuration, OVL `0x7fc003`, RDMA `0x67` and all four SMI gates; it
reported no vblank timeout or display fault.

The direct `/dev/fb0` writes did not add KMS page-flip events, so OVL IRQ did
not advance beyond the initial modeset. This proves repeated display-memory
refresh, not atomic commit behavior. The next test should run a real DRM
userspace probe followed by modetest or Weston.

## V72 DRM capability probe

V72 reused the V70 kernel and DTB and added the reviewed static aarch64
`drmprobe`. Its complete output was:

```text
open /dev/dri/card0 = OK (O_RDWR)
SET_CLIENT_CAP(ATOMIC=3,1) -> 0
SET_CLIENT_CAP(UNIVERSAL_PLANES=2,1) -> 0
DUMB_BUFFER=1
ASYNC_PAGE_FLIP=0
CURSOR=512x512
ADDFB2_MODIFIERS=1
CREATE_DUMB 64x64x32 -> 0 handle=1 pitch=256 size=16384
DESTROY_DUMB -> 0
GETRESOURCES crtcs=1 connectors=1 encoders=1 fbs=0
max WxH=4096x4096
```

The probe exited zero and the subsequent white-frame write completed with no
display warning or vblank timeout. This establishes the KMS client and
dumb-buffer prerequisites. It does not perform framebuffer mapping, `ADDFB2`,
modeset, page flip or completion-event handling.

## V73 raw DRM page flips

V73 reused the exact V70 kernel and DTB and added a freestanding `drmflip`
client. The direct log proves:

```text
SET_MASTER=0
GETCRTC crtc=0x3b current-fb=0x3c mode=1080x2400@63
CREATE_DUMB red/blue=0, 10,368,000 bytes, pitch 4320
MAP_DUMB red/blue=0
ADDFB2 red/blue=0, fb IDs 0x3e/0x3f
PAGE_FLIP 0x3e -> FLIP_COMPLETE user 0x1111 sequence 295
PAGE_FLIP 0x3f -> FLIP_COMPLETE user 0x2222 sequence 407
PAGE_FLIP 0x3c -> FLIP_COMPLETE user 0x3333 sequence 520
restored original framebuffer
DROP_MASTER=0
exit status=0
```

The physical panel showed solid red for about two seconds, solid blue for
about two seconds, then the original console and final white frame. LARB0,
OVL `0x7fc003`, RDMA `0x67` and the SMI gates remained stable, with no vblank
timeout or display fault.

This closes the raw mainline KMS page-flip gate. Remaining work is a full
userspace compositor, longer-duration stress, independent panel power and the
complete PQ chain.
