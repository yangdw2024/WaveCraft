import subprocess
import os
import sys
from ..utils.output_parser import OutputParser


class MultiwfnServiceError(RuntimeError):
    """Multiwfn 服务执行异常。"""
    pass


class MultiwfnService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.multiwfn_path = self._find_multiwfn()
        self.work_dir = None
        self._initialized = True

    def _find_multiwfn(self):
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            candidates = [
                os.path.join(exe_dir, "Multiwfn_3.8_bin_Win64", "Multiwfn.exe"),
                os.path.join(exe_dir, "Multiwfn.exe"),
            ]
        else:
            candidates = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "Multiwfn_3.8_bin_Win64", "Multiwfn.exe"),
                os.path.join("D:", "Multiwfn", "Multiwfn_3.8_bin_Win64", "Multiwfn.exe"),
            ]
        candidates.append(os.environ.get("Multiwfnpath", ""))
        for path in candidates:
            if path and os.path.exists(path):
                return os.path.abspath(path)
        return None

    def find_multiwfn(self):
        return self.multiwfn_path

    def set_work_dir(self, work_dir):
        self.work_dir = work_dir

    def get_supported_file_types(self):
        return [
            {"ext": ".fch", "name": "Gaussian FCHK"},
            {"ext": ".fchk", "name": "Gaussian FCHK"},
            {"ext": ".wfn", "name": "WFN format"},
            {"ext": ".wfx", "name": "WFX format"},
            {"ext": ".mwfn", "name": "Multiwfn MWFN"},
            {"ext": ".molden", "name": "Molden format"},
            {"ext": ".pdb", "name": "PDB format"},
            {"ext": ".xyz", "name": "XYZ format"},
            {"ext": ".mol2", "name": "Mol2 format"},
            {"ext": ".cub", "name": "Gaussian Cube"},
            {"ext": ".gjf", "name": "Gaussian Input"},
        ]

    def validate_input_file(self, file_path):
        if not os.path.exists(file_path):
            return {"valid": False, "message": f"文件不存在: {file_path}"}
        ext = os.path.splitext(file_path)[1].lower()
        supported = [t["ext"] for t in self.get_supported_file_types()]
        if ext not in supported:
            return {"valid": False, "message": f"不支持的文件格式: {ext}"}
        return {"valid": True, "message": "文件有效"}

    def _get_latest_cube_file(self, work_dir):
        """扫描工作目录，返回修改时间最新的 .cub/.cube 文件路径。"""
        cube_candidates = []
        for f in os.listdir(work_dir):
            lower_name = f.lower()
            if lower_name.endswith(".cub") or lower_name.endswith(".cube"):
                fpath = os.path.join(work_dir, f)
                try:
                    mtime = os.path.getmtime(fpath)
                    cube_candidates.append((mtime, fpath))
                except OSError:
                    continue
        if cube_candidates:
            cube_candidates.sort(key=lambda x: x[0], reverse=True)
            return cube_candidates[0][1]
        return None

    def _read_extra_files(self, work_dir, output):
        """读取常见附加输出文件并追加到 output。"""
        extra_files = [
            "lowdin_pop.txt", "dos_data.txt", "DOS.dat", "spectrum.txt",
            "output.txt", "dos_out.txt", "NCI.txt", "IGM.txt",
            "RDG.txt", "DORI.txt",
        ]
        extra_content = []
        for fname in extra_files:
            fpath = os.path.join(work_dir, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="gbk", errors="ignore") as f:
                        content = f.read()
                        if content.strip():
                            extra_content.append(f"--- {fname} ---\n{content}")
                except Exception:
                    continue
        if extra_content:
            return output + "\n" + "\n".join(extra_content)
        return output

    def run_command(self, fchk_path, commands, work_dir=None):
        if not self.multiwfn_path:
            raise MultiwfnServiceError("Multiwfn.exe 未找到，请确保已安装或设置 Multiwfnpath 环境变量")
        if not os.path.exists(fchk_path):
            raise MultiwfnServiceError(f"输入文件不存在: {fchk_path}")

        if work_dir is None:
            work_dir = self.work_dir or os.path.dirname(fchk_path)

        os.makedirs(work_dir, exist_ok=True)

        # 兼容字符串或列表形式的命令
        if isinstance(commands, str):
            command_lines = commands.strip().splitlines()
        else:
            command_lines = list(commands)
        full_commands = "\n" + "\n".join(command_lines) + "\n"

        try:
            result = subprocess.run(
                [self.multiwfn_path, fchk_path],
                input=full_commands.encode("gbk", errors="ignore"),
                capture_output=True,
                cwd=work_dir,
                timeout=1800,
            )
            output = result.stdout.decode("gbk", errors="ignore")
            error = result.stderr.decode("gbk", errors="ignore")

            # 非零退出码时抛出更有意义的错误，包含 stderr
            if result.returncode != 0:
                msg = f"Multiwfn 返回非零退出码 {result.returncode}"
                if error.strip():
                    msg += f"\nstderr: {error.strip()}"
                if output.strip():
                    tail = "\n".join(output.strip().splitlines()[-20:])
                    msg += f"\n输出末尾:\n{tail}"
                raise MultiwfnServiceError(msg)

            result_dict = {"success": True, "output": output, "error": error}

            if "chg" in command_lines:
                chg_file = os.path.join(work_dir, "output.chg")
                if os.path.exists(chg_file):
                    result_dict["chg_data"] = OutputParser.parse_chg_file(chg_file)

            # 增强 cube 文件检测：优先 output.cub/density.cub，否则取最新的 .cub/.cube
            cube_file = os.path.join(work_dir, "output.cub")
            if not os.path.exists(cube_file):
                cube_file = os.path.join(work_dir, "density.cub")
            if not os.path.exists(cube_file):
                cube_file = self._get_latest_cube_file(work_dir)
            if cube_file and os.path.exists(cube_file):
                result_dict["cube_file"] = cube_file

            # 增强额外文件读取
            result_dict["output"] = self._read_extra_files(work_dir, output)

            return result_dict

        except subprocess.TimeoutExpired as e:
            raise MultiwfnServiceError(f"计算超时（超过 {e.timeout} 秒）") from e
        except MultiwfnServiceError:
            raise
        except Exception as e:
            raise MultiwfnServiceError(f"执行失败: {str(e)}") from e
