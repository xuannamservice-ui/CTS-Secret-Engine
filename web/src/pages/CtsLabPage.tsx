import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Check,
  CheckCircle2,
  Copy,
  Cpu,
  Download,
  GitBranch,
  Layers,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Terminal,
  Wand2,
  Zap,
} from "lucide-react";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";
import { Card, CardContent } from "@nous-research/ui/ui/components/card";
import { Input } from "@nous-research/ui/ui/components/input";
import { Label } from "@nous-research/ui/ui/components/label";
import { Spinner } from "@nous-research/ui/ui/components/spinner";
import { fetchJSON } from "@/lib/api";
import { copyTextToClipboard } from "@/lib/clipboard";
import { cn } from "@/lib/utils";

interface PipelineLayer {
  layer: number;
  name: string;
  module: string;
  status: string;
  latency_target: string;
  description: string;
}

interface SkillCatalogItem {
  name: string;
  installed: boolean;
  auto_loaded: boolean;
  size_kb: number;
  path: string;
}

interface LabOverviewResponse {
  engine: string;
  master_prompt_version: string;
  pipeline_layers: PipelineLayer[];
  runtime: {
    python_version: string;
    uvloop_active: boolean;
    v8_node_available: boolean;
    v8_node_binary: string;
  };
  skills: SkillCatalogItem[];
  default_jepa_spec: Record<string, unknown>;
}

interface JepaActionRanking {
  action_id: string;
  label: string;
  description: string;
  free_energy: number;
  goal_loss: number;
  uncertainty_loss: number;
  risk_loss: number;
  action_cost: number;
  trajectory_mean: Record<string, number>[];
  trajectory_std: Record<string, number>[];
  tail_risk_prob: Record<string, number>;
}

interface JepaSimulateResponse {
  title: string;
  horizon: number;
  samples: number;
  elapsed_ms: number;
  optimal_action: JepaActionRanking | null;
  rankings: JepaActionRanking[];
  counterfactual_ate_best_vs_worst: Record<string, number>;
  markdown_report: string;
}

interface SanitizeFinding {
  category: string;
  rule: string;
  match: string;
  line?: number;
  suggestion: string;
}

interface SanitizeResponse {
  original_length: number;
  cleaned_length: number;
  elapsed_ms: number;
  total_findings: number;
  findings: SanitizeFinding[];
  pipeline_violations: SanitizeFinding[];
  v8_audit_notes: string;
  cleaned_text: string;
}

interface ExportDocxResponse {
  filename: string;
  size_bytes: number;
  elapsed_ms: number;
  mime_type: string;
  base64_docx: string;
  cleaned_markdown: string;
}

const SAMPLE_AI_DRAFT = `# Báo cáo Đánh giá Tác động của Mô hình Nhân quả JEPA trong Nghiên cứu Khoa học

Trong bối cảnh hiện nay, khi cuộc cách mạng công nghiệp 4.0 đang diễn ra mạnh mẽ, trí tuệ nhân tạo đóng vai trò vô cùng quan trọng trong công tác nghiên cứu học thuật. Không thể phủ nhận rằng việc ứng dụng các mô hình dự báo là một giải pháp đột phá và toàn diện nhằm nâng tầm chất lượng công bố quốc tế.

Hơn nữa, mô hình JEPA không chỉ giúp tối ưu hóa quy trình thực nghiệm mà còn mở ra kỷ nguyên mới cho tư duy phản thực tế. Bên cạnh đó, ở nhiệt độ $25^\\circ\\text{C}$, hiệu suất xử lý tăng 15-20% với chi phí khoảng $1,200\\text{ USD}$ trong giai đoạn 2024-2026.

Furthermore, it is important to note that researchers must delve into the multifaceted tapestry of causal inference to leverage seamless, transformative outcomes.

• Luận điểm 1: Tăng cường độ chính xác thực nghiệm thông qua "mô phỏng thế giới ngầm".
• Luận điểm 2: Kiểm soát rủi ro đuôi và sai số hệ thống.
• Luận điểm 3: Chuẩn hóa thể thức trình bày văn bản theo Nghị định 30/2020/NĐ-CP.

Tóm lại, những kết quả này là minh chứng rõ nét khẳng định vị thế tiên phong của hệ thống CTS Secret Engine.`;

