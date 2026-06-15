# -*- coding: utf-8 -*-
"""Backend-шлюз (FastAPI).

Принимает аудиофайл от фронтенда, валидирует его и проксирует на сервис
инференса. Отдаёт фронтенду результат: жанр, вероятности, спектрограмму и
Grad-CAM объяснение.
"""
import os

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

INFERENCE_URL = os.environ.get("INFERENCE_URL", "http://inference:9000")
MAX_MB = float(os.environ.get("MAX_UPLOAD_MB", "30"))
ALLOWED_EXT = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
REQUEST_TIMEOUT = float(os.environ.get("INFERENCE_TIMEOUT", "180"))

app = FastAPI(title="Genre Classifier API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{INFERENCE_URL}/health")
            return {"status": "ok", "inference": r.json()}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, detail=f"Сервис инференса недоступен: {e}")


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...), model: str = Form("ast")):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            400, detail=f"Неподдерживаемый формат. Разрешены: {', '.join(sorted(ALLOWED_EXT))}")

    data = await file.read()
    size_mb = len(data) / (1024 * 1024)
    if size_mb > MAX_MB:
        raise HTTPException(413, detail=f"Файл больше {MAX_MB:.0f} МБ ({size_mb:.1f} МБ)")
    if not data:
        raise HTTPException(400, detail="Пустой файл")

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{INFERENCE_URL}/predict",
                files={"file": (file.filename, data, file.content_type or "application/octet-stream")},
                data={"model": model},
            )
    except httpx.RequestError as e:
        raise HTTPException(503, detail=f"Сервис инференса недоступен: {e}")

    if resp.status_code != 200:
        detail = resp.json().get("detail", resp.text) if resp.content else "Ошибка инференса"
        raise HTTPException(resp.status_code, detail=detail)
    return resp.json()
