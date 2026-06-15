# -*- coding: utf-8 -*-
"""Загрузка аудио и извлечение log-Mel-спектрограммы."""
from __future__ import annotations

import librosa
import numpy as np

from . import config as C


def load_audio(path: str) -> tuple[np.ndarray, np.ndarray, float]:
    """Возвращает (y_22k, y_16k, duration_sec).

    y_22k — для CNN и отображаемой спектрограммы, y_16k — для AST.
    """
    y, _ = librosa.load(path, sr=C.SR_CNN, mono=True)
    if y.size < C.SR_CNN // 2:  # короче 0.5 c — считаем повреждённым
        raise ValueError("Аудио слишком короткое или повреждено")
    duration = float(len(y) / C.SR_CNN)
    y16 = librosa.resample(y, orig_sr=C.SR_CNN, target_sr=C.SR_AST)
    return y.astype(np.float32), y16.astype(np.float32), duration


def log_mel(y22: np.ndarray) -> np.ndarray:
    """log-Mel-спектрограмма (128, T) — ровно как при обучении CNN."""
    mel = librosa.feature.melspectrogram(
        y=y22, sr=C.SR_CNN, n_fft=C.N_FFT, hop_length=C.HOP,
        n_mels=C.N_MELS, fmax=C.FMAX, power=2.0,
    )
    return np.log1p(mel).astype(np.float32)


def downsample_time(arr: np.ndarray, max_cols: int) -> np.ndarray:
    """Усредняет по оси времени до max_cols колонок (для компактной передачи)."""
    f, t = arr.shape
    if t <= max_cols:
        return arr
    # делим на max_cols примерно равных блоков и усредняем
    idx = np.linspace(0, t, max_cols + 1).astype(int)
    out = np.empty((f, max_cols), dtype=np.float32)
    for i in range(max_cols):
        a, b = idx[i], max(idx[i] + 1, idx[i + 1])
        out[:, i] = arr[:, a:b].mean(axis=1)
    return out


def normalize01(arr: np.ndarray) -> np.ndarray:
    lo, hi = float(arr.min()), float(arr.max())
    if hi - lo < 1e-8:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)
