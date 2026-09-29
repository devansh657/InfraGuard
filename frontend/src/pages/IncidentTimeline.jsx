import { useEffect, useMemo, useState } from "react";
import { Activity, AlertOctagon, CheckCircle2, GitCommitVertical, RadioTower } from "lucide-react";
import GlassCard from "../components/GlassCard.jsx";
import { ErrorBanner, PageHeader } from "./Dashboard.jsx";
import { getHistory, readApiError } from "../services/api.js";

function IncidentTimeline() {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  async function refresh() {
    try {
      setError("");
      setHistory(await getHistory(100));
    } catch (err) {
      setError(readApiError(err));
    }
  }

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 7000);
    return () => clearInterval(timer);
  }, []);

  const events = useMemo(() => buildEvents(history), [history]);
  const summary = useMemo(() => ({
    total: events.length,
    critical: events.filter((event) => event.severity === "critical").length,
    warning: events.filter((event) => event.severity === "warning").length
  }), [events]);

  return (
    <div className="grid gap-6">
      <PageHeader
        eyebrow="system forensic timeline"
        title="Incident Timeline"
        subtitle="Chronological model outputs with anomaly markers and failure points."
        action={refresh}
      />

      {error ? <ErrorBanner message={error} /> : null}

      <div className="grid grid-cols-3 gap-4 max-[840px]:grid-cols-1">
        <TimelineSummary icon={RadioTower} label="Events tracked" value={summary.total} tone="cyan" />
        <TimelineSummary icon={AlertOctagon} label="Failure points" value={summary.critical} tone="rose" />
        <TimelineSummary icon={Activity} label="Anomaly markers" value={summary.warning} tone="amber" />
      </div>

      <GlassCard>
        <div className="grid gap-4">
          {events.length ? events.map((event) => <TimelineEvent event={event} key={event.id} />) : (
            <div className="rounded-xl border border-white/10 bg-white/[0.04] p-6 text-slate-300">
              No events yet. Use Live Monitor or Prediction Lab to generate entries.
            </div>
          )}
        </div>
      </GlassCard>
    </div>
  );
}

function TimelineSummary({ icon: Icon, label, value, tone }) {
  const toneClass = {
    cyan: "border-cyan-300/15 bg-cyan-300/[0.08] text-cyan-100",
    rose: "border-rose-300/15 bg-rose-300/[0.08] text-rose-100",
    amber: "border-amber-300/15 bg-amber-300/[0.08] text-amber-100"
  }[tone];

  return (
    <GlassCard className="min-h-28">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">{label}</p>
          <h2 className="mt-1 text-3xl font-black text-white">{value}</h2>
        </div>
        <div className={`grid h-11 w-11 place-items-center rounded-xl border ${toneClass}`}>
          <Icon size={20} />
        </div>
      </div>
    </GlassCard>
  );
}

function TimelineEvent({ event }) {
  const critical = event.severity === "critical";
  const warning = event.severity === "warning";
  const Icon = critical ? AlertOctagon : warning ? GitCommitVertical : CheckCircle2;
  const toneClass = critical
    ? "border-rose-300/20 bg-rose-300/10 text-rose-200"
    : warning
      ? "border-amber-300/20 bg-amber-300/10 text-amber-200"
      : "border-emerald-300/20 bg-emerald-300/10 text-emerald-200";

  return (
    <div className="grid grid-cols-[48px_1fr] gap-4">
      <div className={`grid h-12 w-12 place-items-center rounded-xl border ${toneClass}`}>
        <Icon size={20} />
      </div>
      <div className="rounded-xl border border-white/10 bg-slate-950/35 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-black text-white">{event.title}</h3>
          <span className="font-mono text-xs text-slate-400">{event.time}</span>
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-300">{event.message}</p>
      </div>
    </div>
  );
}

function buildEvents(history) {
  return history.map((item) => {
    const critical = item.failure_prediction === 1;
    const warning = item.is_anomaly;
    let timeStr = "N/A";
    if (item.timestamp) {
      try {
        const d = new Date(item.timestamp);
        if (!isNaN(d.getTime())) {
          timeStr = d.toLocaleString();
        }
      } catch (e) {
        console.error(e);
      }
    }
    return {
      id: item.id,
      severity: critical ? "critical" : warning ? "warning" : "safe",
      title: critical ? "Anomalous load prediction triggered" : warning ? "Anomaly marker detected" : "Normal telemetry sample",
      time: timeStr,
      message: `CPU ${(item.cpu_usage ?? 0).toFixed(1)}%, bandwidth ${(item.bandwidth_utilization ?? 0).toFixed(1)}%, IDS alerts ${item.ids_alerts ?? 0}, risk probability ${Math.round((item.failure_probability ?? 0) * 100)}%, anomaly score ${(item.anomaly_score ?? 0).toFixed(2)}.`
    };
  });
}

export default IncidentTimeline;
