import { useEffect, useMemo, useState } from "react";
import {
  Bot,
  BrainCircuit,
  CheckCircle2,
  Gauge,
  GitCompareArrows,
  Lightbulb,
  Route,
  ShieldAlert,
  Sparkles,
  WandSparkles
} from "lucide-react";
import AlertFeed from "../components/AlertFeed.jsx";
import GlassCard from "../components/GlassCard.jsx";
import MetricGauge from "../components/MetricGauge.jsx";
import RiskMeter from "../components/RiskMeter.jsx";
import { ErrorBanner, PageHeader } from "./Dashboard.jsx";
import { analyzeTelemetry, getModelInfo, readApiError, runWhatIf } from "../services/api.js";

const FOCUS_FIELDS = [
  "CPU_Usage",
  "Memory_Usage",
  "Latency",
  "Bandwidth_Utilization",
  "Request_Response_Time",
  "Active_Connections",
  "Auth_Failures",
  "Firewall_Blocks",
  "IDS_Alerts"
];

const PRESETS = [
  {
    id: "steady",
    label: "Steady State",
    description: "Return visible signals to learned central values."
  },
  {
    id: "security",
    label: "Security Burst",
    description: "Stress authentication, firewall, and IDS signals."
  },
  {
    id: "capacity",
    label: "Capacity Pressure",
    description: "Push utilization, response time, and connection pressure."
  },
  {
    id: "mitigation",
    label: "Mitigation Plan",
    description: "Reduce the riskiest pressure signals for what-if analysis."
  }
];

