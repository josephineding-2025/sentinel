from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, review, students

app = FastAPI(title="SENTINEL (AI Wellbeing Safety Net prototype)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(students.router)
app.include_router(review.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