const POLICY_JEPA_PRESET = {
  title: "Phân tích Chính sách Tự chủ Đại học & Đầu tư Phòng thí nghiệm Trọng điểm (Causal JEPA)",
  states: {
    research_output: {
      initial: 0.45,
      goal: 0.88,
      weight: 1.6,
      risk_floor: 0.35,
      decay: 0.04,
      noise: 0.03,
    },
    faculty_retention: {
      initial: 0.58,
      goal: 0.85,
      weight: 1.3,
      risk_floor: 0.4,
      decay: 0.03,
      noise: 0.03,
    },
    budget_reserve: {
      initial: 0.72,
      goal: 0.65,
      weight: 1.0,
      risk_floor: 0.3,
      decay: 0.02,
      noise: 0.02,
    },
    governance_friction: {
      initial: 0.42,
      goal: 0.18,
      weight: 1.1,
      risk_floor: 0.0,
      decay: -0.02,
      noise: 0.03,
    },
  },
  causal_edges: [
    ["budget_reserve", "research_output", 0.24],
    ["faculty_retention", "research_output", 0.32],
    ["governance_friction", "faculty_retention", -0.28],
    ["governance_friction", "research_output", -0.22],
    ["research_output", "budget_reserve", 0.16],
  ],
  interventions: {
    targeted_lab_grant_and_autonomy: {
      label: "Cấp vốn Lab trọng điểm theo KPI thực chất + Khoán chi học thuật",
      description:
        "Phân bổ ngân sách theo chất lượng dữ liệu gốc, cắt giảm thủ tục thanh quyết toán hành chính.",
      cost: 0.07,
      effects: {
        research_output: 0.16,
        faculty_retention: 0.14,
        budget_reserve: -0.04,
        governance_friction: -0.15,
      },
    },
    unfocused_mass_funding: {
      label: "Đầu tư dàn trải đồng loạt không kèm cải cách thủ tục",
      description:
        "Tăng chi ngân sách diện rộng nhưng giữ nguyên cơ chế kiểm duyệt nhiều tầng.",
      cost: 0.14,
      effects: {
        research_output: 0.08,
        faculty_retention: 0.02,
        budget_reserve: -0.18,
        governance_friction: 0.09,
      },
    },
    austerity_status_quo: {
      label: "Giữ nguyên hiện trạng & Thắt chặt chi tiêu ngắn hạn",
      description:
        "Ưu tiên bảo toàn quỹ dự phòng ngắn hạn, trì hoãn đầu tư hạ tầng tính toán.",
      cost: 0.02,
      effects: {
        research_output: -0.05,
        faculty_retention: -0.08,
        budget_reserve: 0.07,
        governance_friction: 0.05,
      },
    },
  },
};

