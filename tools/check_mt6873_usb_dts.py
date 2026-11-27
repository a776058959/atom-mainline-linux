#!/usr/bin/env python3
"""Check the formal MT6873 USB2 peripheral DTS evidence and topology."""

import argparse
import re
from pathlib import Path


LOCAL_MACRO = re.compile(r"\bATOM_MT6873_[A-Z0-9_]+\b")

EXPECTED_CLOCK_MACROS = {
    "ATOM_MT6873_CLK_INFRA_AO_PMIC_CG_TMR": (
        "CLK_INFRA_AO_PMIC_CG_TMR",
        1,
    ),
    "ATOM_MT6873_CLK_INFRA_AO_PMIC_CG_AP": (
        "CLK_INFRA_AO_PMIC_CG_AP",
        2,
    ),
    "ATOM_MT6873_CLK_INFRA_AO_GCE_CG": (
        "CLK_INFRA_AO_GCE_CG",
        9,
    ),
    "ATOM_MT6873_CLK_INFRA_AO_I2C0_CG": (
        "CLK_INFRA_AO_I2C0_CG",
        12,
    ),
    "ATOM_MT6873_CLK_INFRA_AO_UART0_CG": (
        "CLK_INFRA_AO_UART0_CG",
        22,
    ),
    "ATOM_MT6873_CLK_INFRA_AO_UNIPRO_SYSCLK_CG": (
        "CLK_INFRA_AO_UNIPRO_SYSCLK_CG",
        66,
    ),
    "ATOM_MT6873_CLK_INFRA_AO_UFS_MP_SAP_BCLK_CG": (
        "CLK_INFRA_AO_UFS_MP_SAP_BCLK_CG",
        68,
    ),
    "ATOM_MT6873_CLK_INFRA_AO_UFS_CG": (
        "CLK_INFRA_AO_UFS_CG",
        83,
    ),
    "ATOM_MT6873_CLK_INFRA_AO_SSUSB_CG": (
        "CLK_INFRA_AO_SSUSB_CG",
        57,
    ),
    "ATOM_MT6873_CLK_INFRA_AO_SSUSB_XHCI_CG": (
        "CLK_INFRA_AO_SSUSB_XHCI_CG",
        86,
    ),
    "ATOM_MT6873_CLK_INFRA_AO_AP_DMA_CG": (
        "CLK_INFRA_AO_AP_DMA_CG",
        129,
    ),
    "ATOM_MT6873_CLK_IMP_IIC_WRAP_W_AP_I2C5_CG_RO": (
        "CLK_IMP_IIC_WRAP_W_AP_I2C5_CG_RO",
        1,
    ),
    "ATOM_MT6873_CLK_TOP_MUX_DISP": (
        "CLK_TOP_MUX_DISP",
        5,
    ),
    "ATOM_MT6873_CLK_MM_DISP_MUTEX0": (
        "CLK_MM_DISP_MUTEX0",
        1,
    ),
    "ATOM_MT6873_CLK_MM_SMI_INFRA": (
        "CLK_MM_SMI_INFRA",
        12,
    ),
    "ATOM_MT6873_CLK_MM_DSI0": (
        "CLK_MM_DSI0",
        16,
    ),
    "ATOM_MT6873_CLK_MM_SMI_COMMON": (
        "CLK_MM_SMI_COMMON",
        18,
    ),
    "ATOM_MT6873_CLK_MM_SMI_GALS": (
        "CLK_MM_SMI_GALS",
        28,
    ),
    "ATOM_MT6873_CLK_MM_SMI_IOMMU": (
        "CLK_MM_SMI_IOMMU",
        32,
    ),
    "ATOM_MT6873_CLK_MM_DSI_DSI0": (
        "CLK_MM_DSI_DSI0",
        33,
    ),
}

EXPECTED_PIN_MACROS = {
    "ATOM_MT6873_PINMUX_GPIO111_GPIO": (111, 0, "GPIO111"),
    "ATOM_MT6873_PINMUX_GPIO112_GPIO": (112, 0, "GPIO112"),
    "ATOM_MT6873_PINMUX_GPIO113_GPIO": (113, 0, "GPIO113"),
    "ATOM_MT6873_PINMUX_GPIO202_SCL5": (202, 1, "SCL5"),
    "ATOM_MT6873_PINMUX_GPIO203_SDA5": (203, 1, "SDA5"),
}

EXPECTED_POWER_DOMAIN_CONN = 2
EXPECTED_POWER_DOMAIN_DIS = 17
INHERITED_MT8192_POWER_DOMAINS = {
    0: "AUDIO",
    1: "CONN",
    2: "MFG0",
    9: "DISP",
}
VENDOR_ENABLED_ISOLATED_LABELS = {
    "dsi0": ("dsi0-placeholder", "dsi@14010000"),
    "i2c5": ("i2c5-placeholder", "i2c@11e00000"),
    "i2c6": ("i2c6-placeholder", "i2c@11f01000"),
    "spi7": ("spi7-placeholder", "spi@1101e000"),
}
UNSUPPORTED_INHERITED_CONSUMERS = (
    "audsys",
    "afe",
    "mfgcfg",
    "ovl0",
    "ovl_2l0",
    "rdma0",
    "color0",
    "ccorr0",
    "aal0",
    "gamma0",
    "postmask0",
    "dither0",
    "ovl_2l2",
    "rdma4",
    "imgsys",
    "larb9",
    "imgsys2",
    "larb11",
    "vcodec_dec",
    "larb5",
    "vdecsys_soc",
    "larb4",
    "vdecsys",
    "vencsys",
    "larb7",
    "vcodec_enc",
    "camsys",
    "larb13",
    "larb14",
    "larb16",
    "larb17",
    "larb18",
    "camsys_rawa",
    "camsys_rawb",
    "camsys_rawc",
    "ipesys",
    "larb20",
    "larb19",
    "mdpsys",
    "larb2",
)

VENDOR_DTBO_SYMBOLS = (
    Path(__file__).resolve().parent.parent
    / "mainline"
    / "mt6873-atom-vendor-dtbo-symbols.txt"
)
def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def extract_braced_body(text, pattern, description):
    match = re.search(pattern, text, flags=re.M | re.S)
    if not match:
        raise SystemExit("[FATAL] 缺少{}".format(description))

    opening = text.rfind("{", match.start(), match.end())
    if opening < 0:
        raise SystemExit("[FATAL] {} 缺少左花括号".format(description))

    depth = 0
    for offset in range(opening, len(text)):
        char = text[offset]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[opening + 1:offset]
    raise SystemExit("[FATAL] {} 花括号不平衡".format(description))


def require_tokens(name, text, tokens):
    missing = [token for token in tokens if token not in text]
    if missing:
        raise SystemExit(
            "[FATAL] {} 缺少已实测值: {}".format(name, ", ".join(missing))
        )


