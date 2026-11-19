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
  Maximize2,
  Minimize2,
  Play,
  RefreshCw,
  Send,
  Settings2,
  Sliders,
  Sparkles,
  Trash2,
  Upload,
  User,
  X,
  Zap,
} from 'lucide-react';
import { api } from '../api/client';
import { Tooltip } from '../components/Tooltip';
import { MarkdownViewer } from '../components/MarkdownViewer';
import { ExportReportModal } from '../components/ExportReportModal';
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

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  steps?: Array<{ type: string; title: string; detail: string }>;
  images?: Array<{ name: string; dataUrl: string }>;
  actionsExecuted?: string[];
  timestamp: string;
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
  const [apiKey, setApiKey] = useState('sk-9baf34c57c4c47208685ef9751a51660');
  const [model, setModel] = useState('gemini-3.8-flash');
  const [modelsList, setModelsList] = useState<ModelItem[]>(DEFAULT_PRESET_MODELS);
  const [loadingModels, setLoadingModels] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  // Advanced LLM Parameters: Thinking, Context, Multimodal
  const [reasoningEnabled, setReasoningEnabled] = useState(true);
  const [reasoningEffort, setReasoningEffort] = useState<'low' | 'medium' | 'high'>('medium');
  const [maxTokens, setMaxTokens] = useState<number>(16384);
  const [attachedImages, setAttachedImages] = useState<Array<{ name: string; dataUrl: string }>>([]);

  // Fullscreen / Window Maximization state
  const [isMaximized, setIsMaximized] = useState(false);

  // Custom Export Modal State
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [exportContent, setExportContent] = useState<string>('');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

  // Initial greeting
  const initialGreeting: ChatMessage = useMemo(() => {
    const fileName = inspection?.file_name || '未加载分子';
    return {
      id: 'greeting',
      role: 'assistant',
      content: `### 🔬 欢迎使用 WaveCraft 智能计算化学 Agent

我是您的专属量子化学大模型助手。当前已挂载 **Sobko 计算化学文献知识库** (涵盖 Sobereva 老师发表规范与 Multiwfn 核心手册)。

- **当前分子**: \`${fileName}\` (${inspection?.atoms.length || 0} 原子 · ${inspection?.bonds.length || 0} 键)
- **分析能力**: 弱相互作用 (IGMH/RDG) 拓扑量化、前线轨道 (HOMO/LUMO) 跃迁能隙、原子电荷 (CM5/ADCH/Hirshfeld) 计算与发表级分析报告生成。
- **软件指令联动**: 您可以在对话中直接吩咐我执行软件操作，例如：
  - \`“切换到空间填充模式”\` 或 \`“换成球棍模型”\`
  - \`“开启原子序号”\` 或 \`“显示元素符号”\`
  - \`“复位 3D 视角”\`、\`“切换侧视”\`、\`“切换俯视”\`
  - \`“运行 Multiwfn 计算电荷”\`

请输入您的分析需求或直接点击下方的快捷命令：`,
      timestamp: new Date().toLocaleTimeString(),
    };
  }, [inspection?.file_name, inspection?.atoms.length, inspection?.bonds.length]);

  // Conversational message history
  const [messages, setMessages] = useState<ChatMessage[]>([initialGreeting]);
  const [inputPrompt, setInputPrompt] = useState<string>('');
  const [running, setRunning] = useState(false);
  const [actionToast, setActionToast] = useState<string | null>(null);

  // Auto-scroll messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, running]);

  // Handle ESC for fullscreen exit
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) {
        setIsMaximized(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  // Dispatch 3D Actions and return executed action names
  const dispatch3DAction = (action: string, value?: any, label?: string): string => {
    window.dispatchEvent(
      new CustomEvent('wavecraft-3d-action', {
        detail: { action, value },
      })
    );
    const text = label || `执行: ${action}`;
    setActionToast(text);
    setTimeout(() => setActionToast(null), 3000);
    return text;
  };

  // Natural Language Command Detection and Auto-Dispatch
  const detectAndExecuteCommands = (text: string): string[] => {
    const executed: string[] = [];
    const lower = text.toLowerCase();

    // 1. Render Style Commands
    if (lower.includes('空间填充') || lower.includes('cpk') || lower.includes('spacefill') || lower.includes('范德华球')) {
      dispatch3DAction('setStyle', 'spacefill', '🎨 3D 视口已切换为空间填充 (CPK) 模式');
      executed.push('🎨 切换空间填充模式');
    } else if (lower.includes('球棍') || lower.includes('ball-stick') || lower.includes('ball and stick')) {
      dispatch3DAction('setStyle', 'ball-stick', '🔬 3D 视口已切换为球棍模型');
      executed.push('🔬 切换球棍模型');
    } else if (lower.includes('线框') || lower.includes('wireframe')) {
      dispatch3DAction('setStyle', 'wireframe', '📐 3D 视口已切换为线框模式');
      executed.push('📐 切换线框模型');
    }

    // 2. Atom Index & Symbol Commands
    if (lower.includes('开启序号') || lower.includes('显示序号') || lower.includes('开启原子序号') || lower.includes('显示原子序号') || lower.includes('标出序号')) {
      dispatch3DAction('setShowIndices', true, '🏷️ 已开启 3D 原子序号显示');
      executed.push('🏷️ 开启原子序号');
    } else if (lower.includes('关闭序号') || lower.includes('隐藏序号') || lower.includes('关闭原子序号') || lower.includes('隐藏原子序号')) {
      dispatch3DAction('setShowIndices', false, '🏷️ 已关闭 3D 原子序号显示');
      executed.push('🏷️ 关闭原子序号');
    }

    if (lower.includes('开启符号') || lower.includes('显示符号') || lower.includes('开启元素符号') || lower.includes('显示元素符号') || lower.includes('标出元素')) {
      dispatch3DAction('setShowSymbols', true, '⚛️ 已开启 3D 元素符号显示');
      executed.push('⚛️ 开启元素符号');
    } else if (lower.includes('关闭符号') || lower.includes('隐藏符号') || lower.includes('关闭元素符号') || lower.includes('隐藏元素符号')) {
      dispatch3DAction('setShowSymbols', false, '⚛️ 已关闭 3D 元素符号显示');
      executed.push('⚛️ 关闭元素符号');
    }

    // 3. Camera Controls
    if (lower.includes('复位视角') || lower.includes('重置视角') || lower.includes('正视') || lower.includes('居中视角') || lower.includes('复位相机')) {
      dispatch3DAction('resetCamera', null, '🔄 3D 视口已复位至默认等角视角');
      executed.push('🔄 3D 视角复位');
    } else if (lower.includes('侧视') || lower.includes('侧面视角') || lower.includes('side view')) {
      dispatch3DAction('setCameraPreset', 'side', '🔭 3D 视口已切换为侧视角度 (观察 π-π 堆积层)');
      executed.push('🔭 切换侧视');
    } else if (lower.includes('俯视') || lower.includes('顶视') || lower.includes('top view')) {
      dispatch3DAction('setCameraPreset', 'top', '🔭 3D 视口已切换为俯视角度');
      executed.push('🔭 切换俯视');
    }

    // 4. Trackball Tumbling Mode
    if (lower.includes('自由翻转') || lower.includes('360度翻转') || lower.includes('上下翻转') || lower.includes('轨迹球')) {
      dispatch3DAction('setRotationMode', 'free', '🌐 已启用 360° 无约束分子轨迹球自由翻转');
      executed.push('🌐 360° 自由翻转');
    }

    return executed;
  };

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
      setActionToast('📸 成功捕获 3D 分子视口高清快照');
      setTimeout(() => setActionToast(null), 2500);
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

  // Send message to AI Agent
  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend ?? inputPrompt).trim();
    if (!query && attachedImages.length === 0) return;

    // Detect user-specified direct 3D commands first
    const clientActions = detectAndExecuteCommands(query);

    const userMsgId = `user-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: query || '请分析附加的图像',
      images: [...attachedImages],
      actionsExecuted: clientActions.length > 0 ? clientActions : undefined,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt('');
    const curImages = [...attachedImages];
    setAttachedImages([]);
    setRunning(true);

    try {
      const res = await api.agentChat({
        prompt: query,
        file_path: inspection?.file_path,
        api_url: apiUrl,
        api_key: apiKey,
        model,
        reasoning_effort: reasoningEnabled ? reasoningEffort : 'none',
        max_tokens: maxTokens,
        images: curImages.map((img) => img.dataUrl),
      });

      const assistantContent = res.report_markdown || res.answer || '分析完成。';
      // Detect if assistant recommended or executed software commands
      const assistantActions = detectAndExecuteCommands(assistantContent);

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: assistantContent,
        steps: res.steps || [],
        actionsExecuted: assistantActions.length > 0 ? assistantActions : undefined,
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: any) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `❌ **Agent 执行遇到异常**: ${e.message || '调用模型超时或网络连接失败，请检查模型 API 地址与密钥。'}`,
        steps: [
          {
            type: 'error',
            title: '调用失败',
            detail: e.message || '网络连接被拒绝或 Multiwfn 引擎退出',
          },
        ],
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setRunning(false);
    }
  };

  const handleOpenExportModal = (content: string) => {
    setExportContent(content);
    setExportModalOpen(true);
  };

  const handleClearMessages = () => {
    if (confirm('确定要清空当前对话记录吗？')) {
      setMessages([initialGreeting]);
    }
  };

  return (
    <div
      className={`transition-all duration-300 flex flex-col ${
        isMaximized
          ? 'fixed inset-0 z-[9999] p-6 bg-slate-950/98 backdrop-blur-2xl'
          : 'space-y-3'
      }`}
    >
      {/* Action Toast Alert */}
      {actionToast && (
        <div className="fixed top-16 right-6 z-[99999] px-4 py-2 rounded-xl bg-cyan-500/20 border border-cyan-400/60 shadow-xl text-cyan-200 text-xs font-semibold flex items-center gap-2 animate-in fade-in slide-in-from-top-4 duration-200">
          <Zap className="w-4 h-4 text-cyan-400" />
          <span>{actionToast}</span>
        </div>
      )}

      {/* Top Bar: Model Settings & Fullscreen Toggle */}
      <div className="glass-panel rounded-2xl p-3 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-xl bg-gradient-to-tr from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 text-cyan-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-100">WaveCraft 智能化学 Agent</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-mono">
                {activeModelInfo.display_name || model}
              </span>
            </div>
            <p className="text-[10px] text-slate-400">
              Multiwfn 工具链 + Sobko 量子化学知识库驱动 · 支持视口指令与全屏对话
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Quick Model Selector */}
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-2 py-1 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500/60"
          >
            {modelsList.map((m) => (
              <option key={m.id} value={m.id}>
                {m.display_name || m.id} {m.recommended ? '⭐' : ''}
              </option>
            ))}
          </select>

          {/* Reasoning Effort Toggle */}
          <div className="hidden sm:flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-lg p-0.5">
            <button
              onClick={() => setReasoningEnabled(!reasoningEnabled)}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold transition cursor-pointer flex items-center gap-1 ${
                reasoningEnabled
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <Brain className="w-3 h-3" />
              <span>{reasoningEnabled ? '思考中' : '思考关'}</span>
            </button>
            {reasoningEnabled && (
              <select
                value={reasoningEffort}
                onChange={(e) => setReasoningEffort(e.target.value as any)}
                className="bg-transparent text-[10px] text-slate-300 font-mono px-1 border-none focus:outline-none"
              >
                <option value="low">轻度</option>
                <option value="medium">中度</option>
                <option value="high">深度</option>
              </select>
            )}
          </div>

          {/* Config Settings Toggle */}
          <Tooltip content="配置大模型 API 地址、密钥与上下文 Token">
            <button
              onClick={() => setShowConfig(!showConfig)}
              className={`p-1.5 rounded-lg border text-xs transition cursor-pointer ${
                showConfig
                  ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <Settings2 className="w-3.5 h-3.5" />
            </button>
          </Tooltip>

          {/* Clear Messages */}
          <Tooltip content="清空当前对话记录">
            <button
              onClick={handleClearMessages}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-rose-500/40 text-slate-400 hover:text-rose-300 text-xs transition cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </Tooltip>

          {/* Fullscreen Maximize Toggle */}
          <Tooltip content={isMaximized ? '还原常规窗口 (Esc)' : '全屏最大化对话窗口'}>
            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className={`p-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1 transition cursor-pointer ${
                isMaximized
                  ? 'bg-cyan-500/30 border-cyan-400 text-cyan-100 shadow-lg shadow-cyan-500/20'
                  : 'bg-slate-900 border-slate-800 text-slate-300 hover:text-cyan-300 hover:border-cyan-500/40'
              }`}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
              <span className="hidden md:inline">{isMaximized ? '还原' : '全屏'}</span>
            </button>
          </Tooltip>
        </div>
      </div>

      {/* Expandable Model Configuration Panel */}
      {showConfig && (
        <div className="glass-panel rounded-2xl p-4 border border-cyan-500/30 space-y-3 animate-in fade-in duration-200">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-xs font-bold text-slate-200">大语言模型连接设置</span>
            <button
              disabled={loadingModels}
              onClick={handleFetchModels}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
            >
              <RefreshCw className={`w-3 h-3 ${loadingModels ? 'animate-spin' : ''}`} />
              <span>从服务器同步最新可用模型列表</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">OpenAI 兼容 API 代理地址</label>
              <input
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 font-mono text-slate-200 text-xs"
                placeholder="http://127.0.0.1:8045/v1"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">API Key 授权令牌</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 font-mono text-slate-200 text-xs"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">最大生成 Token 数</label>
              <input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value, 10) || 16384)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 font-mono text-slate-200 text-xs"
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Conversational Area */}
      <div
        className={`glass-panel rounded-2xl flex flex-col overflow-hidden border border-slate-800/80 ${
          isMaximized ? 'flex-1 min-h-0' : 'h-[620px]'
        }`}
      >
        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans select-text">
          {messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id}
                className={`flex gap-3 max-w-4xl ${
                  isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
                }`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border shadow-md ${
                    isUser
                      ? 'bg-cyan-500/20 border-cyan-400/40 text-cyan-300'
                      : 'bg-indigo-500/20 border-indigo-400/40 text-indigo-300'
                  }`}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Message Bubble */}
                <div
                  className={`rounded-2xl p-4 space-y-2 border text-xs max-w-[85%] ${
                    isUser
                      ? 'bg-cyan-950/40 border-cyan-500/30 text-slate-100 shadow-lg shadow-cyan-950/20'
                      : 'bg-slate-900/80 border-slate-800 text-slate-200 shadow-xl'
                  }`}
                >
                  {/* Attached Images preview */}
                  {msg.images && msg.images.length > 0 && (
                    <div className="flex items-center gap-2 flex-wrap mb-2">
                      {msg.images.map((img, idx) => (
                        <div key={idx} className="relative group">
                          <img
                            src={img.dataUrl}
                            alt={img.name}
                            className="w-24 h-24 object-cover rounded-lg border border-slate-700 shadow"
                          />
                          <span className="absolute bottom-1 left-1 right-1 text-[9px] bg-slate-950/80 rounded px-1 truncate text-slate-300">
                            {img.name}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Executed Action Pills */}
                  {msg.actionsExecuted && msg.actionsExecuted.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap pb-1 border-b border-slate-800/60">
                      <span className="text-[10px] text-cyan-400 font-semibold flex items-center gap-1">
                        <Zap className="w-3 h-3 text-cyan-400" />
                        <span>已触发 3D 联动指令:</span>
                      </span>
                      {msg.actionsExecuted.map((act, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-200 border border-cyan-400/40 text-[10px] font-mono"
                        >
                          {act}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Message Content Rendered with MarkdownViewer */}
                  <MarkdownViewer content={msg.content} />

                  {/* Agent Reasoning & Tool Steps Accordion */}
                  {msg.steps && msg.steps.length > 0 && (
                    <details className="mt-3 rounded-xl border border-slate-800 bg-slate-950/70 p-2.5">
                      <summary className="cursor-pointer text-xs font-semibold text-cyan-300 hover:text-cyan-200 flex items-center gap-1.5 select-none">
                        <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                        <span>查看 Agent 思考与 Multiwfn 工具执行追踪 ({msg.steps.length} 步)</span>
                      </summary>
                      <div className="space-y-2 mt-2 pt-2 border-t border-slate-800/80">
                        {msg.steps.map((st, i) => (
                          <div
                            key={i}
                            className={`p-2 rounded-lg border text-[11px] font-mono ${
                              st.type === 'error'
                                ? 'bg-rose-950/30 border-rose-800/50 text-rose-300'
                                : st.type === 'thought'
                                ? 'bg-indigo-950/20 border-indigo-800/30 text-indigo-300'
                                : 'bg-slate-900 border-slate-800 text-slate-300'
                            }`}
                          >
                            <div className="font-bold mb-0.5 flex items-center gap-1 text-[11px]">
                              {st.type === 'error' ? (
                                <AlertCircle className="w-3 h-3 text-rose-400" />
                              ) : (
                                <CheckCircle2 className="w-3 h-3 text-cyan-400" />
                              )}
                              <span>{st.title}</span>
                            </div>
                            <p className="opacity-90 leading-relaxed whitespace-pre-wrap text-[10px]">
                              {st.detail}
                            </p>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}

                  {/* Assistant Interactive Action Bar */}
                  {!isUser && msg.id !== 'greeting' && (
                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 mt-2 flex-wrap gap-2">
                      <div className="flex items-center gap-1 flex-wrap">
                        <span className="text-[10px] text-slate-500 mr-1">快捷视口操控:</span>
                        <button
                          onClick={() => dispatch3DAction('setStyle', 'spacefill', '🎨 切换空间填充')}
                          className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 hover:text-white transition cursor-pointer"
                        >
                          🎨 空间填充
                        </button>
                        <button
                          onClick={() => dispatch3DAction('setStyle', 'ball-stick', '🔬 切换球棍模型')}
                          className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 hover:text-white transition cursor-pointer"
                        >
                          🔬 球棍模型
                        </button>
                        <button
                          onClick={() => dispatch3DAction('toggleIndices', null, '🏷️ 开关原子序号')}
                          className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 hover:text-white transition cursor-pointer"
                        >
                          🏷️ 开关序号
                        </button>
                        <button
                          onClick={() => dispatch3DAction('toggleSymbols', null, '⚛️ 开关元素符号')}
                          className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 hover:text-white transition cursor-pointer"
                        >
                          ⚛️ 开关符号
                        </button>
                        <button
                          onClick={() => dispatch3DAction('resetCamera', null, '🔄 复位视角')}
                          className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 hover:text-white transition cursor-pointer"
                        >
                          🔄 复位视角
                        </button>
                      </div>

                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleOpenExportModal(msg.content)}
                          className="px-2.5 py-1 rounded-lg bg-cyan-500/20 border border-cyan-400/40 hover:bg-cyan-500/30 text-[11px] font-semibold text-cyan-200 flex items-center gap-1 transition cursor-pointer"
                        >
                          <FolderCheck className="w-3 h-3 text-cyan-300" />
                          <span>自定义导出报告</span>
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="text-[10px] text-slate-500 text-right pt-0.5">
                    {msg.timestamp}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Running Indicator */}
          {running && (
            <div className="flex items-center gap-3 mr-auto">
              <div className="w-8 h-8 rounded-xl bg-indigo-500/20 border border-indigo-400/40 text-indigo-300 flex items-center justify-center animate-pulse">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              </div>
              <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 text-xs text-slate-300 flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                <span>Agent 正在检索 Sobko 文献准则并执行 Multiwfn 计算剖析...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input & Control Dock */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-900/60 space-y-2">
          {/* Quick Command Chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none text-[11px]">
            <span className="text-slate-400 shrink-0">快捷指令:</span>
            {[
              {
                label: '🚀 全面分析当前分子',
                text: '根据文献标准对当前体系执行深入的弱相互作用 (IGMH) 剖析，定量量化层间 π-π 堆积相互作用与位阻排斥，结合 Sobko 知识库准则撰写专业学术报告。',
              },
              {
                label: '🎨 切换空间填充 (CPK)',
                text: '切换到空间填充模型，并分析当前分子表面位阻空间特征',
              },
              {
                label: '🔬 切换球棍模型',
                text: '切换到球棍模型，并开启原子序号',
              },
              {
                label: '🏷️ 开启原子序号',
                text: '开启原子序号显示，标出核心原子编号',
              },
              {
                label: '⚛️ 开启元素符号',
                text: '开启元素符号显示',
              },
              {
                label: '🔄 复位 3D 视角',
                text: '复位 3D 视角至最佳等角居中视角',
              },
              {
                label: '📐 计算 HOMO/LUMO 能隙',
                text: '计算体系的前线分子轨道能级阶梯与 HOMO-LUMO 能隙，评估电荷转移倾向与光电活性。',
              },
              {
                label: '⚡ Multiwfn 净电荷分析',
                text: '调用 Multiwfn 计算各原子的 CM5 与 Hirshfeld 净电荷，并输出电荷分布表格。',
              },
            ].map((chip) => (
              <button
                key={chip.label}
                onClick={() => {
                  setInputPrompt(chip.text);
                  handleSendMessage(chip.text);
                }}
                className="px-2.5 py-1 rounded-full bg-slate-950 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900 text-slate-300 hover:text-cyan-200 transition whitespace-nowrap cursor-pointer shrink-0"
              >
                {chip.label}
              </button>
            ))}
          </div>

          {/* Attached Images Preview in Input Area */}
          {attachedImages.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap p-2 rounded-xl bg-slate-950 border border-slate-800">
              {attachedImages.map((img, idx) => (
                <div key={idx} className="relative group">
                  <img
                    src={img.dataUrl}
                    alt={img.name}
                    className="w-16 h-16 object-cover rounded-lg border border-slate-700"
                  />
                  <button
                    onClick={() => removeAttachedImage(idx)}
                    className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-rose-500 text-white flex items-center justify-center text-[10px] cursor-pointer"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Main Input Row */}
          <div className="flex items-end gap-2">
            <div className="flex items-center gap-1 shrink-0 pb-1">
              <Tooltip content="截取当前 3D 视口画布快照并传给大模型">
                <button
                  onClick={handleCaptureCanvas}
                  className="p-2 rounded-xl bg-slate-950 border border-slate-800 hover:border-cyan-500/50 text-slate-400 hover:text-cyan-300 transition cursor-pointer"
                >
                  <Camera className="w-4 h-4" />
                </button>
              </Tooltip>

              <Tooltip content="附加本地实验图、光谱图或文献截图">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 rounded-xl bg-slate-950 border border-slate-800 hover:border-cyan-500/50 text-slate-400 hover:text-cyan-300 transition cursor-pointer"
                >
                  <Upload className="w-4 h-4" />
                </button>
              </Tooltip>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={handleUploadImage}
              />
            </div>

            <textarea
              rows={2}
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="向 AI Agent 发送学术分析需求或软件控制命令 (支持回车发送，例如输入“切换到空间填充并开启原子序号”)..."
              className="flex-1 bg-slate-950 border border-slate-800 focus:border-cyan-500/60 rounded-xl p-2.5 text-xs text-slate-100 placeholder-slate-600 focus:outline-none resize-none"
            />

            <button
              disabled={running || (!inputPrompt.trim() && attachedImages.length === 0)}
              onClick={() => handleSendMessage()}
              className="px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer shadow-lg shadow-cyan-500/20 disabled:opacity-40 shrink-0"
            >
              {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span>发送</span>
            </button>
          </div>
        </div>
      </div>

      {/* Custom Export Modal */}
      <ExportReportModal
        isOpen={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        markdownContent={exportContent}
        sourceFilePath={inspection?.file_path}
        moleculeName={inspection?.file_name}
      />
    </div>
  );
};
