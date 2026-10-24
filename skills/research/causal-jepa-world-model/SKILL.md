---
name: causal-jepa-world-model
description: "Causal JEPA (Joint-Embedding Predictive Architecture) World-Model & Counterfactual Decision Rollout. Use when analyzing decisions, policies, system architectures, or research hypotheses to predict how an action do(a_t) propagates through latent state representations s_t -> s_{t+k}, including 1st/2nd/3rd-order cascading effects, counterfactual trajectories, energy/cost functions, and irreversibility risks."
---

# Causal JEPA World-Model & Counterfactual Decision Framework

Use this skill whenever the user asks to:
1. Evaluate a decision, policy, architectural design, or experimental intervention and predict its downstream consequences over time.
2. Apply **Causal JEPA (Joint-Embedding Predictive Architecture)** or World-Model reasoning to scientific research, optimization, or strategic planning.
3. Compare multiple candidate actions $\mathcal{A} = \{a^{(1)}, a^{(2)}, \dots\}$ under uncertainty $z_t$ before committing to execution.

---

## 1. Theoretical Architecture: Causal JEPA World Model

Unlike autoregressive generative models that predict surface tokens directly in observation space $x_{t+1}$, **Causal JEPA** operates in an abstract representation space $s_t \in \mathcal{S}$ coupled with Judea Pearl's structural causal intervention operator $\text{do}(a_t)$:

$$
\begin{aligned}
\text{1. State Encoder:} \quad & s_t = E_\theta(x_t), \quad s_t \in \mathbb{R}^d \\
\text{2. Causal Intervention & Latent Uncertainty:} \quad & u_t = \text{do}(a_t), \quad z_t \sim \mathcal{P}(z \mid s_t) \\
\text{3. Joint-Embedding Predictor (Rollout):} \quad & \hat{s}_{t+k} = P_\phi\big(\hat{s}_{t+k-1}, \text{do}(a_{t+k-1}), z_{t+k-1}\big), \quad k = 1, \dots, H \\
\text{4. Free-Energy / Cost Functional:} \quad & \mathcal{J}(a_{t:t+H-1}) = \sum_{k=1}^{H} \gamma^{k-1} \Big[ C_{\text{goal}}(\hat{s}_{t+k}, s^*) + C_{\text{constraint}}(\hat{s}_{t+k}) + \beta \cdot \mathbb{V}\text{ar}_{z}(\hat{s}_{t+k}) \Big]
\end{aligned}
$$

### Why Causal JEPA Prevents Myopic Decisions
1. **Abstraction ($E_\theta$):** Strips irrelevant surface details from $x_t$ and isolates structural state variables (resources, bottlenecks, coupling, institutional/technical constraints, invariant laws).
2. **Intervention vs. Correlation ($\text{do}(a_t)$):** Distinguishes passive observation $P(s_{t+k} \mid a_t)$ from active intervention $P(s_{t+k} \mid \text{do}(a_t))$ by severing incoming confounding edges into $a_t$ and propagating effects strictly along directed causal mechanisms.
3. **Multi-Horizon Rollout ($k = 1, 2, \dots, H$):** A decision $a_t$ that minimizes immediate cost $C(\hat{s}_{t+1})$ often degrades structural state variables at $t+2$ or $t+3$ (e.g., technical debt, policy distortion, overfitting, resource exhaustion). Causal JEPA evaluates the entire trajectory $\hat{s}_{t+1:t+H}$.
4. **Latent Uncertainty ($z_t$):** Explicitly models unobserved/stochastic environment shifts $z_t$ to test robustness and tail risk rather than assuming a single deterministic future.

---

## 2. Operational Protocol for Decision & Impact Analysis

Whenever evaluating a decision, architectural change, policy proposal, or scientific intervention, execute this 5-step Causal JEPA workflow:

### Step 1: State Space Encoding ($s_t = E_\theta(x_t)$)
Identify the core state variables that govern the system:
- **Structural State Variables ($s_t$):** Capacity, quality/accuracy, latency/throughput, resource budget, institutional/regulatory constraints, coupling/technical debt.
- **Confounders ($U$):** External factors influencing both the choice of action and the outcome.
- **Hard Invariants & Constraints:** Thresholds that must not be violated.

### Step 2: Define Candidate Interventions ($\text{do}(a_t)$) & Baseline ($\text{do}(a_0)$)
- Specify the exact mechanism of each candidate decision $\text{do}(a^{(i)})$ and the status-quo / baseline intervention $\text{do}(a_0)$.
- Specify latent uncertainty variables $z_t$ (best-case, expected, stress/adversarial regimes).

### Step 3: Multi-Horizon Causal Rollout ($P_\phi(s_t, \text{do}(a_t), z_t)$)
Trace the causal propagation across three explicit horizons:
- **Bậc 1 — Tác động trực tiếp / Ngắn hạn ($\hat{s}_{t+1}$):** Immediate changes in target metrics right after applying $\text{do}(a_t)$.
- **Bậc 2 — Phản hồi hệ thống / Trung hạn ($\hat{s}_{t+2}$):** Secondary adaptations, feedback loops (reinforcing or balancing), resource reallocation, and side effects on adjacent subsystems.
- **Bậc 3 — Trạng thái cân bằng mới & Hệ quả dài hạn ($\hat{s}_{t+H}$):** Long-term structural equilibrium, path dependency, lock-in cost, and tail risks.

### Step 4: Counterfactual Effect & Energy Evaluation ($\Delta_{\text{do}}$ & $\mathcal{J}$)
For each candidate decision, evaluate:
- **Causal Treatment Effect:** $\Delta_k(a) = \mathbb{E}[\hat{s}_{t+k} \mid \text{do}(a)] - \mathbb{E}[\hat{s}_{t+k} \mid \text{do}(a_0)]$.
- **Irreversibility / Lock-in Cost:** How costly is it to roll back $\text{do}(a_t)$ at step $t+k$ if latent shock $z_t$ occurs?
- **Pre-Conditions for Success:** What concrete conditions must hold for $\hat{s}_{t+H}$ to reach the desired target state $s^*$?

### Step 5: Quantitative Simulation via `causal_jepa_simulator.py`
When quantitative or structural comparison is needed, run the bundled simulator script to compute multi-step latent state rollouts, Monte Carlo uncertainty bands, and JEPA free-energy rankings:

```bash
# Run built-in demo or custom JSON specification:
python3 skills/research/causal-jepa-world-model/scripts/causal_jepa_simulator.py --demo

# Run with a custom JSON causal model spec:
python3 skills/research/causal-jepa-world-model/scripts/causal_jepa_simulator.py --spec model_spec.json
```