def check_labels(dts, base):
    clean = strip_comments(dts)
    if clean.count("{") != clean.count("}"):
        raise SystemExit(
            "[FATAL] DTS 括号不平衡: {} open, {} close".format(
                clean.count("{"), clean.count("}")
            )
        )

    searchable = base + "\n" + dts
    references = set(
        re.findall(r"&([A-Za-z_][A-Za-z0-9_]*)", re.sub(r'"[^"]*"', "", clean))
    )
    missing = [
        label
        for label in sorted(references)
        if not re.search(r"\b{}\s*:".format(re.escape(label)), searchable)
    ]
    if missing:
        raise SystemExit(
            "[FATAL] DTS 引用了未定义 label: {}".format(
                ", ".join("&" + label for label in missing)
            )
        )


def check_macros(dts, patch_root):
    for header in ("mt6873-clk.h", "mt6873-pinfunc.h"):
        if header in dts:
            raise SystemExit(
                "[FATAL] transitional DTS 不得同时 include 冲突头文件 " + header
            )

    patch_definitions = "\n".join(
        read_text(path) for path in sorted(Path(patch_root).glob("*.patch"))
    )
    local_definitions = {
        match.group(1): match.group(2).strip()
        for match in re.finditer(
            r"^#define\s+(ATOM_MT6873_[A-Z0-9_]+)\s+([^\n]+)",
            dts,
            flags=re.M,
        )
    }
    used = set(LOCAL_MACRO.findall(strip_comments(dts)))
    missing = sorted(used - local_definitions.keys())
    if missing:
        raise SystemExit(
            "[FATAL] DTS 使用了未定义的本地宏: {}".format(", ".join(missing))
        )
    unprefixed = sorted(
        set(re.findall(r"(?<![A-Z0-9_])(?:CLK|PINMUX)_[A-Z0-9_]+", strip_comments(dts)))
    )
    if unprefixed:
        raise SystemExit(
            "[FATAL] DTS 使用了可能与 MT8192 冲突的未加前缀宏: {}".format(
                ", ".join(unprefixed)
            )
        )

    for local_name, (patch_name, expected_value) in EXPECTED_CLOCK_MACROS.items():
        if local_name not in local_definitions:
            raise SystemExit("[FATAL] DTS 缺少本地 clock 宏 " + local_name)
        try:
            actual_value = int(local_definitions[local_name], 0)
        except ValueError:
            raise SystemExit("[FATAL] 本地 clock 宏不是整数: " + local_name)
        patch_values = [
            int(value, 0)
            for value in re.findall(
                r"^\+#define\s+{}\s+([0-9]+)\b".format(
                    re.escape(patch_name)
                ),
                patch_definitions,
                flags=re.M,
            )
        ]
        if not patch_values or patch_values[-1] != expected_value:
            raise SystemExit(
                "[FATAL] 补丁中的 {} 不等于预期值 {}".format(
                    patch_name, expected_value
                )
            )
        if actual_value != expected_value:
            raise SystemExit(
                "[FATAL] {}={}，补丁值为 {}".format(
                    local_name, actual_value, expected_value
                )
            )

    for local_name, (pin, function, function_name) in EXPECTED_PIN_MACROS.items():
        if local_name not in local_definitions:
            raise SystemExit("[FATAL] DTS 缺少本地 pinmux 宏 " + local_name)
        match = re.fullmatch(
            r"\(\(\s*{}\s*<<\s*8\s*\)\s*\|\s*{}\s*\)".format(
                pin, function
            ) if function else r"\(\s*{}\s*<<\s*8\s*\)".format(pin),
            local_definitions[local_name],
        )
        if not match:
            raise SystemExit(
                "[FATAL] {} 不是 GPIO{} 的 MTK pinmux 编码".format(
                    local_name, pin
                )
            )
        patch_pattern = (
            r"^\+#define\s+PINMUX_GPIO{pin}__FUNC_{function_name}\s+"
            r"\(MTK_PIN_NO\({pin}\)\s*\|\s*{function}\)"
        ).format(
            pin=pin,
            function=function,
            function_name=re.escape(function_name),
        )
        if not re.search(patch_pattern, patch_definitions, flags=re.M):
            raise SystemExit(
                "[FATAL] 补丁未定义预期的 GPIO{} pinmux 宏".format(pin)
            )


