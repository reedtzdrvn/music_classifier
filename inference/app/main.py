# -*- coding: utf-8 -*-
"""FastAPI-сервис инференса (роль «модельного сервера» в архитектуре).

Загружает CNN и AST один раз при старте, выполняет предсказание жанра,
строит log-Mel-спектрограмму и Grad-CAM объяснение.
"""
import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from . import config as C
from .models import BUNDLE
from .predictor import analyze


@asynccontextmanager
async def lifespan(app: FastAPI):
    BUNDLE.load()
    yield


app = FastAPI(title="Genre Inference Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "models": ["cnn", "ast"] if BUNDLE.cnn and BUNDLE.ast else [],
        "genres": C.GENRES,
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...), model: str = Form("ast")):
    model = model.lower()
    if model not in ("cnn", "ast"):
        raise HTTPException(400, detail="model должен быть 'cnn' или 'ast'")

    suffix = os.path.splitext(file.filename or "")[1] or ".audio"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(await file.read())
        tmp.close()
        result = analyze(tmp.name, model)
    except ValueError as e:
        raise HTTPException(422, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, detail=f"Ошибка инференса: {e}")
    finally:
        os.unlink(tmp.name)

    result["filename"] = file.filename
    return result
