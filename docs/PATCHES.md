# Patch groups

The patches apply in numeric order to a clean Linux `v6.18.59` tree.

```text
0001          UART and initial PMIC-wrapper clocks
0002-0003     UFS clock IDs and clock chain
0004-0005     MT6873 pinctrl binding and driver data
0006-0007     UFS host/PHY fallback bindings
0008          SPI clock chain
0009-0011     USB clock chain and xHCI/T-PHY fallback bindings
0012-0013     I2C binding and clock chain
0014-0015     MT6360 TCPC alert/control handling
0016-0018     MTU3 binding and MT6873 T-PHY quirks
0019          MT6873 CONN power domain
0020          MT6873 display clock providers
0021          MT6873 GCE clock
0022          MT6873 DISP power domain
0023          MT6873 display mutex
0024-0027     power-domain and bus-protection diagnostics
0028          MT6873 MIPI TX PHY
0029          MT6873 DSI host data
0030          panel-provided MT6873 DSI HS rate
0031          Samsung S6E8FC01 panel driver and binding
0032          MT6873 SMI common/LARB bindings
0033          MT6873 SMI common/LARB provider data
0034          MT6873 main IOMMU binding
0035          MT6873 main IOMMU provider data
0036          MT6873 OVL/OVL-2L/RDMA binding fallbacks
0037          MT6873 direct DRM component-master path
```

Patches are evidence-backed pieces of an in-progress port, not a claim that
all corresponding hardware is fully supported.
