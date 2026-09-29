import { motion } from "framer-motion";

function RiskMeter({ probability = 0, label = "AI Risk" }) {
  const percent = Math.round(Math.max(0, Math.min(1, probability)) * 100);
  const color = percent >= 70 ? "#fb7185" : percent >= 35 ? "#fbbf24" : "#34d399";
  const state = percent >= 70 ? "CRITICAL" : percent >= 35 ? "WATCH" : "SAFE";
  const pulseClass = percent >= 70 ? "risk-pulse-critical" : percent >= 35 ? "risk-pulse-watch" : "risk-pulse-safe";

  return (
    <div className="grid place-items-center gap-4">
      <div className={`risk-meter-shell ${pulseClass} relative grid h-44 w-44 place-items-center`}>
        <motion.div
          className="absolute inset-[-10px] rounded-full border border-white/10"
          animate={{ rotate: 360 }}
          transition={{ duration: 16, repeat: Infinity, ease: "linear" }}
        />
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: `conic-gradient(${color} ${percent * 3.6}deg, rgba(255,255,255,0.08) 0deg)`
          }}
        />
        <div className="absolute inset-3 rounded-full bg-slate-950 shadow-inner shadow-black" />
        <div className="absolute inset-5 rounded-full border border-white/10" />
        <motion.div
          className="relative text-center"
          initial={{ scale: 0.92, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        >
          <p className="text-xs font-black uppercase tracking-[0.22em] text-slate-400">{label}</p>
          <strong className="mt-1 block text-4xl font-black" style={{ color }}>{percent}%</strong>
          <span className="text-xs font-black" style={{ color }}>{state}</span>
        </motion.div>
      </div>
    </div>
  );
}

export default RiskMeter;
