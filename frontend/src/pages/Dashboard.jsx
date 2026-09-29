import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Activity, BrainCircuit, Cpu, Database, RadioTower, ShieldAlert, Zap } from "lucide-react";
import AlertFeed from "../components/AlertFeed.jsx";
import AIFlowMap from "../components/AIFlowMap.jsx";
import GlassCard from "../components/GlassCard.jsx";
import LiveChart from "../components/LiveChart.jsx";
import MetricGauge from "../components/MetricGauge.jsx";
import RiskMeter from "../components/RiskMeter.jsx";
import { getHealth, getHistory, getReport, ingestLiveTick, readApiError } from "../services/api.js";

function Dashboard() {
  const [health, setHealth] = useState(null);
  const [history, setHistory] = useState([]);
  const [report, setReport] = useState(null);
  const [lastTick, setLastTick] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      setError("");
      const tick = await ingestLiveTick();
      const [healthData, historyData, reportData] = await Promise.all([
        getHealth(),
        getHistory(100),
        getReport()
      ]);
      setLastTick(tick);
      setHealth(healthData);
      setHistory(historyData.reverse());
      setReport(reportData);
    } catch (err) {
      setError(readApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => clearInterval(timer);
  }, []);

  const chartData = useMemo(() => normalizeHistory(history), [history]);
  const latest = chartData.at(-1);
  const failureProbability = latest?.failure_probability ?? 0;
  const liveRisk = lastTick?.analysis?.failure?.failure_probability ?? failureProbability;
  const liveVerdict = lastTick?.analysis?.failure?.prediction ? "Anomalous load likely" : "Normal load likely";
  const driverTiles = buildDriverTiles(lastTick);
  const alerts = buildAlerts(history, report);

  return (
    <div className="grid gap-6">
      <PageHeader
        eyebrow="AI reliability control center"
        title="Command Center"
        subtitle="Live health, incident risk, and model-backed infrastructure signals."
        action={refresh}
      />

      {error ? <ErrorBanner message={error} /> : null}

      <AIFlowMap />

      <div className="grid grid-cols-[1.15fr_0.85fr] gap-6 max-[1120px]:grid-cols-1">
        <GlassCard glow className="min-h-[360px]">
          <div className="grid gap-6 lg:grid-cols-[1fr_230px]">
            <div>
              <div className="mb-6 flex items-center gap-3">
                <div className="grid h-11 w-11 place-items-center rounded-2xl bg-emerald-300 text-slate-950">
                  <RadioTower size={22} />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-400">Runtime status</p>
                  <h2 className="text-3xl font-black">{health?.status === "healthy" || health?.status === "ok" || health?.status === "running" ? "Operational" : "Checking"}</h2>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <MetricGauge label="CPU usage" value={latest?.cpu_usage ?? 0} color="#34d399" />
                <MetricGauge label="Bandwidth" value={latest?.bandwidth_utilization ?? 0} color="#60a5fa" />
                <MetricGauge label="Anomalous loads" value={report?.failures ?? 0} max={Math.max(report?.total_requests ?? 1, 1)} color="#fb7185" unit="" />
                <MetricGauge label="Anomalies" value={report?.anomalies ?? 0} max={Math.max(report?.total_requests ?? 1, 1)} color="#fbbf24" unit="" />
              </div>

              <div className="mt-5 rounded-xl border border-cyan-300/15 bg-cyan-300/[0.07] p-4 text-sm leading-6 text-slate-300">
                <div className="mb-2 flex items-center gap-2 text-cyan-100">
                  <Activity size={16} />
                  <strong>Live basis</strong>
                </div>
                {lastTick ? (
                  <span>
                    Replayed secured telemetry sample <strong className="text-white">#{lastTick.record_index}</strong>.
                    Protected outcome is <strong className="text-white">{formatProtectedOutcome(lastTick.actual_label)}</strong>,
                    while the model currently reports
                    <strong className="text-white"> {Math.round(liveRisk * 100)}%</strong> risk.
                  </span>
                ) : (
                  "Waiting for the first telemetry replay tick."
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-slate-950/45 p-4">
              <RiskMeter probability={liveRisk} />
              <p className="mt-2 text-center text-sm font-bold text-white">{liveVerdict}</p>
              <p className="mt-1 text-center text-xs text-slate-400">
                Calculated from the latest live replay diagnosis.
              </p>
              <div className="mt-4 grid gap-2">
                {driverTiles.length ? (
                  driverTiles.map((item) => (
                    <div className="rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2" key={item.feature}>
                      <div className="mb-1 flex items-center justify-between gap-3 text-xs">
                        <span className="truncate font-black text-slate-200">{item.feature}</span>
                        <span className="font-mono text-cyan-100">{item.percent}%</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                        <div className="h-full rounded-full bg-cyan-300" style={{ width: `${item.percent}%` }} />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="rounded-xl border border-white/10 bg-white/[0.04] p-3 text-xs text-slate-400">
                    Driver analysis appears after the first live tick.
                  </p>
                )}
              </div>
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.2em] text-cyan-200">Alert feed</p>
              <h2 className="mt-1 text-2xl font-black">Signal Watch</h2>
            </div>
            <Zap className="text-cyan-200" size={22} />
          </div>
          <AlertFeed alerts={alerts} />
        </GlassCard>
      </div>

      <div className="grid grid-cols-3 gap-6 max-[1120px]:grid-cols-1">
        <GlassCard className="min-h-36">
          <SignalSummary
            icon={BrainCircuit}
            label="Model decision"
            value={liveVerdict}
            detail={lastTick?.explanation ?? "Awaiting the next replay row and model explanation."}
          />
        </GlassCard>
        <GlassCard className="min-h-36">
          <SignalSummary
            icon={Database}
            label="Data stream"
            value="Secured replay"
            detail={`${history.length} stored predictions are driving the graphs and incident feed.`}
          />
        </GlassCard>
        <GlassCard className="min-h-36">
          <SignalSummary
            icon={RadioTower}
            label="Refresh cadence"
            value="5 second loop"
            detail="Every loop ingests one protected sample, runs inference, then refreshes health, history, and report data."
          />
        </GlassCard>
      </div>

      {loading ? (
        <SkeletonGrid />
      ) : chartData.length ? (
        <div className="grid grid-cols-2 gap-6 max-[980px]:grid-cols-1">
          <LiveChart title="CPU usage" data={chartData} dataKey="cpu_usage" color="#34d399" unit="%" />
          <LiveChart title="Bandwidth utilization" data={chartData} dataKey="bandwidth_utilization" color="#60a5fa" unit="%" />
          <LiveChart title="Latency pressure" data={chartData} dataKey="latency" color="#fb7185" unit="ms" area={false} />
          <LiveChart title="IDS alert flow" data={chartData} dataKey="ids_alerts" color="#fbbf24" unit="" />
        </div>
      ) : (
        <GlassCard>
          <div className="flex items-center gap-3 text-slate-300">
            <Database size={20} />
            <p>No prediction history yet. The live replay will populate charts as soon as the runtime is reachable.</p>
          </div>
        </GlassCard>
      )}
    </div>
  );
}

function SignalSummary({ icon: Icon, label, value, detail }) {
  return (
    <div className="flex h-full gap-4">
      <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-cyan-300/20 bg-cyan-300/[0.1] text-cyan-100">
        <Icon size={21} />
      </div>
      <div>
        <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">{label}</p>
        <h3 className="mt-1 text-xl font-black text-white">{value}</h3>
        <p className="mt-2 text-sm leading-6 text-slate-400">{detail}</p>
      </div>
    </div>
  );
}

export function PageHeader({ eyebrow, title, subtitle, action }) {
  return (
    <div className="flex items-end justify-between gap-4 max-[720px]:items-start max-[720px]:flex-col">
      <div>
        <p className="text-xs font-black uppercase tracking-[0.28em] text-emerald-200">{eyebrow}</p>
        <h1 className="mt-2 text-5xl font-black tracking-tight text-white max-[720px]:text-3xl">{title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">{subtitle}</p>
      </div>
      {action ? (
        <button
          className="inline-flex min-h-12 items-center gap-2 rounded-2xl border border-emerald-300/25 bg-emerald-300/[0.15] px-5 text-sm font-black text-emerald-100 transition hover:bg-emerald-300/25"
          onClick={action}
          type="button"
        >
          <Cpu size={18} />
          Refresh telemetry
        </button>
      ) : null}
    </div>
  );
}

export function ErrorBanner({ message }) {
  return (
    <div className="rounded-2xl border border-rose-300/25 bg-rose-500/[0.12] p-4 text-rose-100">
      <div className="flex items-center gap-3">
        <ShieldAlert size={20} />
        <p className="font-bold">{message}</p>
      </div>
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-2 gap-6 max-[980px]:grid-cols-1">
      {[0, 1, 2, 3].map((item) => (
        <motion.div
          className="h-72 rounded-3xl border border-white/10 bg-white/[0.045]"
          key={item}
          animate={{ opacity: [0.35, 0.75, 0.35] }}
          transition={{ repeat: Infinity, duration: 1.6, delay: item * 0.1 }}
        />
      ))}
    </div>
  );
}

export function normalizeHistory(history) {
  return history.map((item) => {
    let timeStr = "N/A";
    if (item.timestamp) {
      try {
        const d = new Date(item.timestamp);
        if (!isNaN(d.getTime())) {
          timeStr = d.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
          });
        }
      } catch (e) {
        console.error("Error parsing date:", e);
      }
    }
    return {
      ...item,
      time: timeStr
    };
  });
}

function buildAlerts(history, report) {
  const recent = [...history].reverse().slice(0, 8);
  const alerts = recent
    .filter((item) => item.is_anomaly || item.failure_prediction)
    .map((item) => {
      let timeStr = "N/A";
      if (item.timestamp) {
        try {
          const d = new Date(item.timestamp);
          if (!isNaN(d.getTime())) {
            timeStr = d.toLocaleTimeString();
          }
        } catch (e) {
          console.error(e);
        }
      }
      return {
        id: item.id,
        severity: item.failure_prediction ? "critical" : "warning",
        title: item.failure_prediction ? "Failure risk" : "Anomaly detected",
        message: `${timeStr} - CPU ${(item.cpu_usage ?? 0).toFixed(1)}%, IDS ${item.ids_alerts ?? 0}, anomaly score ${(item.anomaly_score ?? 0).toFixed(2)}.`
      };
    });

  if (report?.risk_level === "HIGH") {
    alerts.unshift({
      id: "risk-high",
      severity: "critical",
      title: "High platform risk",
      message: `${report.anomalies} anomalies across ${report.total_requests} stored predictions.`
    });
  }

  return alerts;
}

function formatProtectedOutcome(label) {
  if (label === 1) return "elevated";
  if (label === 0) return "normal";
  return "hidden";
}

function buildDriverTiles(lastTick) {
  const explanation = lastTick?.analysis?.failure?.explanation ?? [];
  return explanation.slice(0, 4).map((item) => ({
    feature: item.feature,
    percent: Math.max(4, Math.min(100, Math.round((item.contribution ?? 0) * 100)))
  }));
}

export default Dashboard;
