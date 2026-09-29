import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

function LiveChart({ title, data, dataKey, color = "#34d399", unit = "", area = true }) {
  const Chart = area ? AreaChart : LineChart;
  const latest = data?.at?.(-1)?.[dataKey];
  const latestText = Number.isFinite(Number(latest)) ? `${Number(latest).toFixed(2)}${unit}` : "waiting";

  return (
    <div className="premium-chart relative min-h-[280px] overflow-hidden rounded-2xl border border-white/10 bg-white/[0.045] p-5 backdrop-blur-2xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-black text-white">{title}</h2>
          <p className="mt-1 text-xs text-slate-400">{data?.length ?? 0} stored ticks</p>
        </div>
        <div className="text-right">
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/[0.1] px-3 py-1 text-xs font-black text-emerald-100">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(52,211,153,0.8)]" />
            LIVE
          </span>
          <p className="mt-2 font-mono text-xs text-cyan-100">{latestText}</p>
        </div>
      </div>
      <div className="h-56 min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          <Chart data={data} margin={{ top: 8, right: 10, bottom: 0, left: -16 }}>
            <defs>
              <linearGradient id={`${dataKey}-gradient`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.45} />
                <stop offset="95%" stopColor={color} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="4 4" vertical={false} />
            <XAxis dataKey="time" tick={{ fill: "#94a3b8", fontSize: 11 }} stroke="rgba(255,255,255,0.1)" minTickGap={20} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
            <Tooltip
              formatter={(value) => [`${Number(value).toFixed(2)}${unit}`, title]}
              contentStyle={{
                background: "rgba(15,23,42,0.92)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 16,
                color: "#e2e8f0"
              }}
            />
            {area ? (
              <Area type="monotone" dataKey={dataKey} stroke={color} fill={`url(#${dataKey}-gradient)`} strokeWidth={2} dot={false} />
            ) : (
              <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} />
            )}
          </Chart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default LiveChart;
