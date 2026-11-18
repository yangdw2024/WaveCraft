#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WaveCraft Linux Server Bridge
Handles remote SSH / SFTP interactions with Linux clusters, HPC nodes, and remote Multiwfn binaries.
"""

import sys
import os
import json
import time
import fnmatch
from typing import Dict, Any, List

try:
    import paramiko
except ImportError:
    print(json.dumps({
        "ok": False,
        "error": "Python 环境未安装 paramiko 库，请先执行 pip install paramiko"
    }, ensure_ascii=False))
    sys.exit(1)


QUANTUM_EXTENSIONS = {
    ".fchk", ".chk", ".log", ".out", ".cub", ".cube", ".wfn", ".wfx",
    ".xyz", ".mol2", ".pdb", ".gjf", ".com", ".molden", ".dat", ".txt"
}


def create_ssh_client(config: Dict[str, Any]) -> paramiko.SSHClient:
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
    client = create_ssh_client(payload)
    try:
        stdin, stdout, stderr = client.exec_command("uname -a; echo '---'; which multiwfn 2>/dev/null || true; echo '---'; lscpu 2>/dev/null | grep 'Model name' | head -n 1 || true", timeout=10)
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
        }
    finally:
        client.close()


def handle_list_files(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = create_ssh_client(payload)
    remote_dir = payload.get("remote_dir", "").strip() or "."
    pattern = payload.get("pattern", "*").strip()

    try:
        sftp = client.open_sftp()
        try:
            # Resolve absolute path
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

                # Pattern matching
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

            # Sort: directories first, then quantum files, then alphabetical
            files.sort(key=lambda x: (not x["is_dir"], not x["is_quantum_file"], x["name"].lower()))

            return {
                "ok": True,
                "current_dir": resolved_dir,
                "count": len(files),
                "files": files,
            }
        finally:
            sftp.close()
    finally:
        client.close()


def handle_fetch_file(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = create_ssh_client(payload)
    remote_path = payload.get("remote_path", "").strip()
    local_dir = payload.get("local_dir", "").strip() or "./uploads"

    if not remote_path:
        raise ValueError("必须提供 remote_path")

    os.makedirs(local_dir, exist_ok=True)
    filename = os.path.basename(remote_path)
    local_path = os.path.abspath(os.path.join(local_dir, filename))

    try:
        sftp = client.open_sftp()
        try:
            start_t = time.time()
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
    client = create_ssh_client(payload)
    cmd = payload.get("command", "").strip()
    work_dir = payload.get("work_dir", "").strip()
    timeout = int(payload.get("exec_timeout", 60))

    if not cmd:
        raise ValueError("必须提供 command")

    full_cmd = f"cd {work_dir} && {cmd}" if work_dir else cmd

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
        }
    finally:
        client.close()


def handle_exec_multiwfn(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = create_ssh_client(payload)
    multiwfn_bin = payload.get("multiwfn_bin", "multiwfn").strip()
    remote_file = payload.get("remote_file", "").strip()
    commands = payload.get("commands", [])
    work_dir = payload.get("work_dir", "").strip() or os.path.dirname(remote_file) or "."
    timeout = int(payload.get("exec_timeout", 300))

    if not remote_file:
        raise ValueError("必须提供 remote_file")

    cmd_stream = "\n".join(commands) + "\n" if commands else ""

    try:
        # Check if remote multiwfn executable exists
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
