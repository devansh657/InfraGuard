import { useEffect, useMemo, useState } from "react";
import { Activity, BrainCircuit, Clock3, PauseCircle, PlayCircle } from "lucide-react";
import AlertFeed from "../components/AlertFeed.jsx";
import GlassCard from "../components/GlassCard.jsx";
import LiveChart from "../components/LiveChart.jsx";
import MetricGauge from "../components/MetricGauge.jsx";
import { ErrorBanner, PageHeader, normalizeHistory } from "./Dashboard.jsx";
import { getHistory, getLiveStatus, ingestLiveTick, readApiError } from "../services/api.js";

function LiveMonitor() {
  const [history, setHistory] = useState([]);
  const [liveStatus, setLiveStatus] = useState(null);
  const [lastTick, setLastTick] = useState(null);
  const [liveEnabled, setLiveEnabled] = useState(true);
  const [error, setError] = useState("");
  const [lastRefresh, setLastRefresh] = useState(null);

  async function refresh({ ingest = liveEnabled } = {}) {
    try {
      setError("");
      const status = await getLiveStatus();
      setLiveStatus(status);
      if (ingest) {
        setLastTick(await ingestLiveTick());
      }
      setHistory((await getHistory(120)).reverse());
      setLastRefresh(new Date());
    } catch (err) {
      setError(readApiError(err));
    }
  }

  useEffect(() => {
    refresh({ ingest: true });
  }, []);

  useEffect(() => {
    if (!liveEnabled) return undefined;
    const timer = setInterval(() => refresh({ ingest: true }), 4000);
    return () => clearInterval(timer);
  }, [liveEnabled]);

  const chartData = useMemo(() => normalizeHistory(history), [history]);
  const latest = chartData.at(-1) ?? {};
  const risk = lastTick?.analysis?.failure?.failure_probability ?? latest.failure_probability ?? 0;
  const prediction = lastTick?.analysis?.failure?.prediction;
  const anomaly = lastTick?.analysis?.anomaly?.is_anomaly;
  const driverTiles = buildDriverTiles(lastTick);
  const alerts = chartData
    .filter((item) => item.is_anomaly)
    .slice(-5)
    .reverse()
    .map((item) => ({
      id: item.id,
      severity: item.failure_prediction ? "critical" : "warning",
      title: item.failure_prediction ? "Failure point" : "Anomaly marker",
      message: `${item.time} - IDS alerts ${item.ids_alerts ?? 0}, auth failures ${item.auth_failures ?? 0}, latency ${(item.latency ?? 0).toFixed(1)}ms.`
    }));

  return (
    <div className="grid gap-6">
      <PageHeader
        eyebrow="secured stream replay"
        title="Live Monitor"
        subtitle="Sequentially replays secured telemetry samples, runs AI diagnosis, stores results, and updates the charts."
        action={() => refresh({ ingest: true })}
      />

      {error ? <ErrorBanner message={error} /> : null}

      <div className="grid grid-cols-[1fr_360px] gap-6 max-[1120px]:grid-cols-1">
        <div className="grid gap-6">
          <GlassCard>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.22em] text-cyan-200">Telemetry basis</p>
                <h2 className="mt-1 text-2xl font-black">Sequential Telemetry Replay</h2>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                  Each tick uses the next secured sample, predicts elevated load risk, runs Isolation Forest, then saves the result to history.
                </p>
              </div>
              <button
                className={`inline-flex min-h-12 items-center gap-2 rounded-2xl border px-5 text-sm font-black transition ${
                  liveEnabled
                    ? "border-amber-300/25 bg-amber-300/[0.14] text-amber-100 hover:bg-amber-300/[0.22]"
                    : "border-emerald-300/25 bg-emerald-300/[0.14] text-emerald-100 hover:bg-emerald-300/[0.22]"
                }`}
                onClick={() => setLiveEnabled((current) => !current)}
                type="button"
              >
                {liveEnabled ? <PauseCircle size={18} /> : <PlayCircle size={18} />}
                {liveEnabled ? "Pause live replay" : "Resume live replay"}
              </button>
            </div>
          </GlassCard>
          <LiveChart title="CPU stream" data={chartData} dataKey="cpu_usage" color="#34d399" unit="%" />
          <LiveChart title="Latency stream" data={chartData} dataKey="latency" color="#fb7185" unit="ms" area={false} />
          <LiveChart title="IDS alert stream" data={chartData} dataKey="ids_alerts" color="#fbbf24" unit="" />
        </div>

        <div className="grid content-start gap-6">
          <GlassCard glow>
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-xl font-black">Current Node</h2>
              <Activity className="text-emerald-200" size={22} />
            </div>
            <div className="grid gap-3">
              <MetricGauge label="CPU usage" value={latest.cpu_usage ?? 0} color="#34d399" />
              <MetricGauge label="Bandwidth" value={latest.bandwidth_utilization ?? 0} color="#60a5fa" />
              <MetricGauge label="IDS alerts" value={latest.ids_alerts ?? 0} max={14} color="#fbbf24" unit="" />
              <MetricGauge label="AI risk" value={Math.round(risk * 100)} color={risk >= 0.7 ? "#fb7185" : risk >= 0.35 ? "#fbbf24" : "#34d399"} />
            </div>
            <div className="mt-5 flex items-center gap-2 text-sm text-slate-400">
              <Clock3 size={16} />
              <span>{lastRefresh ? `Ticked ${lastRefresh.toLocaleTimeString()}` : "Waiting for telemetry"}</span>
            </div>
          </GlassCard>

          <GlassCard>
            <h2 className="mb-4 text-xl font-black">Replay State</h2>
            <div className="grid gap-3 text-sm text-slate-300">
              <InfoRow label="Mode" value={liveStatus?.mode ?? "checking"} />
              <InfoRow label="Dataset rows" value={liveStatus?.rows ?? 0} />
              <InfoRow label="Last replay row" value={lastTick?.record_index ?? "none"} />
              <InfoRow label="Actual label" value={formatActualLabel(lastTick?.actual_label)} />
              <InfoRow label="Model result" value={lastTick ? `${Math.round(risk * 100)}% risk` : "waiting"} />
              <InfoRow label="Anomaly engine" value={lastTick ? (anomaly ? "outlier pattern" : "normal envelope") : "waiting"} />
            </div>
            {lastTick?.explanation ? (
              <p className="mt-4 rounded-xl border border-white/10 bg-white/[0.04] p-4 text-sm leading-6 text-slate-300">
                {lastTick.explanation}
              </p>
            ) : null}
          </GlassCard>

          <GlassCard>
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-200">AI Trace</p>
                <h2 className="mt-1 text-xl font-black">Protected Outcome vs Model</h2>
              </div>
              <BrainCircuit className="text-cyan-200" size={22} />
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <VerdictCard label="Protected outcome" value={formatActualLabel(lastTick?.actual_label)} tone={lastTick?.actual_label ? "rose" : "emerald"} />
              <VerdictCard label="Model verdict" value={prediction ? "Anomalous load" : lastTick ? "Normal load" : "waiting"} tone={prediction ? "rose" : "emerald"} />
            </div>
            <div className="mt-4 grid gap-2">
              {driverTiles.length ? (
                driverTiles.map((item) => (
                  <div className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm" key={item.feature}>
                    <span className="truncate font-bold text-slate-300">{item.feature}</span>
                    <span className="font-mono text-cyan-100">{item.percent}% influence</span>
                  </div>
                ))
              ) : (
                <p className="rounded-xl border border-white/10 bg-white/[0.04] p-3 text-sm text-slate-400">
                  Driver chips appear after the next live inference tick.
                </p>
              )}
            </div>
          </GlassCard>

          <GlassCard>
            <h2 className="mb-4 text-xl font-black">Live Alerts</h2>
            <AlertFeed alerts={alerts} />
          </GlassCard>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/[0.035] px-3 py-2">
      <span className="font-bold text-slate-400">{label}</span>
      <span className="font-mono text-cyan-100">{value}</span>
    </div>
  );
}

function VerdictCard({ label, value, tone }) {
  const toneClass = tone === "rose"
    ? "border-rose-300/20 bg-rose-300/[0.09] text-rose-100"
    : "border-emerald-300/20 bg-emerald-300/[0.09] text-emerald-100";
  return (
    <div className={`rounded-xl border p-3 ${toneClass}`}>
      <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <p className="mt-1 font-black">{value}</p>
    </div>
  );
}

function formatActualLabel(label) {
  if (label === 1) return "Elevated risk";
  if (label === 0) return "Normal risk";
  return "unknown";
}

function buildDriverTiles(lastTick) {
  const explanation = lastTick?.analysis?.failure?.explanation ?? [];
  return explanation.slice(0, 4).map((item) => ({
    feature: item.feature,
    percent: Math.max(4, Math.min(100, Math.round((item.contribution ?? 0) * 100)))
  }));
}

export default LiveMonitor;
