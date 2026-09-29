import { motion } from "framer-motion";

function GlassCard({ children, className = "", glow = false }) {
  return (
    <motion.section
      className={`premium-card relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.055] p-5 shadow-2xl shadow-slate-950/30 backdrop-blur-2xl ${glow ? "premium-card-glow" : ""} ${className}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className="relative">{children}</div>
    </motion.section>
  );
}

export default GlassCard;
