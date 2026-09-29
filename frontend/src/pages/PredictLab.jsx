import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BrainCircuit, Send, Sparkles, WandSparkles } from "lucide-react";
import AlertFeed from "../components/AlertFeed.jsx";
import GlassCard from "../components/GlassCard.jsx";
import MetricGauge from "../components/MetricGauge.jsx";
import RiskMeter from "../components/RiskMeter.jsx";
import { ErrorBanner, PageHeader } from "./Dashboard.jsx";
import { getModelInfo, readApiError, runDiagnosis } from "../services/api.js";

const GROUPS = [
  {
    title: "Network Flow",
    fields: ["Packet_Size", "Transmission_Rate", "Latency", "Protocol_Type", "Active_Connections"]
  },
  {
    title: "System Load",
    fields: ["CPU_Usage", "Memory_Usage", "Bandwidth_Utilization", "Request_Response_Time"]
  },
  {
    title: "Security Signals",
    fields: ["Auth_Failures", "Access_Violations", "Firewall_Blocks", "IDS_Alerts"]
  },
  {
    title: "Wavelet Features",
    fields: [
      "DWT_Feature_1",
      "DWT_Feature_2",
      "DWT_Feature_3",
      "DWT_Feature_4",
      "DWT_Feature_5",
      "DWT_Feature_6",
      "DWT_Feature_7",
      "DWT_Feature_8"
    ]
  }
];

const SCENARIOS = [
  { id: "baseline", label: "Baseline", description: "Median telemetry from the trained schema." },
  { id: "load", label: "Load Spike", description: "High CPU, memory, latency, and bandwidth pressure." },
  { id: "security", label: "Security Burst", description: "Elevated IDS, firewall, auth, and access signals." }
];