function AIAnalyst() {
  const [modelInfo, setModelInfo] = useState(null);
  const [form, setForm] = useState({});
  const [candidate, setCandidate] = useState({});
  const [analyst, setAnalyst] = useState(null);
  const [whatIf, setWhatIf] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const info = await getModelInfo();
        setModelInfo(info);
        setForm(info.feature_defaults ?? {});
        setCandidate(buildPreset(info, "mitigation"));
      } catch (err) {
        setError(readApiError(err));
      }
    }
    load();
  }, []);

  async function runAnalyst() {
    if (!modelInfo) return;
    setLoading(true);
    setError("");
    setWhatIf(null);
    try {
      setAnalyst(await analyzeTelemetry(buildPayload(form, modelInfo)));
    } catch (err) {
      setError(readApiError(err));
    } finally {
      setLoading(false);
    }
  }

  async function runSimulation() {
    if (!modelInfo) return;
    setSimulating(true);
    setError("");
    try {
      const baseline = buildPayload(form, modelInfo);
      const proposed = buildPayload(candidate, modelInfo);
      const result = await runWhatIf(baseline, proposed);
      setWhatIf(result);
      setAnalyst(result.baseline);
    } catch (err) {
      setError(readApiError(err));
    } finally {
      setSimulating(false);
    }
  }

  function updateField(name, value, target = "form") {
    const setter = target === "candidate" ? setCandidate : setForm;
    setter((current) => ({ ...current, [name]: Number(value) }));
  }

  function applyPreset(id, target = "form") {
    if (!modelInfo) return;
    const next = buildPreset(modelInfo, id);
    if (target === "candidate") {
      setCandidate(next);
      return;
    }
    setForm(next);
  }

  const displayedAnalyst = analyst ?? whatIf?.baseline;
  const currentRisk = displayedAnalyst?.analysis?.failure?.failure_probability ?? 0;
  const recommendationAlerts = useMemo(
    () => (displayedAnalyst?.recommendations ?? []).map((message, index) => ({
      id: `rec-${index}`,
      severity: index === 0 && ["HIGH", "CRITICAL"].includes(displayedAnalyst?.severity) ? "critical" : "warning",
      title: index === 0 ? "Recommended first move" : "Recommended action",
      message
    })),
    [displayedAnalyst]
  );

  return (
    <div className="grid gap-6">
      <PageHeader
        eyebrow="ai incident intelligence"
        title="AI Analyst"
        subtitle="Root cause analysis, remediation guidance, drift detection, incident narrative, and what-if simulation."
        action={runAnalyst}
      />

      {error ? <ErrorBanner message={error} /> : null}

      <AnalystBriefing />

      <div className="grid grid-cols-[minmax(430px,0.95fr)_1fr] gap-6 max-[1180px]:grid-cols-1">
        <div className="grid content-start gap-6">
          <GlassCard glow>
            <div className="mb-5 flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-cyan-300 text-slate-950">
                <Bot size={22} />
              </div>
              <div>
                <h2 className="text-2xl font-black">Analyst Console</h2>
                <p className="text-sm text-slate-400">Current telemetry sample</p>
              </div>
            </div>

            <PresetGrid presets={PRESETS} onApply={(id) => applyPreset(id, "form")} />
            <TelemetryEditor form={form} modelInfo={modelInfo} onChange={(name, value) => updateField(name, value)} />

            <button
              className="mt-5 inline-flex min-h-[52px] w-full items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-5 font-black text-slate-950 shadow-[0_0_32px_rgba(103,232,249,0.25)] transition hover:bg-cyan-200 disabled:opacity-60"
              disabled={loading || !modelInfo}
              onClick={runAnalyst}
              type="button"
            >
              {loading ? <WandSparkles className="animate-spin" size={19} /> : <BrainCircuit size={19} />}
              {loading ? "Reasoning over telemetry..." : "Run AI Analyst"}
            </button>
          </GlassCard>

          <GlassCard>
            <div className="mb-5 flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-xl border border-violet-300/20 bg-violet-300/[0.1] text-violet-100">
                <GitCompareArrows size={22} />
              </div>
              <div>
                <h2 className="text-2xl font-black">What-If Simulator</h2>
                <p className="text-sm text-slate-400">Proposed candidate state</p>
              </div>
            </div>

            <PresetGrid presets={PRESETS} onApply={(id) => applyPreset(id, "candidate")} compact />
            <TelemetryEditor form={candidate} modelInfo={modelInfo} onChange={(name, value) => updateField(name, value, "candidate")} compact />

            <button
              className="mt-5 inline-flex min-h-[52px] w-full items-center justify-center gap-2 rounded-2xl border border-violet-300/25 bg-violet-300/[0.14] px-5 font-black text-violet-100 transition hover:bg-violet-300/[0.22] disabled:opacity-60"
              disabled={simulating || !modelInfo}
              onClick={runSimulation}
              type="button"
            >
              {simulating ? <WandSparkles className="animate-spin" size={19} /> : <Route size={19} />}
              {simulating ? "Simulating impact..." : "Compare What-If Impact"}
            </button>
          </GlassCard>
        </div>

        <div className="grid content-start gap-6">
          <GlassCard glow>
            {displayedAnalyst ? (
              <div className="grid gap-6 xl:grid-cols-[230px_1fr]">
                <RiskMeter probability={currentRisk} label="AI Risk" />
                <div>
                  <div className="mb-4 grid grid-cols-3 gap-3 max-[720px]:grid-cols-1">
                    <ScoreTile icon={ShieldAlert} label="Severity" value={displayedAnalyst.severity} tone={severityTone(displayedAnalyst.severity)} />
                    <ScoreTile icon={Gauge} label="Priority" value={`${displayedAnalyst.priority_score}/100`} tone="cyan" />
                    <ScoreTile icon={CheckCircle2} label="Confidence" value={`${Math.round(displayedAnalyst.confidence * 100)}%`} tone="emerald" />
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4">
                    <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-100">AI Incident Summary</p>
                    <p className="mt-3 text-sm leading-6 text-slate-300">{displayedAnalyst.incident_summary}</p>
                  </div>
                </div>
              </div>
            ) : (
              <EmptyAnalyst />
            )}
          </GlassCard>

          {displayedAnalyst ? (
            <>
              <div className="grid grid-cols-2 gap-6 max-[920px]:grid-cols-1">
                <GlassCard>
                  <PanelTitle icon={Lightbulb} title="Root Cause Ranking" />
                  <div className="grid gap-3">
                    {displayedAnalyst.root_causes.map((cause) => (
                      <CauseCard key={`${cause.feature}-${cause.category}`} cause={cause} />
                    ))}
                  </div>
                </GlassCard>

                <GlassCard>
                  <PanelTitle icon={Sparkles} title="Remediation Guidance" />
                  <AlertFeed alerts={recommendationAlerts} />
                </GlassCard>
              </div>

              <div className="grid grid-cols-[0.8fr_1.2fr] gap-6 max-[980px]:grid-cols-1">
                <GlassCard>
                  <PanelTitle icon={Route} title="Model Drift" />
                  <MetricGauge
                    label={`Drift level: ${displayedAnalyst.drift.level}`}
                    value={Math.round(displayedAnalyst.drift.drift_score * 100)}
                    color={displayedAnalyst.drift.level === "HIGH" ? "#fb7185" : displayedAnalyst.drift.level === "MEDIUM" ? "#fbbf24" : "#34d399"}
                  />
                  <p className="mt-4 rounded-xl border border-white/10 bg-white/[0.04] p-4 text-sm leading-6 text-slate-300">
                    {displayedAnalyst.drift.summary}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(displayedAnalyst.drift.shifted_features.length ? displayedAnalyst.drift.shifted_features : ["operating envelope stable"]).map((feature) => (
                      <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs font-bold text-slate-300" key={feature}>
                        {feature}
                      </span>
                    ))}
                  </div>
                </GlassCard>

                <GlassCard>
                  <PanelTitle icon={CheckCircle2} title="Response Playbook" />
                  <ol className="grid gap-3">
                    {displayedAnalyst.playbook.map((step, index) => (
                      <li className="grid grid-cols-[34px_1fr] gap-3 rounded-xl border border-white/10 bg-white/[0.04] p-3 text-sm text-slate-300" key={step}>
                        <span className="grid h-8 w-8 place-items-center rounded-xl bg-cyan-300 text-xs font-black text-slate-950">{index + 1}</span>
                        <span className="leading-6">{step}</span>
                      </li>
                    ))}
                  </ol>
                </GlassCard>
              </div>
            </>
          ) : null}

          {whatIf ? (
            <GlassCard glow>
              <PanelTitle icon={GitCompareArrows} title="What-If Impact" />
              <div className="grid gap-4 md:grid-cols-4">
                <ScoreTile icon={Gauge} label="Risk Delta" value={`${Math.round(whatIf.risk_delta * 1000) / 10}%`} tone={whatIf.risk_delta <= 0 ? "emerald" : "rose"} />
                <ScoreTile icon={ShieldAlert} label="Priority Delta" value={`${whatIf.priority_delta > 0 ? "+" : ""}${whatIf.priority_delta}`} tone={whatIf.priority_delta <= 0 ? "emerald" : "rose"} />
                <ScoreTile icon={Route} label="Severity" value={whatIf.severity_change} tone="violet" />
                <ScoreTile icon={CheckCircle2} label="Candidate" value={whatIf.candidate.severity} tone={severityTone(whatIf.candidate.severity)} />
              </div>
              <p className="mt-4 rounded-xl border border-white/10 bg-white/[0.04] p-4 text-sm leading-6 text-slate-300">
                {whatIf.impact_summary}
              </p>
            </GlassCard>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function TelemetryEditor({ form, modelInfo, onChange, compact = false }) {
  const schemaByName = useMemo(
    () => Object.fromEntries((modelInfo?.feature_schema ?? []).map((item) => [item.name, item])),
    [modelInfo]
  );

  return (
    <div className={`mt-5 grid gap-3 ${compact ? "" : "sm:grid-cols-2"}`}>
      {FOCUS_FIELDS.map((name) => {
        const schema = schemaByName[name];
        const value = Number(form[name] ?? schema?.median ?? 0);
        const min = Number(schema?.min ?? 0);
        const max = Number(schema?.max ?? 100);
        const step = schema?.dtype?.includes("int") ? 1 : 0.1;
        return (
          <label className="grid gap-2 rounded-xl border border-white/10 bg-white/[0.035] p-3" key={name}>
            <div className="flex items-center justify-between gap-3">
              <span className="truncate text-xs font-black text-slate-300" title={name}>{name}</span>
              <span className="font-mono text-xs text-cyan-100">{formatValue(value)}</span>
            </div>
            <input
              className="accent-cyan-300"
              type="range"
              min={min}
              max={max}
              step={step}
              value={value}
              onChange={(event) => onChange(name, event.target.value)}
            />
          </label>
        );
      })}
    </div>
  );
}

function PresetGrid({ presets, onApply, compact = false }) {
  return (
    <div className={`grid gap-2 ${compact ? "sm:grid-cols-2" : "sm:grid-cols-4"}`}>
      {presets.map((preset) => (
        <button
          className="rounded-xl border border-white/10 bg-white/[0.045] px-3 py-3 text-left transition hover:border-cyan-300/35 hover:bg-cyan-300/[0.1]"
          key={preset.id}
          onClick={() => onApply(preset.id)}
          type="button"
        >
          <span className="block text-sm font-black text-white">{preset.label}</span>
          <span className="mt-1 block text-xs leading-5 text-slate-400">{preset.description}</span>
        </button>
      ))}
    </div>
  );
}

function CauseCard({ cause }) {
  const percent = Math.max(4, Math.min(100, Math.round(cause.contribution * 100)));
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate font-black text-white">{cause.feature}</h3>
          <p className="text-xs font-bold text-cyan-100">{cause.category} - {cause.severity}</p>
        </div>
        <span className="font-mono text-sm text-slate-300">{percent}%</span>
      </div>
      <div className="mb-3 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-cyan-300" style={{ width: `${percent}%` }} />
      </div>
      <p className="text-sm leading-6 text-slate-400">{cause.evidence}</p>
    </div>
  );
}

function ScoreTile({ icon: Icon, label, value, tone }) {
  const toneClass = {
    emerald: "border-emerald-300/15 bg-emerald-300/[0.08] text-emerald-100",
    cyan: "border-cyan-300/15 bg-cyan-300/[0.08] text-cyan-100",
    violet: "border-violet-300/15 bg-violet-300/[0.08] text-violet-100",
    rose: "border-rose-300/15 bg-rose-300/[0.08] text-rose-100",
    amber: "border-amber-300/15 bg-amber-300/[0.08] text-amber-100"
  }[tone] ?? "border-cyan-300/15 bg-cyan-300/[0.08] text-cyan-100";

  return (
    <div className={`rounded-xl border p-4 ${toneClass}`}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">{label}</p>
        <Icon size={17} />
      </div>
      <p className="truncate text-lg font-black text-white">{value}</p>
    </div>
  );
}

function PanelTitle({ icon: Icon, title }) {
  return (
    <div className="mb-4 flex items-center gap-2">
      <Icon className="text-cyan-200" size={20} />
      <h2 className="text-xl font-black">{title}</h2>
    </div>
  );
}

function AnalystBriefing() {
  const cards = [
    {
      icon: BrainCircuit,
      title: "Predict",
      detail: "Estimates elevated operational risk from protected telemetry."
    },
    {
      icon: Lightbulb,
      title: "Explain",
      detail: "Ranks likely root causes and evidence behind the model decision."
    },
    {
      icon: CheckCircle2,
      title: "Recommend",
      detail: "Creates response guidance and an incident playbook."
    },
    {
      icon: GitCompareArrows,
      title: "Simulate",
      detail: "Tests mitigation scenarios before action."
    }
  ];

  return (
    <GlassCard className="p-4">
      <div className="grid gap-3 md:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div className="rounded-xl border border-white/10 bg-white/[0.035] p-4" key={card.title}>
              <div className="mb-3 flex items-center gap-2 text-cyan-100">
                <Icon size={18} />
                <h3 className="font-black text-white">{card.title}</h3>
              </div>
              <p className="text-sm leading-6 text-slate-400">{card.detail}</p>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}

function EmptyAnalyst() {
  return (
    <div className="grid min-h-[320px] place-items-center text-center">
      <div>
        <div className="mx-auto mb-5 grid h-16 w-16 place-items-center rounded-2xl border border-cyan-300/20 bg-cyan-300/[0.1] text-cyan-100 shadow-[0_0_40px_rgba(103,232,249,0.22)]">
          <Bot size={30} />
        </div>
        <h2 className="text-2xl font-black">AI Analyst is ready</h2>
        <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400">
          Run analysis to generate root cause, recommended actions, drift status, confidence, and a response playbook.
        </p>
      </div>
    </div>
  );
}

function buildPayload(form, modelInfo) {
  const schemaByName = Object.fromEntries((modelInfo?.feature_schema ?? []).map((item) => [item.name, item]));
  return Object.fromEntries(
    Object.entries(modelInfo?.feature_defaults ?? {}).map(([key, defaultValue]) => {
      const rawValue = form[key] ?? defaultValue;
      const numeric = Number(rawValue);
      return [key, schemaByName[key]?.dtype?.includes("int") ? Math.round(numeric) : numeric];
    })
  );
}

function buildPreset(modelInfo, presetId) {
  return Object.fromEntries(
    (modelInfo?.feature_schema ?? []).map((item) => {
      const value = presetValue(item, presetId);
      return [item.name, item.dtype?.includes("int") ? Math.round(value) : Math.round(value * 1000) / 1000];
    })
  );
}

function presetValue(item, presetId) {
  const min = Number(item.min);
  const max = Number(item.max);
  const median = Number(item.median);
  const range = Math.max(max - min, 0);
  const low = min + range * 0.28;
  const mid = Number.isFinite(median) ? median : min + range * 0.5;
  const high = min + range * 0.88;
  const elevated = min + range * 0.72;

  if (presetId === "security" && SECURITY_FIELDS.has(item.name)) return high;
  if (presetId === "security" && SUPPORT_FIELDS.has(item.name)) return elevated;
  if (presetId === "capacity" && CAPACITY_FIELDS.has(item.name)) return high;
  if (presetId === "mitigation" && (SECURITY_FIELDS.has(item.name) || CAPACITY_FIELDS.has(item.name))) return low;
  return mid;
}

function severityTone(severity) {
  if (severity === "CRITICAL") return "rose";
  if (severity === "HIGH") return "amber";
  if (severity === "MEDIUM") return "cyan";
  return "emerald";
}

function formatValue(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "0";
  return Math.abs(number) >= 100 ? number.toFixed(0) : number.toFixed(1);
}

const SECURITY_FIELDS = new Set(["Auth_Failures", "Access_Violations", "Firewall_Blocks", "IDS_Alerts"]);
const CAPACITY_FIELDS = new Set([
  "CPU_Usage",
  "Memory_Usage",
  "Bandwidth_Utilization",
  "Latency",
  "Request_Response_Time",
  "Active_Connections"
]);
const SUPPORT_FIELDS = new Set(["Latency", "Active_Connections", "Bandwidth_Utilization"]);

export default AIAnalyst;
