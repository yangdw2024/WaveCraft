import numpy as np
from typing import List, Optional


class CubeParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.atoms = []
        self.data = None
        self.origin = None
        self.axes = None
        self.dimensions = None
        self.parse()

    def parse(self):
        with open(self.filepath, "r") as f:
            lines = f.readlines()

        idx = 2
        natoms = int(lines[idx].split()[0])
        self.origin = np.array([float(x) for x in lines[idx].split()[1:4]])
        idx += 1

        self.dimensions = []
        self.axes = []
        for i in range(3):
            parts = lines[idx].split()
            self.dimensions.append(int(parts[0]))
            self.axes.append(np.array([float(x) for x in parts[1:4]]))
            idx += 1

        element_names = {
            1: "H", 2: "He", 6: "C", 7: "N", 8: "O", 9: "F",
            11: "Na", 12: "Mg", 14: "Si", 15: "P", 16: "S", 17: "Cl",
            19: "K", 20: "Ca", 26: "Fe", 29: "Cu", 30: "Zn", 35: "Br",
            53: "I", 0: "X",
        }

        self.atoms = []
        for i in range(natoms):
            parts = lines[idx].split()
            z = int(parts[0])
            charge = float(parts[1])
            xyz = np.array([float(x) for x in parts[2:5]])
            element = element_names.get(z, "X")
            self.atoms.append({
                "index": i + 1,
                "element": element,
                "z": z,
                "charge": charge,
                "x": xyz[0],
                "y": xyz[1],
                "z_coord": xyz[2],
            })
            idx += 1

        data_values = []
        while idx < len(lines):
            parts = lines[idx].split()
            data_values.extend([float(x) for x in parts])
            idx += 1

        nx, ny, nz = self.dimensions
        self.data = np.array(data_values).reshape(nz, ny, nx)

    def get_plane_slice(self, plane: str = "xy", index: Optional[int] = None):
        nz, ny, nx = self.data.shape

        if plane == "xy":
            if index is None:
                index = nz // 2
            index = max(0, min(index, nz - 1))
            return self.data[index, :, :]
        elif plane == "xz":
            if index is None:
                index = ny // 2
            index = max(0, min(index, ny - 1))
            return self.data[:, index, :]
        elif plane == "yz":
            if index is None:
                index = nx // 2
            index = max(0, min(index, nx - 1))
            return self.data[:, :, index]
        return self.data

    def get_coordinates(self, axis: str):
        if axis == "x":
            n = self.dimensions[0]
            origin = self.origin[0]
            step = self.axes[0][0]
        elif axis == "y":
            n = self.dimensions[1]
            origin = self.origin[1]
            step = self.axes[1][1]
        elif axis == "z":
            n = self.dimensions[2]
            origin = self.origin[2]
            step = self.axes[2][2]
        else:
            return np.array([0, 1])
        return np.linspace(origin, origin + step * (n - 1), n)

    def get_extent(self, plane: str = "xy") -> List[float]:
        origin = self.origin
        axes = self.axes
        dims = self.dimensions

        if plane == "xy":
            x_min = origin[0]
            x_max = origin[0] + axes[0][0] * (dims[0] - 1)
            y_min = origin[1]
            y_max = origin[1] + axes[1][1] * (dims[1] - 1)
            return [x_min, x_max, y_min, y_max]
        elif plane == "xz":
            x_min = origin[0]
            x_max = origin[0] + axes[0][0] * (dims[0] - 1)
            z_min = origin[2]
            z_max = origin[2] + axes[2][2] * (dims[2] - 1)
            return [x_min, x_max, z_min, z_max]
        elif plane == "yz":
            y_min = origin[1]
            y_max = origin[1] + axes[1][1] * (dims[1] - 1)
            z_min = origin[2]
            z_max = origin[2] + axes[2][2] * (dims[2] - 1)
            return [y_min, y_max, z_min, z_max]
        return [0, 1, 0, 1]

    def get_atom_positions(self, plane: str = "xy"):
        positions = []
        for atom in self.atoms:
            if plane == "xy":
                positions.append((atom["x"], atom["y"], atom["element"]))
            elif plane == "xz":
                positions.append((atom["x"], atom["z_coord"], atom["element"]))
            elif plane == "yz":
                positions.append((atom["y"], atom["z_coord"], atom["element"]))
        return positions

    def get_dimensions(self):
        return self.dimensions
