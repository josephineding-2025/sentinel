const BASE_URL = "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

export const api = {
  listStudents: () => request("/students"),
  getStudent: (studentId) => request(`/students/${studentId}`),
  getReviewQueue: () => request("/review/queue"),
  markReviewed: (studentId, week, reviewed) =>
    request(`/review/${studentId}/${week}`, {
      method: "POST",
      body: JSON.stringify({ reviewed }),
    }),
  sendMessage: (studentId, text) =>
    request(`/students/${studentId}/messages`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
};
