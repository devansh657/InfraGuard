import { motion } from "framer-motion";

function MetricGauge({ label, value = 0, unit = "%", max = 100, color = "#34d399" }) {
  const normalized = Math.max(0, Math.min(100, (Number(value) / max) * 100));
  const display = Number.isFinite(Number(value)) ? Number(value).toFixed(1) : "0.0";

  return (
    <div className="metric-gauge rounded-xl border border-white/10 bg-slate-950/35 p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm font-bold text-slate-300">{label}</p>
        <span className="font-mono text-sm text-slate-300">{display}{unit}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <motion.div
          className="h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${normalized}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          style={{ background: color, boxShadow: `0 0 18px ${color}` }}
        />
      </div>
    </div>
  );
}

export default MetricGauge;
