import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import ContextTags from "../components/ContextTags.jsx";
import RiskBadge from "../components/RiskBadge.jsx";

export default function ReviewQueue() {
  const [queue, setQueue] = useState([]);
  const [error, setError] = useState(null);

  function load() {
    api.getReviewQueue().then(setQueue).catch((e) => setError(e.message));
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  async function handleReview(item) {
    await api.markReviewed(item.student_id, item.week, true);
    load();
  }

  if (error) return <div className="rounded-2xl border border-coral-100 bg-coral-50 p-4 text-sm text-coral-700">{error}</div>;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-extrabold text-ink">Review Queue</h1>
      <p className="mb-6 text-sm text-ink-light">
        AI detects, classifies, and prioritises — a human counsellor decides. Marking an item reviewed removes it
        from this queue.
      </p>

      {queue.length === 0 && (
        <div className="rounded-3xl bg-white p-8 text-center shadow-soft">
          <p className="text-3xl">✨</p>
          <p className="mt-2 text-sm font-semibold text-ink-light">Nothing pending review right now.</p>
        </div>
      )}

      <div className="space-y-3">
        {queue.map((item) => (
          <div
            key={`${item.student_id}-${item.week}`}
            className="rounded-2xl bg-white p-4 shadow-soft"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-3">
                <Link className="font-bold text-sage-700 hover:underline" to={`/students/${item.student_id}`}>
                  {item.student_id}
                </Link>
                <RiskBadge state={item.risk_state} />
                <ContextTags context={item.top_context} />
                <span className="text-sm font-semibold text-ink-faint">score {item.risk_score.toFixed(2)}</span>
              </div>
              <button
                onClick={() => handleReview(item)}
                className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-ink/85"
              >
                Mark reviewed
              </button>
            </div>
            {item.explanation && <p className="mt-3 text-sm leading-relaxed text-ink-light">{item.explanation}</p>}
            {item.routing === "safeguarding_pathway" && (
              <p className="mt-2 inline-block rounded-full bg-terracotta-100 px-3 py-1 text-xs font-semibold text-terracotta-700">
                ⚠ Safeguarding pathway — caregiver may be part of the concern
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
