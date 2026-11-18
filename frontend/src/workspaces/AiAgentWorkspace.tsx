import React, { useState } from 'react';
import {
  AlertCircle,
  BookOpen,
  Bot,
  CheckCircle2,
  Copy,
  Download,
  FileText,
  FolderCheck,
  Loader2,
  Play,
  Send,
  Settings2,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import type { MoleculeInspection } from '../types/quantum';

interface AiAgentWorkspaceProps {
  inspection: MoleculeInspection | null;
}

export const AiAgentWorkspace: React.FC<AiAgentWorkspaceProps> = ({ inspection }) => {
  // Model Configuration matching user's local Antigravity Tools / OpenAI proxy
  const [apiUrl, setApiUrl] = useState('http://127.0.0.1:8045/v1');
  const [apiKey, setApiKey] = useState('sk-76bb4979e3f');
  const [model, setModel] = useState('gemini-3.8-flash');
  const [showConfig, setShowConfig] = useState(false);

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
      title: '前线轨道与电荷转移综合评估',
      desc: '计算 HOMO/LUMO 轨道分布、能隙与 ADCH/Hirshfeld 净电荷',
      text: '计算体系的前线分子轨道能级阶梯与 HOMO-LUMO 能隙，分析给体与受体片段的电荷分布特征，评估电荷转移倾向与光电活性。',
    },
    {
      title: '分子表面静电势 (ESP) 极值与极性位点',
      desc: '计算范德华表面 ESP 最大值与最小值，预测超分子识别位点',
      text: '计算体系的分子表面静电势 (ESP) 极值点分布，输出最负/最正静电势区域及其空间坐标，探讨静电互补性与分子间结合取向。',
    },
  ];

  const runAgent = async () => {
    if (!prompt.trim()) return;
    setRunning(true);
    setExportNotice(null);
    setSteps([
      {
        type: 'thought',
        title: 'AI Agent 启动中',
        detail: `正在连接模型 ${model} (${apiUrl}) 并调取 Multiwfn 核心工具链...`,
      },
    ]);

    try {
      const res = await api.agentChat({
        prompt,
        file_path: inspection?.file_path,
        api_url: apiUrl,
        api_key: apiKey,
        model,
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
            <p className="text-xs text-slate-400 mt-0.5">
              自主调度 Multiwfn 全套量子化学指令与 Sobereva 知识库规范，一键完成文献复刻与出版级分析报告
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
            <span>模型与 MCP 设置 ({model})</span>
          </button>
        </div>
      </div>

      {/* Expandable Model & API Settings */}
      {showConfig && (
        <div className="glass-panel rounded-2xl p-4 grid grid-cols-1 md:grid-cols-3 gap-3 border border-sky-500/30 bg-slate-950/80 animate-in fade-in duration-200">
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
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">
              调用模型名称 (Model)
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200"
            >
              <option value="gemini-3.8-flash">gemini-3.8-flash (推荐 · 快速响应)</option>
              <option value="claude-sonnet-5-5">claude-sonnet-5-5 (学术写作强劲)</option>
              <option value="gemini-4-argon">gemini-4-argon (大上下文推理)</option>
              <option value="claude-opus-5-5">claude-opus-5-5 (最高精度深度构思)</option>
            </select>
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

      {/* Prompt Input & Execution */}
      <div className="glass-panel rounded-2xl p-4 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-slate-200 flex items-center gap-2">
            <span>智能体科研指令 / 粘贴文献段落</span>
            {inspection && (
              <span className="font-mono font-normal text-slate-400 text-[11px]">
                · 当前分子: {inspection.file_name} ({inspection.atoms.length} 原子)
              </span>
            )}
          </label>
        </div>

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
              <div className="flex items-center gap-1.5">
                <button
                  onClick={copyReport}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300 hover:text-white transition cursor-pointer flex items-center gap-1"
                  title="复制报告 Markdown"
                >
                  <Copy className="w-3 h-3" />
                  <span>{copied ? '已复制' : '复制'}</span>
                </button>

                <button
                  onClick={downloadMarkdown}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300 hover:text-white transition cursor-pointer flex items-center gap-1"
                  title="下载报告 Markdown 文件"
                >
                  <Download className="w-3 h-3" />
                  <span>下载 .md</span>
                </button>

                <button
                  onClick={exportReportToDisk}
                  className="px-3 py-1 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-[11px] text-emerald-300 hover:bg-emerald-500/30 transition cursor-pointer flex items-center gap-1 font-semibold"
                  title="一键将学术报告导出并保存到分子相同目录下"
                >
                  <FolderCheck className="w-3 h-3" />
                  <span>保存至分子所在目录</span>
                </button>
              </div>
            )}
          </div>

          {exportNotice && (
            <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/35 text-xs text-emerald-200 flex items-center justify-between">
              <span>{exportNotice}</span>
              <button
                onClick={() => setExportNotice(null)}
                className="text-emerald-400 hover:text-white underline text-[11px]"
              >
                关闭
              </button>
            </div>
          )}

          <div className="flex-1 min-h-[380px] max-h-[580px] overflow-y-auto rounded-xl bg-slate-950 p-4 border border-slate-800 font-sans text-xs text-slate-200 leading-relaxed select-text space-y-3">
            {reportMarkdown ? (
              <div className="prose prose-invert max-w-none text-xs leading-relaxed space-y-3 whitespace-pre-wrap font-sans">
                {reportMarkdown}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-xs text-slate-500 p-8 text-center">
                <FileText className="w-10 h-10 text-slate-700 mb-2" />
                <p>学术报告将在此实时生成</p>
                <p className="text-[11px] text-slate-600 mt-1">
                  支持 LaTeX 公式、物理判据定标表格、机理深入剖析与一键本地同目录归档
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
