#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multiwfn 命令序列生成器。

将 GUI 中选择的中文分析类型转换为 Multiwfn 可识别的数字命令序列。
每个静态方法都附带注释说明其对应的 Multiwfn 主菜单路径。
"""


class InputGenerator:
    """Multiwfn 命令生成器。"""

    # 菜单 7: Population analysis and calculation of atomic charges
    # Multiwfn 3.8 子选项映射：
    # 1=Hirshfeld, 2=VDD, 5=Mulliken, 6=Lowdin, 7=SCPA,
    # 10=Becke, 11=ADCH, 12=CHELPG, 13=MK, 14=AIM,
    # 15=Hirshfeld-I, 16=CM5, 17=EEM, 18=RESP,
    # 19=Gasteiger, 20=MBIS
    CHARGE_METHODS = {
        "Hirshfeld": 1,
        "VDD": 2,
        "Mulliken": 5,
        "Lowdin": 6,
        "SCPA": 7,
        "Becke": 10,
        "ADCH": 11,
        "CHELPG": 12,
        "MK": 13,
        "AIM": 14,
        "Hirshfeld-I": 15,
        "CM5": 16,
        "EEM": 17,
        "RESP": 18,
        "Gasteiger": 19,
        "MBIS": 20,
    }

    # 菜单 9: Bond order analysis
    # 1=Mayer, 2=Mayer+模糊, 3=Wiberg, 4=Mulliken, 5=多中心(AdNDP),
    # 6=离域化指数, 7=Fuzzy, 8=Laplacian, 9=Deformation, 10=π键级, 11=NAO
    BOND_ORDER_METHODS = {
        "Mayer键级": 1,
        "Mayer键级(含模糊键)": 2,
        "Wiberg键级": 3,
        "Mulliken键级": 4,
        "多中心键级": 5,
        "Fuzzy键级": 7,
        "Laplacian键级": 8,
        "Deformation键级": 9,
        "PI键级(π键级)": 10,
        "NAO键级": 11,
    }

    # 菜单 5: Output and plot specific property within a spatial region (Multiwfn 3.8)
    # 实际官方编号：
    # 1=Electron density, 2=Gradient norm, 3=Laplacian, 4=ELF, 5=LOL,
    # 6=Sign(lambda2)*rho, 7=RDG, 8=Hamiltonian KED, 9=Lagrangian KED,
    # 11=Local ionization energy, 13=ESP, 15=Density difference,
    # 16=Fukui function, 17=Dual descriptor, 5(开壳层)=Spin density
    REALSPACE_FUNCTIONS = {
        "Electron density": 1,
        "电子密度": 1,
        "Gradient norm": 2,
        "密度梯度模": 2,
        "Laplacian of density": 3,
        "密度拉普拉斯": 3,
        "ELF": 4,
        "LOL": 5,
        "Sign(lambda2)*rho": 6,
        "sign(lambda2)*rho": 6,
        "RDG": 7,
        "Hamiltonian kinetic energy density": 8,
        "Hamiltonian动能密度": 8,
        "Lagrangian kinetic energy density": 9,
        "Lagrange动能密度": 9,
        "Local ionization energy": 11,
        "局部电离能": 11,
        "ESP": 13,
        "静电势": 13,
        "Density difference": 15,
        "密度差": 15,
        "Fukui function": 16,
        "Fukui函数": 16,
        "Dual descriptor": 17,
        "双描述符": 17,
        "Spin density": 5,
        "自旋密度": 5,
    }

    # 菜单 5 的网格质量映射
    GRID_QUALITIES = {
        "Coarse": 1, "粗糙": 1, "粗糙 (快)": 1,
        "Medium": 2, "中等": 2, "中": 2,
        "Fine": 3, "精细": 3, "精细 (慢)": 3,
        "Ultra fine": 4, "超精细": 4, "超精细 (很慢)": 4, "极细": 4,
        "Custom": 5, "自定义": 5,
    }

    # 菜单 11: Plot spectrum
    # 1=IR, 2=Raman, 3=UV-Vis, 4=ECD, 5=VCD, 6=ROA, 7=NMR
    SPECTRUM_TYPES = {
        "IR": 1,
        "Raman": 2,
        "UV-Vis": 3,
        "ECD": 4,
        "VCD": 5,
        "ROA": 6,
        "NMR": 7,
    }

    # 菜单 100 -> 2: Export current structure to various file formats
    EXPORT_FORMATS = {
        "wfn": "1",
        "wfx": "2",
        "molden": "3",
        "xyz": "4",
        "pdb": "5",
        "mol": "6",
        "gjf": "7",
        "mwfn": "8",
    }

    # 菜单 20: 弱相互作用分析子选项
    # 1=NCI, 2=IGM, 3=mIGM, 4=IGMH, 5=DORI, 6=aRDG, 7=Hirshfeld surface
    WEAK_INTERACTION_TYPES = {
        "NCI散点图": ("1", "2"),
        "NCI等值面": ("1", "1"),
        "IGM散点图": ("2", "2"),
        "IGM分析": ("2", "2"),
        "IGM等值面": ("2", "1"),
        "mIGM散点图": ("3", "2"),
        "mIGM分析": ("3", "2"),
        "mIGM等值面": ("3", "1"),
        "IGMH散点图": ("4", "2"),
        "IGMH分析": ("4", "2"),
        "IGMH等值面": ("4", "1"),
        "DORI散点图": ("5", "2"),
        "DORI分析": ("5", "2"),
        "DORI等值面": ("5", "1"),
        "aRDG散点图": ("6", "2"),
        "aRDG分析": ("6", "2"),
        "aRDG等值面": ("6", "1"),
        "Hirshfeld surface": ("7", None),
    }

    @staticmethod
    def generate_charge_commands(method_name):
        """生成菜单 7 原子电荷计算命令序列。"""
        method_num = InputGenerator.CHARGE_METHODS.get(method_name)
        if method_num is None:
            raise ValueError(f"不支持的电荷方法: {method_name}")

        commands = ["7", str(method_num)]

        # 根据各电荷方法回答 Multiwfn 的交互式提示
        if method_num == 1:  # Hirshfeld
            # 选择 1: 计算并输出原子电荷，然后 n: 不保存为 .chg
            commands.extend(["1", "n"])
        elif method_num == 2:  # VDD
            commands.append("n")
        elif method_num == 5:  # Mulliken
            commands.extend(["1", "n", "0"])
        elif method_num == 6:  # Lowdin
            # 输入保存电子布居的文件名，n 表示不保存为 .chg
            commands.extend(["lowdin_pop.txt", "n"])
        elif method_num == 7:  # SCPA
            commands.extend(["1", "n", "0"])
        elif method_num in (10, 11, 16):  # Becke, ADCH, CM5
            commands.append("n")
        elif method_num in (12, 13):  # CHELPG, MK
            # 1: 计算并输出，y: 保存为 .chg
            commands.extend(["1", "y"])
        elif method_num == 14:  # AIM
            commands.append("")  # 按回车使用默认 basin 积分设置
        elif method_num == 15:  # Hirshfeld-I
            commands.extend(["1", "n"])
        elif method_num == 17:  # EEM
            commands.append("1")
        elif method_num == 18:  # RESP
            commands.extend(["2", "1", ""])
        elif method_num in (19, 20):  # Gasteiger, MBIS
            commands.append("")

        commands.extend(["0", "q"])
        return commands

    @staticmethod
    def generate_bond_order_commands(method_name):
        """生成菜单 9 键级分析命令序列。"""
        method_num = InputGenerator.BOND_ORDER_METHODS.get(method_name)
        if method_num is None:
            raise ValueError(f"不支持的键级方法: {method_name}")

        commands = ["9", str(method_num)]

        if method_num in (1, 2, 3, 4, 7, 8, 9, 10, 11):
            # n: 不保存矩阵到文件，直接输出结果
            commands.append("n")
        elif method_num == 5:  # 多中心键级(AdNDP)
            commands.append("0")

        commands.extend(["0", "q"])
        return commands

    @staticmethod
    def generate_realspace_cube_commands(func_name, grid_quality="Medium"):
        """生成菜单 5 实空间函数 cube 计算命令序列。"""
        func_num = InputGenerator.REALSPACE_FUNCTIONS.get(func_name)
        if func_num is None:
            raise ValueError(f"不支持的实空间函数: {func_name}")

        grid_num = InputGenerator.GRID_QUALITIES.get(grid_quality, 2)

        # 菜单 5 流程：选函数 -> 网格质量 -> 默认盒子(回车3次) -> 2导出cube -> 文件名(回车默认) -> 0退出 -> q
        commands = [
            "5",
            str(func_num),
            str(grid_num),
            "", "", "",  # 默认网格范围
            "2",          # 导出 cube 文件
            "",           # 默认文件名
            "0",          # 退出菜单 5
            "q",
        ]
        return commands

    @staticmethod
    def generate_dos_commands(dos_type):
        """生成菜单 10 态密度分析命令序列。"""
        type_map = {
            "total": "1", "Total DOS": "1", "总态密度(Total DOS)": "1", "总态密度": "1",
            "partial": "2", "PDOS": "2", "分态密度(PDOS)": "2", "分态密度": "2",
            "overlap": "3", "OPDOS": "3", "重叠分态密度(OPDOS)": "3", "重叠分态密度": "3",
            "local": "4", "Local DOS": "4", "局域态密度(Local DOS)": "4", "局域态密度": "4",
            "COHP": "5", "COHP曲线": "5",
            "COOP": "6", "COOP曲线": "6",
            "bandgap": "8", "带隙分析": "8",
            "photoelectron": "10", "光电子能谱": "10",
        }
        dos_cmd = type_map.get(dos_type, "1")

        # 进入菜单 10 -> 选择 DOS 类型 -> -3 保存数据 -> 文件名 -> 回车 -> -10 返回主菜单 -> q
        commands = [
            "10",
            dos_cmd,
            "-3",
            "dos_data.txt",
            "",
            "-10",
            "q",
        ]
        return commands

    @staticmethod
    def generate_spectrum_commands(spec_type, fwhm=0.0):
        """生成菜单 11 光谱分析命令序列。"""
        spec_num = InputGenerator.SPECTRUM_TYPES.get(spec_type)
        if spec_num is None:
            raise ValueError(f"不支持的光谱类型: {spec_type}")

        commands = [
            "11",
            str(spec_num),
            str(fwhm),
            "q",
        ]
        return commands

    @staticmethod
    def _format_fragment_atoms(fragment_atoms):
        """将片段原子参数转换为 Multiwfn 可接受的字符串格式。"""
        if fragment_atoms is None:
            return ""
        if isinstance(fragment_atoms, str):
            return fragment_atoms.strip()
        if isinstance(fragment_atoms, (list, tuple)):
            return ",".join(str(a) for a in fragment_atoms)
        return str(fragment_atoms)

    @staticmethod
    def generate_weak_interaction_commands(analysis_type, grid_quality="Medium", fragment_atoms=None):
        """生成菜单 20 弱相互作用分析命令序列。"""
        mapping = InputGenerator.WEAK_INTERACTION_TYPES.get(analysis_type)
        if mapping is None:
            raise ValueError(f"不支持的弱相互作用分析: {analysis_type}")

        submenu, plot_or_cube = mapping
        grid_num = InputGenerator.GRID_QUALITIES.get(grid_quality, 2)

        if analysis_type == "Hirshfeld surface":
            # 菜单 20 -> 7 -> 1 开始分析 -> 网格质量 -> 默认盒子(3次回车) -> 0 退出 -> q
            return ["20", submenu, "1", str(grid_num), "", "", "0", "0", "q"]

        # 进入菜单 20 -> 子选项
        commands = ["20", submenu]

        # IGM(2)/IGMH(4) 需要定义片段：在进入子选项后、选择输出类型前插入 1 -> 片段 -> 0
        fragment_str = InputGenerator._format_fragment_atoms(fragment_atoms)
        if fragment_str and submenu in ("2", "4"):
            commands.extend(["1", fragment_str, "0", "1"])
        else:
            commands.append("1")

        # 网格质量 -> 默认盒子(3次回车) -> 输出类型(1=cube, 2=散点) -> 默认文件名 -> 返回 -> 退出 -> q
        commands.extend([str(grid_num), "", "", plot_or_cube, "", "0", "0", "q"])
        return commands

    @staticmethod
    def generate_wfn_check_commands():
        """生成获取波函数基本信息的命令序列（菜单 6-1 输出波函数信息）。"""
        return ["6", "1", "q"]

    @staticmethod
    def generate_orbital_view_commands(orbital_index, isovalue=0.02):
        """生成菜单 0-4 轨道可视化 cube 导出命令序列。"""
        commands = [
            "0",
            "4",
            str(orbital_index),
            "1",          # 导出 cube
            str(isovalue),
            "q",
        ]
        return commands

    @staticmethod
    def generate_aim_commands():
        """生成菜单 2-1 AIM 临界点搜索命令序列。"""
        return ["2", "1", "", "", "", "", "q"]

    @staticmethod
    def generate_aromaticity_commands(method, ring_index=1):
        """生成菜单 25 芳香性分析命令序列。"""
        method_lower = method.lower()
        if "nics" in method_lower:
            commands = ["25", "1", str(ring_index), "", "q"]
        elif "flu" in method_lower:
            commands = ["25", "2", "q"]
        elif "homa" in method_lower:
            commands = ["25", "3", "q"]
        elif "mci" in method_lower:
            commands = ["25", "4", "q"]
        elif "acid" in method_lower:
            commands = ["25", "5", "q"]
        else:
            commands = ["25", "1", "", "q"]
        return commands

    @staticmethod
    def generate_excitation_commands(method):
        """生成菜单 18 电子激发分析命令序列。"""
        method_lower = method.lower()
        if "hole" in method_lower or "electron" in method_lower:
            commands = ["18", "1", "q"]
        elif "transition" in method_lower:
            commands = ["18", "2", "q"]
        elif "charge" in method_lower:
            commands = ["18", "3", "q"]
        elif "natural" in method_lower or "nto" in method_lower:
            commands = ["18", "4", "q"]
        else:
            commands = ["18", "1", "q"]
        return commands

    @staticmethod
    def generate_export_commands(format_type):
        """生成菜单 100 -> 2 文件导出命令序列。"""
        fmt_num = InputGenerator.EXPORT_FORMATS.get(format_type)
        if fmt_num is None:
            raise ValueError(f"不支持的导出格式: {format_type}")

        commands = [
            "100",
            "2",
            fmt_num,
            "output",
            "q",
        ]
        return commands
