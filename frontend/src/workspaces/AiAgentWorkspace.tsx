import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  BookOpen,
  Bot,
  Brain,
  Camera,
  Check,
  CheckCircle2,
  ChevronDown,
  Copy,
  Download,
  Eye,
  FileText,
  FolderCheck,
  Image as ImageIcon,
  Layers,
  Loader2,
  Play,
  RefreshCw,
  Send,
  Settings2,
  Sliders,
  Sparkles,
  Trash2,
  Upload,
  X,
  Zap,
} from 'lucide-react';
import { api } from '../api/client';
import type { MoleculeInspection } from '../types/quantum';

interface AiAgentWorkspaceProps {
  inspection: MoleculeInspection | null;
}

interface ModelItem {
  id: string;
  display_name?: string;
  context_length?: number;
  max_completion_tokens?: number;
  supports_images?: boolean;
  supports_thinking?: boolean;
  recommended?: boolean;
}

const DEFAULT_PRESET_MODELS: ModelItem[] = [
  {
    id: 'gemini-3.8-flash',
    display_name: 'Gemini 3.8 Flash',
    context_length: 1048576,
    max_completion_tokens: 131072,
    supports_images: true,
    supports_thinking: true,
    recommended: true,
  },
  {
    id: 'claude-sonnet-5-5',
    display_name: 'Claude Sonnet 5.5',
    context_length: 1000000,
    max_completion_tokens: 128000,
    supports_images: true,
    supports_thinking: true,
    recommended: true,
  },
  {
    id: 'claude-opus-5-5',
    display_name: 'Claude Opus 5.5',
    context_length: 1000000,
    max_completion_tokens: 128000,
    supports_images: true,
    supports_thinking: true,
    recommended: true,
  },
  {
    id: 'claude-sonnet-4-6',
    display_name: 'Claude Sonnet 4.6',
    context_length: 250000,
    max_completion_tokens: 64000,
    supports_images: true,
    supports_thinking: true,
  },
  {
    id: 'gemini-4-argon',
    display_name: 'Gemini 4 Argon',
    context_length: 1048576,
    max_completion_tokens: 65536,
    supports_images: true,
    supports_thinking: true,
  },
  {
    id: 'gpt-oss-120b',
    display_name: 'GPT-OSS 120B',
    context_length: 131072,
    max_completion_tokens: 32768,
    supports_images: false,
    supports_thinking: true,
  },
];

