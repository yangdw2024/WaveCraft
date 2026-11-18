#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multiwfn 输出解析器。

将 Multiwfn 的文本输出解析为结构化的 Python 字典/列表，
供 GUI 表格、图表和导出功能使用。
"""

import re


class OutputParser:
    """Multiwfn 输出解析器。"""

    # 常见元素的原子序数，用于从电子布居数推算净电荷
    NUCLEAR_CHARGES = {
        "H": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7, "O": 8, "F": 9, "Ne": 10,
        "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "P": 15, "S": 16, "Cl": 17, "Ar": 18,
        "K": 19, "Ca": 20, "Sc": 21, "Ti": 22, "V": 23, "Cr": 24, "Mn": 25, "Fe": 26,
        "Co": 27, "Ni": 28, "Cu": 29, "Zn": 30, "Ga": 31, "Ge": 32, "As": 33, "Se": 34,
        "Br": 35, "Kr": 36, "Rb": 37, "Sr": 38, "Y": 39, "Zr": 40, "Nb": 41, "Mo": 42,
        "Tc": 43, "Ru": 44, "Rh": 45, "Pd": 46, "Ag": 47, "Cd": 48, "In": 49, "Sn": 50,
        "Sb": 51, "Te": 52, "I": 53, "Xe": 54, "Cs": 55, "Ba": 56, "La": 57,
        "Hf": 72, "Ta": 73, "W": 74, "Re": 75, "Os": 76, "Ir": 77, "Pt": 78, "Au": 79,
        "Hg": 80, "Tl": 81, "Pb": 82, "Bi": 83,
    }

    @staticmethod
    def _parse_charge_section(output, header_pattern):
        """辅助：根据表头定位一个电荷区块，并解析区块内所有 'idx elem charge' 行。"""
        charges = []
        for section_match in header_pattern.finditer(output):
            start = section_match.end()
            # 区块在下一个空行、下一个 "atomic charges" 表头或文件末尾结束
            end_match = re.search(r"(?:\n\s*\n|(?:[A-Za-z]+\s+atomic\s+charges:))", output[start:], re.IGNORECASE)
            end = start + end_match.start() if end_match else len(output)
            section = output[start:end]
            row_pattern = re.compile(r"^\s*(\d+)\s+([A-Za-z]{1,3})\s+([-+\d.]+)\s*$", re.MULTILINE)
            for match in row_pattern.findall(section):
                try:
                    idx = int(match[0])
                    elem = match[1].strip()
                    val = float(match[2])
                    if abs(val) > 50:
                        continue
                    charges.append({
                        "index": idx,
                        "element": elem,
                        "charge": val,
                    })
                except (ValueError, IndexError):
                    continue
            if charges:
                break
        return charges

    @staticmethod
    def parse_charges(output):
        """解析原子电荷。支持 Mulliken/Lowdin/Hirshfeld/ADCH/CHELPG/MK/Becke/CM5/SCPA/RESP/MBIS/Gasteiger/AIM 等多种格式。"""
        charges = []

        # 常见电荷输出格式正则表达式，按优先级排列
        net_charge_patterns = [
            # Atom   1(O )    Net charge:  -0.123456
            re.compile(r"Atom\s+(\d+)\(([A-Za-z]+)\s*\).*?Net charge:\s*([-+\d.]+)", re.IGNORECASE),
            # Atom  1(O ):   -0.123456
            re.compile(r"^\s*Atom\s+(\d+)\(([A-Za-z]+)\s*\):\s+([-+\d.]+)", re.MULTILINE),
            # Hirshfeld/ADCH/CM5/CHELPG/MK/RESP/MBIS/Becke/Gasteiger/AIM charge of atom   1(O ) is   0.123456
            re.compile(r"(?:Hirshfeld|ADCH|CM5|CHELPG|MK|RESP|MBIS|Becke|Gasteiger|AIM)\s+(?:atomic\s+)?charge\s+of\s+atom\s+(\d+)\(([A-Za-z]+)\s*\)\s+is\s+([-+\d.]+)", re.IGNORECASE),
            # Final atomic charges:  Atom   1(O ):   -0.123456
            re.compile(r"Final atomic charges:.*?Atom\s+(\d+)\(([A-Za-z]+)\s*\):\s+([-+\d.]+)", re.DOTALL | re.IGNORECASE),
            # 通用兜底：原子电荷表格列
            re.compile(r"^\s*(\d+)\s+([A-Za-z]{1,3})\s+([-+\d.]+)\s*$", re.MULTILINE),
        ]

        for pattern in net_charge_patterns:
            matches = pattern.findall(output)
            if matches:
                for match in matches:
                    try:
                        idx = int(match[0])
                        elem = match[1].strip()
                        val = float(match[2])
                        if abs(val) > 50:
                            continue
                        charges.append({
                            "index": idx,
                            "element": elem,
                            "charge": val,
                        })
                    except (ValueError, IndexError):
                        continue
                if charges:
                    break

        # 针对各种 "XXX atomic charges:" 表头进行区块解析
        if not charges:
            section_headers = [
                (r"(?:Mulliken|Lowdin|SCPA)\s+(?:atom\s+)?(?:population\s+and\s+)?atomic\s+charges:", re.IGNORECASE),
                (r"Hirshfeld\s+atomic\s+charges:", re.IGNORECASE),
                (r"Becke\s+atomic\s+charges:", re.IGNORECASE),
                (r"ADCH\s+atomic\s+charges:", re.IGNORECASE),
                (r"CHELPG\s+atomic\s+charges:", re.IGNORECASE),
                (r"MK\s+atomic\s+charges:", re.IGNORECASE),
                (r"CM5\s+atomic\s+charges:", re.IGNORECASE),
                (r"RESP\s+atomic\s+charges:", re.IGNORECASE),
                (r"MBIS\s+atomic\s+charges:", re.IGNORECASE),
                (r"Gasteiger\s+(?:PEOE\s+)?(?:atomic\s+)?charges?:", re.IGNORECASE),
                (r"AIM\s+(?:atomic\s+)?charges?:", re.IGNORECASE),
            ]
            for header_re, flags in section_headers:
                charges = OutputParser._parse_charge_section(output, re.compile(header_re, flags))
                if charges:
                    break

        # 若未解析到净电荷，尝试解析电子布居数并换算
        if not charges:
            population_pattern = re.compile(
                r"(?:atomic\s+)?(?:electron\s+)?population\s+of\s+atom\s+(\d+)\(([A-Za-z]+)\s*\).*?population:\s+([\d.]+)",
                re.IGNORECASE | re.DOTALL
            )
            matches = population_pattern.findall(output)
            for match in matches:
                try:
                    idx = int(match[0])
                    elem = match[1].strip()
                    pop = float(match[2])
                    nuc = OutputParser.NUCLEAR_CHARGES.get(elem, 0)
                    if nuc > 0 and abs(pop - nuc) < 10:
                        charges.append({
                            "index": idx,
                            "element": elem,
                            "charge": nuc - pop,
                        })
                except (ValueError, IndexError):
                    continue

        # 去重并按原子序号排序
        unique = {}
        for c in charges:
            unique[c["index"]] = c
        return sorted(unique.values(), key=lambda x: x["index"])

    @staticmethod
    def parse_chg_file(filepath):
        """解析 Multiwfn 生成的 .chg 电荷文件。"""
        charges = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = re.split(r"\s+", line)
                    if len(parts) >= 3:
                        try:
                            charges.append({
                                "index": int(parts[0]),
                                "element": parts[1],
                                "charge": float(parts[2]),
                            })
                        except (ValueError, IndexError):
                            continue
        except Exception:
            pass
        return charges

    @staticmethod
    def parse_bond_orders(output):
        """解析键级输出。支持标准格式、Wiberg/Mayer bond order between atom X and Y 等。"""
        bond_orders = []
        patterns = [
            # Multiwfn 标准格式: # 1:    1(C )    2(O )    1.234
            re.compile(r"#\s*(\d+):\s*(\d+)\(([A-Za-z]+)\s*\)\s+(\d+)\(([A-Za-z]+)\s*\)\s+([\d.]+)"),
            # 简化格式: 1 2 1.234
            re.compile(r"^(\d+)\s+(\d+)\s+([\d.]+)$", re.MULTILINE),
            # Bond 1-2: 1.234
            re.compile(r"Bond\s+(\d+)-(\d+):\s*([\d.]+)"),
            # Wiberg/Mayer/Fuzzy/Laplacian bond order between atom 1 and 2 ...: 1.234
            re.compile(r"(?:Wiberg|Mayer|Fuzzy|Laplacian|IBSI)\s+bond order\s+between\s+atom\s+(\d+)\s+and\s+(\d+).*?:\s*([\d.]+)", re.IGNORECASE),
            # Bond order between atom 1(C ) and 2(O ): 1.234
            re.compile(r"[Bb]ond order\s+between\s+atom\s+(\d+)\(([A-Za-z]+)\s*\)\s+and\s+(\d+)\(([A-Za-z]+)\s*\):\s*([\d.]+)"),
            # Mulliken bond order between atom 1 and 2: 1.234
            re.compile(r"Mulliken\s+bond order\s+between\s+atom\s+(\d+)\s+and\s+(\d+).*?:\s*([-+\d.]+)", re.IGNORECASE),
            # 原子对带元素符号：1(O )   2(H )   0.898
            re.compile(r"^(\d+)\(([A-Za-z]+)\s*\)\s+(\d+)\(([A-Za-z]+)\s*\)\s+([\d.]+)$", re.MULTILINE),
        ]

        for pattern in patterns:
            matches = pattern.findall(output)
            if matches:
                for match in matches:
                    try:
                        if len(match) == 6:
                            bond_orders.append({
                                "atom1": f"{match[1]}({match[2]})",
                                "atom2": f"{match[3]}({match[4]})",
                                "bond_order": float(match[5]),
                            })
                        elif len(match) == 5:
                            bond_orders.append({
                                "atom1": f"{match[0]}({match[1]})",
                                "atom2": f"{match[2]}({match[3]})",
                                "bond_order": float(match[4]),
                            })
                        elif len(match) == 3:
                            bond_orders.append({
                                "atom1": f"Atom{match[0]}",
                                "atom2": f"Atom{match[1]}",
                                "bond_order": float(match[2]),
                            })
                    except (ValueError, IndexError):
                        continue
                if bond_orders:
                    break

        return sorted(bond_orders, key=lambda x: x["bond_order"], reverse=True)

    @staticmethod
    def parse_dos_data(filepath):
        """解析 dos_data.txt 中的态密度数据。"""
        data = {"energy": [], "density": []}
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            data["energy"].append(float(parts[0]))
                            data["density"].append(float(parts[1]))
                        except ValueError:
                            continue
        except Exception:
            pass
        return data

    @staticmethod
    def parse_spectrum_data(filepath_or_output):
        """解析光谱数据（激发态能量/频率与强度）。"""
        spectrum_data = []
        try:
            if isinstance(filepath_or_output, str) and "\n" not in filepath_or_output:
                import os
                if os.path.exists(filepath_or_output):
                    with open(filepath_or_output, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                else:
                    content = filepath_or_output
            else:
                content = filepath_or_output

            lines = content.split("\n")
            state_idx = 1
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        energy = float(parts[0])
                        intensity = float(parts[1])
                        wavelength = 1240.0 / energy if energy != 0 else 0
                        spectrum_data.append({
                            "state": state_idx,
                            "energy_eV": energy,
                            "wavelength_nm": wavelength,
                            "intensity": intensity,
                        })
                        state_idx += 1
                    except ValueError:
                        continue
        except Exception:
            pass
        return spectrum_data

    @staticmethod
    def parse_atom_info(output):
        """解析输出中的原子坐标信息。支持 Multiwfn 标准格式、XYZ、Gaussian 标准取向等。"""
        atoms = []

        # Multiwfn 菜单 26-1 输出格式示例：
        #  Atom      Z        X/Y/Z coordinate(Angstrom)
        #  1(O )    8    0.000000    0.000000    0.117300
        section_pattern = re.compile(
            r"Atom\s+Z\s+X/Y/Z coordinate.*?\n(.*?)\n\s*\n",
            re.DOTALL | re.IGNORECASE
        )
        section_match = section_pattern.search(output)
        if section_match:
            for line in section_match.group(1).split("\n"):
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        # 第一列可能是 "1(O)" 或 "1" 和 "O"
                        idx_match = re.match(r"(\d+)\(?([A-Za-z]*)\)?", parts[0])
                        if idx_match:
                            idx = int(idx_match.group(1))
                            elem = idx_match.group(2) or parts[1]
                            x, y, z = map(float, parts[2:5])
                            atoms.append({
                                "index": idx,
                                "symbol": elem,
                                "x": x,
                                "y": y,
                                "z": z,
                            })
                    except (ValueError, IndexError):
                        continue

        # XYZ 格式：O    0.000000    0.000000    0.117300
        if not atoms:
            xyz_pattern = re.compile(
                r"^\s*([A-Za-z]{1,3})\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s*$",
                re.MULTILINE
            )
            idx = 1
            for match in xyz_pattern.findall(output):
                try:
                    atoms.append({
                        "index": idx,
                        "symbol": match[0],
                        "x": float(match[1]),
                        "y": float(match[2]),
                        "z": float(match[3]),
                    })
                    idx += 1
                except (ValueError, IndexError):
                    continue

        # 解析 Gaussian cube 文件头中的原子坐标
        if not atoms:
            # cube 头原子行格式：Z  nuclear_charge  x  y  z
            # 例如：8    8.000000    0.000000    0.000000    0.225257
            cube_pattern = re.compile(
                r"^\s*(\d+)\s+[-+\d.Ee]+\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s*$",
                re.MULTILINE
            )
            seen = set()
            for match in cube_pattern.findall(output):
                try:
                    z = int(match[0])
                    elem = OutputParser._z_to_element(z)
                    key = (elem, float(match[1]), float(match[2]), float(match[3]))
                    if key in seen:
                        continue
                    seen.add(key)
                    atoms.append({
                        "index": len(atoms) + 1,
                        "symbol": elem,
                        "x": float(match[1]),
                        "y": float(match[2]),
                        "z": float(match[3]),
                    })
                except (ValueError, IndexError):
                    continue

        # 兜底：直接搜索 "idx elem x y z" 或 "idx Z elem x y z" 格式
        if not atoms:
            patterns = [
                re.compile(r"Atom\s+(\d+)\s+([A-Za-z]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)"),
                re.compile(r"Atom\s+(\d+)\s+\d+\s+([A-Za-z]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)"),
                re.compile(r"(\d+)\s+([A-Za-z]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)"),
                # Gaussian 标准取向：Center     Atomic     Atomic             Coordinates (Angstroms)
                re.compile(r"\d+\s+([A-Za-z]+)\s+\d+\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)"),
            ]
            for pattern in patterns:
                matches = pattern.findall(output)
                if matches:
                    seen = set()
                    for match in matches:
                        try:
                            key = (match[0], float(match[2]), float(match[3]), float(match[4]))
                            if key in seen:
                                continue
                            seen.add(key)
                            atoms.append({
                                "index": len(atoms) + 1,
                                "symbol": match[1],
                                "x": float(match[2]),
                                "y": float(match[3]),
                                "z": float(match[4]),
                            })
                        except (ValueError, IndexError):
                            continue
                    if atoms:
                        break
        return atoms

    @staticmethod
    def _z_to_element(z):
        """根据原子序数返回元素符号。"""
        for elem, num in OutputParser.NUCLEAR_CHARGES.items():
            if num == z:
                return elem
        return "X"

    @staticmethod
    def parse_wfn_info(output):
        """解析波函数文件基本信息。提取能量、电子数、基函数、原子数、偶极矩、维里比、轨道占据等。"""
        info = {}
        patterns = {
            "total_energy": re.compile(r"Total energy\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "num_electrons": re.compile(r"Total/Alpha/Beta electrons:\s*([\d.]+)", re.IGNORECASE),
            "alpha_electrons": re.compile(r"Total/Alpha/Beta electrons:\s*[\d.]+\s+([\d.]+)", re.IGNORECASE),
            "beta_electrons": re.compile(r"Total/Alpha/Beta electrons:\s*[\d.]+\s+[\d.]+\s+([\d.]+)", re.IGNORECASE),
            "num_orbitals": re.compile(r"Basis functions:\s*(\d+)", re.IGNORECASE),
            "num_gtf": re.compile(r"GTFs:\s*(\d+)", re.IGNORECASE),
            "num_atoms": re.compile(r"Atoms:\s*(\d+)", re.IGNORECASE),
            "net_charge": re.compile(r"Net charge:\s*([-+\d.]+)", re.IGNORECASE),
            "multiplicity": re.compile(r"Expected multiplicity:\s*(\d+)", re.IGNORECASE),
            "dipole_moment": re.compile(r"Dipole moment\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "virial_ratio": re.compile(r"Virial ratio\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "homo_energy": re.compile(r"HOMO\s+energy\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "lumo_energy": re.compile(r"LUMO\s+energy\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "homo_lumo_gap": re.compile(r"HOMO-LUMO\s+gap\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "molecular_weight": re.compile(r"Molecule weight:\s*([\d.]+)", re.IGNORECASE),
            "point_group": re.compile(r"Point group:\s*(\S+)", re.IGNORECASE),
            "title": re.compile(r"Title line of this file:\s*(.+)", re.IGNORECASE),
        }
        for key, pattern in patterns.items():
            match = pattern.search(output)
            if match:
                try:
                    value = match.group(1).strip()
                    if key in ("point_group", "title"):
                        info[key] = value
                    elif "." in value or "e" in value.lower():
                        info[key] = float(value)
                    else:
                        info[key] = int(value)
                except ValueError:
                    info[key] = match.group(1).strip()

        # 解析轨道占据范围
        occ_match = re.search(r"Orbitals from\s+(\d+)\s+to\s+(\d+)\s+are occupied", output, re.IGNORECASE)
        if occ_match:
            try:
                info["occ_orbital_start"] = int(occ_match.group(1))
                info["occ_orbital_end"] = int(occ_match.group(2))
                info["num_occ_orbitals"] = info["occ_orbital_end"] - info["occ_orbital_start"] + 1
            except (ValueError, KeyError):
                pass

        # 解析波函数类型
        if re.search(r"restricted single-determinant", output, re.IGNORECASE):
            info["wavefunction_type"] = "RHF/RKS"
        elif re.search(r"unrestricted single-determinant", output, re.IGNORECASE):
            info["wavefunction_type"] = "UHF/UKS"
        elif re.search(r"restricted open-shell", output, re.IGNORECASE):
            info["wavefunction_type"] = "ROHF/ROKS"

        if not info:
            info["status"] = "波函数文件已加载"
        return info

    @staticmethod
    def parse_critical_points(output):
        """解析 AIM 临界点坐标。"""
        cps = []
        # 匹配 "CP #1    0.123   -0.456    0.789" 类似格式
        pattern = re.compile(
            r"CP\s*#?\s*(\d+).*?([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)",
            re.IGNORECASE
        )
        matches = pattern.findall(output)
        for match in matches:
            try:
                cps.append({
                    "index": int(match[0]),
                    "x": float(match[1]),
                    "y": float(match[2]),
                    "z": float(match[3]),
                })
            except (ValueError, IndexError):
                continue
        return cps

    @staticmethod
    def parse_aromaticity_results(output):
        """解析芳香性分析结果（NICS、FLU 等）。"""
        results = {}
        nics_pattern = re.compile(r"NICS\s*[:=]\s*([-+\d.]+)", re.IGNORECASE)
        nics_matches = nics_pattern.findall(output)
        if nics_matches:
            try:
                results["NICS_values"] = [float(v) for v in nics_matches]
            except ValueError:
                pass
        flu_pattern = re.compile(r"FLU\s*[:=]\s*([-+\d.]+)", re.IGNORECASE)
        flu_match = flu_pattern.search(output)
        if flu_match:
            try:
                results["FLU"] = float(flu_match.group(1))
            except ValueError:
                pass
        homa_pattern = re.compile(r"HOMA\s*[:=]\s*([-+\d.]+)", re.IGNORECASE)
        homa_match = homa_pattern.search(output)
        if homa_match:
            try:
                results["HOMA"] = float(homa_match.group(1))
            except ValueError:
                pass
        return results

    @staticmethod
    def parse_spectrum_table(output):
        """解析表格形式的光谱数据。"""
        spectrum_data = []
        pattern = re.compile(r"(\d+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)")
        matches = pattern.findall(output)
        for match in matches:
            try:
                spectrum_data.append({
                    "state": int(match[0]),
                    "energy_eV": float(match[1]),
                    "wavelength_nm": float(match[2]),
                    "intensity": float(match[3]),
                })
            except (ValueError, IndexError):
                continue
        return spectrum_data

    @staticmethod
    def parse_dos(output):
        """从原始输出中解析 DOS 数据。"""
        dos_pattern = re.compile(r"([-+\d.Ee]+)\s+([-+\d.Ee]+)")
        energy = []
        dos = []
        in_dos_section = False
        for line in output.split("\n"):
            if "DOS" in line or "density" in line.lower():
                in_dos_section = True
            if in_dos_section:
                match = dos_pattern.search(line)
                if match:
                    try:
                        energy.append(float(match.group(1)))
                        dos.append(float(match.group(2)))
                    except ValueError:
                        continue
        if energy and dos:
            return {"energy": energy, "dos": dos}
        return None

    @staticmethod
    def parse_spectrum(output):
        """从原始输出中解析光谱数据。"""
        spec_pattern = re.compile(r"([-+\d.Ee]+)\s+([-+\d.Ee]+)")
        frequency = []
        intensity = []
        for line in output.split("\n"):
            match = spec_pattern.search(line)
            if match:
                try:
                    freq_val = float(match.group(1))
                    int_val = float(match.group(2))
                    frequency.append(freq_val)
                    intensity.append(int_val)
                except ValueError:
                    continue
        if frequency and intensity:
            return {
                "frequency": frequency,
                "intensity": intensity,
                "xlabel": "频率",
                "ylabel": "强度",
                "title": "光谱图",
            }
        return None

    @staticmethod
    def parse_nci_data(filepath_or_output):
        """解析 NCI/IGM 散点图数据（output.txt 格式：rho RDG ?? sign lambda2*rho）。"""
        data = []
        try:
            if isinstance(filepath_or_output, str) and "\n" not in filepath_or_output:
                import os
                if os.path.exists(filepath_or_output):
                    with open(filepath_or_output, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                else:
                    content = filepath_or_output
            else:
                content = filepath_or_output

            for line in content.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        rho = float(parts[0])
                        rdg = float(parts[1])
                        sign_val = float(parts[3])
                        data.append({
                            "rho": rho,
                            "rdg": rdg,
                            "sign_lambda2_rho": sign_val,
                        })
                    except ValueError:
                        continue
        except Exception:
            pass
        return data

    @staticmethod
    def parse_dos_table(output):
        """从表格形式解析 DOS 数据，支持 DOS.dat / dos_data.txt / orginfo.txt 等。"""
        energy = []
        dos = []
        lines = output.split("\n") if isinstance(output, str) else output
        # 尝试识别表头，找到包含 Energy / DOS / PDOS 等关键字的起始行
        in_table = False
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # 表头检测：包含 Energy、DOS、Density 等
            if re.search(r"Energy|DOS|Density|PDOS|OPDOS", line, re.IGNORECASE):
                if re.search(r"[-+\d.Ee]+", line):
                    # 如果表头行本身也含数字，需要进一步判断
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            float(parts[0])
                            float(parts[1])
                        except ValueError:
                            in_table = True
                            continue
                else:
                    in_table = True
                    continue
            # 解析数据行：取前两个有效数字作为 energy 和 dos
            parts = line.split()
            if len(parts) >= 2:
                try:
                    e_val = float(parts[0])
                    d_val = float(parts[1])
                    energy.append(e_val)
                    dos.append(d_val)
                except ValueError:
                    continue
        if energy and dos:
            return {"energy": energy, "dos": dos, "count": len(energy)}
        return None

    @staticmethod
    def parse_spectrum_lines(output):
        """从各种光谱输出格式解析数据（UV-Vis/IR/Raman 等），返回能量/频率与强度。"""
        spectrum_data = []
        state_idx = 1
        lines = output.split("\n") if isinstance(output, str) else output

        # 模式 1：明确的光谱表格行，例如 "1  4.50  275.3  0.123"
        table_pattern = re.compile(
            r"^\s*(\d+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s*$"
        )
        # 模式 2：两列数据 "energy  intensity"
        two_col_pattern = re.compile(
            r"^\s*([-+\d.Ee]+)\s+([-+\d.Ee]+)\s*$"
        )
        # 模式 3：激发态输出 "Excited State   1:   Singlet-A      4.50 eV   275.3 nm  f=0.123"
        excited_pattern = re.compile(
            r"Excited\s+State\s+(\d+).*?([-+\d.Ee]+)\s+eV\s+([-+\d.Ee]+)\s+nm.*?f=([-+\d.Ee]+)",
            re.IGNORECASE
        )

        excited_matches = excited_pattern.findall(output)
        if excited_matches:
            for match in excited_matches:
                try:
                    energy_ev = float(match[1])
                    wavelength_nm = float(match[2])
                    intensity = float(match[3])
                    spectrum_data.append({
                        "state": int(match[0]),
                        "energy_eV": energy_ev,
                        "wavelength_nm": wavelength_nm,
                        "intensity": intensity,
                    })
                except (ValueError, IndexError):
                    continue
            return spectrum_data

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = table_pattern.search(line)
            if match:
                try:
                    energy = float(match.group(2))
                    intensity = float(match.group(4))
                    wavelength = 1240.0 / energy if energy != 0 else 0
                    spectrum_data.append({
                        "state": int(match.group(1)),
                        "energy_eV": energy,
                        "wavelength_nm": wavelength,
                        "intensity": intensity,
                    })
                except (ValueError, IndexError):
                    continue
                continue
            match = two_col_pattern.search(line)
            if match:
                try:
                    energy = float(match.group(1))
                    intensity = float(match.group(2))
                    wavelength = 1240.0 / energy if energy != 0 else 0
                    spectrum_data.append({
                        "state": state_idx,
                        "energy_eV": energy,
                        "wavelength_nm": wavelength,
                        "intensity": intensity,
                    })
                    state_idx += 1
                except (ValueError, IndexError):
                    continue
        return spectrum_data

    @staticmethod
    def parse_thermochemistry(output):
        """解析频率/热化学数据，包括零点能、焓、自由能、熵、热容等。"""
        thermo = {}
        patterns = {
            "zero_point_energy": re.compile(r"Zero[-\s]?point\s+(?:energy|correction)\s*[:=]?\s*([-+\d.Ee]+)", re.IGNORECASE),
            "thermal_energy": re.compile(r"Thermal\s+(?:correction\s+to\s+)?energy\s*[:=]?\s*([-+\d.Ee]+)", re.IGNORECASE),
            "enthalpy": re.compile(r"Enthalpy\s*(?:H\s*)?[:=]?\s*([-+\d.Ee]+)", re.IGNORECASE),
            "gibbs_free_energy": re.compile(r"(?:Gibbs\s+free\s+energy|Free\s+energy)\s*(?:G\s*)?[:=]?\s*([-+\d.Ee]+)", re.IGNORECASE),
            "entropy": re.compile(r"Entropy\s*(?:S\s*)?[:=]?\s*([-+\d.Ee]+)", re.IGNORECASE),
            "heat_capacity": re.compile(r"Heat\s+capacity\s*(?:Cv\s*)?[:=]?\s*([-+\d.Ee]+)", re.IGNORECASE),
            "temperature": re.compile(r"Temperature\s*[:=]?\s*([-+\d.Ee]+)\s*K", re.IGNORECASE),
            "pressure": re.compile(r"Pressure\s*[:=]?\s*([-+\d.Ee]+)\s*(?:atm|Pa|bar)", re.IGNORECASE),
        }
        for key, pattern in patterns.items():
            match = pattern.search(output)
            if match:
                try:
                    value = match.group(1).strip()
                    thermo[key] = float(value)
                except ValueError:
                    thermo[key] = match.group(1).strip()

        # 解析振动频率（cm^-1）
        frequencies = []
        freq_patterns = [
            re.compile(r"Vibrational\s+frequencies\s*\(cm\^-1\).*?:\s*([-+\d.\s,]+)", re.IGNORECASE | re.DOTALL),
            re.compile(r"frequencies\s*\(cm\^-1\).*?\n(.*?)(?:\n\s*\n|\Z)", re.IGNORECASE | re.DOTALL),
        ]
        for pattern in freq_patterns:
            match = pattern.search(output)
            if match:
                text = match.group(1) if match.lastindex == 1 else match.group(0)
                for token in re.findall(r"[-+\d.Ee]+", text):
                    try:
                        freq = float(token)
                        if 0 < abs(freq) < 10000:
                            frequencies.append(freq)
                    except ValueError:
                        continue
                if frequencies:
                    break
        if frequencies:
            thermo["frequencies"] = frequencies
            thermo["num_frequencies"] = len(frequencies)

        # 解析虚频
        imag_frequencies = []
        imag_pattern = re.compile(r"imaginary\s+frequenc(?:y|ies).*?([-+\d.\s,]+)", re.IGNORECASE | re.DOTALL)
        match = imag_pattern.search(output)
        if match:
            for token in re.findall(r"[-+\d.Ee]+", match.group(1)):
                try:
                    freq = float(token)
                    if freq < 0:
                        imag_frequencies.append(freq)
                except ValueError:
                    continue
        if imag_frequencies:
            thermo["imaginary_frequencies"] = imag_frequencies
            thermo["num_imaginary_frequencies"] = len(imag_frequencies)

        return thermo