function PredictLab() {
  const [modelInfo, setModelInfo] = useState(null);
  const [form, setForm] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingSchema, setLoadingSchema] = useState(true);
  const [error, setError] = useState("");
  const [validationErrors, setValidationErrors] = useState({});
  const [toast, setToast] = useState(null);

  useEffect(() => {
    async function loadSchema() {
      try {
        setError("");
        const info = await getModelInfo();
        setModelInfo(info);
        setForm(info.feature_defaults ?? {});
      } catch (err) {
        setError(readApiError(err));
      } finally {
        setLoadingSchema(false);
      }
    }
    loadSchema();
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 5000);
    return () => clearTimeout(timer);
  }, [toast]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setValidationErrors((current) => {
      const next = { ...current };
      delete next[name];
      return next;
    });
  }

  function applyScenario(scenarioId) {
    const schema = modelInfo?.feature_schema ?? [];
    const next = Object.fromEntries(schema.map((item) => [item.name, scenarioValue(item, scenarioId)]));
    setForm(next);
    setValidationErrors({});
    setError("");
    setToast({
      severity: "safe",
      title: `${SCENARIOS.find((item) => item.id === scenarioId)?.label ?? "Scenario"} loaded`,
      message: "Values were generated from the trained model schema, not random demo data."
    });
  }

  async function submit(event) {
    event.preventDefault();
    const payload = buildPayload(form, modelInfo?.feature_schema ?? []);
    const fieldErrors = validatePayload(form, modelInfo?.feature_schema ?? []);
    if (Object.keys(fieldErrors).length) {
      setValidationErrors(fieldErrors);
      setResult(null);
      setError(`Invalid telemetry input: ${Object.values(fieldErrors).slice(0, 4).join("; ")}`);
      return;
    }

    setLoading(true);
    setError("");
    setValidationErrors({});
    setResult(null);

    try {
      const diagnosis = await runDiagnosis(payload);
      setResult({ ...diagnosis, input: payload });
      setToast({
        severity: diagnosis.failure.prediction ? "critical" : diagnosis.anomaly.is_anomaly ? "warning" : "safe",
        title: "AI diagnosis complete",
        message: diagnosis.failure.prediction
          ? "Anomalous load risk is elevated."
          : diagnosis.anomaly.is_anomaly
            ? "Unsupervised anomaly pattern detected."
            : "Network telemetry is inside the learned safe envelope."
      });
    } catch (err) {
      setError(readApiError(err));
    } finally {
      setLoading(false);
    }
  }

  const explanation = useMemo(() => buildExplanation(result), [result]);
  const probability = result?.failure.failure_probability ?? 0;

  return (
    <div className="grid gap-6">
      <PageHeader
        eyebrow="network security AI lab"
        title="Prediction Lab"
        subtitle="Run a trained Random Forest and Isolation Forest diagnosis against real network-security telemetry."
      />

      {error ? <ErrorBanner message={error} /> : null}

      <AnimatePresence>
        {toast ? (
          <motion.div
            className="fixed right-6 top-6 z-50 w-[min(420px,calc(100vw-48px))]"
            initial={{ opacity: 0, y: -18, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -18, scale: 0.98 }}
          >
            <AlertFeed alerts={[{ id: "toast", ...toast }]} />
          </motion.div>
        ) : null}
      </AnimatePresence>

      <div className="grid grid-cols-[minmax(460px,0.95fr)_1fr] gap-6 max-[1180px]:grid-cols-1">
        <GlassCard glow>
          <div className="mb-5 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-cyan-300 text-slate-950">
              <BrainCircuit size={22} />
            </div>
            <div>
              <h2 className="text-2xl font-black">Run AI Diagnosis</h2>
              <p className="text-sm text-slate-400">POST /diagnose</p>
            </div>
          </div>

          {loadingSchema ? (
            <ThinkingLoader label="Loading trained model schema..." />
          ) : (
            <form className="grid gap-5" onSubmit={submit} noValidate>
              <div className="grid gap-3 rounded-2xl border border-cyan-300/15 bg-cyan-300/[0.06] p-4">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-100">Schema presets</p>
                  <p className="mt-1 text-sm text-slate-400">
                    Deterministic values derived from trained feature ranges for fast demos.
                  </p>
                </div>
                <div className="grid gap-2 sm:grid-cols-3">
                  {SCENARIOS.map((scenario) => (
                    <button
                      className="rounded-xl border border-white/10 bg-white/[0.045] px-3 py-3 text-left transition hover:border-cyan-300/35 hover:bg-cyan-300/[0.1]"
                      key={scenario.id}
                      onClick={() => applyScenario(scenario.id)}
                      type="button"
                    >
                      <span className="block text-sm font-black text-white">{scenario.label}</span>
                      <span className="mt-1 block text-xs leading-5 text-slate-400">{scenario.description}</span>
                    </button>
                  ))}
                </div>
              </div>

              {GROUPS.map((group) => (
                <fieldset className="grid gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4" key={group.title}>
                  <legend className="px-2 text-sm font-black uppercase tracking-[0.2em] text-cyan-100">
                    {group.title}
                  </legend>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {group.fields.map((name) => {
                      const schema = findSchema(modelInfo, name);
                      return (
                        <FeatureInput
                          key={name}
                          name={name}
                          schema={schema}
                          value={form[name] ?? ""}
                          onChange={updateField}
                          error={validationErrors[name]}
                        />
                      );
                    })}
                  </div>
                </fieldset>
              ))}

              <button
                className="mt-2 inline-flex min-h-[52px] items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-5 font-black text-slate-950 shadow-[0_0_32px_rgba(103,232,249,0.28)] transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={loading}
                type="submit"
              >
                {loading ? <WandSparkles className="animate-spin" size={19} /> : <Send size={19} />}
                {loading ? "Analyzing network behavior..." : "Run AI Diagnosis"}
              </button>
            </form>
          )}
        </GlassCard>

        <div className="grid content-start gap-6">
          <GlassCard className="min-h-[320px]">
            {loading ? (
              <ThinkingLoader label="Analyzing network behavior..." />
            ) : (
              <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
                <RiskMeter probability={probability} label="Anomalous Load Risk" />
                <div>
                  <h2 className="mb-3 text-2xl font-black">AI Explanation Panel</h2>
                  {explanation.length ? (
                    <div className="grid gap-3">
                      {explanation.map((item) => (
                        <MetricGauge key={item.label} label={item.label} value={item.value} color={item.color} />
                      ))}
                    </div>
                  ) : (
                    <p className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 text-slate-300">
                      Submit telemetry to see feature contributions from the trained Random Forest model.
                    </p>
                  )}
                </div>
              </div>
            )}
          </GlassCard>

          <div className="grid gap-6 xl:grid-cols-2">
            <GlassCard>
              <div className="mb-4 flex items-center gap-2">
                <Sparkles className="text-emerald-200" size={20} />
                <h2 className="text-xl font-black">Training Quality</h2>
              </div>
              <MetricList metrics={modelInfo?.failure_metrics} />
            </GlassCard>

            {result ? (
              <GlassCard>
                <div className="mb-4 flex items-center gap-2">
                  <Sparkles className="text-cyan-200" size={20} />
                  <h2 className="text-xl font-black">Diagnosis Output</h2>
                </div>
                <pre className="max-h-[360px] overflow-auto rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-xs text-cyan-100">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </GlassCard>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function FeatureInput({ name, schema, value, onChange, error }) {
  const integer = schema?.dtype?.includes("int");
  const min = Number.isFinite(schema?.min) ? schema.min : undefined;
  const max = Number.isFinite(schema?.max) ? schema.max : undefined;
  return (
    <label className="grid gap-2">
      <div className="flex min-h-5 items-center justify-between gap-3 text-xs font-bold text-slate-300">
        <span className="truncate" title={name}>{name}</span>
        <span className="font-mono text-cyan-200">{formatNumber(value)}</span>
      </div>
      <input
        className={`h-11 rounded-xl border bg-slate-950/50 px-3 text-sm text-white outline-none transition focus:ring-4 ${
          error
            ? "border-rose-300/70 focus:border-rose-300 focus:ring-rose-300/10"
            : "border-white/10 focus:border-cyan-300/60 focus:ring-cyan-300/10"
        }`}
        name={name}
        type="number"
        min={min}
        max={max}
        step={integer ? 1 : 0.001}
        value={value}
        onChange={onChange}
        required
      />
      <div className={`min-h-4 text-[11px] ${error ? "text-rose-200" : "text-slate-500"}`}>
        {error ?? `Allowed: ${formatNumber(min)} to ${formatNumber(max)}`}
      </div>
    </label>
  );
}

function MetricList({ metrics }) {
  if (!metrics) {
    return <p className="text-sm text-slate-400">Model metrics unavailable.</p>;
  }

  const rows = [
    ["Accuracy", metrics.accuracy],
    ["Precision", metrics.precision],
    ["Recall", metrics.recall],
    ["F1-score", metrics.f1_score],
    ["ROC AUC", metrics.roc_auc],
    ["Average precision", metrics.average_precision]
  ];

  return (
    <div className="grid gap-3">
      {rows.map(([label, value]) => (
        <MetricGauge
          key={label}
          label={label}
          value={Math.round((value ?? 0) * 100)}
          color={label === "Recall" ? "#fbbf24" : "#34d399"}
        />
      ))}
    </div>
  );
}

function ThinkingLoader({ label }) {
  return (
    <div className="grid min-h-[220px] place-items-center text-center">
      <div>
        <div className="mx-auto mb-5 h-16 w-16 animate-pulse rounded-full border border-cyan-300/30 bg-cyan-300/10 shadow-[0_0_40px_rgba(103,232,249,0.28)]" />
        <h2 className="text-2xl font-black">{label}</h2>
        <p className="mt-2 text-sm text-slate-400">Synchronizing model schema, thresholds, and learned risk patterns.</p>
      </div>
    </div>
  );
}

function buildPayload(form, schema) {
  const schemaByName = Object.fromEntries(schema.map((item) => [item.name, item]));
  return Object.fromEntries(
    Object.entries(form).map(([key, value]) => {
      const numeric = Number(value);
      const integer = schemaByName[key]?.dtype?.includes("int");
      return [key, integer ? Math.round(numeric) : numeric];
    })
  );
}

function scenarioValue(item, scenarioId) {
  const min = Number(item.min);
  const max = Number(item.max);
  const mean = Number(item.mean);
  const median = Number(item.median);
  const range = Number.isFinite(min) && Number.isFinite(max) ? max - min : 0;
  const base = Number.isFinite(median) ? median : mean;
  const high = Number.isFinite(range) ? min + range * 0.88 : base;
  const elevated = Number.isFinite(range) ? min + range * 0.72 : base;

  let value = base;
  if (scenarioId === "load" && LOAD_PRESSURE_FIELDS.has(item.name)) {
    value = high;
  } else if (scenarioId === "security" && SECURITY_PRESSURE_FIELDS.has(item.name)) {
    value = high;
  } else if (scenarioId === "security" && LOAD_SUPPORT_FIELDS.has(item.name)) {
    value = elevated;
  }

  if (item.dtype?.includes("int")) {
    return Math.round(value);
  }
  return Math.round(value * 1000) / 1000;
}

const LOAD_PRESSURE_FIELDS = new Set([
  "Packet_Size",
  "Transmission_Rate",
  "Latency",
  "Active_Connections",
  "CPU_Usage",
  "Memory_Usage",
  "Bandwidth_Utilization",
  "Request_Response_Time"
]);

const SECURITY_PRESSURE_FIELDS = new Set([
  "Auth_Failures",
  "Access_Violations",
  "Firewall_Blocks",
  "IDS_Alerts"
]);

const LOAD_SUPPORT_FIELDS = new Set([
  "Latency",
  "Active_Connections",
  "CPU_Usage",
  "Memory_Usage",
  "Bandwidth_Utilization"
]);

function validatePayload(form, schema) {
  const errors = {};
  for (const item of schema) {
    const rawValue = form[item.name];
    const value = Number(rawValue);
    if (!Number.isFinite(value)) {
      errors[item.name] = `${item.name} must be a number`;
      continue;
    }

    if (item.dtype?.includes("int") && !Number.isInteger(value)) {
      errors[item.name] = `${item.name} must be an integer`;
      continue;
    }

    if (Number.isFinite(item.min) && value < item.min) {
      errors[item.name] = `${item.name} must be at least ${formatNumber(item.min)}`;
      continue;
    }

    if (Number.isFinite(item.max) && value > item.max) {
      errors[item.name] = `${item.name} must be at most ${formatNumber(item.max)}`;
    }
  }
  return errors;
}

function findSchema(modelInfo, name) {
  return modelInfo?.feature_schema?.find((item) => item.name === name);
}

function buildExplanation(result) {
  if (!result?.failure?.explanation?.length) return [];
  return result.failure.explanation.map((item, index) => ({
    label: `${item.feature} contribution`,
    value: Math.round(item.contribution * 100),
    color: ["#fb7185", "#fbbf24", "#60a5fa", "#34d399", "#a78bfa"][index % 5]
  }));
}

function formatNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "";
  return Math.abs(number) >= 100 ? number.toFixed(0) : number.toFixed(2);
}

export default PredictLab;
