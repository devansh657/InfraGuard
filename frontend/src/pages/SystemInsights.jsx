import { useEffect, useMemo, useRef, useState } from "react";
import { BrainCircuit, FileUp, FileText, LineChart, RefreshCcw, ServerCog, ShieldCheck, UploadCloud } from "lucide-react";
import AlertFeed from "../components/AlertFeed.jsx";
import GlassCard from "../components/GlassCard.jsx";
import MetricGauge from "../components/MetricGauge.jsx";
import { ErrorBanner, PageHeader } from "./Dashboard.jsx";
import {
  API_BASE_URL,
  getBenchmarkReport,
  getEda,
  getHealth,
  getReport,
  readApiError,
  uploadDataset
} from "../services/api.js";

function SystemInsights() {
  const inputRef = useRef(null);
  const [health, setHealth] = useState(null);
  const [report, setReport] = useState(null);
  const [eda, setEda] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [file, setFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);

  async function refresh() {
    try {
      setError("");
      const [healthData, reportData, edaData, benchmarkData] = await Promise.all([
        getHealth(),
        getReport(),
        getEda(),
        getBenchmarkReport()
      ]);
      setHealth(healthData);
      setReport(reportData);
      setEda(edaData);
      setBenchmark(benchmarkData);
    } catch (err) {
      setError(readApiError(err));
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function submitUpload(event) {
    event.preventDefault();
    if (!file) {
      setError("Choose a telemetry package first.");
      return;
    }
    setUploading(true);
    setError("");
    setUploadResult(null);
    try {
      setUploadResult(await uploadDataset(file));
    } catch (err) {
      setError(readApiError(err));
    } finally {
      setUploading(false);
    }
  }

  const summary = useMemo(() => {
    const total = report?.total_requests ?? 0;
    return [
      { label: "Anomaly rate", value: total ? Math.round(((report?.anomalies ?? 0) / total) * 100) : 0, color: "#fbbf24" },
      { label: "Failure rate", value: total ? Math.round(((report?.failures ?? 0) / total) * 100) : 0, color: "#fb7185" },
      { label: "Healthy share", value: total ? Math.max(0, 100 - Math.round((((report?.anomalies ?? 0) + (report?.failures ?? 0)) / total) * 100)) : 100, color: "#34d399" }
    ];
  }, [report]);

  return (
    <div className="grid gap-6">
      <PageHeader
        eyebrow="ops intelligence"
        title="System Insights"
        subtitle="Runtime status, risk summaries, and protected telemetry intake in one control panel."
        action={refresh}
      />

      {error ? <ErrorBanner message={error} /> : null}

      <div className="grid grid-cols-[1fr_420px] gap-6 max-[1120px]:grid-cols-1">
        <GlassCard glow>
          <div className="mb-5 flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-emerald-300 text-slate-950">
              <ServerCog size={23} />
            </div>
            <div>
              <h2 className="text-2xl font-black">Runtime Health</h2>
              <p className="text-sm text-slate-400">{health?.service ?? "InfraGuard AI"} - {health?.status ?? "checking"}</p>
            </div>
          </div>

          <div className="grid gap-3">
            {summary.map((item) => (
              <MetricGauge key={item.label} {...item} />
            ))}
          </div>
        </GlassCard>

        <GlassCard>
          <h2 className="mb-4 text-2xl font-black">Risk Summary</h2>
          <AlertFeed
            alerts={[
              {
                id: "report",
                severity: report?.risk_level === "HIGH" ? "critical" : report?.risk_level === "MEDIUM" ? "warning" : "safe",
                title: `Risk level ${report?.risk_level ?? "LOW"}`,
                message: `${report?.total_requests ?? 0} requests, ${report?.anomalies ?? 0} anomalies, ${report?.failures ?? 0} failures.`
              }
            ]}
          />
        </GlassCard>
      </div>

      <GlassCard glow>
        <div className="mb-5">
          <p className="text-xs font-black uppercase tracking-[0.22em] text-emerald-200">system evidence</p>
          <h2 className="mt-1 text-2xl font-black">Operational Intelligence Signals</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            These cards connect the runtime, trained models, evaluation outputs, and monitoring state into one
            explainable control surface.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <EvidenceCard
            icon={ShieldCheck}
            label="Runtime"
            value={health?.ml_models_loaded ? "Models online" : "Checking models"}
            detail={`Database: ${health?.db_connected ? "connected" : "checking"}`}
            tone="emerald"
          />
          <EvidenceCard
            icon={BrainCircuit}
            label="Risk label"
            value="Protected"
            detail="Random Forest classifier plus Isolation Forest outlier engine."
            tone="cyan"
          />
          <EvidenceCard
            icon={LineChart}
            label="Benchmark"
            value={benchmark?.benchmark?.best_model ?? "pending"}
            detail={`${benchmark?.benchmark?.model_results?.length ?? 0} compared models with holdout metrics.`}
            tone="violet"
          />
          <EvidenceCard
            icon={FileText}
            label="EDA"
            value={eda?.available ? "Graphs ready" : "not generated"}
            detail={`${eda?.summary?.clean_rows ?? 0} clean rows analyzed from the dataset.`}
            tone="rose"
          />
        </div>
      </GlassCard>

      <GlassCard>
        <form className="grid gap-4" onSubmit={submitUpload}>
          <button
            className="grid min-h-48 place-items-center rounded-3xl border border-dashed border-cyan-300/25 bg-cyan-300/[0.08] p-6 text-center transition hover:bg-cyan-300/[0.12]"
            onClick={() => inputRef.current?.click()}
            type="button"
          >
            <UploadCloud className="text-cyan-200" size={38} />
            <strong className="mt-3 text-lg">{file ? "Telemetry package selected" : "Upload telemetry package"}</strong>
            <span className="mt-2 text-sm text-slate-400">Validated against the protected model schema before intake</span>
          </button>
          <input
            ref={inputRef}
            className="sr-only"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <button
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-5 font-black text-slate-950 transition hover:bg-cyan-200 disabled:opacity-60"
            disabled={uploading}
            type="submit"
          >
            {uploading ? <RefreshCcw className="animate-spin" size={18} /> : <FileUp size={18} />}
            {uploading ? "Uploading dataset" : "Validate Upload"}
          </button>
        </form>

        {uploadResult ? (
          <div className="mt-5 rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-4 text-emerald-100">
            Secure upload validated with {uploadResult.rows} rows. Reference: {uploadResult.upload_id}.
          </div>
        ) : null}
      </GlassCard>

      <GlassCard glow>
        <div className="mb-5 flex items-center justify-between gap-4 max-[720px]:items-start max-[720px]:flex-col">
          <div>
            <h2 className="text-2xl font-black">Exploratory Data Analysis</h2>
            <p className="mt-2 text-sm text-slate-400">
              Generated from the protected telemetry training run.
            </p>
          </div>
          <div className="rounded-2xl border border-emerald-300/20 bg-emerald-300/10 px-4 py-3 text-sm font-black text-emerald-100">
            {eda?.available ? "EDA ready" : "EDA unavailable"}
          </div>
        </div>

        {eda?.available ? (
          <div className="grid gap-6">
            <div className="grid gap-3 md:grid-cols-3">
              <MetricGauge label="Clean rows" value={eda.summary?.clean_rows ?? 0} max={eda.summary?.source_rows ?? 1} color="#34d399" unit="" />
              <MetricGauge label="Recall" value={Math.round((eda.evaluation?.failure_metrics?.recall ?? 0) * 100)} color="#fbbf24" />
              <MetricGauge label="ROC AUC" value={Math.round((eda.evaluation?.failure_metrics?.roc_auc ?? 0) * 100)} color="#60a5fa" />
            </div>

            <div className="grid grid-cols-2 gap-5 max-[980px]:grid-cols-1">
              {[
                ["Feature Distribution Overview", "feature_distributions.png"],
                ["Correlation Heatmap", "correlation_heatmap.png"],
                ["Missing Values Audit", "missing_values.png"],
                ["Class Balance", "label_distribution.png"],
                ["ROC Curve", "roc_curve.png"],
                ["Precision-Recall Curve", "precision_recall_curve.png"],
                ["Confusion Matrix", "confusion_matrix.png"],
                ["Feature Importance", "feature_importance.png"],
                ["Anomaly Scores", "anomaly_score_distribution.png"]
              ].map(([title, filename]) => (
                <figure className="overflow-hidden rounded-2xl border border-white/10 bg-slate-950/45" key={filename}>
                  <img
                    alt={title}
                    className="h-full w-full bg-white object-contain"
                    src={`${API_BASE_URL}/eda-assets/${filename}`}
                  />
                  <figcaption className="border-t border-white/10 px-4 py-3 text-sm font-bold text-slate-300">
                    {title}
                  </figcaption>
                </figure>
              ))}
            </div>
          </div>
        ) : (
          <p className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 text-slate-300">
            Run the ML training pipeline to regenerate EDA artifacts.
          </p>
        )}
      </GlassCard>

      <GlassCard glow>
        <div className="mb-5 flex items-center justify-between gap-4 max-[720px]:items-start max-[720px]:flex-col">
          <div>
            <h2 className="text-2xl font-black">Model Benchmark</h2>
            <p className="mt-2 text-sm text-slate-400">
              Cross-validation and holdout comparison across multiple ML models for transparent evaluation.
            </p>
          </div>
          <div className="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-4 py-3 text-sm font-black text-cyan-100">
            Best: {benchmark?.benchmark?.best_model ?? "checking"}
          </div>
        </div>

        {benchmark?.available ? (
          <div className="grid gap-6">
            <BenchmarkTable results={benchmark.benchmark?.model_results ?? []} />
            <div className="grid grid-cols-2 gap-5 max-[980px]:grid-cols-1">
              {[
                ["Model Comparison", "model_comparison.png"],
                ["ROC Comparison", "roc_comparison.png"]
              ].map(([title, filename]) => (
                <figure className="overflow-hidden rounded-2xl border border-white/10 bg-slate-950/45" key={filename}>
                  <img
                    alt={title}
                    className="h-full w-full bg-white object-contain"
                    src={`${API_BASE_URL}/eda-assets/${filename}`}
                  />
                  <figcaption className="border-t border-white/10 px-4 py-3 text-sm font-bold text-slate-300">
                    {title}
                  </figcaption>
                </figure>
              ))}
            </div>
            <AlertFeed
              alerts={(benchmark.benchmark?.evaluation_notes ?? []).map((note, index) => ({
                id: `evaluation-note-${index}`,
                severity: index === 0 ? "warning" : "safe",
                title: index === 0 ? "Evaluation caution" : "Evaluation note",
                message: note
              }))}
            />
          </div>
        ) : (
          <p className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 text-slate-300">
            Run the ML training pipeline to regenerate benchmark artifacts.
          </p>
        )}
      </GlassCard>
    </div>
  );
}

function EvidenceCard({ icon: Icon, label, value, detail, tone }) {
  const toneClass = {
    emerald: "border-emerald-300/15 bg-emerald-300/[0.08] text-emerald-100",
    cyan: "border-cyan-300/15 bg-cyan-300/[0.08] text-cyan-100",
    violet: "border-violet-300/15 bg-violet-300/[0.08] text-violet-100",
    rose: "border-rose-300/15 bg-rose-300/[0.08] text-rose-100"
  }[tone];

  return (
    <div className={`rounded-xl border p-4 ${toneClass}`}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">{label}</p>
        <Icon size={18} />
      </div>
      <h3 className="text-lg font-black text-white">{value}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-400">{detail}</p>
    </div>
  );
}

function BenchmarkTable({ results }) {
  if (!results.length) {
    return <p className="text-sm text-slate-400">Benchmark results unavailable.</p>;
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="bg-white/[0.06] text-xs uppercase tracking-[0.18em] text-cyan-100">
          <tr>
            <th className="px-4 py-3">Model</th>
            <th className="px-4 py-3">Recall</th>
            <th className="px-4 py-3">F1</th>
            <th className="px-4 py-3">ROC AUC</th>
            <th className="px-4 py-3">PR AUC</th>
          </tr>
        </thead>
        <tbody>
          {results.map((item) => (
            <tr className="border-t border-white/10 text-slate-200" key={item.model}>
              <td className="px-4 py-3 font-black text-white">{item.model}</td>
              <td className="px-4 py-3">{formatMetric(item.holdout?.recall)}</td>
              <td className="px-4 py-3">{formatMetric(item.holdout?.f1_score)}</td>
              <td className="px-4 py-3">{formatMetric(item.holdout?.roc_auc)}</td>
              <td className="px-4 py-3">{formatMetric(item.holdout?.average_precision)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatMetric(value) {
  return `${Math.round((value ?? 0) * 1000) / 10}%`;
}

export default SystemInsights;
