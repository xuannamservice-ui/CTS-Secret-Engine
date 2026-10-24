"""CTS Lab — Creative Technologies and Simulation Research Studio API Router.

Provides endpoints for the interactive CTS Lab WebUI:
- ``GET /api/cts-lab/overview``: Active CTS FastCore 4-layer pipeline telemetry, research skills catalog, and default Causal JEPA world-model spec.
- ``POST /api/cts-lab/jepa-simulate``: Interactive Monte Carlo Structural Causal Model (SCM) + Latent JEPA rollout simulation across $t+1 \\to t+3 \\to t+H$.
- ``POST /api/cts-lab/sanitize``: MASTER PROMPT v5.4.1 Anti-AI / Claude Markdown sanitizer & V8 JIT style audit.
- ``POST /api/cts-lab/export-docx``: Rule 58 / Nghị định 30/2020/NĐ-CP Word (.docx) document builder and base64 download payload.
"""

from __future__ import annotations

import base64
import importlib.util
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILLS_RESEARCH_DIR = PROJECT_ROOT / "skills" / "research"

router = APIRouter(prefix="/api/cts-lab", tags=["cts-lab"])


def _load_script_module(module_name: str, script_path: Path):
    if not script_path.is_file():
        raise HTTPException(status_code=500, detail=f"Missing CTS Lab script: {script_path}")
    parent_dir = str(script_path.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    spec = importlib.util.spec_from_file_location(module_name, str(script_path))
    if spec is None or spec.loader is None:
        raise HTTPException(status_code=500, detail=f"Unable to load module spec: {script_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


class JepaSimulateRequest(BaseModel):
    spec: Dict[str, Any] = Field(default_factory=dict)
    horizon: int = Field(default=6, ge=2, le=24)
    samples: int = Field(default=250, ge=20, le=2000)
    seed: int = Field(default=42)


class SanitizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    strip_markdown: bool = Field(default=False)
    run_v8_audit: bool = Field(default=True)


class ExportDocxRequest(BaseModel):
    text: str = Field(..., min_length=1)
    title: str = Field(default="")
    sanitize_first: bool = Field(default=True)


def _normalize_jepa_spec(raw_spec: Dict[str, Any], horizon: int, samples: int, seed: int) -> Dict[str, Any]:
    """Normalize either list-based DEMO_SPEC or dict-based interventions spec into canonical simulator format."""
    title = str(raw_spec.get("title") or "Mô phỏng Nhân quả JEPA — CTS Lab")
    raw_states = raw_spec.get("states") or []
    states_list: List[Dict[str, Any]] = []
    if isinstance(raw_states, dict):
        for s_name, s_cfg in raw_states.items():
            states_list.append(
                {
                    "name": str(s_name),
                    "initial": float(s_cfg.get("initial", 0.5)),
                    "target": float(s_cfg.get("target", s_cfg.get("goal", 0.85))),
                    "weight": float(s_cfg.get("weight", 1.0)),
                    "min_bound": float(s_cfg["risk_floor"]) if "risk_floor" in s_cfg else s_cfg.get("min_bound"),
                    "max_bound": s_cfg.get("max_bound"),
                    "noise_std": float(s_cfg.get("noise_std", s_cfg.get("noise", 0.03))),
                }
            )
    else:
        for s in raw_states:
            states_list.append(
                {
                    "name": str(s["name"]),
                    "initial": float(s.get("initial", 0.5)),
                    "target": float(s.get("target", s.get("goal", 0.85))),
                    "weight": float(s.get("weight", 1.0)),
                    "min_bound": s.get("min_bound"),
                    "max_bound": s.get("max_bound"),
                    "noise_std": float(s.get("noise_std", 0.03)),
                }
            )

    raw_actions = raw_spec.get("actions") or raw_spec.get("interventions") or []
    actions_list: List[Dict[str, Any]] = []
    if isinstance(raw_actions, dict):
        for act_id, a_cfg in raw_actions.items():
            effects = dict(a_cfg.get("effects") or a_cfg.get("direct_delta") or {})
            sustained = {k: round(v * 0.35, 4) for k, v in effects.items()}
            actions_list.append(
                {
                    "action_id": str(act_id),
                    "name": str(a_cfg.get("label") or act_id),
                    "description": str(a_cfg.get("description") or ""),
                    "direct_delta": effects,
                    "sustained_delta": dict(a_cfg.get("sustained_delta") or sustained),
                    "lock_in_cost": float(a_cfg.get("lock_in_cost", a_cfg.get("cost", 0.0))),
                }
            )
    else:
        for a in raw_actions:
            actions_list.append(
                {
                    "action_id": str(a.get("action_id") or a.get("name") or "do(a)"),
                    "name": str(a.get("label") or a.get("name") or "do(a)"),
                    "description": str(a.get("description") or ""),
                    "direct_delta": dict(a.get("direct_delta") or {}),
                    "sustained_delta": dict(a.get("sustained_delta") or {}),
                    "lock_in_cost": float(a.get("lock_in_cost", a.get("cost", 0.0))),
                }
            )

    return {
        "title": title,
        "horizon": horizon,
        "mc_samples": samples,
        "seed": seed,
        "states": states_list,
        "causal_edges": list(raw_spec.get("causal_edges") or []),
        "actions": actions_list,
    }


def _polish_academic_typography(text: str) -> str:
    """Apply Rule 47 & Rule 58 typography: curly quotes, en-dash number ranges, and standard bullets."""
    out = text
    # Convert straight double quotes around phrases into curly quotes “...”
    out = re.sub(r'"([^"\n]{1,200})"', r"“\1”", out)
    # Convert numeric ranges like 10-15% or 2024-2026 into en-dash 10–15%, 2024–2026
    out = re.sub(r"(\b\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?(?:\s*%|\b))", r"\1–\2", out)
    return out


@router.get("/overview")
async def get_cts_lab_overview() -> Dict[str, Any]:
    """Return CTS FastCore 4-layer pipeline telemetry, research skills, and default JEPA spec."""
    jepa_mod = _load_script_module(
        "cts_jepa_sim",
        SKILLS_RESEARCH_DIR / "causal-jepa-world-model" / "scripts" / "causal_jepa_simulator.py",
    )

    uvloop_active = False
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        uvloop_active = "uvloop" in type(loop).__module__.lower()
    except Exception:
        pass

    from agent.cts_pipeline import DEFAULT_CTS_AUTO_LOAD_SKILLS

    node_bin = shutil.which("node") or "/home/illusorius/.hermes/tools/node-26.12.1-linux-x64/bin/node"
    check_style_js = SKILLS_RESEARCH_DIR / "avoid-ai-writing" / "scripts" / "check-style.js"

    skills_catalog = []
    for name in [
        "cts-core-kernel",
        "master-academic-writing",
        "causal-jepa-world-model",
        "avoid-ai-writing",
        "claude-markdown-cleaner",
        "ai-writing-detector",
        "voice-preserving-rewriter",
        "preservation-verifier",
    ]:
        skill_md = SKILLS_RESEARCH_DIR / name / "SKILL.md"
        size_kb = round(skill_md.stat().st_size / 1024, 1) if skill_md.is_file() else 0.0
        skills_catalog.append(
            {
                "name": name,
                "installed": skill_md.is_file(),
                "auto_loaded": name in DEFAULT_CTS_AUTO_LOAD_SKILLS,
                "size_kb": size_kb,
                "path": f"skills/research/{name}/SKILL.md",
            }
        )

    return {
        "engine": "CTS Secret Engine — CTS Lab (Creative Technologies and Simulation)",
        "active_model": "CTS Model",
        "provider": "cts",
        "master_prompt_version": "MASTER PROMPT v5.4.1 — FINAL MASTER EDITION (79 Rules)",
        "pipeline_layers": [
            {
                "layer": 1,
                "name": "RAM-Cached Compiled Kernel Auto-Load",
                "module": "agent/skill_commands.py",
                "status": "active",
                "latency_target": "0.02 ms/turn (O(1) RAM cache)",
                "description": "Tự động nạp cts-core-kernel (6.7 KB nén từ 79 quy tắc MASTER PROMPT v5.4.1, Causal JEPA, Anti-AI & Nghị định 30) vào System Prompt.",
            },
            {
                "layer": 2,
                "name": "Causal JEPA & Deep Reasoning Framework",
                "module": "SOUL.md + skills/research/causal-jepa-world-model",
                "status": "active",
                "latency_target": "~11 ms (250 MC rollouts × 6 steps)",
                "description": "Mô hình hóa trạng thái tiềm ẩn s_t = Enc(x_t), toán tử can thiệp do(a_t), dự báo đa tầng t+1 → t+3 → t+H và tối ưu hàm Free-Energy J(a).",
            },
            {
                "layer": 3,
                "name": "Active Self-Critique Stop-Gate + V8 JIT Audit",
                "module": "agent/turn_stop_gates.py",
                "status": "active",
                "latency_target": "< 25 ms",
                "description": "Chặn câu trả lời ngay trước khi xuất nếu phát hiện sáo ngữ AI, từ nối công thức, hoặc cấu trúc nhân quả thiếu đối chiếu phản thực tế; yêu cầu LLM tự biên tập lại.",
            },
            {
                "layer": 4,
                "name": "Deterministic Post-Generation Sanitizer",
                "module": "agent/turn_finalizer.py + agent/cts_pipeline.py",
                "status": "active",
                "latency_target": "0.14 ms/turn",
                "description": "Tự động sửa dấu ngoặc kép thẳng sang ngoặc kép cong (“…”), chuẩn hóa en-dash số liệu (10–15%), gỡ LaTeX đơn vị dư thừa và xóa dấu vết Markdown của Claude.",
            },
        ],
        "runtime": {
            "python_version": sys.version.split()[0],
            "uvloop_active": uvloop_active,
            "v8_node_available": bool(Path(node_bin).is_file() and check_style_js.is_file()),
            "v8_node_binary": node_bin if Path(node_bin).is_file() else "unavailable",
        },
        "skills": skills_catalog,
        "default_jepa_spec": jepa_mod.DEMO_SPEC(),
    }


@router.post("/jepa-simulate")
async def run_jepa_simulation(req: JepaSimulateRequest) -> Dict[str, Any]:
    """Run Monte Carlo Causal JEPA world-model rollout and return structured rankings + Markdown report."""
    t0 = time.perf_counter()
    jepa_mod = _load_script_module(
        "cts_jepa_sim",
        SKILLS_RESEARCH_DIR / "causal-jepa-world-model" / "scripts" / "causal_jepa_simulator.py",
    )
    raw_spec = req.spec if req.spec and req.spec.get("states") else jepa_mod.DEMO_SPEC()
    try:
        norm = _normalize_jepa_spec(raw_spec, req.horizon, req.samples, req.seed)
        states = [jepa_mod.StateDim(**s) for s in norm["states"]]
        initial_map = {s.name: round(s.initial, 4) for s in states}
        target_map = {s.name: s.target for s in states}
        weight_map = {s.name: s.weight for s in states}
        edges = [(e[0], e[1], float(e[2])) for e in norm["causal_edges"]]

        sim = jepa_mod.CausalJEPASimulator(
            states=states,
            causal_edges=edges,
            horizon=req.horizon,
            mc_samples=req.samples,
            seed=req.seed,
        )

        rankings: List[Dict[str, Any]] = []
        for a_dict in norm["actions"]:
            action_spec = jepa_mod.ActionSpec(
                name=a_dict["name"],
                description=a_dict["description"],
                direct_delta=a_dict["direct_delta"],
                sustained_delta=a_dict["sustained_delta"],
                lock_in_cost=a_dict["lock_in_cost"],
            )
            ev = sim.evaluate_action(action_spec)
            full_traj = [initial_map] + list(ev["full_mean_trajectory"])
            std_last = ev["uncertainty_std_long_term"]
            std_traj = [{k: 0.0 for k in initial_map}] + [std_last for _ in range(req.horizon)]

            # Decompose Free-Energy components for UI cards
            last_state = full_traj[-1]
            goal_loss = sum(
                weight_map[k] * ((last_state[k] - target_map[k]) ** 2) for k in initial_map
            )
            uncertainty_loss = sum((std_last.get(k, 0.0) ** 2) for k in initial_map)
            risk_loss = ev["constraint_violation_rate"] * 0.5
            tail_prob = {k: round(ev["constraint_violation_rate"], 4) for k in initial_map}

            rankings.append(
                {
                    "action_id": a_dict["action_id"],
                    "label": a_dict["name"],
                    "description": a_dict["description"],
                    "free_energy": round(float(ev["jepa_free_energy"]), 4),
                    "goal_loss": round(float(goal_loss), 4),
                    "uncertainty_loss": round(float(uncertainty_loss), 4),
                    "risk_loss": round(float(risk_loss), 4),
                    "action_cost": round(float(ev["lock_in_cost"]), 4),
                    "trajectory_mean": full_traj,
                    "trajectory_std": std_traj,
                    "tail_risk_prob": tail_prob,
                }
            )

        rankings.sort(key=lambda x: x["free_energy"])
        ate: Dict[str, float] = {}
        if len(rankings) >= 2:
            best_end = rankings[0]["trajectory_mean"][-1]
            worst_end = rankings[-1]["trajectory_mean"][-1]
            ate = {k: round(best_end[k] - worst_end[k], 4) for k in best_end}

        sim_spec_for_report = {
            "title": norm["title"],
            "horizon": req.horizon,
            "mc_samples": req.samples,
            "seed": req.seed,
            "states": norm["states"],
            "causal_edges": norm["causal_edges"],
            "actions": [
                {
                    "name": a["name"],
                    "description": a["description"],
                    "direct_delta": a["direct_delta"],
                    "sustained_delta": a["sustained_delta"],
                    "lock_in_cost": a["lock_in_cost"],
                }
                for a in norm["actions"]
            ],
        }
        report_md = jepa_mod.run_simulation(sim_spec_for_report, as_json=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Causal JEPA simulation error: {exc}") from exc

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "title": norm["title"],
        "horizon": req.horizon,
        "samples": req.samples,
        "elapsed_ms": elapsed_ms,
        "optimal_action": rankings[0] if rankings else None,
        "rankings": rankings,
        "counterfactual_ate_best_vs_worst": ate,
        "markdown_report": report_md,
    }


@router.post("/sanitize")
async def sanitize_academic_text(req: SanitizeRequest) -> Dict[str, Any]:
    """Audit and sanitize text against MASTER PROMPT v5.4.1, avoid-ai-writing, and Claude Markdown traces."""
    t0 = time.perf_counter()
    cleaner_mod = _load_script_module(
        "cts_md_cleaner",
        SKILLS_RESEARCH_DIR / "claude-markdown-cleaner" / "scripts" / "clean_ai_markdown.py",
    )
    from agent.cts_pipeline import (
        detect_cts_quality_violations,
        run_v8_style_audit,
        sanitize_cts_response,
    )

    raw_findings: List[str] = cleaner_mod.audit_text(req.text)
    structured_findings: List[Dict[str, Any]] = []
    lines_lower = [ln.lower() for ln in req.text.splitlines()]

    for item in raw_findings:
        m = re.match(r"^\[([^\]]+)\]\s*(.*)$", item)
        rule_tag = m.group(1) if m else "MASTER PROMPT v5.4.1"
        desc = m.group(2) if m else item
        quoted = re.search(r"'([^']+)'", desc)
        phrase = quoted.group(1) if quoted else desc
        line_no = 1
        if quoted:
            for idx, ln in enumerate(lines_lower, 1):
                if phrase.lower() in ln:
                    line_no = idx
                    break
        structured_findings.append(
            {
                "category": "anti-ai",
                "rule": rule_tag,
                "match": phrase,
                "line": line_no,
                "suggestion": "Thay bằng dữ kiện thực nghiệm, cơ chế nhân quả cụ thể hoặc diễn đạt học thuật tự nhiên (MASTER PROMPT v5.4.1).",
            }
        )

    pipeline_violations = detect_cts_quality_violations(req.text)
    v8_notes = ""
    if req.run_v8_audit:
        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=True) as tf:
            tf.write(req.text)
            tf.flush()
            v8_notes = run_v8_style_audit(tf.name)

    cleaned_first = sanitize_cts_response(req.text)
    cleaned_md = cleaner_mod.clean_markdown(cleaned_first, strip_markdown=req.strip_markdown)
    cleaned_final = _polish_academic_typography(cleaned_md)

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "original_length": len(req.text),
        "cleaned_length": len(cleaned_final),
        "elapsed_ms": elapsed_ms,
        "total_findings": len(structured_findings),
        "findings": structured_findings,
        "pipeline_violations": [
            {
                "category": "fastcore-gate",
                "rule": "CTS FastCore Gate",
                "match": v,
                "suggestion": "Loại bỏ theo MASTER PROMPT v5.4.1",
            }
            for v in pipeline_violations
        ],
        "v8_audit_notes": v8_notes,
        "cleaned_text": cleaned_final,
    }


