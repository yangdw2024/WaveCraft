#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WaveCraft Linux Server Bridge
Handles remote SSH / SFTP interactions with Linux clusters, HPC nodes,
and native local WSL2 environments running Multiwfn.
"""

import sys
import os
import json
import time
import shutil
import fnmatch
import subprocess
from typing import Dict, Any, List

QUANTUM_EXTENSIONS = {
    ".fchk", ".chk", ".log", ".out", ".cub", ".cube", ".wfn", ".wfx",
    ".xyz", ".mol2", ".pdb", ".gjf", ".com", ".molden", ".dat", ".txt"
}


def is_wsl_mode(config: Dict[str, Any]) -> bool:
    host = str(config.get("host", "")).strip().lower()
    return bool(config.get("is_wsl")) or host in ("wsl", "localhost-wsl", "wsl-ubuntu", "wsl2")


def get_wsl_distro(config: Dict[str, Any]) -> str:
    return config.get("distro", "").strip() or config.get("wsl_distro", "").strip() or "Ubuntu"


def to_wsl_unc_path(linux_path: str, distro: str = "Ubuntu") -> str:
    clean = linux_path.replace("\\", "/").strip()
    if clean.startswith("/"):
        clean = clean[1:]
    unc1 = os.path.join(f"\\\\wsl$\\{distro}", clean.replace("/", "\\"))
    if os.path.exists(unc1):
        return unc1
    unc2 = os.path.join(f"\\\\wsl.localhost\\{distro}", clean.replace("/", "\\"))
    if os.path.exists(unc2):
        return unc2
    return unc1


def run_wsl_command(cmd: str, distro: str = "Ubuntu", timeout: int = 60, input_data: str = None):
    args = ["wsl", "-d", distro, "bash", "-c", cmd]
    p = subprocess.Popen(
        args,
        stdin=subprocess.PIPE if input_data is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    out, err = p.communicate(input=input_data, timeout=timeout)
    return p.returncode, out, err


def create_ssh_client(config: Dict[str, Any]):
    try:
        import paramiko
    except ImportError:
        raise RuntimeError("Python 环境未安装 paramiko 库，请先执行 pip install paramiko 以启用远程 SSH")

    host = config.get("host", "").strip()
    port = int(config.get("port", 22))
    username = config.get("username", "").strip()
    password = config.get("password")
    key_path = config.get("key_path")
    key_data = config.get("key_data")
    timeout = float(config.get("timeout", 10.0))

    if not host or not username:
        raise ValueError("必须提供 host 与 username")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = {
        "hostname": host,
        "port": port,
        "username": username,
        "timeout": timeout,
        "banner_timeout": timeout,
    }

    if password:
        connect_kwargs["password"] = password
    elif key_path and os.path.exists(key_path):
        connect_kwargs["key_filename"] = key_path
    elif key_data:
        import io
        try:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_data))
        except Exception:
            pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(key_data))
        connect_kwargs["pkey"] = pkey

    client.connect(**connect_kwargs)
    return client


def handle_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    if is_wsl_mode(payload):
        distro = get_wsl_distro(payload)
        test_cmd = (
            "uname -a; echo '---'; "
            "which Multiwfn 2>/dev/null || which multiwfn 2>/dev/null || "
            "(test -x /home/administrator/opt/Multiwfn/bin/Multiwfn && echo '/home/administrator/opt/Multiwfn/bin/Multiwfn') || true; "
            "echo '---'; "
            "lscpu 2>/dev/null | grep 'Model name' | head -n 1 || true"
        )
        code, out, err = run_wsl_command(test_cmd, distro=distro, timeout=12)
        if code != 0 and not out:
            raise RuntimeError(f"WSL2 ({distro}) 测试连接失败: {err.strip()}")

        parts = out.split('---')
        uname = parts[0].strip() if len(parts) > 0 else ""
        multiwfn_path = parts[1].strip() if len(parts) > 1 else ""
        cpu_model = parts[2].strip() if len(parts) > 2 else ""

        return {
            "ok": True,
            "message": f"本地 WSL2 ({distro}) 原生连接成功",
            "uname": uname,
            "cpu_model": cpu_model,
            "remote_multiwfn_path": multiwfn_path if multiwfn_path else "/home/administrator/opt/Multiwfn/bin/Multiwfn",
            "is_wsl": True,
            "distro": distro,
        }

    client = create_ssh_client(payload)
    try:
        stdin, stdout, stderr = client.exec_command(
            "uname -a; echo '---'; which multiwfn 2>/dev/null || true; echo '---'; lscpu 2>/dev/null | grep 'Model name' | head -n 1 || true",
            timeout=10
        )
        out = stdout.read().decode('utf-8', errors='replace').strip()
        parts = out.split('---')
        uname = parts[0].strip() if len(parts) > 0 else ""
        multiwfn_path = parts[1].strip() if len(parts) > 1 else ""
        cpu_model = parts[2].strip() if len(parts) > 2 else ""

        return {
            "ok": True,
            "message": "SSH 连接成功",
            "uname": uname,
            "cpu_model": cpu_model,
            "remote_multiwfn_path": multiwfn_path if multiwfn_path else None,
            "is_wsl": False,
        }
    finally:
        client.close()


def handle_list_files(payload: Dict[str, Any]) -> Dict[str, Any]:
    remote_dir = payload.get("remote_dir", "").strip() or "."
    pattern = payload.get("pattern", "*").strip()

    if is_wsl_mode(payload):
        distro = get_wsl_distro(payload)
        unc_dir = to_wsl_unc_path(remote_dir, distro=distro)

        if os.path.exists(unc_dir) and os.path.isdir(unc_dir):
            files: List[Dict[str, Any]] = []
            with os.scandir(unc_dir) as entries:
                for entry in entries:
                    name = entry.name
                    if name.startswith("."):
                        continue
                    try:
                        stat = entry.stat()
                        is_dir = entry.is_dir()
                        ext = os.path.splitext(name)[1].lower()
                        is_quantum = ext in QUANTUM_EXTENSIONS

                        if not is_dir and pattern and pattern != "*":
                            if not fnmatch.fnmatch(name.lower(), pattern.lower()):
                                continue

                        linux_path = (remote_dir.rstrip("/") + "/" + name).replace("//", "/")
                        files.append({
                            "name": name,
                            "path": linux_path,
                            "size": stat.st_size if not is_dir else 0,
                            "is_dir": is_dir,
                            "mtime": stat.st_mtime,
                            "is_quantum_file": is_quantum,
                            "ext": ext,
                        })
                    except Exception:
                        continue

            files.sort(key=lambda x: (not x["is_dir"], not x["is_quantum_file"], x["name"].lower()))
            return {
                "ok": True,
                "current_dir": remote_dir,
                "count": len(files),
                "files": files,
                "is_wsl": True,
            }

        # Fallback via wsl ls command
        code, out, err = run_wsl_command(f"ls -la '{remote_dir}'", distro=distro)
        return {
            "ok": code == 0,
            "current_dir": remote_dir,
            "count": 0,
            "files": [],
            "raw_output": out,
            "is_wsl": True,
        }

    client = create_ssh_client(payload)
    try:
        sftp = client.open_sftp()
        try:
            try:
                resolved_dir = sftp.normalize(remote_dir)
            except Exception:
                resolved_dir = remote_dir

            entries = sftp.listdir_attr(resolved_dir)
            files: List[Dict[str, Any]] = []

            for attr in entries:
                name = attr.filename
                if name.startswith("."):
                    continue
                is_dir = bool(attr.st_mode and (attr.st_mode & 0o040000))
                full_path = os.path.join(resolved_dir, name).replace("\\", "/")
                ext = os.path.splitext(name)[1].lower()
                is_quantum = ext in QUANTUM_EXTENSIONS

                if not is_dir and pattern and pattern != "*":
                    if not fnmatch.fnmatch(name.lower(), pattern.lower()):
                        continue

                files.append({
                    "name": name,
                    "path": full_path,
                    "size": attr.st_size if not is_dir else 0,
                    "is_dir": is_dir,
                    "mtime": attr.st_mtime,
                    "is_quantum_file": is_quantum,
                    "ext": ext,
                })

            files.sort(key=lambda x: (not x["is_dir"], not x["is_quantum_file"], x["name"].lower()))

            return {
                "ok": True,
                "current_dir": resolved_dir,
                "count": len(files),
                "files": files,
                "is_wsl": False,
            }
        finally:
            sftp.close()
    finally:
        client.close()


def handle_fetch_file(payload: Dict[str, Any]) -> Dict[str, Any]:
    remote_path = payload.get("remote_path", "").strip()
    local_dir = payload.get("local_dir", "").strip() or "./uploads"

    if not remote_path:
        raise ValueError("必须提供 remote_path")

    os.makedirs(local_dir, exist_ok=True)
    filename = os.path.basename(remote_path)
    local_path = os.path.abspath(os.path.join(local_dir, filename))

    start_t = time.time()

    if is_wsl_mode(payload):
        distro = get_wsl_distro(payload)
        unc_path = to_wsl_unc_path(remote_path, distro=distro)
        if os.path.exists(unc_path):
            shutil.copyfile(unc_path, local_path)
            duration = time.time() - start_t
            file_size = os.path.getsize(local_path)
            return {
                "ok": True,
                "remote_path": remote_path,
                "local_path": local_path,
                "filename": filename,
                "size_bytes": file_size,
                "duration_seconds": round(duration, 3),
                "message": f"成功从 WSL2 读取文件 {filename} ({round(file_size / 1024 / 1024, 2)} MB)",
            }
        # Fallback to wsl cat or cp
        code, out, err = run_wsl_command(f"cat '{remote_path}'", distro=distro)
        if code == 0:
            with open(local_path, "wb") as f:
                f.write(out.encode("utf-8", errors="replace"))
            duration = time.time() - start_t
            file_size = os.path.getsize(local_path)
            return {
                "ok": True,
                "remote_path": remote_path,
                "local_path": local_path,
                "filename": filename,
                "size_bytes": file_size,
                "duration_seconds": round(duration, 3),
                "message": f"成功从 WSL2 流式传输文件 {filename}",
            }
        raise FileNotFoundError(f"WSL2 文件不存在: {remote_path} (UNC: {unc_path})")

    client = create_ssh_client(payload)
    try:
        sftp = client.open_sftp()
        try:
            sftp.get(remote_path, local_path)
            duration = time.time() - start_t
            file_size = os.path.getsize(local_path)

            return {
                "ok": True,
                "remote_path": remote_path,
                "local_path": local_path,
                "filename": filename,
                "size_bytes": file_size,
                "duration_seconds": round(duration, 3),
                "message": f"成功拉取文件 {filename} ({round(file_size / 1024 / 1024, 2)} MB)",
            }
        finally:
            sftp.close()
    finally:
        client.close()


def handle_exec_cmd(payload: Dict[str, Any]) -> Dict[str, Any]:
    cmd = payload.get("command", "").strip()
    work_dir = payload.get("work_dir", "").strip()
    timeout = int(payload.get("exec_timeout", 60))

    if not cmd:
        raise ValueError("必须提供 command")

    full_cmd = f"cd '{work_dir}' && {cmd}" if work_dir else cmd

    if is_wsl_mode(payload):
        distro = get_wsl_distro(payload)
        code, out_text, err_text = run_wsl_command(full_cmd, distro=distro, timeout=timeout)
        return {
            "ok": code == 0,
            "exit_code": code,
            "stdout": out_text,
            "stderr": err_text,
            "is_wsl": True,
        }

    client = create_ssh_client(payload)
    try:
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
        out_text = stdout.read().decode('utf-8', errors='replace')
        err_text = stderr.read().decode('utf-8', errors='replace')
        exit_code = stdout.channel.recv_exit_status()

        return {
            "ok": exit_code == 0,
            "exit_code": exit_code,
            "stdout": out_text,
            "stderr": err_text,
            "is_wsl": False,
        }
    finally:
        client.close()


def handle_exec_multiwfn(payload: Dict[str, Any]) -> Dict[str, Any]:
    multiwfn_bin = payload.get("multiwfn_bin", "multiwfn").strip()
    remote_file = payload.get("remote_file", "").strip()
    commands = payload.get("commands", [])
    work_dir = payload.get("work_dir", "").strip() or os.path.dirname(remote_file) or "."
    timeout = int(payload.get("exec_timeout", 300))

    if not remote_file:
        raise ValueError("必须提供 remote_file")

    cmd_stream = "\n".join(commands) + "\n" if commands else ""

    if is_wsl_mode(payload):
        distro = get_wsl_distro(payload)
        remote_cmd = (
            f"cd '{work_dir}' && "
            f"export OMP_NUM_THREADS=$(nproc 2>/dev/null || echo 4); "
            f"'{multiwfn_bin}' '{remote_file}'"
        )
        code, out_text, err_text = run_wsl_command(
            remote_cmd, distro=distro, timeout=timeout, input_data=cmd_stream
        )
        return {
            "ok": code == 0,
            "exit_code": code,
            "stdout": out_text,
            "stderr": err_text,
            "work_dir": work_dir,
            "is_wsl": True,
        }

    client = create_ssh_client(payload)
    try:
        remote_cmd = f"cd {work_dir} && export OMP_NUM_THREADS=$(nproc 2>/dev/null || echo 4); {multiwfn_bin} {remote_file}"
        stdin, stdout, stderr = client.exec_command(remote_cmd, timeout=timeout)

        if cmd_stream:
            stdin.write(cmd_stream)
            stdin.flush()
            stdin.channel.shutdown_write()

        out_text = stdout.read().decode('utf-8', errors='replace')
        err_text = stderr.read().decode('utf-8', errors='replace')
        exit_code = stdout.channel.recv_exit_status()

        return {
            "ok": exit_code == 0,
            "exit_code": exit_code,
            "stdout": out_text,
            "stderr": err_text,
            "work_dir": work_dir,
            "is_wsl": False,
        }
    finally:
        client.close()


def main():
    data = {}
    if len(sys.argv) >= 3 and sys.argv[1] == "--json":
        data = json.loads(sys.argv[2])
    elif not sys.stdin.isatty():
        raw_input = sys.stdin.read()
        if raw_input.strip():
            data = json.loads(raw_input)
    elif len(sys.argv) >= 2:
        data = {"action": sys.argv[1]}

    action = data.get("action", "")

    try:
        if action == "test":
            res = handle_test(data)
        elif action == "list_files":
            res = handle_list_files(data)
        elif action == "fetch_file":
            res = handle_fetch_file(data)
        elif action == "exec_cmd":
            res = handle_exec_cmd(data)
        elif action == "exec_multiwfn":
            res = handle_exec_multiwfn(data)
        else:
            res = {"ok": False, "error": f"未知 action: {action}"}
        print(json.dumps(res, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
