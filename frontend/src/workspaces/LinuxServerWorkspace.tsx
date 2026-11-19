import React, { useEffect, useState, useRef } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Cpu,
  Download,
  Folder,
  FolderOpen,
  GripHorizontal,
  HardDrive,
  Key,
  Layers,
  Loader2,
  Maximize2,
  Minimize2,
  Play,
  RefreshCw,
  Save,
  Search,
  Server,
  Settings2,
  Terminal,
  Trash2,
  UploadCloud,
  Zap,
} from 'lucide-react';
import { api } from '../api/client';
import { ExpandableConsole } from '../components/ExpandableConsole';
import { Tooltip } from '../components/Tooltip';
import { ResizableSplitPane } from '../components/ResizableSplitPane';
import type { MoleculeInspection, RemoteFileInfo, RemoteServerProfile } from '../types/quantum';

interface LinuxServerWorkspaceProps {
  inspection: MoleculeInspection | null;
  onSelectFile?: (path: string) => void;
}

const WSL_DEFAULT_SERVER: RemoteServerProfile = {
  id: 'wsl-ubuntu',
  name: '本地 WSL2 Ubuntu (原生极速)',
  host: 'wsl',
  port: 0,
  username: 'administrator',
  password: '',
  key_path: '',
  remote_work_dir: '/home/administrator/work/mwfn_cm5_test',
  remote_multiwfn_path: '/home/administrator/opt/Multiwfn/bin/Multiwfn',
  is_wsl: true,
  distro: 'Ubuntu',
};

const CLUSTER_SERVER: RemoteServerProfile = {
  id: 'cluster-default',
  name: '超算 / 课题组 Linux 计算节点',
  host: '192.168.1.100',
  port: 22,
  username: 'calc',
  password: '',
  key_path: '',
  remote_work_dir: '/home/calc/jobs',
  remote_multiwfn_path: 'multiwfn',
  is_wsl: false,
};

const INITIAL_SERVERS = [WSL_DEFAULT_SERVER, CLUSTER_SERVER];

