import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client.js";
import ContextTags from "../components/ContextTags.jsx";
import ConversationFeed from "../components/ConversationFeed.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import RiskExplanation from "../components/RiskExplanation.jsx";
import TrendChart from "../components/TrendChart.jsx";

function SectionCard({ step, title, subtitle, children }) {
  return (
    <div className="mb-5 rounded-3xl bg-white p-5 shadow-soft">
      <div className="mb-4 flex items-start gap-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-sage-100 text-sm font-extrabold text-sage-700">
          {step}
        </span>
        <div>
          <h2 className="text-sm font-extrabold uppercase tracking-wide text-ink">{title}</h2>
          {subtitle && <p className="mt-0.5 text-xs text-ink-faint">{subtitle}</p>}
        </div>
      </div>
      {children}
    </div>
  );
}

export default function StudentProfile() {
  const { studentId } = useParams();
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  function load() {
    api.getStudent(studentId).then(setDetail).catch((e) => setError(e.message));
  }

  useEffect(load, [studentId]);

  if (error) return <div className="rounded-2xl border border-coral-100 bg-coral-50 p-4 text-sm text-coral-700">{error}</div>;
  if (!detail) return <div className="text-sm text-ink-light">Loading...</div>;

  const latest = detail.risk_assessments[detail.risk_assessments.length - 1];
  const canReview = latest && ["potential_concern", "high_priority"].includes(latest.risk_state);

  async function toggleReviewed() {
    setBusy(true);
    await api.markReviewed(studentId, latest.week, !latest.reviewed);
    load();
    setBusy(false);
  }

  return (
    <div>
      <Link to="/" className="mb-4 inline-flex items-center gap-1 text-sm font-semibold text-sage-700 hover:underline">
        &larr; Back to overview
      </Link>

      <div className="mb-6 flex items-center justify-between rounded-3xl bg-ink px-5 py-4 shadow-card">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-sm font-extrabold text-white">
            {detail.student_id.slice(-2)}
          </span>
          <div>
            <h1 className="text-xl font-extrabold text-white">{detail.student_id}</h1>
            <ContextTags context={latest?.top_context} />
          </div>
        </div>
        <RiskBadge state={latest?.risk_state} />
      </div>

      <SectionCard
        step="①"
        title="AI Conversation Analysis"
        subtitle="Recent AI-conversation snippets, each classified for contributing context and distress signal"
      >
        <ConversationFeed conversations={detail.conversations} />
      </SectionCard>

      <SectionCard
        step="②"
        title="Longitudinal Evidence (school signals)"
        subtitle="Attendance, academic score, and fused risk score over time, compared against this student's own baseline"
      >
        <TrendChart weeklySignals={detail.weekly_signals} riskAssessments={detail.risk_assessments} />
      </SectionCard>

      <SectionCard
        step="③"
        title="Evidence Fusion & Human Review"
        subtitle="Why the current score is what it is, and who should review it"
      >
        {latest && <RiskExplanation assessment={latest} />}
        {canReview && (
          <button
            onClick={toggleReviewed}
            disabled={busy}
            className="mt-4 rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-ink/85 disabled:opacity-50"
          >
            {latest.reviewed ? "Mark as unreviewed" : "Mark reviewed"}
          </button>
        )}
      </SectionCard>

      <div className="rounded-3xl bg-white p-5 shadow-soft">
        <h2 className="mb-3 text-sm font-extrabold uppercase tracking-wide text-ink">Week-by-week risk state</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs font-bold uppercase text-ink-faint">
              <tr>
                <th className="py-2 pr-4">Week</th>
                <th className="py-2 pr-4">Risk state</th>
                <th className="py-2 pr-4">Score</th>
                <th className="py-2">Context</th>
              </tr>
            </thead>
            <tbody>
              {detail.risk_assessments.map((r) => (
                <tr key={r.week} className="border-t border-cream-200">
                  <td className="py-2.5 pr-4 font-semibold text-ink">{r.week}</td>
                  <td className="py-2.5 pr-4"><RiskBadge state={r.risk_state} /></td>
                  <td className="py-2.5 pr-4 tabular-nums text-ink-light">{r.risk_score.toFixed(2)}</td>
                  <td className="py-2.5"><ContextTags context={r.top_context} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