export default function CtsLabPage() {
  const [activeTab, setActiveTab] = useState<"jepa" | "sanitizer" | "architecture">("jepa");
  const [overview, setOverview] = useState<LabOverviewResponse | null>(null);
  const [loadingOverview, setLoadingOverview] = useState(true);

  // JEPA state
  const [jepaSpecText, setJepaSpecText] = useState("");
  const [jepaHorizon, setJepaHorizon] = useState(6);
  const [jepaSamples, setJepaSamples] = useState(300);
  const [jepaLoading, setJepaLoading] = useState(false);
  const [jepaError, setJepaError] = useState<string | null>(null);
  const [jepaResult, setJepaResult] = useState<JepaSimulateResponse | null>(null);
  const [selectedActionIdx, setSelectedActionIdx] = useState(0);

  // Sanitizer & DOCX state
  const [draftText, setDraftText] = useState(SAMPLE_AI_DRAFT);
  const [docTitle, setDocTitle] = useState(
    "Báo cáo Phân tích Nhân quả JEPA và Chuẩn hóa Văn bản Học thuật",
  );
  const [stripMarkdown, setStripMarkdown] = useState(false);
  const [sanitizeLoading, setSanitizeLoading] = useState(false);
  const [sanitizeResult, setSanitizeResult] = useState<SanitizeResponse | null>(null);
  const [docxLoading, setDocxLoading] = useState(false);
  const [copiedCleaned, setCopiedCleaned] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);

  const runJepaSimulationWithSpec = useCallback(
    async (specObj: Record<string, unknown>, horizonVal: number, samplesVal: number) => {
      setJepaLoading(true);
      setJepaError(null);
      try {
        const res = await fetchJSON<JepaSimulateResponse>("/api/cts-lab/jepa-simulate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            spec: specObj,
            horizon: horizonVal,
            samples: samplesVal,
            seed: 42,
          }),
        });
        setJepaResult(res);
        setSelectedActionIdx(0);
      } catch (err) {
        setJepaError(err instanceof Error ? err.message : String(err));
      } finally {
        setJepaLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    let cancelled = false;
    setLoadingOverview(true);
    fetchJSON<LabOverviewResponse>("/api/cts-lab/overview")
      .then((data) => {
        if (cancelled) return;
        setOverview(data);
        const pretty = JSON.stringify(data.default_jepa_spec, null, 2);
        setJepaSpecText(pretty);
        void runJepaSimulationWithSpec(data.default_jepa_spec, 6, 300);
      })
      .catch((err) => {
        if (!cancelled) {
          setJepaError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingOverview(false);
      });
    return () => {
      cancelled = true;
    };
  }, [runJepaSimulationWithSpec]);

  const handleRunJepaClick = async () => {
    try {
      const parsed = JSON.parse(jepaSpecText) as Record<string, unknown>;
      await runJepaSimulationWithSpec(parsed, jepaHorizon, jepaSamples);
    } catch (err) {
      setJepaError(
        `Lỗi cú pháp JSON trong cấu hình mô hình nhân quả: ${
          err instanceof Error ? err.message : String(err)
        }`,
      );
    }
  };

  const handleLoadJepaPreset = (preset: "research" | "policy") => {
    const spec =
      preset === "policy"
        ? POLICY_JEPA_PRESET
        : (overview?.default_jepa_spec ?? POLICY_JEPA_PRESET);
    setJepaSpecText(JSON.stringify(spec, null, 2));
    void runJepaSimulationWithSpec(spec, jepaHorizon, jepaSamples);
  };

  const handleRunSanitize = useCallback(async () => {
    if (!draftText.trim()) return;
    setSanitizeLoading(true);
    try {
      const res = await fetchJSON<SanitizeResponse>("/api/cts-lab/sanitize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: draftText,
          strip_markdown: stripMarkdown,
          run_v8_audit: true,
        }),
      });
      setSanitizeResult(res);
    } finally {
      setSanitizeLoading(false);
    }
  }, [draftText, stripMarkdown]);

  const handleExportDocx = async (textToExport?: string, customTitle?: string) => {
    const payloadText = textToExport ?? sanitizeResult?.cleaned_text ?? draftText;
    if (!payloadText.trim()) return;
    setDocxLoading(true);
    try {
      const res = await fetchJSON<ExportDocxResponse>("/api/cts-lab/export-docx", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: payloadText,
          title: customTitle ?? docTitle,
          sanitize_first: true,
        }),
      });
      const binary = atob(res.base64_docx);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: res.mime_type });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = res.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setDocxLoading(false);
    }
  };

  const handleSendJepaReportToSanitizer = () => {
    if (!jepaResult?.markdown_report) return;
    setDraftText(jepaResult.markdown_report);
    setDocTitle(jepaResult.title);
    setActiveTab("sanitizer");
  };

  const activeRanking =
    jepaResult?.rankings?.[selectedActionIdx] ?? jepaResult?.optimal_action ?? null;

  return (
    <div className="flex flex-col gap-6">
      {/* Flagship CTS Lab Header Banner */}
      <div className="relative overflow-hidden border border-midground/30 bg-background-elevated/70 p-5 sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 border border-midground bg-midground/15 px-2.5 py-0.5 font-mono text-xs font-extrabold tracking-widest text-midground uppercase">
                <Sparkles className="h-3.5 w-3.5" />
                CTS LAB STUDIO v1.6
              </span>
              <Badge className="border border-current/25 font-mono text-xs">
                MASTER PROMPT v5.4.1 (79 RULES)
              </Badge>
              <Badge className="border border-current/25 font-mono text-xs">
                CAUSAL JEPA WORLD-MODEL
              </Badge>
              <Badge className="border border-current/25 font-mono text-xs">
                NGHỊ ĐỊNH 30/2020/NĐ-CP DOCX
              </Badge>
            </div>

            <h1 className="font-sans text-xl font-bold tracking-wide text-text-primary sm:text-2xl">
              CTS Lab — Không gian Nghiên cứu Khoa học, Mô phỏng Nhân quả JEPA & Chuẩn hóa Học thuật
            </h1>
            <p className="max-w-4xl text-sm leading-relaxed text-text-secondary">
              Hệ thống tích hợp mô hình thế giới ngầm nhân quả{" "}
              <span className="font-mono text-text-primary">
                s_t = Enc(x_t), do(a_t) → ŝ_(t+H)
              </span>{" "}
              để lượng hóa hệ quả quyết định theo đa tầng thời gian, kết hợp bộ lọc chống văn phong AI (
              <span className="font-mono text-text-primary">MASTER PROMPT v5.4.1</span>), xóa dấu vết Markdown của Claude và xuất bản trực tiếp hồ sơ Word{" "}
              <span className="font-mono text-text-primary">.docx</span> chuẩn Quy tắc 58.
            </p>
          </div>

          <div className="flex shrink-0 flex-wrap items-center gap-2.5">
            <Link to="/chat">
              <Button size="sm" className="gap-2 font-mono text-xs uppercase tracking-wider">
                <Terminal className="h-3.5 w-3.5" />
                Mở Terminal Nghiên cứu (/chat)
              </Button>
            </Link>
            <Link to="/skills">
              <Button
                ghost
                size="sm"
                className="gap-2 border border-current/25 font-mono text-xs uppercase tracking-wider"
              >
                <BookOpen className="h-3.5 w-3.5" />
                Quản lý Skills ({overview?.skills?.length ?? 8})
              </Button>
            </Link>
          </div>
        </div>

        {/* Studio Navigation Tabs */}
        <div className="mt-5 flex flex-wrap gap-2 border-t border-current/15 pt-4">
          <button
            type="button"
            onClick={() => setActiveTab("jepa")}
            className={cn(
              "inline-flex items-center gap-2 px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer",
              activeTab === "jepa"
                ? "border border-midground bg-midground/15 text-midground"
                : "border border-current/15 text-text-secondary hover:text-text-primary",
            )}
          >
            <GitBranch className="h-3.5 w-3.5" />
            1. Mô phỏng Nhân quả JEPA (World-Model)
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("sanitizer")}
            className={cn(
              "inline-flex items-center gap-2 px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer",
              activeTab === "sanitizer"
                ? "border border-midground bg-midground/15 text-midground"
                : "border border-current/15 text-text-secondary hover:text-text-primary",
            )}
          >
            <Wand2 className="h-3.5 w-3.5" />
            2. Xưởng Biên tập Chống AI & Xuất Word Nghị định 30
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("architecture")}
            className={cn(
              "inline-flex items-center gap-2 px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer",
              activeTab === "architecture"
                ? "border border-midground bg-midground/15 text-midground"
                : "border border-current/15 text-text-secondary hover:text-text-primary",
            )}
          >
            <Layers className="h-3.5 w-3.5" />
            3. Kiến trúc CTS FastCore 4 Tầng & Telemetry
          </button>
        </div>
      </div>

      {/* TAB 1: CAUSAL JEPA WORLD-MODEL STUDIO */}
      {activeTab === "jepa" && (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
          {/* Left Column: Spec Editor & Simulation Controls */}
          <Card className="xl:col-span-5">
            <CardContent className="flex flex-col gap-4 p-5">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-midground" />
                  <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-text-primary">
                    Cấu hình Đồ thị Nhân quả SCM + JEPA
                  </h2>
                </div>
                <div className="flex items-center gap-1.5">
                  <Button
                    ghost
                    size="sm"
                    onClick={() => handleLoadJepaPreset("research")}
                    className="border border-current/20 px-2.5 py-1 font-mono text-[11px]"
                  >
                    Mẫu Nghiên cứu Q1
                  </Button>
                  <Button
                    ghost
                    size="sm"
                    onClick={() => handleLoadJepaPreset("policy")}
                    className="border border-current/20 px-2.5 py-1 font-mono text-[11px]"
                  >
                    Mẫu Chính sách ĐH
                  </Button>
                </div>
              </div>

              <div className="rounded border border-current/15 bg-background-base/60 p-3 font-mono text-xs text-text-secondary">
                <div>
                  • Biểu diễn trạng thái ngầm:{" "}
                  <span className="text-text-primary">s_t = Enc(x_t) ∈ [0, 1]^d</span>
                </div>
                <div>
                  • Dự báo can thiệp:{" "}
                  <span className="text-text-primary">
                    ŝ_(t+k) = Pred(ŝ_(t+k-1), do(a_t), z_(t+k))
                  </span>
                </div>
                <div>
                  • Hàm mục tiêu Free-Energy:{" "}
                  <span className="text-text-primary">
                    J(a) = Σ γ^k [w_g‖ŝ - s*‖² + w_u·Var(ŝ) + w_r·Risk(ŝ)]
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="font-mono text-xs">
                    Tầm nhìn dự báo (Horizon H: 2–24 bước)
                  </Label>
                  <Input
                    type="number"
                    min={2}
                    max={24}
                    value={jepaHorizon}
                    onChange={(e) =>
                      setJepaHorizon(Math.max(2, Math.min(24, Number(e.target.value) || 6)))
                    }
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                <div>
                  <Label className="font-mono text-xs">
                    Số quỹ đạo Monte Carlo (Samples N)
                  </Label>
                  <Input
                    type="number"
                    min={50}
                    max={2000}
                    step={50}
                    value={jepaSamples}
                    onChange={(e) =>
                      setJepaSamples(Math.max(50, Math.min(2000, Number(e.target.value) || 300)))
                    }
                    className="mt-1 font-mono text-sm"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <Label className="font-mono text-xs">
                  Đặc tả JSON (`states`, `causal_edges`, `interventions`)
                </Label>
                <textarea
                  value={jepaSpecText}
                  onChange={(e) => setJepaSpecText(e.target.value)}
                  rows={18}
                  spellCheck={false}
                  className="w-full rounded border border-current/20 bg-background-base p-3 font-mono text-xs leading-relaxed text-text-primary focus:border-midground focus:outline-none"
                />
              </div>

              {jepaError && (
                <div className="flex items-start gap-2 rounded border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-300">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{jepaError}</span>
                </div>
              )}

              <Button
                onClick={() => void handleRunJepaClick()}
                disabled={jepaLoading}
                className="w-full gap-2 font-mono text-xs font-bold uppercase tracking-wider"
              >
                {jepaLoading ? <Spinner /> : <Play className="h-4 w-4" />}
                Chạy Mô phỏng Nhân quả JEPA ({jepaSamples} Quỹ đạo × {jepaHorizon} Bước)
              </Button>
            </CardContent>
          </Card>

          {/* Right Column: Rollout Results, Trajectories & Counterfactual ATE */}
          <div className="flex flex-col gap-6 xl:col-span-7">
            {loadingOverview && !jepaResult ? (
              <Card>
                <CardContent className="flex min-h-[16rem] items-center justify-center gap-2 p-6">
                  <Spinner />
                  <span className="font-mono text-sm text-text-secondary">
                    Đang khởi tạo mô hình nhân quả JEPA...
                  </span>
                </CardContent>
              </Card>
            ) : jepaResult ? (
              <>
                {/* Optimal Decision Highlight Card */}
                {jepaResult.optimal_action && (
                  <Card className="border-midground/50 bg-midground/5">
                    <CardContent className="flex flex-col gap-4 p-5">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <Badge className="bg-midground font-mono text-xs font-bold text-background-base">
                            QUYẾT ĐỊNH TỐI ƯU do(a*)
                          </Badge>
                          <span className="font-mono text-xs text-text-secondary">
                            Thời gian tính toán: {jepaResult.elapsed_ms} ms
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            ghost
                            size="sm"
                            onClick={handleSendJepaReportToSanitizer}
                            className="gap-1.5 border border-current/25 font-mono text-xs"
                          >
                            <Wand2 className="h-3.5 w-3.5" />
                            Chuyển sang Xưởng Biên tập
                          </Button>
                          <Button
                            size="sm"
                            disabled={docxLoading}
                            onClick={() =>
                              void handleExportDocx(jepaResult.markdown_report, jepaResult.title)
                            }
                            className="gap-1.5 font-mono text-xs"
                          >
                            <Download className="h-3.5 w-3.5" />
                            Xuất Word (.docx) Nghị định 30
                          </Button>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-bold text-text-primary">
                          {jepaResult.optimal_action.label}{" "}
                          <span className="font-mono text-xs font-normal text-midground">
                            [{jepaResult.optimal_action.action_id}]
                          </span>
                        </h3>
                        <p className="mt-1 text-sm text-text-secondary">
                          {jepaResult.optimal_action.description}
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                        <div className="rounded border border-current/15 bg-background-base/70 p-3">
                          <div className="font-mono text-[11px] uppercase text-text-secondary">
                            Tổng năng lượng J(a*)
                          </div>
                          <div className="mt-1 font-mono text-lg font-bold text-midground">
                            {jepaResult.optimal_action.free_energy.toFixed(4)}
                          </div>
                          <div className="text-[11px] text-text-tertiary">
                            Càng thấp càng tối ưu
                          </div>
                        </div>
                        <div className="rounded border border-current/15 bg-background-base/70 p-3">
                          <div className="font-mono text-[11px] uppercase text-text-secondary">
                            Độ lệch Mục tiêu
                          </div>
                          <div className="mt-1 font-mono text-lg font-bold text-text-primary">
                            {jepaResult.optimal_action.goal_loss.toFixed(4)}
                          </div>
                          <div className="text-[11px] text-text-tertiary">
                            ‖ŝ_(t+k) - s*‖₂²
                          </div>
                        </div>
                        <div className="rounded border border-current/15 bg-background-base/70 p-3">
                          <div className="font-mono text-[11px] uppercase text-text-secondary">
                            Bất định Nhận thức
                          </div>
                          <div className="mt-1 font-mono text-lg font-bold text-text-primary">
                            {jepaResult.optimal_action.uncertainty_loss.toFixed(4)}
                          </div>
                          <div className="text-[11px] text-text-tertiary">
                            Phương sai quỹ đạo MC
                          </div>
                        </div>
                        <div className="rounded border border-current/15 bg-background-base/70 p-3">
                          <div className="font-mono text-[11px] uppercase text-text-secondary">
                            Phạt Rủi ro Đuôi
                          </div>
                          <div className="mt-1 font-mono text-lg font-bold text-text-primary">
                            {jepaResult.optimal_action.risk_loss.toFixed(4)}
                          </div>
                          <div className="text-[11px] text-text-tertiary">
                            Vi phạm ngưỡng an toàn
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Action Ranking Selector Table */}
                <Card>
                  <CardContent className="flex flex-col gap-4 p-5">
                    <div className="flex items-center justify-between">
                      <h3 className="font-mono text-sm font-bold uppercase tracking-wider text-text-primary">
                        Bảng Xếp hạng Phương án Can thiệp Nhân quả do(a_t)
                      </h3>
                      <span className="font-mono text-xs text-text-secondary">
                        Nhấn vào từng phương án để xem quỹ đạo t+1 → t+{jepaResult.horizon}
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse text-left font-mono text-xs">
                        <thead>
                          <tr className="border-b border-current/20 text-text-secondary">
                            <th className="py-2 pr-3">Hạng</th>
                            <th className="py-2 pr-3">Phương án do(a)</th>
                            <th className="py-2 pr-3">Free-Energy J(a)</th>
                            <th className="py-2 pr-3">Độ lệch Mục tiêu</th>
                            <th className="py-2 pr-3">Rủi ro Đuôi</th>
                            <th className="py-2">Chi phí</th>
                          </tr>
                        </thead>
                        <tbody>
                          {jepaResult.rankings.map((r, idx) => {
                            const selected = idx === selectedActionIdx;
                            return (
                              <tr
                                key={r.action_id}
                                onClick={() => setSelectedActionIdx(idx)}
                                className={cn(
                                  "cursor-pointer border-b border-current/10 transition-colors",
                                  selected
                                    ? "bg-midground/15 text-text-primary"
                                    : "hover:bg-current/5 text-text-secondary",
                                )}
                              >
                                <td className="py-2.5 pr-3 font-bold">
                                  #{idx + 1} {idx === 0 && "★"}
                                </td>
                                <td className="py-2.5 pr-3 font-sans font-medium text-text-primary">
                                  {r.label}
                                </td>
                                <td className="py-2.5 pr-3 font-bold text-midground">
                                  {r.free_energy.toFixed(4)}
                                </td>
                                <td className="py-2.5 pr-3">{r.goal_loss.toFixed(4)}</td>
                                <td className="py-2.5 pr-3">{r.risk_loss.toFixed(4)}</td>
                                <td className="py-2.5">{r.action_cost.toFixed(3)}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>

                {/* Multi-Horizon Trajectory Inspector */}
                {activeRanking && (
                  <Card>
                    <CardContent className="flex flex-col gap-4 p-5">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h3 className="font-mono text-sm font-bold uppercase tracking-wider text-text-primary">
                          Quỹ đạo Trạng thái Ngầm Đa tầng:{" "}
                          <span className="text-midground">{activeRanking.label}</span>
                        </h3>
                        <Badge className="border border-current/25 font-mono text-xs">
                          t=0 → t+1 → t+{Math.max(2, Math.floor(jepaResult.horizon / 2))} → t+
                          {jepaResult.horizon}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        {Object.keys(activeRanking.trajectory_mean[0] ?? {}).map((stateName) => {
                          const H = jepaResult.horizon;
                          const mid = Math.max(2, Math.floor(H / 2));
                          const v0 = activeRanking.trajectory_mean[0]?.[stateName] ?? 0;
                          const v1 = activeRanking.trajectory_mean[1]?.[stateName] ?? 0;
                          const vMid = activeRanking.trajectory_mean[mid]?.[stateName] ?? 0;
                          const vH = activeRanking.trajectory_mean[H]?.[stateName] ?? 0;
                          const stdH = activeRanking.trajectory_std[H]?.[stateName] ?? 0;
                          const tailProb =
                            (activeRanking.tail_risk_prob?.[stateName] ?? 0) * 100;
                          const ateVal =
                            jepaResult.counterfactual_ate_best_vs_worst?.[stateName];

                          return (
                            <div
                              key={stateName}
                              className="flex flex-col gap-2 rounded border border-current/15 bg-background-base/50 p-3.5"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-mono text-xs font-bold text-text-primary">
                                  {stateName}
                                </span>
                                {ateVal !== undefined && (
                                  <span
                                    className={cn(
                                      "font-mono text-[11px] font-semibold",
                                      ateVal >= 0 ? "text-emerald-400" : "text-amber-400",
                                    )}
                                  >
                                    ATE Δ(a* vs worst): {ateVal >= 0 ? "+" : ""}
                                    {ateVal.toFixed(3)}
                                  </span>
                                )}
                              </div>

                              <div className="space-y-1.5 font-mono text-[11px]">
                                {[
                                  { label: "t = 0 (Hiện tại)", val: v0 },
                                  { label: "t + 1 (Ngắn hạn)", val: v1 },
                                  { label: `t + ${mid} (Trung hạn)`, val: vMid },
                                  {
                                    label: `t + ${H} (Dài hạn ±${stdH.toFixed(2)})`,
                                    val: vH,
                                  },
                                ].map((step) => (
                                  <div key={step.label} className="flex items-center gap-2">
                                    <span className="w-36 shrink-0 text-text-secondary">
                                      {step.label}
                                    </span>
                                    <div className="h-2 flex-1 overflow-hidden rounded-sm bg-current/10">
                                      <div
                                        className="h-full bg-midground transition-all duration-300"
                                        style={{
                                          width: `${Math.max(
                                            2,
                                            Math.min(100, Math.round(step.val * 100)),
                                          )}%`,
                                        }}
                                      />
                                    </div>
                                    <span className="w-12 text-right font-bold text-text-primary">
                                      {step.val.toFixed(3)}
                                    </span>
                                  </div>
                                ))}
                              </div>

                              <div className="mt-1 flex items-center justify-between border-t border-current/10 pt-1.5 font-mono text-[11px] text-text-tertiary">
                                <span>Xác suất vi phạm ngưỡng rủi ro đuôi:</span>
                                <span
                                  className={cn(
                                    "font-bold",
                                    tailProb > 15 ? "text-red-400" : "text-emerald-400",
                                  )}
                                >
                                  {tailProb.toFixed(1)}%
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Markdown Report Preview */}
                      <div className="mt-2 flex flex-col gap-2">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs font-bold uppercase text-text-secondary">
                            Báo cáo Phân tích Nhân quả JEPA (Chuẩn học thuật)
                          </span>
                          <Button
                            ghost
                            size="sm"
                            onClick={() => {
                              void copyTextToClipboard(jepaResult.markdown_report);
                              setCopiedReport(true);
                              setTimeout(() => setCopiedReport(false), 2000);
                            }}
                            className="gap-1.5 border border-current/20 px-2.5 py-1 font-mono text-xs"
                          >
                            {copiedReport ? (
                              <Check className="h-3.5 w-3.5" />
                            ) : (
                              <Copy className="h-3.5 w-3.5" />
                            )}
                            {copiedReport ? "Đã sao chép" : "Sao chép Báo cáo"}
                          </Button>
                        </div>
                        <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded border border-current/15 bg-background-base p-3.5 font-mono text-xs leading-relaxed text-text-secondary">
                          {jepaResult.markdown_report}
                        </pre>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : null}
          </div>
        </div>
      )}

      {/* TAB 2: MASTER PROMPT v5.4.1 ANTI-AI & CLAUDE MARKDOWN SANITIZER STUDIO */}
      {activeTab === "sanitizer" && (
        <div className="flex flex-col gap-6">
          <Card>
            <CardContent className="flex flex-col gap-4 p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-text-primary">
                    Xưởng Kiểm định Chống Văn phong AI, Xóa Dấu vết Markdown Claude & Xuất Word Nghị định 30
                  </h2>
                  <p className="mt-0.5 text-xs text-text-secondary">
                    Áp dụng trực tiếp 79 Quy tắc của{" "}
                    <span className="font-mono text-text-primary">MASTER PROMPT v5.4.1</span>, bộ quy tắc{" "}
                    <span className="font-mono text-text-primary">conorbronsdon/avoid-ai-writing</span>, V8 JIT{" "}
                    <span className="font-mono text-text-primary">check-style.js</span> và trình dựng{" "}
                    <span className="font-mono text-text-primary">.docx</span> chuẩn Quy tắc 58 (A4, Times New Roman 13pt, căn đều Justified, giãn dòng Multiple 1.3).
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    ghost
                    size="sm"
                    onClick={() => {
                      setDraftText(SAMPLE_AI_DRAFT);
                      setSanitizeResult(null);
                    }}
                    className="gap-1.5 border border-current/20 font-mono text-xs"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    Nạp Văn bản Mẫu có Lỗi AI
                  </Button>

                  <Button
                    onClick={() => void handleRunSanitize()}
                    disabled={sanitizeLoading}
                    size="sm"
                    className="gap-1.5 font-mono text-xs font-bold uppercase tracking-wider"
                  >
                    {sanitizeLoading ? <Spinner /> : <Wand2 className="h-3.5 w-3.5" />}
                    Kiểm định & Làm sạch Chuẩn v5.4.1
                  </Button>

                  <Button
                    onClick={() => void handleExportDocx()}
                    disabled={docxLoading}
                    size="sm"
                    className="gap-1.5 border border-midground bg-midground/20 font-mono text-xs font-bold uppercase tracking-wider text-midground hover:bg-midground/30"
                  >
                    {docxLoading ? <Spinner /> : <Download className="h-3.5 w-3.5" />}
                    Xuất File Word (.docx) Nghị định 30
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div className="sm:col-span-2">
                  <Label className="font-mono text-xs">
                    Tiêu đề Tài liệu / Báo cáo Khoa học (in đậm 15pt trong file .docx)
                  </Label>
                  <Input
                    value={docTitle}
                    onChange={(e) => setDocTitle(e.target.value)}
                    placeholder="Nhập tiêu đề báo cáo nghiên cứu hoặc tờ trình chính sách..."
                    className="mt-1 font-sans text-sm"
                  />
                </div>
                <div className="flex items-end pb-1">
                  <label className="flex cursor-pointer items-center gap-2 text-xs text-text-secondary">
                    <input
                      type="checkbox"
                      checked={stripMarkdown}
                      onChange={(e) => setStripMarkdown(e.target.checked)}
                      className="h-4 w-4 accent-midground"
                    />
                    <span>
                      Gỡ toàn bộ ký hiệu Markdown (`#`, `**`, `` ` ``) thành văn bản thuần (Plain-Text)
                    </span>
                  </label>
                </div>
              </div>

              {/* Side-by-side Draft vs Cleaned Output */}
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between">
                    <Label className="font-mono text-xs uppercase text-text-secondary">
                      Bản thảo Đầu vào (Tiếng Việt / Tiếng Anh)
                    </Label>
                    <span className="font-mono text-[11px] text-text-tertiary">
                      {draftText.length} ký tự
                    </span>
                  </div>
                  <textarea
                    value={draftText}
                    onChange={(e) => setDraftText(e.target.value)}
                    rows={16}
                    className="w-full rounded border border-current/20 bg-background-base p-3.5 font-sans text-sm leading-relaxed text-text-primary focus:border-midground focus:outline-none"
                    placeholder="Dán bản thảo bài báo khoa học, đề cương nghiên cứu, hoặc văn bản do Claude/GPT sinh ra vào đây..."
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between">
                    <Label className="font-mono text-xs uppercase text-midground">
                      Văn bản Đã Làm sạch (Chuẩn Hoá Dấu câu, Số liệu & Xóa Dấu vết Claude)
                    </Label>
                    <div className="flex items-center gap-2">
                      {sanitizeResult && (
                        <span className="font-mono text-[11px] text-text-tertiary">
                          Xử lý trong {sanitizeResult.elapsed_ms} ms
                        </span>
                      )}
                      <Button
                        ghost
                        size="sm"
                        disabled={!sanitizeResult?.cleaned_text}
                        onClick={() => {
                          if (!sanitizeResult?.cleaned_text) return;
                          void copyTextToClipboard(sanitizeResult.cleaned_text);
                          setCopiedCleaned(true);
                          setTimeout(() => setCopiedCleaned(false), 2000);
                        }}
                        className="gap-1 border border-current/20 px-2 py-0.5 font-mono text-[11px]"
                      >
                        {copiedCleaned ? (
                          <Check className="h-3 w-3" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                        {copiedCleaned ? "Đã chép" : "Sao chép"}
                      </Button>
                    </div>
                  </div>
                  <textarea
                    readOnly
                    value={
                      sanitizeResult?.cleaned_text ??
                      "Nhấn nút «Kiểm định & Làm sạch Chuẩn v5.4.1» để xem văn bản sau khi chuẩn hóa dấu ngoặc kép cong (“…”), en-dash số liệu (15–20%), gỡ LaTeX đơn vị dư thừa (25 °C, 1,200 USD) và kiểm định sáo ngữ AI."
                    }
                    rows={16}
                    className="w-full rounded border border-midground/40 bg-background-base/90 p-3.5 font-sans text-sm leading-relaxed text-text-primary focus:outline-none"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Findings & Style Audit Report */}
          {sanitizeResult && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
              <Card className="lg:col-span-8">
                <CardContent className="flex flex-col gap-3 p-5">
                  <div className="flex items-center justify-between">
                    <h3 className="font-mono text-sm font-bold uppercase tracking-wider text-text-primary">
                      Danh mục Phát hiện Vi phạm Quy tắc Chống AI ({sanitizeResult.total_findings} mục)
                    </h3>
                    <Badge
                      className={cn(
                        "border font-mono text-xs",
                        sanitizeResult.total_findings === 0
                          ? "border-emerald-500/50 text-emerald-400"
                          : "border-amber-500/50 text-amber-300",
                      )}
                    >
                      {sanitizeResult.total_findings === 0
                        ? "ĐẠT CHUẨN MASTER PROMPT v5.4.1"
                        : `PHÁT HIỆN ${sanitizeResult.total_findings} DẤU VẾT CẦN LƯU Ý`}
                    </Badge>
                  </div>

                  {sanitizeResult.findings.length === 0 ? (
                    <div className="flex items-center gap-2 rounded border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-300">
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                      <span>
                        Không phát hiện sáo ngữ mở bài, từ vựng sáo rỗng hay dấu vết định dạng máy móc của Claude/GPT.
                      </span>
                    </div>
                  ) : (
                    <div className="max-h-80 overflow-y-auto">
                      <table className="w-full border-collapse text-left text-xs">
                        <thead>
                          <tr className="border-b border-current/20 font-mono text-text-secondary">
                            <th className="py-2 pr-3">Dòng</th>
                            <th className="py-2 pr-3">Quy tắc MASTER PROMPT</th>
                            <th className="py-2 pr-3">Cụm từ Phát hiện</th>
                            <th className="py-2">Hướng xử lý học thuật</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sanitizeResult.findings.map((f, idx) => (
                            <tr key={idx} className="border-b border-current/10">
                              <td className="py-2 pr-3 font-mono text-text-tertiary">
                                #{f.line ?? "-"}
                              </td>
                              <td className="py-2 pr-3 font-mono font-semibold text-midground">
                                {f.rule}
                              </td>
                              <td className="py-2 pr-3 font-mono text-amber-300">
                                “{f.match}”
                              </td>
                              <td className="py-2 text-text-secondary">{f.suggestion}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="lg:col-span-4">
                <CardContent className="flex flex-col gap-3 p-5">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-midground" />
                    <h3 className="font-mono text-sm font-bold uppercase tracking-wider text-text-primary">
                      Báo cáo V8 JIT Style Audit (`check-style.js`)
                    </h3>
                  </div>
                  <pre className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded border border-current/15 bg-background-base p-3.5 font-mono text-xs leading-relaxed text-text-secondary">
                    {sanitizeResult.v8_audit_notes ||
                      "Không phát hiện cảnh báo bổ sung từ bộ quét V8 JIT."}
                  </pre>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: CTS FASTCORE 4-LAYER ARCHITECTURE & RESEARCH SKILLS */}
      {activeTab === "architecture" && overview && (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {overview.pipeline_layers.map((layer) => (
              <Card key={layer.layer} className="border-current/20">
                <CardContent className="flex h-full flex-col justify-between gap-3 p-5">
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <Badge className="bg-midground/20 font-mono text-xs text-midground">
                        TẦNG {layer.layer}
                      </Badge>
                      <span className="font-mono text-[11px] text-emerald-400">
                        ● {layer.latency_target}
                      </span>
                    </div>
                    <h3 className="font-sans text-base font-bold text-text-primary">
                      {layer.name}
                    </h3>
                    <div className="font-mono text-[11px] text-text-tertiary">
                      Module: {layer.module}
                    </div>
                    <p className="text-xs leading-relaxed text-text-secondary">
                      {layer.description}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5 border-t border-current/10 pt-2 font-mono text-[11px] text-emerald-400">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Trạng thái: ĐANG KÍCH HOẠT (ACTIVE)
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <Card className="lg:col-span-8">
              <CardContent className="flex flex-col gap-4 p-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-mono text-sm font-bold uppercase tracking-wider text-text-primary">
                    Bộ Kỹ năng Nghiên cứu Khoa học Tích hợp (`skills/research/`)
                  </h3>
                  <Link to="/skills">
                    <Button
                      ghost
                      size="sm"
                      className="gap-1 border border-current/20 font-mono text-xs"
                    >
                      Mở Trình quản lý Skills <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-left font-mono text-xs">
                    <thead>
                      <tr className="border-b border-current/20 text-text-secondary">
                        <th className="py-2 pr-3">Tên Kỹ năng (Skill)</th>
                        <th className="py-2 pr-3">Chế độ Nạp</th>
                        <th className="py-2 pr-3">Dung lượng</th>
                        <th className="py-2">Đường dẫn</th>
                      </tr>
                    </thead>
                    <tbody>
                      {overview.skills.map((s) => (
                        <tr key={s.name} className="border-b border-current/10">
                          <td className="py-2.5 pr-3 font-bold text-text-primary">{s.name}</td>
                          <td className="py-2.5 pr-3">
                            {s.auto_loaded ? (
                              <span className="text-emerald-400">
                                ★ Auto-Load RAM Cache (Mọi lượt)
                              </span>
                            ) : (
                              <span className="text-text-secondary">Nạp theo ngữ cảnh</span>
                            )}
                          </td>
                          <td className="py-2.5 pr-3">{s.size_kb} KB</td>
                          <td className="py-2.5 text-text-tertiary">{s.path}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-4">
              <CardContent className="flex flex-col gap-3 p-5">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-midground" />
                  <h3 className="font-mono text-sm font-bold uppercase tracking-wider text-text-primary">
                    Thông số Runtime Tối ưu Hóa
                  </h3>
                </div>
                <div className="space-y-2.5 font-mono text-xs">
                  <div className="flex items-center justify-between border-b border-current/10 pb-2">
                    <span className="text-text-secondary">Python Engine:</span>
                    <span className="font-bold text-text-primary">
                      Python {overview.runtime.python_version} (.pyc Level-1)
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-current/10 pb-2">
                    <span className="text-text-secondary">Cython Event Loop (`uvloop`):</span>
                    <span className="font-bold text-emerald-400">
                      {overview.runtime.uvloop_active ? "ĐANG BẬT (ACTIVE)" : "SẴN SÀNG"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-current/10 pb-2">
                    <span className="text-text-secondary">V8 JIT Regex Sidecar:</span>
                    <span className="font-bold text-emerald-400">
                      {overview.runtime.v8_node_available ? "READY (Node v26)" : "FALLBACK"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pb-1">
                    <span className="text-text-secondary">Chuẩn Trình bày Văn bản:</span>
                    <span className="font-bold text-midground">
                      Quy tắc 58 / NĐ 30/2020
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