export const LinuxServerWorkspace: React.FC<LinuxServerWorkspaceProps> = ({
  inspection,
  onSelectFile,
}) => {
  // Server Profiles
  const [servers, setServers] = useState<RemoteServerProfile[]>(INITIAL_SERVERS);
  const [selectedServerId, setSelectedServerId] = useState<string>(WSL_DEFAULT_SERVER.id);
  const [showConfig, setShowConfig] = useState(false);

  // Active Server Config
  const activeServer =
    servers.find((s) => s.id === selectedServerId) || servers[0] || WSL_DEFAULT_SERVER;

  // Connection & System Status
  const [testing, setTesting] = useState(false);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [statusMsg, setStatusMsg] = useState<string>('');
  const [remoteUname, setRemoteUname] = useState<string>('');
  const [remoteCpu, setRemoteCpu] = useState<string>('');
  const [remoteMultiwfnFound, setRemoteMultiwfnFound] = useState<string | null>(null);

  // Remote File Browser
  const [currentRemoteDir, setCurrentRemoteDir] = useState<string>(activeServer.remote_work_dir || '/home');
  const [filterPattern, setFilterPattern] = useState<string>('*.fchk');
  const [remoteFiles, setRemoteFiles] = useState<RemoteFileInfo[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [fetchingFile, setFetchingFile] = useState<string | null>(null);
  const [fetchNotice, setFetchNotice] = useState<string | null>(null);

  // Remote Terminal & Shell Execution
  const [shellCmd, setShellCmd] = useState<string>('squeue -u $USER');
  const [runningCmd, setRunningCmd] = useState(false);
  const [cmdStdout, setCmdStdout] = useState<string>('');
  const [cmdExitCode, setCmdExitCode] = useState<number | null>(null);

  // Remote Multiwfn Execution
  const [remoteTargetFile, setRemoteTargetFile] = useState<string>('');
  const [remoteCommands, setRemoteCommands] = useState<string>('0\n1\nq');
  const [runningMultiwfn, setRunningMultiwfn] = useState(false);
  const [multiwfnStdout, setMultiwfnStdout] = useState<string>('');

  // Layout Flexibility & Fullscreen state
  const [sftpFileListHeight, setSftpFileListHeight] = useState<number>(420);
  const [sftpMaximized, setSftpMaximized] = useState<boolean>(false);
  const [layoutProportion, setLayoutProportion] = useState<'equal' | 'file-first' | 'term-first'>('equal');
  const [isDraggingSftp, setIsDraggingSftp] = useState<boolean>(false);
  const sftpStartYRef = useRef(0);
  const sftpStartHRef = useRef(0);

  const startDragSftp = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingSftp(true);
    sftpStartYRef.current = e.clientY;
    sftpStartHRef.current = sftpFileListHeight;

    const onMouseMove = (ev: MouseEvent) => {
      const delta = ev.clientY - sftpStartYRef.current;
      const nextH = Math.max(220, Math.min(1000, sftpStartHRef.current + delta));
      setSftpFileListHeight(nextH);
    };

    const onMouseUp = () => {
      setIsDraggingSftp(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  // Load Saved Configurations on Mount
  useEffect(() => {
    api
      .getRemoteConfig()
      .then((res) => {
        if (res?.servers && res.servers.length > 0) {
          setServers(res.servers);
          setSelectedServerId(res.servers[0].id);
          if (res.servers[0].remote_work_dir) {
            setCurrentRemoteDir(res.servers[0].remote_work_dir);
          }
        }
      })
      .catch(() => {});
  }, []);

  const updateActiveServer = (partial: Partial<RemoteServerProfile>) => {
    setServers((prev) =>
      prev.map((s) => (s.id === selectedServerId ? { ...s, ...partial } : s))
    );
  };

  const saveConfiguration = async () => {
    try {
      await api.saveRemoteConfig({ servers });
      setStatusMsg('远程配置保存成功！');
      setTimeout(() => setStatusMsg(''), 3000);
    } catch (e: any) {
      alert(`保存失败: ${e.message}`);
    }
  };

  // Test Connection
  const testConnection = async () => {
    setTesting(true);
    setConnected(null);
    setStatusMsg(activeServer.is_wsl ? '正在连接本地 WSL2 实例...' : '正在通过 SSH 探测远程 Linux 节点...');
    try {
      const res = await api.testRemoteServer({
        host: activeServer.host,
        port: activeServer.port,
        username: activeServer.username,
        password: activeServer.password || undefined,
        key_path: activeServer.key_path || undefined,
        is_wsl: activeServer.is_wsl,
        distro: activeServer.distro,
      });

      if (res.ok) {
        setConnected(true);
        setStatusMsg(res.message);
        setRemoteUname(res.uname || 'Linux');
        setRemoteCpu(res.cpu_model || '标准 HPC 节点');
        setRemoteMultiwfnFound(res.remote_multiwfn_path || null);
        // Auto refresh files
        refreshRemoteFiles(currentRemoteDir);
      } else {
        setConnected(false);
        setStatusMsg(res.error || '连接被拒绝');
      }
    } catch (e: any) {
      setConnected(false);
      setStatusMsg(`连接异常: ${e.message}`);
    } finally {
      setTesting(false);
    }
  };

  // List Files
  const refreshRemoteFiles = async (dirToRead = currentRemoteDir) => {
    setLoadingFiles(true);
    try {
      const res = await api.listRemoteFiles({
        host: activeServer.host,
        port: activeServer.port,
        username: activeServer.username,
        password: activeServer.password || undefined,
        key_path: activeServer.key_path || undefined,
        remote_dir: dirToRead,
        pattern: filterPattern,
        is_wsl: activeServer.is_wsl,
        distro: activeServer.distro,
      });

      if (res.ok) {
        setRemoteFiles(res.files || []);
        setCurrentRemoteDir(res.current_dir);
        if (connected === null) setConnected(true);
      }
    } catch (e: any) {
      console.warn('获取远程文件列表失败:', e);
    } finally {
      setLoadingFiles(false);
    }
  };

  // Fetch Remote File to Local & Open
  const handleFetchAndLoad = async (remotePath: string) => {
    setFetchingFile(remotePath);
    setFetchNotice(`正在从服务器拉取 ${remotePath}...`);
    try {
      const res = await api.fetchRemoteFile({
        host: activeServer.host,
        port: activeServer.port,
        username: activeServer.username,
        password: activeServer.password || undefined,
        key_path: activeServer.key_path || undefined,
        remote_path: remotePath,
        is_wsl: activeServer.is_wsl,
        distro: activeServer.distro,
      });

      if (res.ok) {
        setFetchNotice(res.message);
        if (onSelectFile && res.local_path) {
          onSelectFile(res.local_path);
        }
      } else {
        setFetchNotice(`拉取失败: ${res.error}`);
      }
    } catch (e: any) {
      setFetchNotice(`拉取失败: ${e.message}`);
    } finally {
      setFetchingFile(null);
    }
  };

  // Run Remote Shell Command
  const runShellCommand = async (cmdToRun = shellCmd) => {
    if (!cmdToRun.trim()) return;
    setRunningCmd(true);
    try {
      const res = await api.execRemoteCmd({
        host: activeServer.host,
        port: activeServer.port,
        username: activeServer.username,
        password: activeServer.password || undefined,
        key_path: activeServer.key_path || undefined,
        command: cmdToRun,
        work_dir: currentRemoteDir,
        is_wsl: activeServer.is_wsl,
        distro: activeServer.distro,
      });
      setCmdStdout(res.stdout || res.stderr || '命令执行完成（无输出）');
      setCmdExitCode(res.exit_code);
    } catch (e: any) {
      setCmdStdout(`执行错误: ${e.message}`);
      setCmdExitCode(-1);
    } finally {
      setRunningCmd(false);
    }
  };

  // Run Remote Multiwfn
  const runRemoteMultiwfn = async () => {
    if (!remoteTargetFile) {
      alert('请先在左侧选择或输入远程波函数文件路径');
      return;
    }
    setRunningMultiwfn(true);
    try {
      const cmds = remoteCommands.split(/\r?\n/).map((s) => s.trimEnd());
      const res = await api.execRemoteMultiwfn({
        host: activeServer.host,
        port: activeServer.port,
        username: activeServer.username,
        password: activeServer.password || undefined,
        key_path: activeServer.key_path || undefined,
        remote_file: remoteTargetFile,
        commands: cmds,
        multiwfn_bin: activeServer.remote_multiwfn_path || 'multiwfn',
        work_dir: currentRemoteDir,
        is_wsl: activeServer.is_wsl,
        distro: activeServer.distro,
      });
      setMultiwfnStdout(res.stdout || res.stderr || 'Multiwfn 执行完成');
    } catch (e: any) {
      setMultiwfnStdout(`远程 Multiwfn 执行异常: ${e.message}`);
    } finally {
      setRunningMultiwfn(false);
    }
  };

  const navUpDir = () => {
    const parts = currentRemoteDir.replace(/\\/g, '/').split('/').filter(Boolean);
    if (parts.length <= 1) {
      refreshRemoteFiles('/');
    } else {
      parts.pop();
      refreshRemoteFiles('/' + parts.join('/'));
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Banner: Connection Status & Server Profile Picker */}
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-slate-950 via-cyan-950/20 to-slate-950 border-cyan-500/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-slate-950 font-bold shadow-lg shadow-cyan-500/25">
            <Server className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-100">
                Linux 智算中心 · 远程集群与超算交互通道
              </h2>
              {connected === true && (
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-[10px] font-mono text-emerald-300 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  已连接至 {activeServer.host}
                </span>
              )}
              {connected === false && (
                <span className="px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/30 text-[10px] font-mono text-rose-300 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                  未连接 / 连接失败
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-2 flex-wrap">
              <span>打通本地 WaveCraft 与 Linux 超算集群</span>
              <span className="text-slate-600">|</span>
              <span className="font-mono text-cyan-300 font-semibold">{activeServer.username}@{activeServer.host}:{activeServer.port}</span>
              {remoteUname && (
                <>
                  <span className="text-slate-600">|</span>
                  <span className="text-slate-400 font-mono">{remoteUname.split(' ')[0]} {remoteUname.split(' ')[2] || ''}</span>
                </>
              )}
              {remoteMultiwfnFound && (
                <>
                  <span className="text-slate-600">|</span>
                  <span className="text-emerald-400 font-mono">Multiwfn: {remoteMultiwfnFound}</span>
                </>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            disabled={testing}
            onClick={testConnection}
            className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:brightness-110 text-slate-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50 transition shadow-lg shadow-cyan-500/20"
          >
            {testing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
            <span>{testing ? '探测中...' : '测试并连接服务器'}</span>
          </button>

          <button
            onClick={() => setShowConfig((v) => !v)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition cursor-pointer flex items-center gap-1.5 ${
              showConfig
                ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:text-white'
            }`}
          >
            <Settings2 className="w-3.5 h-3.5" />
            <span>配置与凭证</span>
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className={`p-2.5 rounded-xl text-xs flex items-center gap-2 ${connected ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-200' : 'bg-slate-900 border border-slate-800 text-slate-300'}`}>
          <AlertCircle className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* Expandable Configuration Drawer */}
      {showConfig && (
        <div className="glass-panel rounded-2xl p-4 space-y-4 border border-cyan-500/30 bg-slate-950/90 animate-in fade-in duration-200">
          {/* Mode Switcher */}
          <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
            <span className="text-xs font-medium text-slate-400">连接模式:</span>
            <button
              onClick={() => updateActiveServer({ is_wsl: true, host: 'wsl' })}
              className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition ${
                activeServer.is_wsl
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 shadow-sm'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              本地 WSL2 原生极速 (免 SSH 服务)
            </button>
            <button
              onClick={() => updateActiveServer({ is_wsl: false, host: activeServer.host === 'wsl' ? '192.168.1.100' : activeServer.host })}
              className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition ${
                !activeServer.is_wsl
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-400/40 shadow-sm'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              远程 SSH / 超算集群
            </button>
            {activeServer.is_wsl && (
              <span className="text-[11px] text-emerald-400 ml-auto font-mono bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                ✓ 原生支持 \\wsl$\Ubuntu 极速文件流
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                服务器名称 (备注)
              </label>
              <input
                value={activeServer.name}
                onChange={(e) => updateActiveServer({ name: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200"
                placeholder="校级超算节点 / 本地 WSL2"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                {activeServer.is_wsl ? 'WSL 分发版名称 (Distro)' : '主机 IP / 域名 (Host)'}
              </label>
              <input
                value={activeServer.is_wsl ? (activeServer.distro || 'Ubuntu') : activeServer.host}
                onChange={(e) =>
                  activeServer.is_wsl
                    ? updateActiveServer({ distro: e.target.value, host: 'wsl' })
                    : updateActiveServer({ host: e.target.value })
                }
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200"
                placeholder={activeServer.is_wsl ? 'Ubuntu' : '192.168.1.100 或 cluster.edu.cn'}
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                {activeServer.is_wsl ? '端口 (WSL 内部免配)' : '端口 (Port)'}
              </label>
              <input
                type="number"
                disabled={activeServer.is_wsl}
                value={activeServer.port}
                onChange={(e) => updateActiveServer({ port: Number(e.target.value) || 22 })}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 disabled:opacity-40"
                placeholder="22"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                用户名 (Username)
              </label>
              <input
                value={activeServer.username}
                onChange={(e) => updateActiveServer({ username: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200"
                placeholder="administrator 或 calc"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                SSH 密码 (留空则使用密钥)
              </label>
              <input
                type="password"
                value={activeServer.password || ''}
                onChange={(e) => updateActiveServer({ password: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                私钥文件路径 (SSH Key Path)
              </label>
              <input
                value={activeServer.key_path || ''}
                onChange={(e) => updateActiveServer({ key_path: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200"
                placeholder="C:\Users\...\.ssh\id_rsa"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                远程 Multiwfn 路径
              </label>
              <input
                value={activeServer.remote_multiwfn_path || ''}
                onChange={(e) => updateActiveServer({ remote_multiwfn_path: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200"
                placeholder="multiwfn 或 /home/calc/bin/Multiwfn"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-1">
            <button
              onClick={saveConfiguration}
              className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
            >
              <Save className="w-3.5 h-3.5 text-cyan-400" />
              <span>保存配置到本地</span>
            </button>
          </div>
        </div>
      )}

      {/* Proportions & Layout Controls */}
      <div className="flex items-center justify-between flex-wrap gap-2 px-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span>支持多面板拖拽调节高度与全屏拉伸</span>
        </div>
      </div>

      {/* Main Responsive Two-Column Layout with ResizableSplitPane */}
      <ResizableSplitPane
        storageKey="linux_bridge"
        defaultSplit={42}
        left={
          <div
            className={`${
              sftpMaximized
                ? 'fixed inset-4 z-[9999] rounded-2xl bg-slate-950/95 border border-cyan-500/50 shadow-2xl p-6 flex flex-col backdrop-blur-2xl'
                : 'glass-panel rounded-2xl p-4 space-y-3 flex flex-col'
            }`}
          >
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <FolderOpen className="w-3.5 h-3.5 text-cyan-400" />
              <span>远程文件系统浏览器 (SFTP)</span>
            </h3>

            <div className="flex items-center gap-1">
              {/* SFTP Height Presets */}
              {!sftpMaximized && (
                <div className="hidden sm:flex items-center gap-1 mr-1">
                  {[
                    { label: '标准', h: 360 },
                    { label: '高纵深', h: 540 },
                    { label: '巨幕', h: 780 },
                  ].map((p) => (
                    <button
                      key={p.label}
                      onClick={() => setSftpFileListHeight(p.h)}
                      className={`px-1.5 py-0.5 rounded text-[10px] font-mono cursor-pointer transition ${
                        sftpFileListHeight === p.h
                          ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-400/50'
                          : 'bg-slate-900 text-slate-500 border border-slate-800 hover:text-slate-300'
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              )}

              <button
                disabled={loadingFiles}
                onClick={() => refreshRemoteFiles(currentRemoteDir)}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer mr-1"
              >
                <RefreshCw className={`w-3 h-3 ${loadingFiles ? 'animate-spin' : ''}`} />
                <span>刷新</span>
              </button>

              <Tooltip content={sftpMaximized ? '还原窗口' : '全屏最大化文件浏览器'}>
                <button
                  onClick={() => setSftpMaximized(!sftpMaximized)}
                  className="p-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500/40 text-slate-400 hover:text-cyan-300 cursor-pointer transition"
                >
                  {sftpMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                </button>
              </Tooltip>
            </div>
          </div>

          {/* Directory Navigation & Filter */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <button
                onClick={navUpDir}
                className="px-2 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 cursor-pointer"
                title="返回上一级目录"
              >
                &larr; 上级
              </button>
              <input
                value={currentRemoteDir}
                onChange={(e) => setCurrentRemoteDir(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && refreshRemoteFiles(currentRemoteDir)}
                className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs font-mono text-slate-200"
                placeholder="/home/calc/jobs"
              />
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-[11px] text-slate-400">过滤格式:</span>
              {(['*.fchk', '*.log', '*.cub', '*'] as const).map((pat) => (
                <button
                  key={pat}
                  onClick={() => {
                    setFilterPattern(pat);
                    setTimeout(() => refreshRemoteFiles(currentRemoteDir), 10);
                  }}
                  className={`px-2 py-0.5 rounded text-[10px] font-mono cursor-pointer transition ${
                    filterPattern === pat
                      ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-400/50'
                      : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
                  }`}
                >
                  {pat}
                </button>
              ))}
            </div>
          </div>

          {fetchNotice && (
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-[11px] text-cyan-200">
              {fetchNotice}
            </div>
          )}

          {/* File Entries List with Dynamic Height */}
          <div
            style={sftpMaximized ? undefined : { height: `${sftpFileListHeight}px` }}
            className={`w-full overflow-y-auto rounded-xl border border-slate-800 bg-slate-950/60 divide-y divide-slate-800/60 ${
              sftpMaximized ? 'flex-1 min-h-0' : ''
            }`}
          >
            {remoteFiles.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center p-8 text-center text-xs text-slate-500">
                <HardDrive className="w-8 h-8 text-slate-700 mb-2" />
                <p>该目录下暂无匹配文件，或尚未连接到服务器</p>
                <p className="text-[10px] text-slate-600 mt-1">
                  点击上方「测试并连接服务器」以加载文件树
                </p>
              </div>
            ) : (
              remoteFiles.map((file) => (
                <div
                  key={file.path}
                  className="p-2.5 flex items-center justify-between gap-2 hover:bg-slate-900/60 transition group text-xs"
                >
                  <div
                    className="flex items-center gap-2 min-w-0 cursor-pointer flex-1"
                    onClick={() => {
                      if (file.is_dir) {
                        refreshRemoteFiles(file.path);
                      } else {
                        setRemoteTargetFile(file.path);
                      }
                    }}
                  >
                    {file.is_dir ? (
                      <Folder className="w-4 h-4 text-amber-400 shrink-0" />
                    ) : file.is_quantum_file ? (
                      <HardDrive className="w-4 h-4 text-cyan-400 shrink-0" />
                    ) : (
                      <Folder className="w-4 h-4 text-slate-500 shrink-0" />
                    )}
                    <div className="min-w-0">
                      <p className="font-mono text-slate-200 truncate group-hover:text-cyan-300 transition-colors">
                        {file.name}
                      </p>
                      <p className="text-[10px] text-slate-500 font-mono">
                        {file.is_dir
                          ? '目录'
                          : `${(file.size / 1024 / 1024).toFixed(2)} MB · ${file.ext.toUpperCase()}`}
                      </p>
                    </div>
                  </div>

                  {!file.is_dir && (
                    <div className="flex items-center gap-1.5 shrink-0">
                      <button
                        disabled={fetchingFile === file.path}
                        onClick={() => handleFetchAndLoad(file.path)}
                        className="px-2.5 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/40 text-[11px] font-semibold text-cyan-200 flex items-center gap-1 transition cursor-pointer"
                        title="下载到本地并立即在 WaveCraft 中载入 3D 分子视口"
                      >
                        {fetchingFile === file.path ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Download className="w-3 h-3 text-cyan-300" />
                        )}
                        <span>拉取并载入</span>
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Draggable Height Resizer for SFTP */}
          {!sftpMaximized && (
            <div
              onMouseDown={startDragSftp}
              className={`w-full h-2.5 flex items-center justify-center cursor-row-resize rounded-md transition select-none group ${
                isDraggingSftp ? 'bg-cyan-500/40' : 'hover:bg-cyan-500/20'
              }`}
              title="按住上下拖拽可自由调节文件列表高度"
            >
              <div className="w-12 h-1 rounded-full bg-slate-700 group-hover:bg-cyan-400 transition" />
            </div>
          )}
        </div>
      }
      right={
        <div className="space-y-4">
          {/* Slurm & Remote Shell Terminal */}
          <div className="glass-panel rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span>Linux 超算集群控制台 (Slurm · SSH Command)</span>
              </h3>
              {cmdExitCode !== null && (
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                    cmdExitCode === 0
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                  }`}
                >
                  退出状态码: {cmdExitCode}
                </span>
              )}
            </div>

            {/* Quick Slurm Command Badges */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] text-slate-400">快速指令:</span>
              {[
                { label: 'squeue (作业排队)', cmd: 'squeue -u $USER' },
                { label: 'sinfo (节点负载)', cmd: 'sinfo' },
                { label: 'nvidia-smi (显卡)', cmd: 'nvidia-smi' },
                { label: 'ls -lh (文件)', cmd: 'ls -lh' },
                { label: 'df -h (磁盘)', cmd: 'df -h' },
              ].map((item) => (
                <button
                  key={item.label}
                  onClick={() => {
                    setShellCmd(item.cmd);
                    runShellCommand(item.cmd);
                  }}
                  className="px-2 py-0.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500/40 text-[11px] font-mono text-slate-300 hover:text-cyan-200 transition cursor-pointer"
                >
                  {item.label}
                </button>
              ))}
            </div>

            {/* Terminal Input */}
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-cyan-400 font-mono text-xs">
                  $
                </span>
                <input
                  value={shellCmd}
                  onChange={(e) => setShellCmd(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && runShellCommand(shellCmd)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-7 pr-3 py-2 text-xs font-mono text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-500/60"
                  placeholder="输入 Linux Shell 指令，例如: squeue -u $USER 或 formchk job.chk job.fchk"
                />
              </div>
              <button
                disabled={runningCmd}
                onClick={() => runShellCommand(shellCmd)}
                className="px-4 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/40 text-cyan-200 text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50"
              >
                {runningCmd ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                <span>执行指令</span>
              </button>
            </div>

            {/* Expandable and Resizable Terminal Output Window */}
            <ExpandableConsole
              title="终端输出流"
              content={cmdStdout}
              placeholder="# 远程终端输出将显示在此处 (支持 Slurm 作业监控、formchk 转换、查看日志等)..."
              initialHeight={220}
              onClear={() => setCmdStdout('')}
            />
          </div>

          {/* Remote Multiwfn Execution Engine */}
          <div className="glass-panel rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-blue-400" />
                <span>远程 Multiwfn 算力卸载引擎 (免下载即时计算)</span>
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-start">
              <div className="md:col-span-5 space-y-2">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                    远程目标文件 (在左侧点击或手动填入)
                  </label>
                  <input
                    value={remoteTargetFile}
                    onChange={(e) => setRemoteTargetFile(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-200"
                    placeholder="/home/calc/jobs/zmy01_dimer_opt.fchk"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                    Multiwfn 输入命令序列 (每行一条)
                  </label>
                  <textarea
                    rows={4}
                    value={remoteCommands}
                    onChange={(e) => setRemoteCommands(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2 text-xs font-mono text-cyan-300"
                    placeholder="0&#10;1&#10;q"
                  />
                </div>

                <button
                  disabled={runningMultiwfn || !remoteTargetFile}
                  onClick={runRemoteMultiwfn}
                  className="w-full py-2 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-bold text-xs flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50 transition shadow-lg shadow-blue-500/20"
                >
                  {runningMultiwfn ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Play className="w-3.5 h-3.5" />
                  )}
                  <span>在 Linux 节点上执行 Multiwfn</span>
                </button>
              </div>

              <div className="md:col-span-7">
                <ExpandableConsole
                  title="远程 Multiwfn 标准输出流"
                  content={multiwfnStdout}
                  placeholder="远程 Multiwfn 执行输出将实时显示于此..."
                  initialHeight={220}
                  onClear={() => setMultiwfnStdout('')}
                />
              </div>
            </div>
          </div>
        </div>
      }
    />
    </div>
  );
};
