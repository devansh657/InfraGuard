import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Clock3, Database, RadioTower, ShieldCheck, WifiOff } from "lucide-react";
import { getHealth, getLiveStatus, readApiError } from "../services/api.js";

function CommandPulse() {
  const [health, setHealth] = useState(null);
  const [liveStatus, setLiveStatus] = useState(null);
  const [error, setError] = useState("");
  const [checkedAt, setCheckedAt] = useState(null);

  async function refresh() {
    try {
      setError("");
      const [healthData, liveData] = await Promise.all([getHealth(), getLiveStatus()]);
      setHealth(healthData);
      setLiveStatus(liveData);
      setCheckedAt(new Date());
    } catch (err) {
      setError(readApiError(err));
      setCheckedAt(new Date());
    }
  }

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 8000);
    return () => clearInterval(timer);
  }, []);

  const healthy = ["healthy", "ok", "running"].includes(health?.status);
  const modelReady = Boolean(health?.ml_models_loaded);
  const databaseReady = Boolean(health?.db_connected);
  const statusText = error ? "Runtime offline" : healthy ? "Mission ready" : "Degraded";
  const uptime = useMemo(() => formatUptime(health?.uptime_seconds), [health]);

  return (
    <motion.section
      className="command-pulse relative mb-6 overflow-hidden rounded-2xl border border-white/10 bg-slate-950/50 p-4 shadow-2xl shadow-slate-950/30 backdrop-blur-2xl"
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-200/70 to-transparent" />
      <div className="grid grid-cols-[1.15fr_repeat(4,minmax(130px,1fr))] gap-3 max-[1180px]:grid-cols-2 max-[720px]:grid-cols-1">
        <div className="flex min-h-[76px] items-center gap-4 rounded-xl border border-white/10 bg-white/[0.045] px-4">
          <div className={`status-orbit ${error ? "status-orbit-offline" : healthy ? "status-orbit-online" : "status-orbit-watch"}`}>
            {error ? <WifiOff size={22} /> : <Activity size={22} />}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-black uppercase tracking-[0.24em] text-cyan-100">Control Link</p>
            <h2 className="truncate text-xl font-black text-white">{statusText}</h2>
            <p className="truncate text-xs text-slate-400">
              {error || "Encrypted local runtime channel"}
            </p>
          </div>
        </div>

        <PulseTile
          icon={ShieldCheck}
          label="Models"
          value={modelReady ? "Loaded" : "Checking"}
          tone={modelReady ? "emerald" : "amber"}
        />
        <PulseTile
          icon={Database}
          label="Database"
          value={databaseReady ? "Connected" : "Checking"}
          tone={databaseReady ? "cyan" : "amber"}
        />
        <PulseTile
          icon={RadioTower}
          label="Replay Row"
          value={`${liveStatus?.next_record_index ?? 0} / ${liveStatus?.rows ?? 0}`}
          tone="violet"
        />
        <PulseTile
          icon={Clock3}
          label="Uptime"
          value={uptime}
          tone="rose"
          subvalue={checkedAt ? `checked ${checkedAt.toLocaleTimeString()}` : "syncing"}
        />
      </div>
    </motion.section>
  );
}

function PulseTile({ icon: Icon, label, value, tone = "cyan", subvalue }) {
  const toneClass = {
    emerald: "border-emerald-300/15 bg-emerald-300/[0.075] text-emerald-100",
    cyan: "border-cyan-300/15 bg-cyan-300/[0.075] text-cyan-100",
    amber: "border-amber-300/15 bg-amber-300/[0.075] text-amber-100",
    violet: "border-violet-300/15 bg-violet-300/[0.075] text-violet-100",
    rose: "border-rose-300/15 bg-rose-300/[0.075] text-rose-100"
  }[tone];

  return (
    <div className={`min-h-[76px] rounded-xl border px-4 py-3 ${toneClass}`}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">{label}</p>
        <Icon size={17} />
      </div>
      <p className="truncate text-lg font-black text-white">{value}</p>
      <p className="mt-1 truncate text-[11px] text-slate-400">{subvalue ?? "live telemetry"}</p>
    </div>
  );
}

function formatUptime(seconds) {
  const total = Number(seconds);
  if (!Number.isFinite(total) || total < 0) return "Syncing";
  if (total < 60) return `${Math.round(total)}s`;
  const minutes = Math.floor(total / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  return `${hours}h ${remaining}m`;
}

export default CommandPulse;
