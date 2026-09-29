import { AlertTriangle, CheckCircle2, Siren } from "lucide-react";
import { motion } from "framer-motion";

function AlertFeed({ alerts = [] }) {
  const displayAlerts = alerts.length ? alerts : [{ id: "quiet", severity: "safe", message: "No active incidents detected." }];

  return (
    <div className="grid gap-3">
      {displayAlerts.slice(0, 5).map((alert) => {
        const isCritical = alert.severity === "critical";
        const isWarning = alert.severity === "warning";
        const Icon = isCritical ? Siren : isWarning ? AlertTriangle : CheckCircle2;
        return (
          <motion.div
            className={`flex items-start gap-3 rounded-xl border p-4 ${
              isCritical
                ? "border-rose-300/25 bg-rose-400/10 text-rose-100"
                : isWarning
                  ? "border-amber-300/25 bg-amber-300/10 text-amber-100"
                  : "border-emerald-300/20 bg-emerald-300/10 text-emerald-100"
            }`}
            key={alert.id}
            initial={{ opacity: 0, x: 8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Icon size={18} className="mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-black">{alert.title ?? alert.severity?.toUpperCase() ?? "STATUS"}</p>
              <p className="mt-1 text-sm text-slate-300">{alert.message}</p>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

export default AlertFeed;
