#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multiwfn 中文菜单数据。

提供主菜单、子菜单名称、功能描述以及参数化命令模板，
用于功能菜单Tab模拟中文版Multiwfn 3.8的命令导航。
"""


class MultiwfnMenu:
    """Multiwfn 中文菜单数据管理类。"""

    MAIN_MENU = {
        "0": {"name": "显示分子结构与轨道", "desc": "显示分子结构和分子轨道", "icon": "structure"},
        "1": {"name": "单点性质计算", "desc": "计算某点的所有性质", "icon": "point"},
        "2": {"name": "拓扑分析", "desc": "AIM/Bader理论、临界点分析", "icon": "topology"},
        "3": {"name": "线性质分析", "desc": "输出并绘制线上的性质", "icon": "line"},
        "4": {"name": "平面性质分析", "desc": "输出并绘制平面上的性质", "icon": "plane"},
        "5": {"name": "空间区域分析", "desc": "计算并绘制空间区域内的性质(网格数据)", "icon": "space"},
        "6": {"name": "波函数检查与修改", "desc": "检查和修改波函数", "icon": "wfn"},
        "7": {"name": "布居分析与电荷计算", "desc": "多种电荷方法(Mulliken/Hirshfeld/ADCH等)", "icon": "charge"},
        "8": {"name": "轨道成分分析", "desc": "分析轨道的成分", "icon": "orbital"},
        "9": {"name": "键级分析", "desc": "Mayer/Wiberg/Fuzzy键级", "icon": "bond"},
        "10": {"name": "态密度与谱图", "desc": "DOS/PDOS/OPDOS/COHP/光电子能谱", "icon": "dos"},
        "11": {"name": "光谱分析", "desc": "IR/Raman/UV-Vis/ECD/VCD/ROA/NMR", "icon": "spectrum"},
        "12": {"name": "分子表面定量分析", "desc": "分子表面性质分析", "icon": "surface"},
        "13": {"name": "网格数据处理", "desc": "处理已有的网格数据", "icon": "grid"},
        "14": {"name": "AdNDP分析", "desc": "自适应自然密度划分", "icon": "adndp"},
        "15": {"name": "模糊原子空间分析", "desc": "Fuzzy原子空间分析", "icon": "fuzzy"},
        "16": {"name": "电荷分解分析", "desc": "CDA分析与轨道相互作用图", "icon": "cda"},
        "17": {"name": "盆分析", "desc": "AIM/ELF/LOL盆分析", "icon": "basin"},
        "18": {"name": "电子激发分析", "desc": "激发态分析", "icon": "excitation"},
        "19": {"name": "轨道定域化分析", "desc": "轨道定域化", "icon": "localize"},
        "20": {"name": "弱相互作用可视化", "desc": "NCI/IGM/DORI等弱相互作用分析", "icon": "weak"},
        "21": {"name": "能量分解分析", "desc": "能量分解方法", "icon": "energy"},
        "22": {"name": "概念DFT分析", "desc": "Fukui函数、软硬度等", "icon": "cdft"},
        "23": {"name": "ETS-NOCV分析", "desc": "扩展过渡态-NOCV分析", "icon": "etsnocv"},
        "24": {"name": "(超)极化率分析", "desc": "极化率计算", "icon": "polar"},
        "25": {"name": "电子离域与芳香性分析", "desc": "芳香性指标计算", "icon": "aromatic"},
        "26": {"name": "结构与几何相关分析", "desc": "几何结构分析", "icon": "geometry"},
        "100": {"name": "其他功能(一)", "desc": "附加功能组1", "icon": "other1"},
        "200": {"name": "其他功能(二)", "desc": "附加功能组2", "icon": "other2"},
        "300": {"name": "其他功能(三)", "desc": "附加功能组3", "icon": "other3"},
    }

    SUB_MENUS = {}
    PARAMETER_TEMPLATES = {}

    # 常用参数模板（便于复用）
    _COMMON_PARAMS = {
        "grid_quality": {
            "name": "网格质量",
            "key": "grid",
            "type": "combo",
            "options": ["粗糙", "中等", "精细", "超精细"],
            "default": 1,
            "desc": "计算网格的疏密程度，越精细耗时越长",
        },
        "grid_quality3": {
            "name": "网格质量",
            "key": "grid",
            "type": "combo",
            "options": ["粗糙", "中等", "精细"],
            "default": 1,
            "desc": "计算网格的疏密程度，越精细耗时越长",
        },
        "isovalue": {
            "name": "等值面值",
            "key": "isovalue",
            "type": "double",
            "min": 0.001,
            "max": 1.0,
            "default": 0.05,
            "step": 0.01,
            "decimals": 3,
            "desc": "轨道等值面的数值，通常0.02-0.05",
        },
        "orbital_index": {
            "name": "轨道编号",
            "key": "orbital",
            "type": "int",
            "min": 1,
            "max": 9999,
            "default": 1,
            "desc": "要指定的分子轨道编号",
        },
        "point_xyz": [
            {
                "name": "X坐标",
                "key": "x",
                "type": "double",
                "min": -9999.0,
                "max": 9999.0,
                "default": 0.0,
                "step": 0.1,
                "decimals": 4,
                "desc": "点的X笛卡尔坐标(埃)",
            },
            {
                "name": "Y坐标",
                "key": "y",
                "type": "double",
                "min": -9999.0,
                "max": 9999.0,
                "default": 0.0,
                "step": 0.1,
                "decimals": 4,
                "desc": "点的Y笛卡尔坐标(埃)",
            },
            {
                "name": "Z坐标",
                "key": "z",
                "type": "double",
                "min": -9999.0,
                "max": 9999.0,
                "default": 0.0,
                "step": 0.1,
                "decimals": 4,
                "desc": "点的Z笛卡尔坐标(埃)",
            },
        ],
        "func_number": {
            "name": "函数编号",
            "key": "func",
            "type": "int",
            "min": 1,
            "max": 999,
            "default": 1,
            "desc": "实空间函数编号，如1=电子密度、8=ESP",
        },
        "fwhm": {
            "name": "半高宽",
            "key": "fwhm",
            "type": "double",
            "min": 0.0,
            "max": 1000.0,
            "default": 0.0,
            "step": 1.0,
            "decimals": 2,
            "desc": "展宽半高宽(eV或cm^-1)，0表示使用默认",
        },
        "filename": {
            "name": "输出文件名",
            "key": "filename",
            "type": "line",
            "default": "output.txt",
            "desc": "结果输出文件名",
        },
    }

    _GRID_MAP_4 = {"粗糙": "1", "中等": "2", "精细": "3", "超精细": "4"}
    _GRID_MAP_3 = {"粗糙": "1", "中等": "2", "精细": "3"}

    @classmethod
    def _ensure_templates(cls):
        """初始化所有参数模板（延迟加载）。"""
        if cls.PARAMETER_TEMPLATES:
            return
        t = cls.PARAMETER_TEMPLATES
        P = cls._COMMON_PARAMS

        # ==================== 菜单 0: 显示分子结构与轨道 ====================
        t["0_1"] = {
            "name": "显示分子结构",
            "desc": "在可视化窗口中显示分子结构",
            "params": [],
            "commands": ["0", "q"],
            "result_type": "text",
        }
        t["0_2"] = {
            "name": "显示HOMO轨道",
            "desc": "显示最高占据分子轨道(HOMO)的等值面",
            "params": [dict(P["isovalue"])],
            "commands": ["0", "4", "homo", "1", "{isovalue}", "q"],
            "result_type": "text",
        }
        t["0_3"] = {
            "name": "显示LUMO轨道",
            "desc": "显示最低未占分子轨道(LUMO)的等值面",
            "params": [dict(P["isovalue"])],
            "commands": ["0", "4", "lumo", "1", "{isovalue}", "q"],
            "result_type": "text",
        }
        t["0_4"] = {
            "name": "显示指定轨道",
            "desc": "显示指定编号的分子轨道等值面",
            "params": [dict(P["orbital_index"]), dict(P["isovalue"])],
            "commands": ["0", "4", "{orbital}", "1", "{isovalue}", "q"],
            "result_type": "text",
        }
        t["0_5"] = {
            "name": "显示所有占据轨道",
            "desc": "按顺序显示所有占据分子轨道",
            "params": [dict(P["isovalue"])],
            "commands": ["0", "4", "occ", "1", "{isovalue}", "q"],
            "result_type": "text",
        }
        t["0_6"] = {
            "name": "显示所有虚轨道",
            "desc": "按顺序显示所有虚分子轨道",
            "params": [dict(P["isovalue"])],
            "commands": ["0", "4", "vir", "1", "{isovalue}", "q"],
            "result_type": "text",
        }
        t["0_7"] = {
            "name": "显示电子密度等值面",
            "desc": "显示电子密度的三维等值面",
            "params": [dict(P["isovalue"])],
            "commands": ["0", "5", "1", "{isovalue}", "q"],
            "result_type": "text",
        }
        t["0_8"] = {
            "name": "显示自旋密度等值面",
            "desc": "显示自旋密度的三维等值面",
            "params": [dict(P["isovalue"])],
            "commands": ["0", "5", "5", "{isovalue}", "q"],
            "result_type": "text",
        }
        t["0_9"] = {
            "name": "显示基函数",
            "desc": "显示指定基函数的等值面",
            "params": [
                {"name": "基函数编号", "key": "bas", "type": "int", "min": 1, "max": 9999, "default": 1,
                 "desc": "要显示的基函数编号"},
                dict(P["isovalue"]),
            ],
            "commands": ["0", "6", "{bas}", "1", "{isovalue}", "q"],
            "result_type": "text",
        }
        t["0_10"] = {
            "name": "查看轨道信息列表",
            "desc": "列出所有轨道的能量与占据数",
            "params": [],
            "commands": ["0", "1", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 1: 单点性质计算 ====================
        t["1_1"] = {
            "name": "计算某点全部性质",
            "desc": "计算指定坐标点处的所有实空间函数值",
            "params": [dict(p) for p in P["point_xyz"]],
            "commands": ["1", "{x}", "{y}", "{z}", "q"],
            "result_type": "text",
        }
        t["1_2"] = {
            "name": "计算某点电子密度",
            "desc": "计算指定点的电子密度及其梯度、拉普拉斯",
            "params": [dict(p) for p in P["point_xyz"]],
            "commands": ["1", "{x}", "{y}", "{z}", "1", "q"],
            "result_type": "text",
        }
        t["1_3"] = {
            "name": "计算某点静电势",
            "desc": "计算指定点的静电势(ESP)",
            "params": [dict(p) for p in P["point_xyz"]],
            "commands": ["1", "{x}", "{y}", "{z}", "13", "q"],
            "result_type": "text",
        }
        t["1_4"] = {
            "name": "批量计算点性质(从文件)",
            "desc": "从外部文件读取多个点坐标并计算性质",
            "params": [dict(P["filename"])],
            "commands": ["1", "-1", "{filename}", "q"],
            "result_type": "text",
        }
        t["1_5"] = {
            "name": "计算原子核位置的性质",
            "desc": "输出所有原子核位置的实空间函数值",
            "params": [],
            "commands": ["1", "-2", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 2: 拓扑分析 ====================
        t["2_1"] = {
            "name": "搜索临界点(默认)",
            "desc": "自动搜索分子中的AIM临界点",
            "params": [],
            "commands": ["2", "1", "", "", "", "", "q"],
            "result_type": "text",
        }
        t["2_2"] = {
            "name": "显示临界点信息",
            "desc": "显示所有找到的临界点",
            "params": [],
            "commands": ["2", "2", "q"],
            "result_type": "text",
        }
        t["2_3"] = {
            "name": "绘制分子图",
            "desc": "绘制AIM分子结构图",
            "params": [],
            "commands": ["2", "3", "q"],
            "result_type": "text",
        }
        t["2_4"] = {
            "name": "积分计算(原子盆)",
            "desc": "计算原子盆积分",
            "params": [],
            "commands": ["2", "4", "q"],
            "result_type": "text",
        }
        t["2_5"] = {
            "name": "ELF盆分析",
            "desc": "ELF盆搜索与积分",
            "params": [],
            "commands": ["2", "5", "q"],
            "result_type": "text",
        }
        t["2_6"] = {
            "name": "LOL盆分析",
            "desc": "LOL盆搜索与积分",
            "params": [],
            "commands": ["2", "6", "q"],
            "result_type": "text",
        }
        t["2_7"] = {
            "name": "只搜索键临界点",
            "desc": "仅定位分子中的键临界点(BCP)",
            "params": [],
            "commands": ["2", "7", "q"],
            "result_type": "text",
        }
        t["2_8"] = {
            "name": "只搜索环临界点",
            "desc": "仅定位分子中的环临界点(RCP)",
            "params": [],
            "commands": ["2", "8", "q"],
            "result_type": "text",
        }
        t["2_9"] = {
            "name": "只搜索笼临界点",
            "desc": "仅定位分子中的笼临界点(CCP)",
            "params": [],
            "commands": ["2", "9", "q"],
            "result_type": "text",
        }
        t["2_10"] = {
            "name": "生成拓扑分析摘要",
            "desc": "输出拓扑性质的汇总信息",
            "params": [],
            "commands": ["2", "10", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 3: 线性质分析 ====================
        t["3_1"] = {
            "name": "绘制线性质图",
            "desc": "沿一条直线绘制指定实空间函数的变化",
            "params": [dict(P["func_number"])],
            "commands": ["3", "{func}", "1", "", "", "", "q"],
            "result_type": "text",
        }
        t["3_2"] = {
            "name": "输出线性质数据",
            "desc": "将线性质数据输出到文本文件",
            "params": [dict(P["func_number"]), dict(P["filename"])],
            "commands": ["3", "{func}", "2", "{filename}", "", "", "q"],
            "result_type": "text",
        }
        t["3_3"] = {
            "name": "通过两个原子定义线",
            "desc": "以两个原子连线作为分析路径",
            "params": [
                dict(P["func_number"]),
                {"name": "原子1", "key": "atom1", "type": "int", "min": 1, "max": 9999, "default": 1,
                 "desc": "路径起点原子编号"},
                {"name": "原子2", "key": "atom2", "type": "int", "min": 1, "max": 9999, "default": 2,
                 "desc": "路径终点原子编号"},
            ],
            "commands": ["3", "{func}", "3", "{atom1}", "{atom2}", "", "", "q"],
            "result_type": "text",
        }
        t["3_4"] = {
            "name": "线性质图保存为图像",
            "desc": "将线性质图保存到文件",
            "params": [dict(P["func_number"]), dict(P["filename"])],
            "commands": ["3", "{func}", "4", "{filename}", "", "", "q"],
            "result_type": "text",
        }
        t["3_5"] = {
            "name": "自定义路径上的性质",
            "desc": "沿用户自定义折线路径计算性质",
            "params": [dict(P["func_number"])],
            "commands": ["3", "{func}", "5", "", "", "", "q"],
            "result_type": "text",
        }
        t["3_6"] = {
            "name": "线性质积分",
            "desc": "沿指定直线对函数进行数值积分",
            "params": [dict(P["func_number"])],
            "commands": ["3", "{func}", "6", "", "", "", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 4: 平面性质分析 ====================
        t["4_1"] = {
            "name": "绘制平面等值线图",
            "desc": "在平面上绘制实空间函数的等值线",
            "params": [dict(P["func_number"])],
            "commands": ["4", "{func}", "1", "", "", "", "q"],
            "result_type": "text",
        }
        t["4_2"] = {
            "name": "绘制平面填色图",
            "desc": "在平面上绘制实空间函数的填色图",
            "params": [dict(P["func_number"])],
            "commands": ["4", "{func}", "2", "", "", "", "q"],
            "result_type": "text",
        }
        t["4_3"] = {
            "name": "绘制平面矢量场",
            "desc": "在平面上绘制矢量场(如电子密度梯度)",
            "params": [
                {"name": "函数编号", "key": "func", "type": "int", "min": 1, "max": 999, "default": 2,
                 "desc": "实空间函数编号，梯度编号为2"},
            ],
            "commands": ["4", "{func}", "4", "", "", "", "q"],
            "result_type": "text",
        }
        t["4_4"] = {
            "name": "平面填色图保存为图像",
            "desc": "将平面填色图保存为图像文件",
            "params": [dict(P["func_number"]), dict(P["filename"])],
            "commands": ["4", "{func}", "5", "{filename}", "", "", "q"],
            "result_type": "text",
        }
        t["4_5"] = {
            "name": "输出平面网格数据",
            "desc": "将平面网格数据导出到文本文件",
            "params": [dict(P["func_number"]), dict(P["filename"])],
            "commands": ["4", "{func}", "6", "{filename}", "", "", "q"],
            "result_type": "text",
        }
        t["4_6"] = {
            "name": "通过三个原子定义平面",
            "desc": "以三个原子定义分析平面",
            "params": [
                dict(P["func_number"]),
                {"name": "原子1", "key": "a1", "type": "int", "min": 1, "max": 9999, "default": 1,
                 "desc": "定义平面的第一个原子"},
                {"name": "原子2", "key": "a2", "type": "int", "min": 1, "max": 9999, "default": 2,
                 "desc": "定义平面的第二个原子"},
                {"name": "原子3", "key": "a3", "type": "int", "min": 1, "max": 9999, "default": 3,
                 "desc": "定义平面的第三个原子"},
            ],
            "commands": ["4", "{func}", "7", "{a1}", "{a2}", "{a3}", "", "q"],
            "result_type": "text",
        }
        t["4_7"] = {
            "name": "通过两个原子定义平面",
            "desc": "以两个原子的中垂面作为分析平面",
            "params": [
                dict(P["func_number"]),
                {"name": "原子1", "key": "a1", "type": "int", "min": 1, "max": 9999, "default": 1,
                 "desc": "定义平面的第一个原子"},
                {"name": "原子2", "key": "a2", "type": "int", "min": 1, "max": 9999, "default": 2,
                 "desc": "定义平面的第二个原子"},
            ],
            "commands": ["4", "{func}", "8", "{a1}", "{a2}", "", "", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 5: 空间区域分析(实空间函数) ====================
        func5_items = [
            ("5_1", "电子密度", "电子密度 rho(r)", 1),
            ("5_2", "密度梯度模", "电子密度梯度模 |∇ρ(r)|", 2),
            ("5_3", "密度拉普拉斯", "电子密度拉普拉斯 ∇²ρ(r)", 3),
            ("5_4", "ELF", "电子定域化函数 Electron localization function", 4),
            ("5_5", "LOL", "局部化轨道定位函数 Localized orbital locator", 5),
            ("5_6", "sign(lambda2)*rho", "sign(λ₂)ρ，常用于NCI分析", 6),
            ("5_7", "RDG", "约化密度梯度 Reduced density gradient", 7),
            ("5_8", "Hamiltonian动能密度", "Hamiltonian kinetic energy density K(r)", 8),
            ("5_9", "Lagrange动能密度", "Lagrange kinetic energy density G(r)", 9),
            ("5_10", "局部电离能", "局部电离能 Local ionization energy", 11),
            ("5_11", "ESP", "静电势 Electrostatic potential", 13),
            ("5_12", "密度差", "电子密度差 Density difference", 15),
            ("5_13", "Fukui函数", "Fukui函数(概念DFT反应性指标)", 16),
            ("5_14", "双描述符", "双描述符 Dual descriptor", 17),
            ("5_15", "电子能量密度", "电子能量密度 H(r)", 18),
            ("5_16", "自旋密度", "自旋密度 Spin density", 5),
            ("5_17", "磁屏蔽密度", "NMR磁屏蔽密度", 19),
            ("5_18", "分子暴露表面", "分子暴露表面对应的函数", 20),
        ]
        for key, name, desc, func_num in func5_items:
            params = [dict(P["grid_quality"])]
            commands = ["5", str(func_num), "{grid}", "", "", "", "2", "", "0", "q"]
            t[key] = {
                "name": name,
                "desc": desc,
                "params": params,
                "commands": commands,
                "grid_map": dict(cls._GRID_MAP_4),
                "result_type": "cube",
            }

        # ==================== 菜单 6: 波函数检查与修改 ====================
        t["6_1"] = {
            "name": "检查波函数信息",
            "desc": "显示波函数文件的基本信息",
            "params": [],
            "commands": ["6", "1", "q"],
            "result_type": "text",
        }
        t["6_2"] = {
            "name": "修改波函数",
            "desc": "对波函数进行简单修改(如删除基函数)",
            "params": [],
            "commands": ["6", "2", "q"],
            "result_type": "text",
        }
        t["6_3"] = {
            "name": "查看基函数信息",
            "desc": "列出所有基函数的类型与中心",
            "params": [],
            "commands": ["6", "3", "q"],
            "result_type": "text",
        }
        t["6_4"] = {
            "name": "查看原子信息",
            "desc": "列出所有原子的坐标与核电荷",
            "params": [],
            "commands": ["6", "4", "q"],
            "result_type": "text",
        }
        t["6_5"] = {
            "name": "波函数正交化检查",
            "desc": "检查基函数的重叠矩阵",
            "params": [],
            "commands": ["6", "5", "q"],
            "result_type": "text",
        }
        t["6_6"] = {
            "name": "导出波函数信息",
            "desc": "将波函数相关信息保存到文件",
            "params": [dict(P["filename"])],
            "commands": ["6", "6", "{filename}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 7: 布居分析与电荷计算 ====================
        charge_items = [
            ("7_1", "Hirshfeld电荷", "基于Hirshfeld密度划分", ["7", "1", "1", "n", "0", "q"]),
            ("7_2", "VDD电荷", "Voronoi变形密度电荷", ["7", "2", "n", "0", "q"]),
            ("7_3", "Mulliken电荷", "经典Mulliken布居分析", ["7", "5", "1", "n", "0", "0", "q"]),
            ("7_4", "Lowdin电荷", "对称正交化Mulliken电荷", ["7", "6", "lowdin_pop.txt", "n", "0", "q"]),
            ("7_5", "SCPA电荷", "自洽极化近似布居", ["7", "7", "1", "n", "0", "0", "q"]),
            ("7_6", "Becke电荷", "基于Becke权重划分", ["7", "10", "n", "0", "q"]),
            ("7_7", "ADCH电荷", "原子偶极矩校正Hirshfeld", ["7", "11", "n", "0", "q"]),
            ("7_8", "CHELPG电荷", "ChElPG静电势拟合电荷", ["7", "12", "1", "y", "0", "q"]),
            ("7_9", "MK电荷", "Merz-Kollmann静电势拟合电荷", ["7", "13", "1", "y", "0", "q"]),
            ("7_10", "AIM/QTAIM电荷", "原子盆积分电荷", ["7", "14", "", "0", "q"]),
            ("7_11", "Hirshfeld-I电荷", "迭代Hirshfeld方法", ["7", "15", "1", "n", "0", "q"]),
            ("7_12", "CM5电荷", "电荷模型5", ["7", "16", "n", "0", "q"]),
            ("7_13", "EEM电荷", "电荷均衡方法", ["7", "17", "1", "0", "q"]),
            ("7_14", "RESP电荷", "受限静电势拟合", ["7", "18", "2", "1", "", "0", "q"]),
            ("7_15", "Gasteiger电荷", "Gasteiger-Marsili方法", ["7", "19", "", "0", "q"]),
            ("7_16", "MBIS电荷", "最小基组迭代Stockholder", ["7", "20", "", "0", "q"]),
            ("7_17", "模糊空间布居", "Fuzzy原子空间布居分析", ["7", "21", "n", "0", "q"]),
        ]
        for key, name, desc, cmds in charge_items:
            t[key] = {
                "name": name,
                "desc": desc,
                "params": [],
                "commands": cmds,
                "result_type": "charge",
            }

        # ==================== 菜单 8: 轨道成分分析 ====================
        t["8_1"] = {
            "name": "轨道成分分析",
            "desc": "分析轨道的原子/片段成分",
            "params": [dict(P["orbital_index"])],
            "commands": ["8", "1", "{orbital}", "q"],
            "result_type": "text",
        }
        t["8_2"] = {
            "name": "轨道-键相互作用",
            "desc": "分析轨道与键的相互作用",
            "params": [],
            "commands": ["8", "2", "q"],
            "result_type": "text",
        }
        t["8_3"] = {
            "name": "Natural Adaption Orbitals成分",
            "desc": "基于NAO分析轨道成分",
            "params": [dict(P["orbital_index"])],
            "commands": ["8", "3", "{orbital}", "q"],
            "result_type": "text",
        }
        t["8_4"] = {
            "name": "所有轨道成分汇总",
            "desc": "批量输出所有轨道的成分",
            "params": [],
            "commands": ["8", "4", "q"],
            "result_type": "text",
        }
        t["8_5"] = {
            "name": "片段轨道成分",
            "desc": "按自定义片段分析轨道成分",
            "params": [dict(P["orbital_index"])],
            "commands": ["8", "5", "{orbital}", "", "q"],
            "result_type": "text",
        }
        t["8_6"] = {
            "name": "轨道定域化成分",
            "desc": "分析定域化轨道的成分",
            "params": [],
            "commands": ["8", "6", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 9: 键级分析 ====================
        bond_items = [
            ("9_1", "Mayer键级", "Mayer键级矩阵", ["9", "1", "n", "0", "q"]),
            ("9_2", "Wiberg键级", "Wiberg键级", ["9", "3", "n", "0", "q"]),
            ("9_3", "Mulliken键级", "Mulliken键级", ["9", "4", "n", "0", "q"]),
            ("9_4", "AdNDP键级", "自适应自然密度划分键级", ["9", "5", "0", "q"]),
            ("9_5", "Fuzzy键级", "模糊键级", ["9", "7", "n", "0", "q"]),
            ("9_6", "Laplacian键级", "基于拉普拉斯的键级", ["9", "8", "n", "0", "q"]),
            ("9_7", "Deformation键级", "变形密度键级", ["9", "9", "n", "0", "q"]),
            ("9_8", "PI键级", "π键级分析", ["9", "10", "n", "0", "q"]),
            ("9_9", "多中心键级", "计算多中心键级", ["9", "11", "", "0", "q"]),
            ("9_10", "NAO键级", "自然原子轨道键级", ["9", "11", "n", "0", "q"]),
        ]
        for key, name, desc, cmds in bond_items:
            t[key] = {
                "name": name,
                "desc": desc,
                "params": [],
                "commands": cmds,
                "result_type": "bond",
            }

        # ==================== 菜单 10: 态密度与谱图 ====================
        dos_items = [
            ("10_1", "总态密度(Total DOS)", "总态密度图", ["10", "1", "-3", "dos_data.txt", "", "-10", "q"]),
            ("10_2", "分态密度(PDOS)", "分态密度图", ["10", "2", "", "-3", "pdos_data.txt", "", "-10", "q"]),
            ("10_3", "重叠分态密度(OPDOS)", "重叠分态密度", ["10", "3", "", "-3", "opdos_data.txt", "", "-10", "q"]),
            ("10_4", "局域态密度(Local DOS)", "局域态密度", ["10", "4", "", "-3", "ldos_data.txt", "", "-10", "q"]),
            ("10_5", "COHP分析", "晶体轨道哈密顿布居", ["10", "5", "", "-3", "cohp_data.txt", "", "-10", "q"]),
            ("10_6", "COOP分析", "晶体轨道重叠布居", ["10", "6", "", "-3", "coop_data.txt", "", "-10", "q"]),
            ("10_7", "光电子能谱(默认)", "光电子能谱分析(子选项10)", ["10", "10", "", "q"]),
            ("10_8", "光电子能谱(考虑振宽)", "光电子能谱分析(子选项11)", ["10", "11", "", "q"]),
            ("10_9", "光电子能谱(高级设置)", "光电子能谱分析(子选项12)", ["10", "12", "", "q"]),
            ("10_10", "带隙分析", "分析HOMO-LUMO带隙", ["10", "20", "", "q"]),
            ("10_11", "费米能级附近的态", "绘制费米能级附近的态", ["10", "21", "", "q"]),
            ("10_12", "DOS数据后处理", "对已有DOS数据进行后处理", ["10", "30", "", "q"]),
        ]
        for key, name, desc, cmds in dos_items:
            t[key] = {
                "name": name,
                "desc": desc,
                "params": [],
                "commands": cmds,
                "result_type": "dos",
            }

        # ==================== 菜单 11: 光谱分析 ====================
        spec_items = [
            ("11_1", "IR光谱", "红外光谱", "1"),
            ("11_2", "Raman光谱", "拉曼光谱", "2"),
            ("11_3", "UV-Vis光谱", "紫外-可见光谱", "3"),
            ("11_4", "ECD光谱", "电子圆二色谱", "4"),
            ("11_5", "VCD光谱", "振动圆二色谱", "5"),
            ("11_6", "ROA光谱", "拉曼光学活性光谱", "6"),
            ("11_7", "NMR光谱", "核磁共振谱", "7"),
            ("11_8", "电子吸收光谱", "计算电子吸收光谱", "8"),
            ("11_9", "荧光光谱", "计算荧光发射光谱", "9"),
            ("11_10", "磷光光谱", "计算磷光发射光谱", "10"),
            ("11_11", "振子强度表", "输出所有激发态振子强度", "11"),
            ("11_12", "振动频率表", "输出所有振动频率", "12"),
        ]
        for key, name, desc, num in spec_items:
            t[key] = {
                "name": name,
                "desc": desc,
                "params": [dict(P["fwhm"])],
                "commands": ["11", num, "{fwhm}", "q"],
                "result_type": "spectrum",
            }

        # ==================== 菜单 12: 分子表面定量分析 ====================
        t["12_1"] = {
            "name": "定量分子表面分析",
            "desc": "计算分子表面的静电势、面积等定量性质",
            "params": [dict(P["grid_quality3"])],
            "commands": ["12", "1", "{grid}", "", "q"],
            "grid_map": dict(cls._GRID_MAP_3),
            "result_type": "text",
        }
        t["12_2"] = {
            "name": "分析表面静电势极值点",
            "desc": "搜索分子表面静电势的极大/极小值",
            "params": [],
            "commands": ["12", "2", "q"],
            "result_type": "text",
        }
        t["12_3"] = {
            "name": "分子表面积与体积",
            "desc": "计算分子表面积和分子体积",
            "params": [dict(P["grid_quality3"])],
            "commands": ["12", "3", "{grid}", "", "q"],
            "grid_map": dict(cls._GRID_MAP_3),
            "result_type": "text",
        }
        t["12_4"] = {
            "name": "平均局部电离能表面",
            "desc": "计算分子表面上的平均局部电离能",
            "params": [dict(P["grid_quality3"])],
            "commands": ["12", "4", "{grid}", "", "q"],
            "grid_map": dict(cls._GRID_MAP_3),
            "result_type": "text",
        }
        t["12_5"] = {
            "name": "局部Fukui函数表面",
            "desc": "计算分子表面的局部Fukui函数",
            "params": [dict(P["grid_quality3"])],
            "commands": ["12", "5", "{grid}", "", "q"],
            "grid_map": dict(cls._GRID_MAP_3),
            "result_type": "text",
        }
        t["12_6"] = {
            "name": "表面静电势统计量",
            "desc": "输出表面静电势的统计参数",
            "params": [],
            "commands": ["12", "6", "q"],
            "result_type": "text",
        }
        t["12_7"] = {
            "name": "导出表面网格数据",
            "desc": "将分子表面数据导出到文件",
            "params": [dict(P["filename"])],
            "commands": ["12", "7", "{filename}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 13: 网格数据处理 ====================
        t["13_1"] = {
            "name": "处理已有网格数据",
            "desc": "对已有cube网格数据进行操作",
            "params": [],
            "commands": ["13", "1", "q"],
            "result_type": "text",
        }
        t["13_2"] = {
            "name": "网格数据运算",
            "desc": "对多个网格数据进行加减乘除等运算",
            "params": [],
            "commands": ["13", "2", "q"],
            "result_type": "text",
        }
        t["13_3"] = {
            "name": "网格数据差值",
            "desc": "计算两个cube文件的差值",
            "params": [
                {"name": "文件2", "key": "file2", "type": "line", "default": "grid2.cube",
                 "desc": "用于相减的第二个cube文件路径"},
            ],
            "commands": ["13", "3", "{file2}", "", "q"],
            "result_type": "text",
        }
        t["13_4"] = {
            "name": "提取特定截面",
            "desc": "从三维cube数据中提取二维截面",
            "params": [],
            "commands": ["13", "4", "q"],
            "result_type": "text",
        }
        t["13_5"] = {
            "name": "网格重采样",
            "desc": "对网格数据进行重采样或插值",
            "params": [],
            "commands": ["13", "5", "q"],
            "result_type": "text",
        }
        t["13_6"] = {
            "name": "网格数据积分",
            "desc": "对整个网格空间进行数值积分",
            "params": [],
            "commands": ["13", "6", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 14: AdNDP分析 ====================
        t["14_1"] = {
            "name": "AdNDP分析",
            "desc": "自适应自然密度划分",
            "params": [],
            "commands": ["14", "1", "q"],
            "result_type": "text",
        }
        t["14_2"] = {
            "name": "AdNDP占用数阈值",
            "desc": "设置AdNDP搜索的占用数阈值",
            "params": [
                {"name": "阈值", "key": "thresh", "type": "double", "min": 0.0, "max": 2.0, "default": 1.7,
                 "step": 0.05, "decimals": 2, "desc": "自然占用数阈值，通常1.5-1.9"},
            ],
            "commands": ["14", "2", "{thresh}", "q"],
            "result_type": "text",
        }
        t["14_3"] = {
            "name": "AdNDP轨道可视化",
            "desc": "将AdNDP轨道导出为cube文件",
            "params": [dict(P["isovalue"])],
            "commands": ["14", "3", "{isovalue}", "q"],
            "result_type": "text",
        }
        t["14_4"] = {
            "name": "AdNDP结果导出",
            "desc": "将AdNDP分析结果保存到文件",
            "params": [dict(P["filename"])],
            "commands": ["14", "4", "{filename}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 15: 模糊原子空间分析 ====================
        t["15_1"] = {
            "name": "Fuzzy原子空间",
            "desc": "Fuzzy原子空间分析",
            "params": [],
            "commands": ["15", "1", "q"],
            "result_type": "text",
        }
        t["15_2"] = {
            "name": "Fuzzy原子空间积分",
            "desc": "在Fuzzy原子空间中进行积分",
            "params": [],
            "commands": ["15", "2", "q"],
            "result_type": "text",
        }
        t["15_3"] = {
            "name": "Fuzzy原子偶极矩",
            "desc": "计算Fuzzy原子空间的偶极矩",
            "params": [],
            "commands": ["15", "3", "q"],
            "result_type": "text",
        }
        t["15_4"] = {
            "name": "Fuzzy原子多极矩",
            "desc": "计算Fuzzy原子空间的多极矩",
            "params": [],
            "commands": ["15", "4", "q"],
            "result_type": "text",
        }
        t["15_5"] = {
            "name": "Fuzzy原子能量",
            "desc": "计算Fuzzy原子空间的能量",
            "params": [],
            "commands": ["15", "5", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 16: 电荷分解分析 ====================
        t["16_1"] = {
            "name": "CDA分析",
            "desc": "电荷分解分析",
            "params": [],
            "commands": ["16", "1", "q"],
            "result_type": "text",
        }
        t["16_2"] = {
            "name": "轨道相互作用图",
            "desc": "绘制轨道相互作用图",
            "params": [],
            "commands": ["16", "2", "q"],
            "result_type": "text",
        }
        t["16_3"] = {
            "name": "CDA能量分解",
            "desc": "基于CDA的能量分解分析",
            "params": [],
            "commands": ["16", "3", "q"],
            "result_type": "text",
        }
        t["16_4"] = {
            "name": "广义CDA",
            "desc": "广义电荷分解分析",
            "params": [],
            "commands": ["16", "4", "q"],
            "result_type": "text",
        }
        t["16_5"] = {
            "name": "CDA结果导出",
            "desc": "导出CDA分析结果",
            "params": [dict(P["filename"])],
            "commands": ["16", "5", "{filename}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 17: 盆分析 ====================
        t["17_1"] = {
            "name": "AIM盆积分",
            "desc": "QTAIM Basin积分",
            "params": [],
            "commands": ["17", "1", "q"],
            "result_type": "text",
        }
        t["17_2"] = {
            "name": "ELF盆积分",
            "desc": "ELF盆积分",
            "params": [],
            "commands": ["17", "2", "q"],
            "result_type": "text",
        }
        t["17_3"] = {
            "name": "LOL盆积分",
            "desc": "LOL盆积分",
            "params": [],
            "commands": ["17", "3", "q"],
            "result_type": "text",
        }
        t["17_4"] = {
            "name": "盆间连接图",
            "desc": "绘制盆之间的连接关系",
            "params": [],
            "commands": ["17", "4", "q"],
            "result_type": "text",
        }
        t["17_5"] = {
            "name": "盆属性汇总",
            "desc": "输出所有盆的积分属性",
            "params": [],
            "commands": ["17", "5", "q"],
            "result_type": "text",
        }
        t["17_6"] = {
            "name": "盆可视化",
            "desc": "将盆边界导出为可视化文件",
            "params": [dict(P["filename"])],
            "commands": ["17", "6", "{filename}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 18: 电子激发分析 ====================
        t["18_1"] = {
            "name": "激发态信息",
            "desc": "显示激发态能量和振子强度",
            "params": [
                {"name": "激发态编号", "key": "state", "type": "int", "min": 1, "max": 999, "default": 1,
                 "desc": "要查看的激发态编号"},
            ],
            "commands": ["18", "1", "{state}", "q"],
            "result_type": "text",
        }
        t["18_2"] = {
            "name": "电荷转移分析",
            "desc": "分析激发态电荷转移",
            "params": [
                {"name": "激发态编号", "key": "state", "type": "int", "min": 1, "max": 999, "default": 1,
                 "desc": "要分析的激发态编号"},
            ],
            "commands": ["18", "2", "{state}", "q"],
            "result_type": "text",
        }
        t["18_3"] = {
            "name": "跃迁密度矩阵",
            "desc": "计算跃迁密度矩阵",
            "params": [
                {"name": "激发态编号", "key": "state", "type": "int", "min": 1, "max": 999, "default": 1,
                 "desc": "要计算的激发态编号"},
            ],
            "commands": ["18", "3", "{state}", "q"],
            "result_type": "text",
        }
        t["18_4"] = {
            "name": "自然跃迁轨道",
            "desc": "生成自然跃迁轨道(NTO)",
            "params": [
                {"name": "激发态编号", "key": "state", "type": "int", "min": 1, "max": 999, "default": 1,
                 "desc": "要生成NTO的激发态编号"},
            ],
            "commands": ["18", "4", "{state}", "q"],
            "result_type": "text",
        }
        t["18_5"] = {
            "name": "空穴-电子分析",
            "desc": "分析激发态的空穴与电子分布",
            "params": [
                {"name": "激发态编号", "key": "state", "type": "int", "min": 1, "max": 999, "default": 1,
                 "desc": "要分析的激发态编号"},
            ],
            "commands": ["18", "5", "{state}", "q"],
            "result_type": "text",
        }
        t["18_6"] = {
            "name": "激发态偶极矩",
            "desc": "计算激发态的偶极矩",
            "params": [
                {"name": "激发态编号", "key": "state", "type": "int", "min": 1, "max": 999, "default": 1,
                 "desc": "要计算的激发态编号"},
            ],
            "commands": ["18", "6", "{state}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 19: 轨道定域化分析 ====================
        t["19_1"] = {
            "name": "Foster-Boys定域化",
            "desc": "Foster-Boys轨道定域化",
            "params": [],
            "commands": ["19", "1", "q"],
            "result_type": "text",
        }
        t["19_2"] = {
            "name": "Pipek-Mezey定域化",
            "desc": "Pipek-Mezey轨道定域化",
            "params": [],
            "commands": ["19", "2", "q"],
            "result_type": "text",
        }
        t["19_3"] = {
            "name": "自然定域化轨道",
            "desc": "自然定域化分子轨道",
            "params": [],
            "commands": ["19", "3", "q"],
            "result_type": "text",
        }
        t["19_4"] = {
            "name": "定域化轨道导出",
            "desc": "将定域化轨道保存到文件",
            "params": [dict(P["filename"])],
            "commands": ["19", "4", "{filename}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 20: 弱相互作用可视化 ====================
        weak_items = [
            ("20_1", "NCI分析", "非共价相互作用分析", "1"),
            ("20_2", "IGM分析", "独立梯度模型", "2"),
            ("20_3", "mIGM分析", "改进的独立梯度模型", "3"),
            ("20_4", "IGMH分析", "IGM Hirshfeld变体", "4"),
            ("20_5", "DORI分析", "密度重叠区域指示函数", "5"),
            ("20_6", "aRDG分析", "各向异性约化密度梯度", "6"),
        ]
        for key, name, desc, submenu in weak_items:
            t[key] = {
                "name": name,
                "desc": desc,
                "params": [
                    dict(P["grid_quality3"]),
                    {"name": "输出类型", "key": "output", "type": "combo",
                     "options": ["散点图", "导出cube"], "default": 0,
                     "desc": "选择生成散点图数据还是导出cube文件"},
                ],
                "commands": ["20", submenu, "1", "{grid}", "", "", "{output}", "", "0", "0", "q"],
                "grid_map": dict(cls._GRID_MAP_3),
                "output_map": {"散点图": "2", "导出cube": "1"},
                "result_type": "nci",
            }
        # Hirshfeld surface 固定为表面分析
        t["20_7"] = {
            "name": "Hirshfeld surface",
            "desc": "Hirshfeld表面分析",
            "params": [dict(P["grid_quality3"])],
            "commands": ["20", "7", "1", "{grid}", "", "", "0", "0", "q"],
            "grid_map": dict(cls._GRID_MAP_3),
            "result_type": "nci",
        }
        t["20_8"] = {
            "name": "IGM片段间相互作用",
            "desc": "分析片段间的IGM相互作用",
            "params": [dict(P["grid_quality3"])],
            "commands": ["20", "8", "1", "{grid}", "", "", "2", "", "0", "0", "q"],
            "grid_map": dict(cls._GRID_MAP_3),
            "result_type": "nci",
        }
        t["20_9"] = {
            "name": "弱相互作用指数汇总",
            "desc": "输出多种弱相互作用指标",
            "params": [],
            "commands": ["20", "10", "q"],
            "result_type": "nci",
        }

        # ==================== 菜单 21: 能量分解分析 ====================
        t["21_1"] = {
            "name": "基于片段的能量分解",
            "desc": "片段能量分解",
            "params": [],
            "commands": ["21", "1", "q"],
            "result_type": "text",
        }
        t["21_2"] = {
            "name": "基于轨道的能量分解",
            "desc": "轨道能量分解",
            "params": [],
            "commands": ["21", "2", "q"],
            "result_type": "text",
        }
        t["21_3"] = {
            "name": "SAPT能量分解",
            "desc": "对称化微扰理论能量分解",
            "params": [],
            "commands": ["21", "3", "q"],
            "result_type": "text",
        }
        t["21_4"] = {
            "name": "ALMO能量分解",
            "desc": " absolutely localized molecular orbital EDA",
            "params": [],
            "commands": ["21", "4", "q"],
            "result_type": "text",
        }
        t["21_5"] = {
            "name": "能量分解结果导出",
            "desc": "导出能量分解结果到文件",
            "params": [dict(P["filename"])],
            "commands": ["21", "5", "{filename}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 22: 概念DFT分析 ====================
        t["22_1"] = {
            "name": "Fukui函数",
            "desc": "亲电/亲核Fukui函数",
            "params": [],
            "commands": ["22", "1", "q"],
            "result_type": "text",
        }
        t["22_2"] = {
            "name": "软硬度",
            "desc": "全局软硬度",
            "params": [],
            "commands": ["22", "2", "q"],
            "result_type": "text",
        }
        t["22_3"] = {
            "name": "局部软度",
            "desc": "局部软度分析",
            "params": [],
            "commands": ["22", "3", "q"],
            "result_type": "text",
        }
        t["22_4"] = {
            "name": "电负性/化学势",
            "desc": "计算电负性与化学势",
            "params": [],
            "commands": ["22", "4", "q"],
            "result_type": "text",
        }
        t["22_5"] = {
            "name": "亲电指数",
            "desc": "计算全局与局部亲电指数",
            "params": [],
            "commands": ["22", "5", "q"],
            "result_type": "text",
        }
        t["22_6"] = {
            "name": "概念DFT结果导出",
            "desc": "导出概念DFT分析结果",
            "params": [dict(P["filename"])],
            "commands": ["22", "6", "{filename}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 23: ETS-NOCV分析 ====================
        t["23_1"] = {
            "name": "ETS-NOCV分析",
            "desc": "扩展过渡态自然轨道",
            "params": [],
            "commands": ["23", "1", "q"],
            "result_type": "text",
        }
        t["23_2"] = {
            "name": "NOCV轨道可视化",
            "desc": "将NOCV轨道导出为cube",
            "params": [dict(P["isovalue"])],
            "commands": ["23", "2", "{isovalue}", "q"],
            "result_type": "text",
        }
        t["23_3"] = {
            "name": "ETS能量分解项",
            "desc": "输出ETS能量分解各项",
            "params": [],
            "commands": ["23", "3", "q"],
            "result_type": "text",
        }
        t["23_4"] = {
            "name": "NOCV结果导出",
            "desc": "导出NOCV分析结果",
            "params": [dict(P["filename"])],
            "commands": ["23", "4", "{filename}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 24: (超)极化率分析 ====================
        t["24_1"] = {
            "name": "极化率计算",
            "desc": "静态极化率",
            "params": [],
            "commands": ["24", "1", "q"],
            "result_type": "text",
        }
        t["24_2"] = {
            "name": "超极化率计算",
            "desc": "静态超极化率",
            "params": [],
            "commands": ["24", "2", "q"],
            "result_type": "text",
        }
        t["24_3"] = {
            "name": "极化率各向异性",
            "desc": "分析极化率张量的各向异性",
            "params": [],
            "commands": ["24", "3", "q"],
            "result_type": "text",
        }
        t["24_4"] = {
            "name": "SHG超极化率",
            "desc": "二次谐波产生超极化率",
            "params": [],
            "commands": ["24", "4", "q"],
            "result_type": "text",
        }
        t["24_5"] = {
            "name": "极化率结果导出",
            "desc": "导出极化率计算结果",
            "params": [dict(P["filename"])],
            "commands": ["24", "5", "{filename}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 25: 电子离域与芳香性分析 ====================
        t["25_1"] = {
            "name": "NICS分析",
            "desc": "核独立化学位移",
            "params": [
                {"name": "环编号", "key": "ring", "type": "int", "min": 1, "max": 100, "default": 1,
                 "desc": "要计算NICS的环编号"},
            ],
            "commands": ["25", "1", "{ring}", "", "q"],
            "result_type": "text",
        }
        t["25_2"] = {
            "name": "FLU指数",
            "desc": "芳香性波动指数",
            "params": [],
            "commands": ["25", "2", "q"],
            "result_type": "text",
        }
        t["25_3"] = {
            "name": "HOMA指数",
            "desc": "谐振子模型芳香性",
            "params": [],
            "commands": ["25", "3", "q"],
            "result_type": "text",
        }
        t["25_4"] = {
            "name": "MCI指数",
            "desc": "多中心指数",
            "params": [],
            "commands": ["25", "4", "q"],
            "result_type": "text",
        }
        t["25_5"] = {
            "name": "NICS_ZZ分析",
            "desc": "垂直于环平面的NICS分量",
            "params": [
                {"name": "环编号", "key": "ring", "type": "int", "min": 1, "max": 100, "default": 1,
                 "desc": "要计算NICS_ZZ的环编号"},
            ],
            "commands": ["25", "5", "{ring}", "", "q"],
            "result_type": "text",
        }
        t["25_6"] = {
            "name": "电子离域指数",
            "desc": "计算电子离域指数(EDI)",
            "params": [],
            "commands": ["25", "6", "q"],
            "result_type": "text",
        }
        t["25_7"] = {
            "name": "芳香性结果汇总",
            "desc": "输出多种芳香性指标汇总",
            "params": [],
            "commands": ["25", "7", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 26: 结构与几何相关分析 ====================
        t["26_1"] = {
            "name": "显示原子坐标",
            "desc": "显示所有原子的笛卡尔坐标",
            "params": [],
            "commands": ["26", "1", "q"],
            "result_type": "text",
        }
        t["26_2"] = {
            "name": "显示键长键角",
            "desc": "计算并显示所有键长和键角",
            "params": [],
            "commands": ["26", "2", "q"],
            "result_type": "text",
        }
        t["26_3"] = {
            "name": "显示分子对称性",
            "desc": "检测并显示分子点群",
            "params": [],
            "commands": ["26", "3", "q"],
            "result_type": "text",
        }
        t["26_4"] = {
            "name": "坐标变换",
            "desc": "平移、旋转等坐标变换",
            "params": [],
            "commands": ["26", "4", "q"],
            "result_type": "text",
        }
        t["26_5"] = {
            "name": "计算质心与转动惯量",
            "desc": "输出分子的质心与主轴",
            "params": [],
            "commands": ["26", "5", "q"],
            "result_type": "text",
        }
        t["26_6"] = {
            "name": "计算偶极矩",
            "desc": "输出分子偶极矩",
            "params": [],
            "commands": ["26", "6", "q"],
            "result_type": "text",
        }
        t["26_7"] = {
            "name": "计算特定键长",
            "desc": "计算两个原子之间的距离",
            "params": [
                {"name": "原子1", "key": "a1", "type": "int", "min": 1, "max": 9999, "default": 1,
                 "desc": "第一个原子编号"},
                {"name": "原子2", "key": "a2", "type": "int", "min": 1, "max": 9999, "default": 2,
                 "desc": "第二个原子编号"},
            ],
            "commands": ["26", "7", "{a1}", "{a2}", "q"],
            "result_type": "text",
        }
        t["26_8"] = {
            "name": "计算特定键角",
            "desc": "计算三个原子形成的键角",
            "params": [
                {"name": "原子1", "key": "a1", "type": "int", "min": 1, "max": 9999, "default": 1,
                 "desc": "键角第一个原子编号"},
                {"name": "原子2", "key": "a2", "type": "int", "min": 1, "max": 9999, "default": 2,
                 "desc": "键角顶点原子编号"},
                {"name": "原子3", "key": "a3", "type": "int", "min": 1, "max": 9999, "default": 3,
                 "desc": "键角第三个原子编号"},
            ],
            "commands": ["26", "8", "{a1}", "{a2}", "{a3}", "q"],
            "result_type": "text",
        }
        t["26_9"] = {
            "name": "计算二面角",
            "desc": "计算四个原子形成的二面角",
            "params": [
                {"name": "原子1", "key": "a1", "type": "int", "min": 1, "max": 9999, "default": 1,
                 "desc": "二面角第一个原子编号"},
                {"name": "原子2", "key": "a2", "type": "int", "min": 1, "max": 9999, "default": 2,
                 "desc": "二面角第二个原子编号"},
                {"name": "原子3", "key": "a3", "type": "int", "min": 1, "max": 9999, "default": 3,
                 "desc": "二面角第三个原子编号"},
                {"name": "原子4", "key": "a4", "type": "int", "min": 1, "max": 9999, "default": 4,
                 "desc": "二面角第四个原子编号"},
            ],
            "commands": ["26", "9", "{a1}", "{a2}", "{a3}", "{a4}", "q"],
            "result_type": "text",
        }

        # ==================== 菜单 100/200/300: 其他功能 ====================
        other_100 = [
            ("100_1", "计算键偶极矩", "计算化学键的偶极矩", ["100", "1", "q"]),
            ("100_2", "原子核处性质", "原子核位置的实空间函数", ["100", "2", "q"]),
            ("100_3", "计算分子直径", "分子的最长距离", ["100", "3", "q"]),
            ("100_4", "输出重叠矩阵", "输出基函数重叠矩阵", ["100", "4", "q"]),
            ("100_5", "输出密度矩阵", "输出密度矩阵到文件", ["100", "5", "q"]),
            ("100_6", "输出Fock矩阵", "输出Fock/Kohn-Sham矩阵", ["100", "6", "q"]),
            ("100_7", "输出Hamiltonian矩阵", "输出单电子Hamiltonian矩阵", ["100", "7", "q"]),
            ("100_8", "计算Virial比值", "动能与势能的比值", ["100", "8", "q"]),
        ]
        other_200 = [
            ("200_1", "输出占据数", "输出自然轨道占据数", ["200", "1", "q"]),
            ("200_2", "输出轨道能量", "输出所有轨道能量", ["200", "2", "q"]),
            ("200_3", "输出Mulliken布居", "Mulliken布居矩阵", ["200", "3", "q"]),
            ("200_4", "计算Stoddart指数", "Stoddart 连通性指数", ["200", "4", "q"]),
            ("200_5", "计算信息论指标", "Shannon熵等信息论量", ["200", "5", "q"]),
            ("200_6", "计算ESP拟合电荷", "静电势拟合电荷(简化流程)", ["200", "6", "q"]),
            ("200_7", "输出偶极矩积分", "电偶极矩积分矩阵", ["200", "7", "q"]),
            ("200_8", "输出角动量矩阵", "角动量算符矩阵元", ["200", "8", "q"]),
        ]
        other_300 = [
            ("300_1", "生成输入文件", "为其他程序生成输入文件", ["300", "1", "q"]),
            ("300_2", "批量处理", "批量处理多个波函数文件", ["300", "2", "q"]),
            ("300_3", "执行外部脚本", "调用外部脚本或命令", ["300", "3", "q"]),
            ("300_4", "设置工作目录", "更改当前工作目录", ["300", "4", "", "q"]),
            ("300_5", "内存与线程设置", "设置并行线程数", ["300", "5", "q"]),
            ("300_6", "查看计算设置", "输出当前所有设置参数", ["300", "6", "q"]),
            ("300_7", "保存设置", "将当前设置保存到配置文件", ["300", "7", "q"]),
            ("300_8", "加载设置", "从配置文件加载设置", ["300", "8", "q"]),
        ]
        for key, name, desc, cmds in other_100 + other_200 + other_300:
            t[key] = {
                "name": name,
                "desc": desc,
                "params": [],
                "commands": cmds,
                "result_type": "text",
            }

        # 填充 SUB_MENUS 索引
        cls.SUB_MENUS.clear()
        for parent_key, items in t.items():
            parts = parent_key.split("_")
            if len(parts) == 2:
                main_key, sub_key = parts[0], parts[1]
                if main_key not in cls.SUB_MENUS:
                    cls.SUB_MENUS[main_key] = {}
                cls.SUB_MENUS[main_key][sub_key] = {
                    "name": items["name"],
                    "desc": items.get("desc", "")
                }

    @classmethod
    def get_main_menu_items(cls):
        """获取排序后的主菜单项列表。"""
        cls._ensure_templates()

        def sort_key(item):
            key = item[0]
            try:
                return int(key)
            except Exception:
                return 999
        return sorted(cls.MAIN_MENU.items(), key=sort_key)

    @classmethod
    def get_sub_menu(cls, parent_key):
        """获取指定主菜单下的子菜单。"""
        cls._ensure_templates()
        return cls.SUB_MENUS.get(parent_key, {})

    @classmethod
    def get_command_template(cls, parent_key, sub_key):
        """获取指定子菜单的命令模板。"""
        cls._ensure_templates()
        key = f"{parent_key}_{sub_key}"
        return cls.PARAMETER_TEMPLATES.get(key)

    @staticmethod
    def build_command_sequence(template, params):
        """根据模板和参数构建 Multiwfn 命令序列。"""
        commands = []
        for cmd in template.get("commands", []):
            cmd_str = str(cmd)
            if cmd_str.startswith("{") and cmd_str.endswith("}"):
                param_key = cmd_str[1:-1]
                mapping_key = f"{param_key}_map"
                if mapping_key in template:
                    mapping = template[mapping_key]
                    value = params.get(param_key)
                    if value is None:
                        commands.append("")
                    else:
                        mapped = mapping.get(value)
                        commands.append("" if mapped is None else str(mapped))
                else:
                    value = params.get(param_key)
                    commands.append("" if value is None else str(value))
            else:
                commands.append(cmd_str)
        return commands