def check_power_domains(dts, patch_root):
    clean = strip_comments(dts)
    match = re.search(r"&spm\s*\{(?P<body>.*?)\n\};", clean, flags=re.S)
    if not match:
        raise SystemExit("[FATAL] DTS 缺少 MT6873 SPM 覆盖节点 &spm")

    body = match.group("body")
    require_tokens(
        "power domains",
        body,
        (
            'compatible = "mediatek,mt6873-power-controller"',
            "access-controllers = <&infracfg>",
            "reg = <ATOM_MT6873_POWER_DOMAIN_CONN>",
            "reg = <ATOM_MT6873_POWER_DOMAIN_DIS>",
            "clocks = <&topckgen ATOM_MT6873_CLK_TOP_MUX_DISP>",
            "<&mmsys ATOM_MT6873_CLK_MM_SMI_INFRA>",
            'clock-names = "disp", "disp-0", "disp-1", "disp-2", "disp-3"',
            "mediatek,infracfg = <&infracfg>",
            "#power-domain-cells = <0>",
        ),
    )

    for domain_id, name in INHERITED_MT8192_POWER_DOMAINS.items():
        deleted = "/delete-node/ power-domain@{};".format(domain_id)
        if deleted not in body:
            raise SystemExit(
                "[FATAL] &spm 未删除继承的 MT8192 {} domain {}".format(
                    name, domain_id
                )
            )

    domains = re.findall(
        r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*:\s*)?"
        r"power-domain@([0-9A-Fa-f]+)\s*\{",
        body,
        flags=re.M,
    )
    expected_domains = [
        str(EXPECTED_POWER_DOMAIN_CONN),
        str(EXPECTED_POWER_DOMAIN_DIS),
    ]
    if domains != expected_domains:
        raise SystemExit(
            "[FATAL] formal DTS power domains must be {}; found {}".format(
                "/".join(expected_domains),
                ", ".join(domains) if domains else "none",
            )
        )

    for token in ("CLK_TOP_AUD_INTBUS_SEL", "MT8192_POWER_DOMAIN"):
        if token in body:
            raise SystemExit(
                "[FATAL] MT6873 power domain contains MT8192 resource: " + token
            )

    local_macro = re.search(
        r"^#define\s+ATOM_MT6873_POWER_DOMAIN_CONN\s+([0-9]+)\s*$",
        clean,
        flags=re.M,
    )
    if (
        not local_macro
        or int(local_macro.group(1), 0) != EXPECTED_POWER_DOMAIN_CONN
    ):
        raise SystemExit(
            "[FATAL] ATOM_MT6873_POWER_DOMAIN_CONN 必须等于 {}".format(
                EXPECTED_POWER_DOMAIN_CONN
            )
        )

    patch = (
        Path(patch_root)
        / "0019-pmdomain-mediatek-add-mt6873-conn-domain-v6.18.patch"
    ).read_text(encoding="utf-8")
    if not re.search(
        r"^\+#define\s+MT6873_POWER_DOMAIN_CONN\s+2\b",
        patch,
        flags=re.M,
    ):
        raise SystemExit("[FATAL] 0019 的 MT6873 CONN domain 编号不是 2")

    for marker in (
        'compatible = "mediatek,mt6873-power-controller"',
        "[MT6873_POWER_DOMAIN_CONN] = {",
        ".sta_mask = BIT(1)",
        ".ctl_offs = 0x0304",
        ".pwr_sta_offs = 0x016c",
        ".pwr_sta2nd_offs = 0x0170",
        ".caps = MTK_SCPD_KEEP_DEFAULT_OFF",
        "MT6873_TOP_AXI_PROT_EN_CONN_2ND",
        "MT6873_TOP_AXI_PROT_EN_1_CONN",
    ):
        if marker not in patch:
            raise SystemExit(
                "[FATAL] 0019 缺少 MT6873 CONN 源码依据标记: " + marker
            )


    local_macro = re.search(
        r"^#define\s+ATOM_MT6873_POWER_DOMAIN_DIS\s+([0-9]+)\s*$",
        clean,
        flags=re.M,
    )
    if (
        not local_macro
        or int(local_macro.group(1), 0) != EXPECTED_POWER_DOMAIN_DIS
    ):
        raise SystemExit(
            "[FATAL] ATOM_MT6873_POWER_DOMAIN_DIS must equal {}".format(
                EXPECTED_POWER_DOMAIN_DIS
            )
        )

    dis_patch = (
        Path(patch_root)
        / "0022-pmdomain-mediatek-add-mt6873-dis-domain-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "[MT6873_POWER_DOMAIN_DIS] = {",
        ".sta_mask = BIT(20)",
        ".ctl_offs = 0x0350",
        ".pwr_sta_offs = 0x016c",
        ".pwr_sta2nd_offs = 0x0170",
        ".sram_pdn_bits = GENMASK(8, 8)",
        ".sram_pdn_ack_bits = GENMASK(12, 12)",
        ".caps = MTK_SCPD_KEEP_DEFAULT_OFF",
        "MT6873_TOP_AXI_PROT_EN_MM_DISP",
        "MT6873_TOP_AXI_PROT_EN_MM_2_DISP",
        "MT6873_TOP_AXI_PROT_EN_DISP",
        "MT6873_TOP_AXI_PROT_EN_MM_DISP_2ND",
        "MT6873_TOP_AXI_PROT_EN_MM_2_DISP_2ND",
    ):
        if marker not in dis_patch:
            raise SystemExit(
                "[FATAL] 0022 missing MT6873 DIS source marker: " + marker
            )


def check_display_clock_provider(dts, patch_root):
    clean = strip_comments(dts)

    deletion = re.search(
        r"^\s*&\{/soc\}\s*\{(?P<body>.*?)\};",
        clean,
        flags=re.M | re.S,
    )
    if not deletion:
        raise SystemExit("[FATAL] 缺少 &{/soc} 节点覆盖")

    mmsys = extract_braced_body(
        clean,
        r"^\s*&mmsys\s*\{",
        "MT6873 MMSYS provider 覆盖节点",
    )
    require_tokens(
        "MMSYS provider",
        mmsys,
        (
            'compatible = "mediatek,mt6873-mmsys", "syscon"',
            'status = "okay"',
        ),
    )

    patch = (
        Path(patch_root)
        / "0020-clk-mediatek-add-mt6873-display-clock-providers-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "+static const struct mtk_mmsys_driver_data mt6873_mmsys_driver_data",
        '+	.clk_driver = "clk-mt6873-mm"',
        "+static const struct mtk_gate_regs mm0_cg_regs",
        "+	.set_ofs = 0x104",
        "+	.clr_ofs = 0x108",
        "+	.sta_ofs = 0x100",
        "+static const struct mtk_gate_regs mm1_cg_regs",
        "+	.set_ofs = 0x114",
        "+	.clr_ofs = 0x118",
        "+	.sta_ofs = 0x110",
        "+static const struct mtk_gate_regs mm2_cg_regs",
        "+	.set_ofs = 0x1a4",
        "+	.clr_ofs = 0x1a8",
        "+	.sta_ofs = 0x1a0",
        '+	FACTOR(CLK_TOP_UNIVPLL_D6_D2, "univpll_d6_d2", "univpll", 1, 12)',
        '+	FACTOR(CLK_TOP_MMPLL_D5_D2, "mmpll_d5_d2", "mmpll", 1, 10)',
        '+	FACTOR(CLK_TOP_MMPLL_D6_D2, "mmpll_d6_d2", "mmpll", 1, 12)',
        '+	FACTOR(CLK_TOP_MMPLL_D7, "mmpll_d7", "mmpll", 1, 7)',
        '+	MUX_GATE_CLR_SET_UPD(CLK_TOP_MUX_DISP, "disp_sel", disp_parents',
        "+		.id = CLK_APMIXED_MMPLL",
        "+		.reg = 0x360",
        "+		.pwr_reg = 0x36c",
        "+#define CLK_TOP_MUX_DISP		5",
        "+#define CLK_APMIXED_MMPLL		4",
        "+#define CLK_MM_DISP_MUTEX0		1",
        "+#define CLK_MM_DSI0			16",
        "+#define CLK_MM_DSI_DSI0			33",
        "+#define CLK_MM_NR_CLK			38",
    ):
        if marker not in patch:
            raise SystemExit(
                "[FATAL] 0020 缺少 MT6873 display provider 源码依据: "
                + marker
            )

    for forbidden in (
        "mt8192_mmsys_driver_data,\n+}",
        '"dpi_sel"',
        "MT8192_POWER_DOMAIN_DISP",
        "MT8192_MMSYS_SW0_RST_B_DISP_DSI0",
    ):
        if forbidden in patch:
            raise SystemExit(
                "[FATAL] 0020 不应把 MT8192 显示值当作 MT6873 值: "
                + forbidden
            )

    gce = extract_braced_body(
        clean,
        r"^\s*&gce\s*\{",
        "MT6873 GCE 时钟覆盖节点",
    )
    require_tokens(
        "GCE clock",
        gce,
        (
            "clocks = <&infracfg ATOM_MT6873_CLK_INFRA_AO_GCE_CG>",
        ),
    )

    gce_patch = read_text(
        Path(patch_root)
        / "0021-clk-mediatek-add-mt6873-gce-clock-v6.18.patch"
    )
    for marker in (
        "+#define CLK_INFRA_AO_GCE_CG		9",
        '+	GATE_MTK(CLK_INFRA_AO_GCE_CG, "infracfg_ao_gce_cg",',
        '+		 "axi_sel", &infra_ao_cg_regs, 8,',
    ):
        if marker not in gce_patch:
            raise SystemExit(
                "[FATAL] 0021 缺少 MT6873 GCE 时钟源码依据: " + marker
            )


def check_mmsys_routes(patch_root):
    patch = (
        Path(patch_root)
        / "0025-soc-mediatek-add-mt6873-mmsys-routes-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "+#define MT6873_DISP_OVL0_2L_OUT0_MOUT_EN",
        "+#define MT6873_DISP_OVL0_OUT1_MOUT_EN",
        "+#define MT6873_DISP_RDMA0_SEL_IN",
        "+#define MT6873_DISP_RDMA0_SOUT_SEL",
        "+#define MT6873_DISP_DITHER0_MOUT_EN",
        "+#define MT6873_DISP_DSI0_SEL_IN",
        "+#define MT6873_DISP_OVL2_2L_OUT0_MOUT_EN",
        "+static const struct mtk_mmsys_routes mt6873_mmsys_routing_table[]",
        "+	.routes = mt6873_mmsys_routing_table",
        "+	.num_routes = ARRAY_SIZE(mt6873_mmsys_routing_table)",
        '+#include "mt6873-mmsys.h"',
    ):
        if marker not in patch:
            raise SystemExit(
                "[FATAL] 0025 missing MT6873 MMSYS route marker: " + marker
            )

    forbidden = "MT8192_"
    if forbidden in patch:
        raise SystemExit(
            "[FATAL] 0025 must not reuse MT8192 route constants"
        )


def check_bus_protection_diagnostics(patch_root):
    patch = (
        Path(patch_root)
        / "0026-pmdomain-mediatek-report-bus-protection-failure-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "static void scpsys_bus_protect_dump_failure",
        "expected_ack = (bpd->bus_prot_sta_block ==",
        "bus-protection[%d] clear failed:",
        "set[%#x]=%#x(rc=%d) clr[%#x]=%#x(rc=%d)",
        "scpsys_bus_protect_dump_failure(pd, bpd, i);",
    ):
        if marker not in patch:
            raise SystemExit(
                "[FATAL] 0026 missing bus-protection diagnostic marker: "
                + marker
            )


def check_bus_protection_ack_policy(patch_root):
    patch = (
        Path(patch_root)
        / (
            "0027-pmdomain-mediatek-ignore-mt6873-disp-bus-prot-ack-"
            "v6.18.patch"
        )
    ).read_text(encoding="utf-8")
    marker = "+\t\t\tBUS_PROT_WR_IGN(INFRA,"
    if patch.count(marker) != 3:
        raise SystemExit(
            "[FATAL] 0027 must convert exactly three DIS protection entries"
        )
    for name in (
        "MT6873_TOP_AXI_PROT_EN_DISP",
        "MT6873_TOP_AXI_PROT_EN_MM_DISP_2ND",
        "MT6873_TOP_AXI_PROT_EN_MM_2_DISP_2ND",
    ):
        if name not in patch:
            raise SystemExit(
                "[FATAL] 0027 missing DIS protection mask: " + name
            )


def check_mt6873_mipi_tx(patch_root):
    patch = (
        Path(patch_root)
        / "0028-phy-mediatek-add-mt6873-mipi-tx-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "+#define MIPITX_VOLTAGE_SEL",
        "+#define MIPITX_PLL_CON4",
        "+static u32 mtk_mipi_tx_get_pcw",
        "+static int mtk_mipi_tx_pll_enable",
        "+static void mtk_mipi_tx_pll_disable",
        "+const struct mtk_mipitx_data mt6873_mipitx_data",
        '+	{ .compatible = "mediatek,mt6873-mipi-tx"',
        "+phy-mtk-mipi-dsi-drv-y",
        "+      - const: mediatek,mt6873-mipi-tx",
    ):
        if marker not in patch:
            raise SystemExit(
                "[FATAL] 0028 missing MT6873 MIPI TX marker: " + marker
            )


def check_display_probe_dts(dts, patch_root):
    clean = strip_comments(dts)

    mipi_tx = extract_braced_body(
        clean,
        r"^\s*&mipi_tx0\s*\{",
        "MT6873 MIPI TX override",
    )
    require_tokens(
        "MT6873 MIPI TX",
        mipi_tx,
        (
            'compatible = "mediatek,mt6873-mipi-tx"',
            "clocks = <&clk26m>",
            'clock-output-names = "mipi_tx0_pll"',
            'status = "okay"',
        ),
    )

    dsi = extract_braced_body(
        clean,
        r"^\s*mt6873_dsi:\s*dsi@14010000\s*\{",
        "MT6873 DSI host",
    )
    require_tokens(
        "MT6873 DSI host",
        dsi,
        (
            'compatible = "mediatek,mt6873-dsi"',
            "reg = <0 0x14010000 0 0x1000>",
            "GIC_SPI 265 IRQ_TYPE_LEVEL_HIGH",
            "ATOM_MT6873_CLK_MM_DSI0",
            "ATOM_MT6873_CLK_MM_DSI_DSI0",
            "<&mipi_tx0>",
            'clock-names = "engine", "digital", "hs"',
            "power-domains = <&spm ATOM_MT6873_POWER_DOMAIN_DIS>",
            'phy-names = "dphy"',
            'status = "okay"',
        ),
    )
    panel = extract_braced_body(
        dsi,
        r"^\s*panel@0\s*\{",
        "S6E8FC01 panel child",
    )
    require_tokens(
        "S6E8FC01 panel child",
        panel,
        (
            'compatible = "samsung,s6e8fc01"',
            "power-supply = <&mt6359_vibr_ldo_reg>",
            "enable-gpios = <&pio 29 GPIO_ACTIVE_HIGH>",
            "reset-gpios = <&pio 42 GPIO_ACTIVE_HIGH>",
            'status = "okay"',
            "remote-endpoint = <&dsi_out>",
        ),
    )
    if "remote-endpoint = <&panel_in>" not in dsi:
        raise SystemExit("[FATAL] DSI output 未连接到 S6E8FC01 panel")
    if re.search(r"\bresets\s*=", dsi):
        raise SystemExit(
            "[FATAL] DSI probe topology 不得猜测 MMSYS reset 映射"
        )

    patches = {
        "DSI host": (
            "0029-drm-mediatek-add-mt6873-dsi-host-v6.18.patch",
            (
                '+	{ .compatible = "mediatek,mt6873-dsi"',
                "+	bool bypass_shadow;",
                "+	.bypass_shadow = true,",
                "+	.has_size_ctl = true,",
            ),
        ),
        "panel rate": (
            "0030-drm-mediatek-use-mt6873-panel-hs-rate-v6.18.patch",
            (
                "+	bool use_peripheral_hs_rate;",
                "+	dsi->data_rate = dsi->peripheral->hs_rate;",
                "+	.use_peripheral_hs_rate = true;",
            ),
        ),
        "panel": (
            "0031-drm-panel-add-samsung-s6e8fc01-v6.18.patch",
            (
                '+    const: samsung,s6e8fc01',
                '+	{ .compatible = "samsung,s6e8fc01" }',
                "+	dsi->hs_rate = 1098000000;",
                "+		usleep_range(10000, 11000);",
            ),
        ),
    }

    for label, (filename, markers) in patches.items():
        patch = (Path(patch_root) / filename).read_text(encoding="utf-8")
        normalized_patch = re.sub(r"\s+", " ", patch)
        for marker in markers:
            normalized_marker = re.sub(r"\s+", " ", marker).rstrip(";")
            if normalized_marker not in normalized_patch:
                raise SystemExit(
                    "[FATAL] {} 补丁缺少显示 probe 依据: {}".format(
                        label, marker
                    )
                )


def check_mutex_consumer(dts, patch_root):
    clean = strip_comments(dts)
    mutex = extract_braced_body(
        clean,
        r"^\s*&mutex\s*\{",
        "MT6873 mutex consumer",
    )
    require_tokens(
        "MT6873 mutex consumer",
        mutex,
        (
            'compatible = "mediatek,mt6873-disp-mutex"',
            "clocks = <&mmsys ATOM_MT6873_CLK_MM_DISP_MUTEX0>",
            "power-domains = <&spm ATOM_MT6873_POWER_DOMAIN_DIS>",
            'status = "okay"',
        ),
    )

    patch = (
        Path(patch_root)
        / "0023-soc-mediatek-add-mt6873-disp-mutex-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "+      - mediatek,mt6873-disp-mutex",
        "+              - mediatek,mt6873-disp-mutex",
        "+#define MT6873_MUTEX_MOD_DISP_RSZ0",
        "+#define MT6873_MUTEX_MOD_DISP_DSC0",
        "+#define MT6873_MUTEX_MOD_DISP_DSC1",
        "+#define MT6873_MUTEX_MOD_DISP_WDMA0",
        "+#define MT6873_MUTEX_MOD_DISP_PWM0",
        "+#define MT6873_MUTEX_MOD_MDP_RDMA4",
        "+static const u8 mt6873_mutex_mod",
        "+static const struct mtk_mutex_data mt6873_mutex_driver_data",
        "+	.mutex_mod = mt6873_mutex_mod",
        "+	.mutex_sof = mt8183_mutex_sof",
        "+	.mutex_mod_reg = MT8183_MUTEX0_MOD0",
        "+	.mutex_mod1_reg = MT8183_MUTEX0_MOD1",
        "+	.mutex_sof_reg = MT8183_MUTEX0_SOF0",
        (
            '+	{ .compatible = "mediatek,mt6873-disp-mutex", '
            ".data = &mt6873_mutex_driver_data },"
        ),
    ):
        if marker not in patch:
            raise SystemExit(
                "[FATAL] 0023 missing MT6873 mutex source marker: " + marker
            )

    power_patch = (
        Path(patch_root)
        / "0024-pmdomain-mediatek-log-power-on-failures-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "failed to enable domain clocks",
        "failed to power on",
        "failed to enable subsystem clocks",
        "failed to enable SRAM",
        "failed to release bus protection",
    ):
        if marker not in power_patch:
            raise SystemExit(
                "[FATAL] 0024 missing power-stage diagnostic: " + marker
            )


def check_smi_providers(dts, patch_root):
    clean = strip_comments(dts)

    smi_common = extract_braced_body(
        clean,
        r"^\s*&smi_common\s*\{",
        "MT6873 SMI common provider",
    )
    require_tokens(
        "MT6873 SMI common",
        smi_common,
        (
            'compatible = "mediatek,mt6873-smi-common"',
            "<&mmsys ATOM_MT6873_CLK_MM_SMI_COMMON>",
            "<&mmsys ATOM_MT6873_CLK_MM_SMI_INFRA>",
            "<&mmsys ATOM_MT6873_CLK_MM_SMI_GALS>",
            'clock-names = "apb", "smi", "gals0", "gals1"',
            "power-domains = <&spm ATOM_MT6873_POWER_DOMAIN_DIS>",
            'status = "okay"',
        ),
    )
    if smi_common.count("ATOM_MT6873_CLK_MM_SMI_GALS") != 2:
        raise SystemExit(
            "[FATAL] MT6873 SMI common must feed both gals0 and gals1"
        )

    for larb_id in (0, 1):
        larb = extract_braced_body(
            clean,
            r"^\s*&larb{}\s*\{{".format(larb_id),
            "MT6873 LARB{} provider".format(larb_id),
        )
        require_tokens(
            "MT6873 LARB{}".format(larb_id),
            larb,
            (
                'compatible = "mediatek,mt6873-smi-larb"',
                "clocks = <&clk26m>, <&clk26m>",
                'clock-names = "apb", "smi"',
                "power-domains = <&spm ATOM_MT6873_POWER_DOMAIN_DIS>",
                'status = "okay"',
            ),
        )

    iommu = extract_braced_body(
        clean,
        r"^\s*&iommu0\s*\{",
        "MT6873 main IOMMU provider",
    )
    require_tokens(
        "MT6873 main IOMMU",
        iommu,
        (
            'compatible = "mediatek,mt6873-m4u"',
            "reg = <0 0x1401d000 0 0x1000>",
            "interrupts = <GIC_SPI 277 IRQ_TYPE_LEVEL_HIGH 0>",
            "clocks = <&mmsys ATOM_MT6873_CLK_MM_SMI_IOMMU>",
            'clock-names = "bclk"',
            "power-domains = <&spm ATOM_MT6873_POWER_DOMAIN_DIS>",
            "mediatek,larbs = <&larb0>, <&larb1>",
            "#iommu-cells = <1>",
            'status = "okay"',
        ),
    )

    binding = (
        Path(patch_root)
        / "0032-dt-bindings-memory-mediatek-add-mt6873-smi-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "+          - mediatek,mt6873-smi-common",
        "+          - mediatek,mt6873-smi-larb",
        "+            - mediatek,mt6873-smi-common",
        "+              - mediatek,mt6873-smi-larb",
    ):
        if marker not in binding:
            raise SystemExit(
                "[FATAL] 0032 missing MT6873 SMI binding marker: " + marker
            )

    driver = (
        Path(patch_root)
        / "0033-memory-mediatek-add-mt6873-smi-provider-data-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "+static const u8 mtk_smi_larb_mt6873_ostd",
        "+	[0] = {0x2, 0x2, 0x28, 0xa, 0xc, 0x28},",
        "+	[1] = {0x2, 0x2, 0x18, 0x18, 0x18, 0xa, 0xc, 0x28},",
        "+	.flags_general",
        "+				      MTK_SMI_FLAG_SW_FLAG,",
        "+static const struct mtk_smi_reg_pair mtk_smi_common_mt6873_init",
        "+	{SMI_FIFO_TH1, 0x90a090a},",
        "+	.bus_sel  = F_MMU1_LARB(1) | F_MMU1_LARB(2) | F_MMU1_LARB(5) |",
        '+	{.compatible = "mediatek,mt6873-smi-larb",',
        '+	{.compatible = "mediatek,mt6873-smi-common",',
    ):
        if marker not in driver:
            raise SystemExit(
                "[FATAL] 0033 missing MT6873 SMI driver marker: " + marker
            )

    iommu_binding = (
        Path(patch_root)
        / "0034-dt-bindings-iommu-add-mt6873-main-iommu-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "+          - mediatek,mt6873-m4u",
        "+              - mediatek,mt6873-m4u",
        "+            - mediatek,mt6873-m4u",
    ):
        if marker not in iommu_binding:
            raise SystemExit(
                "[FATAL] 0034 missing MT6873 IOMMU binding marker: " + marker
            )

    iommu_driver = (
        Path(patch_root)
        / "0035-iommu-mediatek-add-mt6873-main-iommu-data-v6.18.patch"
    ).read_text(encoding="utf-8")
    for marker in (
        "+static const struct mtk_iommu_plat_data mt6873_data",
        "+	.m4u_plat     = M4U_MT8192,",
        "+	.banks_num    = 1,",
        "+	.larbid_remap    = {{0}, {1}, {4, 5}, {7}, {2}, {9, 11, 19, 20},",
        '+	{ .compatible = "mediatek,mt6873-m4u", .data = &mt6873_data},',
    ):
        if marker not in iommu_driver:
            raise SystemExit(
                "[FATAL] 0035 missing MT6873 IOMMU driver marker: " + marker
            )
    if (
        "+			WR_THROT_EN | IOVA_34_EN | SHARE_PGTABLE |"
        in iommu_driver
    ):
        raise SystemExit(
            "[FATAL] single-IOMMU MT6873 data must not enable SHARE_PGTABLE "
            "without hw_list"
        )


def check_unsupported_inherited_consumers(dts):
    clean = strip_comments(dts)

    deletion = re.search(
        r"^\s*&\{/soc\}\s*\{(?P<body>.*?)\};",
        clean,
        flags=re.M | re.S,
    )
    if not deletion:
        raise SystemExit(
            "[FATAL] 缺少删除 vendor 会启用的 MT8192 节点的 "
            "&{/soc} 覆盖"
        )
    deletion_body = deletion.group("body")
    for label, (placeholder, node_name) in (
        VENDOR_ENABLED_ISOLATED_LABELS.items()
    ):
        if "/delete-node/ {};".format(node_name) not in deletion_body:
            raise SystemExit(
                "[FATAL] 未删除 vendor 会启用的 MT8192 节点 "
                "{} ({})".format(node_name, label)
            )
        if not re.search(
            r"{label}:\s*{name}\s*\{{\s*status\s*=\s*\"disabled\";\s*\}};"
            .format(
                label=re.escape(label),
                name=re.escape(placeholder),
            ),
            clean,
            flags=re.S,
        ):
            raise SystemExit(
                "[FATAL] vendor fixup 标签 {} 未迁到 disabled 占位节点 {}"
                .format(label, placeholder)
            )

    not_disabled = []
    for label in UNSUPPORTED_INHERITED_CONSUMERS:
        match = re.search(
            r"&{}\s*\{{(?P<body>.*?)\}};".format(re.escape(label)),
            clean,
            flags=re.S,
        )
        if not match:
            not_disabled.append(label + ":missing-overlay")
        elif not re.search(
            r'^\s*status\s*=\s*"disabled";',
            match.group("body"),
            flags=re.M,
        ):
            not_disabled.append(label + ":enabled")
    if not_disabled:
        raise SystemExit(
            "[FATAL] 未禁用的继承 MT8192 多媒体/IOMMU 消费者: {}".format(
                ", ".join(not_disabled)
            )
        )


def check_vendor_dtbo_symbols(dts, base):
    lines = VENDOR_DTBO_SYMBOLS.read_text(encoding="utf-8").splitlines()
    labels = [line.strip() for line in lines if line and not line.startswith("#")]
    if len(labels) != 61 or len(set(labels)) != 61:
        raise SystemExit(
            "[FATAL] 原厂 dtbo 符号清单必须包含 61 个唯一标签"
        )

    searchable = strip_comments(base + "\n" + dts)
    missing = [
        label
        for label in labels
        if not re.search(r"\b{}\s*:".format(re.escape(label)), searchable)
    ]
    if missing:
        raise SystemExit(
            "[FATAL] 主 DTB 缺少原厂 dtbo fixup 标签: {}".format(
                ", ".join(missing)
            )
        )


def check_i2c5_mt6360(dts, patch_root):
    clean = strip_comments(dts)

    deletion = re.search(
        r"^\s*&\{/soc\}\s*\{(?P<body>.*?)\};",
        clean,
        flags=re.M | re.S,
    )
    if not deletion or "/delete-node/ i2c@11e00000;" not in deletion.group("body"):
        raise SystemExit(
            "[FATAL] 未删除 vendor dtbo 会扩展的继承 MT8192 I2C5 节点"
        )

    ulposc = extract_braced_body(
        clean,
        r"\bulposc:\s*oscillator-ulposc\s*\{",
        "260 MHz ULPOSC 固定时钟",
    )
    require_tokens(
        "ULPOSC",
        ulposc,
        (
            'compatible = "fixed-clock"',
            "clock-frequency = <260000000>",
            'clock-output-names = "ulposc"',
        ),
    )

    imp = extract_braced_body(
        clean,
        r"&imp_iic_wrap_w\s*\{",
        "MT6873 IMP_IIC_WRAP_W provider 覆盖",
    )
    require_tokens(
        "IMP_IIC_WRAP_W",
        imp,
        (
            'compatible = "mediatek,mt6873-imp_iic_wrap_w"',
            'status = "okay"',
        ),
    )

    pins = extract_braced_body(
        clean,
        r"\batom_i2c5_pins:\s*mainline-i2c5-pins\s*\{",
        "GPIO202/203 I2C5 pinmux",
    )
    require_tokens(
        "I2C5 pinmux",
        pins,
        (
            "ATOM_MT6873_PINMUX_GPIO202_SCL5",
            "ATOM_MT6873_PINMUX_GPIO203_SDA5",
        ),
    )

    if re.search(
        r"\bi2c5\s*:\s*i2c@11e00000\s*\{",
        clean,
    ):
        raise SystemExit(
            "[FATAL] 正式 I2C5 不得保留 i2c5 fixup 标签；"
            "该标签必须指向 disabled 隔离占位节点"
        )

    i2c5 = extract_braced_body(
        clean,
        r"(?<![A-Za-z0-9_-])i2c@11e00000\s*\{",
        "MT6873 I2C5 节点",
    )
    require_tokens(
        "I2C5",
        i2c5,
        (
            'compatible = "mediatek,mt6873-i2c"',
            '"mediatek,mt8192-i2c"',
            "reg = <0 0x11e00000 0 0x1000>",
            "<0 0x10217500 0 0x80>",
            "GIC_SPI 117 IRQ_TYPE_LEVEL_HIGH 0",
            "ATOM_MT6873_CLK_IMP_IIC_WRAP_W_AP_I2C5_CG_RO",
            "ATOM_MT6873_CLK_INFRA_AO_AP_DMA_CG",
            'clock-names = "main", "dma"',
            "clock-div = <3>",
            "pinctrl-0 = <&atom_i2c5_pins>",
            "#address-cells = <1>",
            "#size-cells = <0>",
            'status = "okay"',
        ),
    )
    for forbidden in (
        "subpmic@34",
        "usb_type_c@4e",
        "subpmic_pmic@1a",
        "subpmic_ldo@64",
    ):
        if forbidden in i2c5:
            raise SystemExit(
                "[FATAL] 正式 I2C5 不应保留未审查的 vendor 客户端: "
                + forbidden
            )

    mt6360 = extract_braced_body(
        i2c5,
        r"\bmt6360:\s*pmic@34\s*\{",
        "MT6360 MFD 节点",
    )
    require_tokens(
        "MT6360 MFD",
        mt6360,
        (
            'compatible = "mediatek,mt6360"',
            "reg = <0x34>",
            "interrupt-parent = <&pio>",
            "interrupts = <24 IRQ_TYPE_EDGE_FALLING>",
            'interrupt-names = "IRQB"',
            "interrupt-controller",
            "#interrupt-cells = <1>",
        ),
    )

    charger = extract_braced_body(
        mt6360,
        r"\bcharger\s*\{",
        "MT6360 charger 节点",
    )
    require_tokens(
        "MT6360 charger",
        charger,
        (
            'compatible = "mediatek,mt6360-chg"',
            "regulator-name = \"usb-otg-vbus\"",
            "regulator-min-microvolt = <4425000>",
            "regulator-max-microvolt = <5825000>",
        ),
    )

    tcpc = extract_braced_body(
        mt6360,
        r"\btcpc\s*\{",
        "MT6360 TCPC 节点",
    )
    require_tokens(
        "MT6360 TCPC",
        tcpc,
        (
            'compatible = "mediatek,mt6360-tcpc"',
            "interrupt-parent = <&pio>",
            "interrupts = <25 IRQ_TYPE_EDGE_FALLING>",
            'interrupt-names = "PD_IRQB"',
        ),
    )
    connector = extract_braced_body(
        tcpc,
        r"\bconnector\s*\{",
        "MT6360 Type-C connector 节点",
    )
    require_tokens(
        "MT6360 Type-C connector",
        connector,
        (
            'compatible = "usb-c-connector"',
            'label = "USB-C"',
            'data-role = "dual"',
            'power-role = "dual"',
            'try-power-role = "sink"',
            "source-pdos = <0x19096>",
            "sink-pdos = <0x1912c>",
            "op-sink-microwatt = <15000000>",
        ),
    )

    i2c_binding = read_text(
        Path(patch_root) / "0012-dt-bindings-i2c-add-mt6873-fallback-v6.18.patch"
    )
    if "+              - mediatek,mt6873-i2c" not in i2c_binding:
        raise SystemExit(
            "[FATAL] 0012 未把 mediatek,mt6873-i2c 接到 MT8192 fallback"
        )

    clock_patch = read_text(
        Path(patch_root)
        / "0013-clk-mediatek-add-mt6873-i2c-clock-chain-v6.18.patch"
    )
    for marker in (
        'compatible = "mediatek,mt6873-imp_iic_wrap_w"',
        "reg = <0x11e01000 0x1000>",
        "CLK_TOP_MUX_AXI",
        "CLK_TOP_MUX_I2C",
        "CLK_INFRA_AO_I2C0_CG",
        "CLK_INFRA_AO_AP_DMA_CG",
        "CLK_IMP_IIC_WRAP_W_AP_I2C5_CG_RO",
        ".sta_ofs = 0xe00",
        "CLK_OPS_PARENT_ENABLE",
    ):
        if marker not in clock_patch:
            raise SystemExit(
                "[FATAL] 0013 缺少 MT6873 I2C5 时钟链源码依据: " + marker
            )


def check_topology(dts):
    clean = strip_comments(dts)
    if "earlycon" in clean:
        raise SystemExit(
            "[FATAL] 无物理串口的诊断 DTS 不得启用 earlycon"
        )
    if not re.search(
        r"^\s*reserved_memory:\s*reserved-memory\s*\{",
        clean,
        flags=re.M,
    ):
        raise SystemExit(
            "[FATAL] DTS 必须保留 LK overlay 所需的 "
            "reserved_memory 标签"
        )
    if re.search(
        r"^\s*ramoops@4d010000\s*\{",
        clean,
        flags=re.M,
    ):
        raise SystemExit(
            "[FATAL] DTS 不得声明与 LK pstore mblock 冲突的固定 "
            "ramoops@4d010000"
        )
    chosen = re.search(
        r"^\s*chosen:\s*chosen\s*\{(?P<body>.*?)\n\t\};",
        clean,
        flags=re.M | re.S,
    )
    if not chosen:
        raise SystemExit(
            "[FATAL] DTS 必须为原厂 LK overlay 提供 chosen 标签"
        )
    if not re.search(
        r'^\s*bootargs\s*=\s*""\s*;',
        chosen.group("body"),
        flags=re.M,
    ):
        raise SystemExit(
            "[FATAL] /chosen/bootargs 必须存在并保持为空，供 LK 注入命令行"
        )
    if len(re.findall(r"^\s*bootargs\s*=", clean, flags=re.M)) != 1:
        raise SystemExit(
            "[FATAL] DTS 只能有一个空 /chosen/bootargs 种子"
        )
    overlay_targets = re.search(
        r"lk_overlay_targets:\s*lk-overlay-targets\s*\{(?P<body>.*?)\n\t\};",
        clean,
        flags=re.S,
    )
    if not overlay_targets:
        raise SystemExit("[FATAL] 缺少隔离的 lk-overlay-targets 容器")
    if 'status = "disabled";' not in overlay_targets.group("body"):
        raise SystemExit(
            "[FATAL] lk-overlay-targets 容器必须保持 disabled"
        )

    handoff_shims = re.search(
        r"lk_handoff_shims:\s*lk-handoff-shims\s*\{(?P<body>.*?)\n\t\};",
        clean,
        flags=re.S,
    )
    if not handoff_shims:
        raise SystemExit("[FATAL] 缺少 LK SCP/ADSP handoff shims 容器")
    shim_body = handoff_shims.group("body")
    for label, name, compatible in (
        ("lk_scp_shim", "scp", "mediatek,scp"),
        ("lk_adsp_common_shim", "adsp-common", "mediatek,adsp_common"),
    ):
        pattern = (
            r"{label}:\s*{name}\s*\{{\s*"
            r'compatible = "{compatible}";\s*'
            r'status = "disabled";\s*\}};'
        ).format(
            label=re.escape(label),
            name=re.escape(name),
            compatible=re.escape(compatible),
        )
        if not re.search(pattern, shim_body, flags=re.S):
            raise SystemExit(
                "[FATAL] LK handoff shim {} 必须匹配 {} 且保持 disabled".format(
                    label, compatible
                )
            )

    soc = re.search(
        r"^\tsoc\s*\{(?P<body>.*?)\n\t\};",
        clean,
        flags=re.M | re.S,
    )
    if not soc:
        raise SystemExit("[FATAL] 缺少板级 soc 节点")
    if not re.search(
        r"lk_dramc:\s*dramc\s*\{\s*status = \"disabled\";\s*\};",
        soc.group("body"),
        flags=re.S,
    ):
        raise SystemExit(
            "[FATAL] LK 必须在 /soc/dramc 找到 disabled DRAMC handoff shim"
        )

    require_tokens(
        "provider",
        dts,
        (
            'compatible = "mediatek,mt6873-topckgen", "syscon"',
            'compatible = "mediatek,mt6873-infracfg_ao", "syscon"',
            '/delete-property/ #reset-cells',
            'compatible = "mediatek,mt6873-apmixedsys", "syscon"',
            'compatible = "mediatek,mt6873-pinctrl"',
            '"mediatek,mt6873-tphy"',
            '"mediatek,mt6873-mtu3"',
            '"mediatek,mtu3"',
            '"mediatek,mt6873-ufshci"',
            '"mediatek,mt8183-ufshci"',
            '"mediatek,mt6873-ufsphy"',
            '"mediatek,mt8183-ufsphy"',
            'compatible = "mediatek,mt6359"',
            'compatible = "mediatek,mt6359-regulator"',
            'mt6359_vusb: ldo_vusb',
        ),
    )
    require_tokens(
        "UFS",
        dts,
        (
            "reg = <0 0x11270000 0 0x2300>",
            "GIC_SPI 105 IRQ_TYPE_LEVEL_HIGH 0",
            "ATOM_MT6873_CLK_INFRA_AO_UFS_CG",
            "clock-names = \"ufs\"",
            "freq-table-hz = <0 0>",
            "mediatek,ufs-disable-mcq",
            "phys = <&ufs_phy>",
            "vcc-supply = <&atom_ufs_vcc>",
            "lanes-per-direction = <2>",
            "reg = <0 0x11fa0000 0 0xc000>",
            "ATOM_MT6873_CLK_INFRA_AO_UNIPRO_SYSCLK_CG",
            "ATOM_MT6873_CLK_INFRA_AO_UFS_MP_SAP_BCLK_CG",
            "clock-names = \"unipro\", \"mp\"",
            "#phy-cells = <0>",
            "regulator-min-microvolt = <3000000>",
            "regulator-max-microvolt = <3000000>",
            "regulator-boot-on",
            "regulator-always-on",
        ),
    )
    require_tokens(
        "MTU3",
        dts,
        (
            "reg = <0 0x11201000 0 0x2e00>",
            "<0 0x11203e00 0 0x0100>",
            "GIC_SPI 96 IRQ_TYPE_LEVEL_HIGH",
            "ATOM_MT6873_CLK_INFRA_AO_SSUSB_CG",
            "ATOM_MT6873_CLK_INFRA_AO_SSUSB_XHCI_CG",
            "ATOM_MT6873_CLK_INFRA_AO_PMIC_CG_AP",
            "ATOM_MT6873_CLK_INFRA_AO_PMIC_CG_TMR",
            "ATOM_MT6873_CLK_INFRA_AO_UART0_CG",
            "PHY_TYPE_USB2",
            "PHY_TYPE_USB3",
            "dr_mode = \"peripheral\"",
            "maximum-speed = \"high-speed\"",
            "vusb33-supply = <&mt6359_vusb>",
        ),
    )
    require_tokens(
        "TPHY",
        dts,
        (
            "mediatek,eye-src = <4>",
            "mediatek,eye-vrt = <2>",
            "mediatek,eye-term = <2>",
            "mediatek,intr = <30>",
            "mediatek,discth = <7>",
            "mediatek,pre-emphasis = <1>",
        ),
    )
    require_tokens(
        "USB-C reverse",
        dts,
        (
            "ATOM_MT6873_PINMUX_GPIO111_GPIO",
            "ATOM_MT6873_PINMUX_GPIO112_GPIO",
            "ATOM_MT6873_PINMUX_GPIO113_GPIO",
            "input-schmitt-enable",
            "bias-disable",
            "output-high",
        ),
    )

    xhci = re.search(r"&xhci\s*\{(?P<body>.*?)\};", dts, flags=re.S)
    if not xhci or 'status = "disabled";' not in xhci.group("body"):
        raise SystemExit("[FATAL] peripheral-only DTS 未显式禁用根 xHCI")

    for label in ("lvts_ap", "svs", "lvts_mcu"):
        match = re.search(
            r"&{}\s*\{{(?P<body>.*?)\}};".format(re.escape(label)),
            dts,
            flags=re.S,
        )
        if not match:
            raise SystemExit("[FATAL] 缺少无关 thermal 节点禁用项 &" + label)
        body = match.group("body")
        if "/delete-property/ resets;" not in body:
            raise SystemExit("[FATAL] &" + label + " 仍引用未实现的 reset provider")
        if 'status = "disabled";' not in body:
            raise SystemExit("[FATAL] &" + label + " 未禁用")
    svs = re.search(r"&svs\s*\{(?P<body>.*?)\};", dts, flags=re.S)
    if "/delete-property/ reset-names;" not in svs.group("body"):
        raise SystemExit("[FATAL] &svs reset-names 未删除")

    patch = (
        Path(__file__).resolve().parent.parent
        / "mainline/patches"
        / "0016-dt-bindings-usb-add-mt6873-mtu3-fallback-v6.18.patch"
    ).read_text(encoding="utf-8")
    if "+    minItems: 1" not in patch:
        raise SystemExit(
            "[FATAL] MTU3 binding 未把可选 wakeup IRQ 建模为 minItems: 1"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dts",
        default="mainline/mt6873-atom-usb.dts",
        help="formal atom USB DTS",
    )
    parser.add_argument(
        "--base-dts",
        required=True,
        help="upstream mt8192.dtsi used for label resolution",
    )
    parser.add_argument(
        "--patch-root",
        default="mainline/patches",
        help="directory containing the applied MT6873 patches",
    )
    args = parser.parse_args()

    dts = read_text(args.dts)
    base = read_text(args.base_dts)
    check_labels(dts, base)
    check_macros(dts, args.patch_root)
    check_power_domains(dts, args.patch_root)
    check_display_clock_provider(dts, args.patch_root)
    check_mmsys_routes(args.patch_root)
    check_bus_protection_diagnostics(args.patch_root)
    check_bus_protection_ack_policy(args.patch_root)
    check_mt6873_mipi_tx(args.patch_root)
    check_display_probe_dts(dts, args.patch_root)
    check_mutex_consumer(dts, args.patch_root)
    check_smi_providers(dts, args.patch_root)
    check_unsupported_inherited_consumers(dts)
    check_vendor_dtbo_symbols(dts, base)
    check_i2c5_mt6360(dts, args.patch_root)
    check_topology(dts)
    print(
        "[ok] MT6873 formal DTS USB/UFS/I2C5/SMI/IOMMU topology and "
        "evidence checks passed"
    )


if __name__ == "__main__":
    main()
