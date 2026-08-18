import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import ContextTags from "../components/ContextTags.jsx";
import RiskBadge from "../components/RiskBadge.jsx";

const AVATAR_STYLES = {
  no_concern: "bg-sage-100 text-sage-700",
  insufficient_evidence: "bg-lavender-100 text-lavender-600",
  potential_concern: "bg-terracotta-100 text-terracotta-700",
  high_priority: "bg-coral-100 text-coral-700",
};

const RISK_ORDER = { high_priority: 0, potential_concern: 1, insufficient_evidence: 2, no_concern: 3 };

export default function Dashboard() {
  const [students, setStudents] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    function load() {
      api.listStudents().then(setStudents).catch((e) => setError(e.message));
    }
    load();
    // Poll so a message sent on the Student Chat page shows up here without a
    // manual refresh -- the "flags the student on the admin dashboard" part
    // of the demo flow.
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  if (error) return <ErrorBox message={error} />;

  const needsAttention = students.filter((s) => s.latest_risk_state === "high_priority" || s.latest_risk_state === "potential_concern").length;
  const healthy = students.filter((s) => s.latest_risk_state === "no_concern").length;
  const insufficient = students.filter((s) => s.latest_risk_state === "insufficient_evidence").length;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-extrabold text-ink">Student Overview</h1>
      <p className="mb-6 text-sm text-ink-light">
        Sorted by priority. These are AI-detected risk states, not diagnoses — open a student to see the evidence
        behind the score.
      </p>

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard icon="🔥" label="Needs attention" value={needsAttention} bg="bg-terracotta-500" />
        <StatCard icon="🌿" label="No concern" value={healthy} bg="bg-sage-500" />
        <StatCard icon="💭" label="Insufficient evidence" value={insufficient} bg="bg-lavender-500" />
      </div>

      <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-ink-faint">All students</h2>
      <div className="space-y-2.5">
        {[...students]
          .sort((a, b) => (RISK_ORDER[a.latest_risk_state] ?? 9) - (RISK_ORDER[b.latest_risk_state] ?? 9))
          .map((s) => (
            <Link
              key={s.student_id}
              to={`/students/${s.student_id}`}
              className="flex items-center gap-4 rounded-2xl bg-white p-4 shadow-soft transition-shadow hover:shadow-card"
            >
              <span
                className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-sm font-extrabold ${AVATAR_STYLES[s.latest_risk_state] ?? "bg-ink/8 text-ink-light"}`}
              >
                {s.student_id.slice(-2)}
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-bold text-ink">{s.student_id}</p>
                <ContextTags context={s.latest_top_context} />
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <RiskBadge state={s.latest_risk_state} />
                <span className="text-xs font-semibold tabular-nums text-ink-faint">score {s.latest_risk_score.toFixed(2)}</span>
              </div>
            </Link>
          ))}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, bg }) {
  return (
    <div className={`rounded-3xl p-5 text-white shadow-card ${bg}`}>
      <div className="mb-6 flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="text-3xl font-extrabold leading-none">{value}</p>
      <p className="mt-1 text-sm font-semibold text-white/85">{label}</p>
    </div>
  );
}

function ErrorBox({ message }) {
  return (
    <div className="rounded-2xl border border-coral-100 bg-coral-50 p-4 text-sm text-coral-700">
      Couldn't reach the backend ({message}). Is it running at http://localhost:8000 and have you run
      scripts/seed_db.py?
    </div>
  );
}
