import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function TrendChart({ weeklySignals, riskAssessments }) {
  const data = weeklySignals.map((signal) => {
    const risk = riskAssessments.find((r) => r.week === signal.week);
    return {
      week: signal.week,
      attendance: signal.attendance_pct,
      academic: signal.academic_score,
      risk_score: risk ? risk.risk_score : null,
    };
  });

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#EDE5D3" />
        <XAxis
          dataKey="week"
          label={{ value: "Week", position: "insideBottom", offset: -5 }}
          stroke="#9C8F84"
          tick={{ fill: "#6B5D53", fontSize: 12 }}
        />
        <YAxis yAxisId="left" domain={[0, 100]} stroke="#9C8F84" tick={{ fill: "#6B5D53", fontSize: 12 }} />
        <YAxis yAxisId="right" orientation="right" stroke="#9C8F84" tick={{ fill: "#6B5D53", fontSize: 12 }} />
        <Tooltip contentStyle={{ borderRadius: 12, borderColor: "#EDE5D3", fontFamily: "Nunito" }} />
        <Legend />
        <Line yAxisId="left" type="monotone" dataKey="attendance" stroke="#8CA888" dot={false} name="Attendance %" strokeWidth={2} />
        <Line yAxisId="left" type="monotone" dataKey="academic" stroke="#A99BC7" dot={false} name="Academic score" strokeWidth={2} />
        <Line yAxisId="right" type="monotone" dataKey="risk_score" stroke="#D96B5C" dot={false} name="Risk score" strokeWidth={2.5} />
      </LineChart>
    </ResponsiveContainer>
  );
}
