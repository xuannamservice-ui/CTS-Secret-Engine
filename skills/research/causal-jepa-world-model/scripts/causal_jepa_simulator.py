#!/usr/bin/env python3
"""Causal JEPA (Joint-Embedding Predictive Architecture) World-Model & Counterfactual Decision Simulator.

Simulates multi-horizon latent state trajectories s_{t+1..t+H} under causal interventions do(a_t)
and latent environment uncertainty z_t, computing:
1. 1st-order (t+1), 2nd-order (mid-horizon), and 3rd-order (long-horizon equilibrium) state predictions.
2. Counterfactual Average Treatment Effects (ATE) relative to baseline do(a_0).
3. JEPA Free-Energy / Cost functional J(a) = Goal_Error + Risk_Penalty + Constraint_Penalty + LockIn_Cost.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StateDim:
    name: str
    initial: float
    target: float
    weight: float = 1.0
    min_bound: float | None = None
    max_bound: float | None = None
    noise_std: float = 0.03


@dataclass
class ActionSpec:
    name: str
    description: str
    direct_delta: dict[str, float]
    sustained_delta: dict[str, float]
    lock_in_cost: float = 0.0


def _clamp(val: float, lo: float = -10.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, val))


class CausalJEPASimulator:
    """Latent-space Joint-Embedding Predictor with structural causal transition dynamics."""

    def __init__(
        self,
        states: list[StateDim],
        causal_edges: list[tuple[str, str, float]],
        horizon: int = 6,
        discount: float = 0.92,
        damping: float = 0.85,
        risk_aversion: float = 0.5,
        mc_samples: int = 200,
        seed: int = 42,
    ) -> None:
        self.states = states
        self.state_index = {s.name: i for i, s in enumerate(states)}
        self.d = len(states)
        self.horizon = horizon
        self.discount = discount
        self.damping = damping
        self.risk_aversion = risk_aversion
        self.mc_samples = mc_samples
        self.seed = seed

        # Build structural causal transition matrix W (src -> dst)
        self.W = [[0.0] * self.d for _ in range(self.d)]
        for src, dst, weight in causal_edges:
            if src in self.state_index and dst in self.state_index:
                i = self.state_index[src]
                j = self.state_index[dst]
                self.W[i][j] = float(weight)

    def _step_predictor(
        self,
        s_prev: list[float],
        s_init: list[float],
        action: ActionSpec,
        step_k: int,
        rng: random.Random,
    ) -> list[float]:
        """JEPA Predictor P_phi(s_{t+k-1}, do(a), z_{t+k-1}) -> s_{t+k}."""
        s_next = [0.0] * self.d
        # Deviation from initial state propagates through causal edges W
        dev = [s_prev[i] - s_init[i] for i in range(self.d)]
        for j, st in enumerate(self.states):
            causal_inflow = sum(dev[i] * self.W[i][j] for i in range(self.d))
            direct = action.direct_delta.get(st.name, 0.0) if step_k == 1 else 0.0
            sustained = action.sustained_delta.get(st.name, 0.0)
            z_noise = rng.gauss(0.0, st.noise_std)
            # Smooth nonlinear response with mean-reverting damping + causal propagation
            raw_shift = self.damping * dev[j] + causal_inflow + direct + sustained + z_noise
            # Soft saturation prevents runaway explosion while preserving sign/magnitude
            bounded_shift = 2.0 * math.tanh(raw_shift / 2.0)
            s_next[j] = _clamp(s_init[j] + bounded_shift, -5.0, 5.0)
        return s_next

    def evaluate_action(self, action: ActionSpec) -> dict[str, Any]:
        rng = random.Random(self.seed)
        s_init = [s.initial for s in self.states]

        # trajectories[sample][step_k (1..H)][dim]
        trajectories: list[list[list[float]]] = []
        for _ in range(self.mc_samples):
            s_curr = list(s_init)
            traj: list[list[float]] = []
            for k in range(1, self.horizon + 1):
                s_curr = self._step_predictor(s_curr, s_init, action, k, rng)
                traj.append(s_curr)
            trajectories.append(traj)

        mean_traj: list[dict[str, float]] = []
        std_traj: list[dict[str, float]] = []
        step_energies: list[float] = []
        violation_counts = 0
        total_checks = 0

        for k_idx in range(self.horizon):
            means: dict[str, float] = {}
            stds: dict[str, float] = {}
            step_cost = 0.0
            for j, st in enumerate(self.states):
                vals = [trajectories[m][k_idx][j] for m in range(self.mc_samples)]
                mu = sum(vals) / self.mc_samples
                var = sum((v - mu) ** 2 for v in vals) / self.mc_samples
                sd = math.sqrt(var)
                means[st.name] = round(mu, 4)
                stds[st.name] = round(sd, 4)

                # Goal distance + risk variance penalty
                goal_err = st.weight * ((mu - st.target) ** 2)
                risk_pen = st.weight * self.risk_aversion * var

                # Constraint violation penalty
                c_pen = 0.0
                for v in vals:
                    total_checks += 1
                    if st.min_bound is not None and v < st.min_bound:
                        c_pen += 5.0 * ((st.min_bound - v) ** 2) / self.mc_samples
                        violation_counts += 1
                    if st.max_bound is not None and v > st.max_bound:
                        c_pen += 5.0 * ((v - st.max_bound) ** 2) / self.mc_samples
                        violation_counts += 1

                step_cost += goal_err + risk_pen + c_pen

            discounted_cost = (self.discount ** k_idx) * step_cost
            step_energies.append(round(discounted_cost, 4))
            mean_traj.append(means)
            std_traj.append(stds)

        total_energy = round(sum(step_energies) + action.lock_in_cost, 4)
        violation_rate = round(violation_counts / max(1, total_checks), 4)

        mid_idx = max(0, (self.horizon // 2) - 1)
        return {
            "action": action.name,
            "description": action.description,
            "jepa_free_energy": total_energy,
            "lock_in_cost": action.lock_in_cost,
            "constraint_violation_rate": violation_rate,
            "horizons": {
                "t+1_immediate": mean_traj[0],
                f"t+{mid_idx + 1}_second_order": mean_traj[mid_idx],
                f"t+{self.horizon}_long_term": mean_traj[-1],
            },
            "uncertainty_std_long_term": std_traj[-1],
            "full_mean_trajectory": mean_traj,
        }


def DEMO_SPEC() -> dict[str, Any]:
    """Built-in demonstration: Research & Engineering Decision under Causal JEPA."""
    return {
        "title": "Đánh giá quyết định kiến trúc & chiến lược triển khai hệ thống nghiên cứu AI",
        "horizon": 6,
        "states": [
            {"name": "research_quality", "initial": 0.50, "target": 0.90, "weight": 2.0, "min_bound": 0.40},
            {"name": "delivery_speed", "initial": 0.55, "target": 0.80, "weight": 1.2, "min_bound": 0.35},
            {"name": "system_reliability", "initial": 0.60, "target": 0.85, "weight": 1.8, "min_bound": 0.50},
            {"name": "technical_debt", "initial": 0.30, "target": 0.15, "weight": 1.5, "max_bound": 0.60},
            {"name": "compute_budget_load", "initial": 0.40, "target": 0.45, "weight": 1.0, "max_bound": 0.80},
        ],
        "causal_edges": [
            ["technical_debt", "delivery_speed", -0.35],
            ["technical_debt", "system_reliability", -0.40],
            ["system_reliability", "research_quality", 0.30],
            ["delivery_speed", "research_quality", 0.15],
            ["compute_budget_load", "system_reliability", -0.15],
        ],
        "actions": [
            {
                "name": "do(a0_baseline)",
                "description": "Giữ nguyên hiện trạng (Baseline status-quo)",
                "direct_delta": {},
                "sustained_delta": {"technical_debt": 0.03},
                "lock_in_cost": 0.0,
            },
            {
                "name": "do(a1_quick_shortcut)",
                "description": "Đẩy nhanh tốc độ ngắn hạn bằng giải pháp tình thế (bỏ qua chuẩn hóa & kiểm chứng)",
                "direct_delta": {"delivery_speed": 0.28, "technical_debt": 0.22},
                "sustained_delta": {"technical_debt": 0.08, "system_reliability": -0.05},
                "lock_in_cost": 0.35,
            },
            {
                "name": "do(a2_causal_modular_architecture)",
                "description": "Chuẩn hóa kiến trúc mô-đun, kiểm chứng trích dẫn/dữ liệu tự động & tối ưu hóa mô phỏng",
                "direct_delta": {"delivery_speed": -0.05, "system_reliability": 0.15, "technical_debt": -0.10},
                "sustained_delta": {"research_quality": 0.08, "system_reliability": 0.05, "technical_debt": -0.04, "compute_budget_load": 0.03},
                "lock_in_cost": 0.08,
            },
        ],
    }


def run_simulation(spec: dict[str, Any], as_json: bool = False) -> str:
    states = [StateDim(**s) for s in spec["states"]]
    edges = [(e[0], e[1], float(e[2])) for e in spec.get("causal_edges", [])]
    sim = CausalJEPASimulator(
        states=states,
        causal_edges=edges,
        horizon=int(spec.get("horizon", 6)),
        discount=float(spec.get("discount", 0.92)),
        damping=float(spec.get("damping", 0.85)),
        risk_aversion=float(spec.get("risk_aversion", 0.5)),
        mc_samples=int(spec.get("mc_samples", 200)),
        seed=int(spec.get("seed", 42)),
    )
    results = [sim.evaluate_action(ActionSpec(**a)) for a in spec["actions"]]
    baseline = results[0] if results else None

    if baseline:
        long_key = f"t+{sim.horizon}_long_term"
        for r in results:
            r["counterfactual_ate_long_term"] = {
                k: round(r["horizons"][long_key][k] - baseline["horizons"][long_key][k], 4)
                for k in r["horizons"][long_key]
            }

    ranked = sorted(results, key=lambda x: x["jepa_free_energy"])
    if as_json:
        return json.dumps({"title": spec.get("title", "Causal JEPA Simulation"), "ranked_decisions": ranked}, ensure_ascii=False, indent=2)

    lines: list[str] = []
    lines.append(f"# Báo cáo Mô phỏng Nhân quả JEPA: {spec.get('title', 'Causal JEPA Rollout')}")
    lines.append("")
    lines.append("## 1. Xếp hạng Quyết định theo Hàm Năng lượng Tự do JEPA (Thấp hơn = Tối ưu hơn)")
    lines.append("")
    lines.append("| Hạng | Quyết định `do(a_t)` | Mô tả | JEPA Free-Energy `J(a)` | Tỷ lệ vi phạm ràng buộc | Chi phí khóa chặt (Lock-in) |")
    lines.append("| :--- | :--- | :--- | :---: | :---: | :---: |")
    for idx, r in enumerate(ranked, 1):
        lines.append(
            f"| {idx} | `{r['action']}` | {r['description']} | **{r['jepa_free_energy']:.4f}** | "
            f"{r['constraint_violation_rate']*100:.1f}% | {r['lock_in_cost']:.2f} |"
        )

    lines.append("")
    lines.append("## 2. Dự báo Quỹ đạo Trạng thái Tiềm ẩn (Bậc 1 -> Bậc 2 -> Bậc 3) & Hiệu ứng Phản thực tế (ATE)")
    for r in ranked:
        lines.append("")
        lines.append(f"### Quyết định: `{r['action']}` — {r['description']}")
        h_keys = list(r["horizons"].keys())
        lines.append(f"| Biến trạng thái (`s_t`) | Khởi đầu (`t=0`) | Mục tiêu (`s*`) | Ngắn hạn (`{h_keys[0]}`) | Trung hạn (`{h_keys[1]}`) | Dài hạn (`{h_keys[2]}`) | Hiệu ứng Nhân quả `ATE` (so với Baseline) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for st in states:
            v1 = r["horizons"][h_keys[0]][st.name]
            v2 = r["horizons"][h_keys[1]][st.name]
            v3 = r["horizons"][h_keys[2]][st.name]
            ate = r.get("counterfactual_ate_long_term", {}).get(st.name, 0.0)
            ate_str = f"{ate:+.4f}"
            lines.append(f"| `{st.name}` | {st.initial:.2f} | {st.target:.2f} | {v1:.3f} | {v2:.3f} | **{v3:.3f}** | `{ate_str}` |")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", help="Path to JSON causal model specification")
    parser.add_argument("--demo", action="store_true", help="Run built-in demonstration model")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if args.spec:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    else:
        spec = DEMO_SPEC()

    sys.stdout.write(run_simulation(spec, as_json=args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