@router.post("/export-docx")
async def export_nd30_docx(req: ExportDocxRequest) -> Dict[str, Any]:
    """Generate a Rule 58 / Nghị định 30/2020/NĐ-CP compliant .docx file and return base64 bytes."""
    t0 = time.perf_counter()
    cleaner_mod = _load_script_module(
        "cts_md_cleaner",
        SKILLS_RESEARCH_DIR / "claude-markdown-cleaner" / "scripts" / "clean_ai_markdown.py",
    )
    docx_mod = _load_script_module(
        "cts_docx_nd30",
        SKILLS_RESEARCH_DIR / "claude-markdown-cleaner" / "scripts" / "md_to_docx_nd30.py",
    )
    source_text = (
        _polish_academic_typography(cleaner_mod.clean_markdown(req.text, strip_markdown=False))
        if req.sanitize_first
        else req.text
    )
    if req.title.strip() and not source_text.lstrip().startswith("# "):
        source_text = f"# {req.title.strip()}\n\n{source_text}"

    with tempfile.TemporaryDirectory(prefix="cts_lab_docx_") as tmpdir:
        out_path = Path(tmpdir) / "CTS_Lab_Report_ND30.docx"
        try:
            docx_mod.build_docx(source_text, out_path)
            raw_bytes = out_path.read_bytes()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"DOCX export error: {exc}") from exc

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    safe_slug = (
        "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in (req.title or "CTS_Lab_Document"))
        .strip("_")[:48]
        or "CTS_Lab_Document"
    )
    return {
        "filename": f"{safe_slug}_ND30.docx",
        "size_bytes": len(raw_bytes),
        "elapsed_ms": elapsed_ms,
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "base64_docx": base64.b64encode(raw_bytes).decode("ascii"),
        "cleaned_markdown": source_text,
    }