export const AiAgentWorkspace: React.FC<AiAgentWorkspaceProps> = ({ inspection }) => {
  // Model Configuration matching user's local Antigravity Tools / OpenAI proxy
  const [apiUrl, setApiUrl] = useState('http://127.0.0.1:8045/v1');
  const [apiKey, setApiKey] = useState('sk-c94f8f28c01d43dd84865a0cc8e0c9a3');
  const [model, setModel] = useState('gemini-3.8-flash');
  const [modelsList, setModelsList] = useState<ModelItem[]>(DEFAULT_PRESET_MODELS);
  const [loadingModels, setLoadingModels] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  // Advanced LLM Parameters: Thinking, Context, Multimodal
  const [reasoningEnabled, setReasoningEnabled] = useState(true);
  const [reasoningEffort, setReasoningEffort] = useState<'low' | 'medium' | 'high'>('medium');
  const [maxTokens, setMaxTokens] = useState<number>(16384);
  const [attachedImages, setAttachedImages] = useState<Array<{ name: string; dataUrl: string }>>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Selected Model details
  const activeModelInfo = useMemo(() => {
    return (
      modelsList.find((m) => m.id === model) || {
        id: model,
        display_name: model,
        context_length: 1048576,
        max_completion_tokens: 131072,
        supports_images: true,
        supports_thinking: true,
      }
    );
  }, [modelsList, model]);

  // User Prompt & Literature Input
  const [prompt, setPrompt] = useState(
    '根据文献标准对当前体系执行深入的弱相互作用 (IGMH) 剖析，定量量化层间 π-π 堆积相互作用与位阻排斥，结合 Sobko 知识库准则撰写专业学术报告。'
  );

  // Agent State
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<Array<{ type: string; title: string; detail: string }>>([]);
  const [reportMarkdown, setReportMarkdown] = useState<string>('');
  const [exportedPaths, setExportedPaths] = useState<string[]>([]);
  const [exportNotice, setExportNotice] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Preset Workflows
  const presets = [
    {
      title: '二聚体 π-π 弱相互作用深度剖析',
      desc: '调用 Multiwfn IGMH 引擎定量提取 δg_inter 峰值与 BGR 色阶机理',
      text: '根据文献标准对当前体系执行深入的弱相互作用 (IGMH) 剖析，定量量化层间 π-π 堆积相互作用与位阻排斥，结合 Sobko 知识库准则撰写专业学术报告。',
    },
    {
      title: '文献分析工作流精准复刻',
      desc: '解析实验或理论文献方法，自动配置 Multiwfn 参数并复刻图表分析',
      text: '复刻经典文献中关于有机半导体二聚体堆积界面相互作用分析，采用 Hirshfeld 划分模型提取范德华接触面积与层间相互作用指纹，并输出对比结论。',
    },
    {
      title: '多模态 3D 等值面视觉直观解构',
      desc: '捕获当前 3D 绿色 π-π 堆积等值面视觉图像，由大模型亲眼辨识空间取向',
      text: '请观察我捕获的当前分子 3D 相互作用等值面几何图像，结合 Multiwfn 计算数据，以第一人称专业计算化学家视角深度剖析空间立体接触区、极性末端分布与超分子识别特征。',
    },
    {
      title: '前线轨道与电荷转移综合评估',
      desc: '计算 HOMO/LUMO 轨道分布、能隙与 ADCH/Hirshfeld 净电荷',
      text: '计算体系的前线分子轨道能级阶梯与 HOMO-LUMO 能隙，分析给体与受体片段的电荷分布特征，评估电荷转移倾向与光电活性。',
    },
  ];

  // Fetch Available Models from /v1/models
  const handleFetchModels = async () => {
    setLoadingModels(true);
    try {
      const res = await api.fetchAgentModels({ api_url: apiUrl, api_key: apiKey });
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        setModelsList(res.data);
        if (!res.data.some((m) => m.id === model)) {
          setModel(res.data[0].id);
        }
      }
    } catch (e: any) {
      console.warn('获取可用模型列表失败，使用预设目录:', e);
    } finally {
      setLoadingModels(false);
    }
  };

  // Capture Current 3D Canvas / Plot Image
  const handleCaptureCanvas = () => {
    try {
      const canvases = Array.from(document.querySelectorAll('canvas'));
      if (canvases.length === 0) {
        alert('未在当前界面检测到活动的 3D 分子视口画布，请先在结构或弱相互作用模块渲染分子');
        return;
      }
      // Get the largest canvas (typically the 3D WebGL viewport)
      canvases.sort((a, b) => b.width * b.height - a.width * a.height);
      const targetCanvas = canvases[0];
      const dataUrl = targetCanvas.toDataURL('image/png');
      const timestamp = new Date().toLocaleTimeString();
      setAttachedImages((prev) => [
        ...prev,
        {
          name: `3D分子等值面快照_${timestamp}.png`,
          dataUrl,
        },
      ]);
    } catch (e: any) {
      alert(`截取 3D 画布失败: ${e.message}`);
    }
  };

  // Upload Local Image File
  const handleUploadImage = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          setAttachedImages((prev) => [
            ...prev,
            {
              name: file.name,
              dataUrl: reader.result as string,
            },
          ]);
        }
      };
      reader.readAsDataURL(file);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeAttachedImage = (idx: number) => {
    setAttachedImages((prev) => prev.filter((_, i) => i !== idx));
  };

  const runAgent = async () => {
    if (!prompt.trim()) return;
    setRunning(true);
    setExportNotice(null);
    setSteps([
      {
        type: 'thought',
        title: 'AI Agent 启动中',
        detail: `连接模型: ${model} | 思考强度: ${reasoningEnabled ? reasoningEffort : '关闭'} | 多模态图像: ${attachedImages.length} 张 | 调取 Multiwfn 核心工具链...`,
      },
    ]);

    try {
      const res = await api.agentChat({
        prompt,
        file_path: inspection?.file_path,
        api_url: apiUrl,
        api_key: apiKey,
        model,
        reasoning_effort: reasoningEnabled ? reasoningEffort : 'none',
        max_tokens: maxTokens,
        images: attachedImages.map((img) => img.dataUrl),
      });

      setSteps(res.steps || []);
      setReportMarkdown(res.report_markdown || res.answer || '');
    } catch (e: any) {
      setSteps((prev) => [
        ...prev,
        {
          type: 'error',
          title: 'Agent 执行异常',
          detail: e.message || '调用模型或工具执行超时',
        },
      ]);
    } finally {
      setRunning(false);
    }
  };

  const exportReportToDisk = async () => {
    if (!inspection || !reportMarkdown) return;
    try {
      const res = await api.exportSave({
        file_path: inspection.file_path,
        report_markdown: reportMarkdown,
        export_csv: false,
        export_obj: false,
        export_cubes: false,
        export_report: true,
        export_log: false,
      });
      setExportedPaths(res.files_written);
      setExportNotice(res.message);
    } catch (e: any) {
      setExportNotice(`导出报告失败: ${e.message}`);
    }
  };

  const copyReport = () => {
    if (!reportMarkdown) return;
    navigator.clipboard.writeText(reportMarkdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadMarkdown = () => {
    if (!reportMarkdown) return;
    const blob = new Blob([reportMarkdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${inspection?.file_name || 'molecule'}_quantum_ai_report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Top Banner & Model Configuration Toggle */}
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-slate-950 via-sky-950/20 to-slate-950 border-sky-500/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 to-indigo-600 flex items-center justify-center text-slate-950 font-bold shadow-lg shadow-sky-500/25">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-100">
                WaveCraft AI 量子化学学术智能体 (DeepSeek Harness · MCP Architecture)
              </h2>
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-[10px] font-mono text-emerald-300 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Sobko 知识库就绪
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-2 flex-wrap">
              <span>自主调度 Multiwfn 全套量子化学指令与 Sobereva 规范</span>
              <span className="text-slate-600">|</span>
              <span className="font-mono text-sky-400 font-semibold">{model}</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400">
                上下文: {activeModelInfo.context_length ? (activeModelInfo.context_length / 1024).toFixed(0) + 'K' : '1M'}
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-emerald-400">
                {reasoningEnabled ? `思考: ${reasoningEffort}` : '标准'}
              </span>
              {attachedImages.length > 0 && (
                <span className="px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px]">
                  多模态: {attachedImages.length} 图
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowConfig((v) => !v)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition cursor-pointer flex items-center gap-1.5 ${
              showConfig
                ? 'bg-sky-500/20 border-sky-400 text-sky-200'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:text-white'
            }`}
          >
            <Settings2 className="w-3.5 h-3.5" />
            <span>模型与高级接口配置 ({model})</span>
          </button>
        </div>
      </div>

      {/* Expandable Model, Reasoning & Multimodal Settings */}
      {showConfig && (
        <div className="glass-panel rounded-2xl p-4 space-y-4 border border-sky-500/30 bg-slate-950/90 animate-in fade-in duration-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                API 地址 (OpenAI 协议 / 本地代理)
              </label>
              <input
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200"
                placeholder="http://127.0.0.1:8045/v1"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                API 密钥 (API Key)
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200"
                placeholder="sk-..."
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-semibold text-slate-400 block">
                  调用模型 (Model)
                </label>
                <button
                  disabled={loadingModels}
                  onClick={handleFetchModels}
                  className="text-[11px] text-sky-400 hover:text-sky-300 flex items-center gap-1 cursor-pointer font-medium"
                >
                  <RefreshCw className={`w-3 h-3 ${loadingModels ? 'animate-spin' : ''}`} />
                  <span>获取可用模型</span>
                </button>
              </div>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200"
              >
                {modelsList.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.display_name || m.id} (
                    {m.context_length ? (m.context_length / 1024).toFixed(0) + 'K' : '1M'}
                    {m.supports_thinking ? ' · 思考' : ''}
                    {m.supports_images ? ' · 视觉' : ''})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Model Capabilities & Detailed Parameter Controls */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 1. Reasoning / Thinking Effort */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5 text-sky-400" />
                  <span>深度思考 / 推理等级</span>
                </span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={reasoningEnabled}
                    onChange={(e) => setReasoningEnabled(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-8 h-4 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-sky-500"></div>
                </label>
              </div>

              {reasoningEnabled ? (
                <div className="flex gap-1.5">
                  {(['low', 'medium', 'high'] as const).map((lvl) => (
                    <button
                      key={lvl}
                      onClick={() => setReasoningEffort(lvl)}
                      className={`flex-1 py-1 rounded-lg text-[11px] font-mono font-medium transition cursor-pointer border ${
                        reasoningEffort === lvl
                          ? 'bg-sky-500/25 border-sky-400 text-sky-200 font-bold'
                          : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {lvl.toUpperCase()}
                      <span className="block text-[9px] opacity-70">
                        {lvl === 'low' ? '轻量' : lvl === 'medium' ? '适中' : '极限'}
                      </span>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-slate-500">已关闭思考模式，采用标准推理速度</p>
              )}
            </div>

            {/* 2. Context Window & Max Tokens */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-indigo-400" />
                  <span>上下文与最大输出 Token</span>
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  上限: {activeModelInfo.context_length ? (activeModelInfo.context_length / 1024).toFixed(0) + 'K' : '1024K'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={2048}
                  max={activeModelInfo.max_completion_tokens || 65536}
                  step={2048}
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(Number(e.target.value))}
                  className="flex-1 accent-sky-400"
                />
                <span className="text-xs font-mono text-sky-300 w-16 text-right font-bold">
                  {maxTokens.toLocaleString()}
                </span>
              </div>
              <p className="text-[10px] text-slate-500">单次学术分析报告最大生成输出 Token 预算</p>
            </div>

            {/* 3. Input Modality Badges */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                <span>输入模态支持</span>
              </span>
              <div className="flex items-center gap-2 pt-0.5">
                <label className="flex items-center gap-1.5 text-xs text-slate-300">
                  <input type="checkbox" checked disabled className="rounded accent-sky-500" />
                  <span>文本输入</span>
                </label>
                <label className="flex items-center gap-1.5 text-xs text-slate-300">
                  <input
                    type="checkbox"
                    checked={activeModelInfo.supports_images !== false}
                    disabled
                    className="rounded accent-sky-500"
                  />
                  <span>图片 / 视觉多模态</span>
                </label>
              </div>
              <p className="text-[10px] text-slate-500">
                支持 3D 分子立体等值面、紫外可见/红外光谱及文献图表直接图像解析
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Preset Strategy Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        {presets.map((p, i) => (
          <div
            key={i}
            onClick={() => setPrompt(p.text)}
            className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-sky-500/50 hover:bg-slate-900/60 transition cursor-pointer group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200 group-hover:text-sky-300 transition-colors">
                <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                <span>{p.title}</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{p.desc}</p>
            </div>
            <div className="mt-2 text-[10px] text-sky-400/80 font-mono flex items-center gap-1">
              <span>点击载入工作流</span>
              <span>&rarr;</span>
            </div>
          </div>
        ))}
      </div>

      {/* Prompt Input, Multimodal Image Attachment & Execution */}
      <div className="glass-panel rounded-2xl p-4 space-y-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <label className="text-xs font-bold text-slate-200 flex items-center gap-2">
            <span>智能体科研指令 / 粘贴文献段落</span>
            {inspection && (
              <span className="font-mono font-normal text-slate-400 text-[11px]">
                · 当前分子: {inspection.file_name} ({inspection.atoms.length} 原子)
              </span>
            )}
          </label>

          {/* Multimodal Image Actions */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCaptureCanvas}
              className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-sky-500/50 text-[11px] text-slate-300 hover:text-sky-300 flex items-center gap-1.5 transition cursor-pointer"
              title="截取当前 3D 分子视口或 2D 散点图并传入视觉大模型"
            >
              <Camera className="w-3.5 h-3.5 text-sky-400" />
              <span>捕获当前 3D 分子视口</span>
            </button>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-sky-500/50 text-[11px] text-slate-300 hover:text-sky-300 flex items-center gap-1.5 transition cursor-pointer"
              title="上传外部文献图表、谱图或分子结构图"
            >
              <Upload className="w-3.5 h-3.5 text-indigo-400" />
              <span>上传文献/谱图图片</span>
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={handleUploadImage}
            />
          </div>
        </div>

        {/* Attached Multimodal Image Previews */}
        {attachedImages.length > 0 && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {attachedImages.map((img, idx) => (
              <div
                key={idx}
                className="relative group shrink-0 rounded-xl overflow-hidden border border-sky-500/40 bg-slate-950 p-1 flex items-center gap-2"
              >
                <img
                  src={img.dataUrl}
                  alt={img.name}
                  className="w-12 h-12 object-cover rounded-lg bg-black/40"
                />
                <div className="pr-2 max-w-[140px]">
                  <p className="text-[10px] font-mono text-slate-200 truncate">{img.name}</p>
                  <span className="text-[9px] text-sky-400 font-mono">视觉模态已就绪</span>
                </div>
                <button
                  onClick={() => removeAttachedImage(idx)}
                  className="absolute top-1 right-1 p-0.5 rounded-full bg-rose-600/80 text-white hover:bg-rose-600 transition"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={3}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/60 resize-none font-sans"
            placeholder="输入您的科研分析需求，或粘贴文献中关于计算方法的描述..."
          />
          <button
            disabled={running || !prompt.trim()}
            onClick={runAgent}
            className="absolute bottom-3 right-3 px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50 shadow-lg shadow-sky-500/20 hover:brightness-110 transition"
          >
            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            <span>启动 Agent 自主分析</span>
          </button>
        </div>
      </div>

      {/* Main Execution Trace & Generated Academic Report */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Real-time Agent Reasoning & Tool Calls */}
        <div className="lg:col-span-5 glass-panel rounded-2xl p-4 space-y-3 flex flex-col">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-sky-400" />
              <span>Agent 决策流与工具执行追踪</span>
            </h3>
            {running && (
              <span className="text-[10px] font-mono text-sky-300 animate-pulse">执行中...</span>
            )}
          </div>

          <div className="flex-1 min-h-[380px] max-h-[580px] overflow-y-auto space-y-2.5 pr-1">
            {steps.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-xs text-slate-500 p-6 text-center">
                <Bot className="w-10 h-10 text-slate-700 mb-2" />
                <p>点击上方「启动 Agent 自主分析」开始自主工作流</p>
                <p className="text-[11px] text-slate-600 mt-1">
                  Agent 将自主执行分子解析、Sobko 知识库检索、Multiwfn 量化计算与学术报告撰写
                </p>
              </div>
            ) : (
              steps.map((st, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-xl border text-xs transition ${
                    st.type === 'tool_call'
                      ? 'bg-sky-500/10 border-sky-500/30 text-sky-200'
                      : st.type === 'tool_result'
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
                        : st.type === 'final_answer'
                          ? 'bg-indigo-500/15 border-indigo-500/40 text-indigo-200'
                          : st.type === 'error'
                            ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                            : 'bg-slate-900/80 border-slate-800 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between font-semibold mb-1">
                    <span className="flex items-center gap-1.5">
                      {st.type === 'tool_result' ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      ) : st.type === 'tool_call' ? (
                        <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                      ) : (
                        <Bot className="w-3.5 h-3.5 text-indigo-400" />
                      )}
                      <span>{st.title}</span>
                    </span>
                    <span className="text-[10px] font-mono opacity-60">步骤 {idx + 1}</span>
                  </div>
                  <p className="text-[11px] opacity-90 leading-relaxed font-mono whitespace-pre-wrap">
                    {st.detail}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Publication-Standard Academic Report */}
        <div className="lg:col-span-7 glass-panel rounded-2xl p-4 space-y-3 flex flex-col">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span>AI 生成专业量子化学学术分析报告</span>
            </h3>

            {reportMarkdown && (
              <div className="flex items-center gap-2">
                <button
                  onClick={copyReport}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 hover:text-white flex items-center gap-1 transition cursor-pointer"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? '已复制' : '复制 Markdown'}</span>
                </button>
                <button
                  onClick={downloadMarkdown}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 hover:text-white flex items-center gap-1 transition cursor-pointer"
                >
                  <Download className="w-3 h-3" />
                  <span>下载 .md</span>
                </button>
                <button
                  onClick={exportReportToDisk}
                  className="px-2.5 py-1 rounded-lg bg-sky-500/20 border border-sky-400/40 hover:bg-sky-500/30 text-xs text-sky-200 flex items-center gap-1 transition cursor-pointer"
                >
                  <FolderCheck className="w-3 h-3 text-sky-400" />
                  <span>保存至分子所在目录</span>
                </button>
              </div>
            )}
          </div>

          {exportNotice && (
            <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/30 text-xs text-sky-200 flex items-center gap-2">
              <FolderCheck className="w-4 h-4 text-sky-400 shrink-0" />
              <span>{exportNotice}</span>
            </div>
          )}

          <div className="flex-1 min-h-[380px] max-h-[580px] overflow-y-auto p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 font-sans text-xs text-slate-200 leading-relaxed">
            {reportMarkdown ? (
              <div className="space-y-4">
                <div className="prose prose-invert prose-xs max-w-none whitespace-pre-wrap font-sans">
                  {reportMarkdown}
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-xs text-slate-500 p-6 text-center">
                <FileText className="w-10 h-10 text-slate-700 mb-2" />
                <p>暂无报告，执行 Agent 工作流后将在此处自动生成</p>
                <p className="text-[11px] text-slate-600 mt-1">
                  报告包含拓扑判据表格、π-π 堆积/位阻机理解析与 Sobko 学术期刊级发表指引
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
