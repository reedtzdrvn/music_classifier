# -*- coding: utf-8 -*-
"""Инференс + Grad-CAM объяснения для CNN и AST.

Обе модели возвращают усреднённые по окнам вероятности и тепловую карту
Grad-CAM, выровненную по отображаемой log-Mel-спектрограмме всего трека.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F

from . import audio as A
from . import config as C
from .models import BUNDLE


# --------------------------------------------------------------------------- #
# вспомогательные функции
# --------------------------------------------------------------------------- #
def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max())
    return e / e.sum()


def _cap(starts: list[int], n: int) -> list[int]:
    """Прореживает список окон до n равномерно распределённых (длинные треки)."""
    if len(starts) <= n:
        return starts
    idx = np.linspace(0, len(starts) - 1, n).astype(int)
    return [starts[i] for i in sorted(set(idx.tolist()))]


def _slice_cnn(logmel: np.ndarray, s: int) -> np.ndarray:
    w = logmel[:, s:s + C.WINDOW_FRAMES]
    if w.shape[1] < C.WINDOW_FRAMES:
        w = np.pad(w, ((0, 0), (0, C.WINDOW_FRAMES - w.shape[1])))
    return w


def _round2d(arr: np.ndarray) -> list[list[float]]:
    return np.round(arr, 3).astype(float).tolist()


def _finalize_cam(cam_full: np.ndarray, cnt: np.ndarray) -> np.ndarray:
    cnt = cnt.copy()
    cnt[cnt == 0] = 1.0
    return cam_full / cnt[None, :]


def _ast_last_layer(model):
    """Последний блок трансформера AST (совместимо с transformers 4.x и 5.x)."""
    backbone = model.audio_spectrogram_transformer
    if hasattr(backbone, "layers"):              # transformers >= 5.x
        return backbone.layers[-1]
    return backbone.encoder.layer[-1]            # transformers 4.x


# --------------------------------------------------------------------------- #
# CNN
# --------------------------------------------------------------------------- #
def analyze_cnn(logmel_full: np.ndarray):
    model = BUNDLE.cnn
    genres = BUNDLE.cnn_genres
    t_full = logmel_full.shape[1]

    starts = list(range(0, t_full - C.WINDOW_FRAMES + 1, C.WINDOW_FRAMES)) or [0]
    starts = _cap(starts, C.MAX_WINDOWS)

    # --- проход 1: вероятности по окнам (без градиентов) ---
    win_logits = []
    for s in starts:
        x = torch.from_numpy(_slice_cnn(logmel_full, s))[None, None]
        with torch.no_grad():
            win_logits.append(model(x)[0].numpy())
    win_logits = np.stack(win_logits)
    win_probs = np.stack([_softmax(l) for l in win_logits])
    mean_probs = win_probs.mean(0)
    mean_logits = win_logits.mean(0)
    cls = int(np.argmax(mean_probs))

    # --- проход 2: Grad-CAM по последнему свёрточному блоку для класса cls ---
    store = {}
    target = model.block4
    h1 = target.register_forward_hook(lambda m, i, o: store.__setitem__("a", o))
    h2 = target.register_full_backward_hook(lambda m, gi, go: store.__setitem__("g", go[0]))

    cam_full = np.zeros((C.N_MELS, t_full), dtype=np.float32)
    cnt = np.zeros(t_full, dtype=np.float32)
    for s in starts:
        x = torch.from_numpy(_slice_cnn(logmel_full, s))[None, None]
        model.zero_grad(set_to_none=True)
        logits = model(x)
        logits[0, cls].backward()
        a, g = store["a"], store["g"]                      # (1,512,h,w)
        weights = g.mean(dim=(2, 3), keepdim=True)         # GAP по градиентам
        cam = F.relu((weights * a).sum(1, keepdim=True))   # (1,1,h,w)
        cam = F.interpolate(cam, size=(C.N_MELS, C.WINDOW_FRAMES),
                            mode="bilinear", align_corners=False)
        cam = cam[0, 0].detach().numpy()
        e = min(s + C.WINDOW_FRAMES, t_full)
        cam_full[:, s:e] += cam[:, :e - s]
        cnt[s:e] += 1.0
    h1.remove(); h2.remove()

    return mean_probs, mean_logits, _finalize_cam(cam_full, cnt), genres


# --------------------------------------------------------------------------- #
# AST
# --------------------------------------------------------------------------- #
def analyze_ast(y16: np.ndarray, t_full: int):
    model = BUNDLE.ast
    fe = BUNDLE.ast_fe
    genres = BUNDLE.ast_genres
    win = int(C.SR_AST * C.AST_WINDOW_SEC)

    starts = list(range(0, max(1, len(y16) - win + 1), win)) or [0]
    starts = _cap(starts, C.MAX_WINDOWS)

    # --- проход 1: фичи + вероятности по окнам ---
    feats_cache = []
    win_logits = []
    for s in starts:
        seg = y16[s:s + win]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        feats = fe(seg, sampling_rate=C.SR_AST, return_tensors="pt")
        feats_cache.append((s, feats))
        with torch.no_grad():
            win_logits.append(model(**feats).logits[0].numpy())
    win_logits = np.stack(win_logits)
    win_probs = np.stack([_softmax(l) for l in win_logits])
    mean_probs = win_probs.mean(0)
    mean_logits = win_logits.mean(0)
    cls = int(np.argmax(mean_probs))

    # --- проход 2: Grad-CAM по токенам последнего блока трансформера ---
    f_dim = (C.N_MELS - 16) // 10 + 1   # 12 частотных патчей
    store = {}
    layer = _ast_last_layer(model)
    h1 = layer.register_forward_hook(
        lambda m, i, o: store.__setitem__("a", o[0] if isinstance(o, tuple) else o))
    h2 = layer.register_full_backward_hook(lambda m, gi, go: store.__setitem__("g", go[0]))

    cam_full = np.zeros((C.N_MELS, t_full), dtype=np.float32)
    cnt = np.zeros(t_full, dtype=np.float32)
    win_cols = int(round(C.AST_WINDOW_SEC * C.DISPLAY_FPS))
    for s, feats in feats_cache:
        model.zero_grad(set_to_none=True)
        logits = model(**feats).logits
        logits[0, cls].backward()
        a, g = store["a"], store["g"]                 # (1, seq, hidden)
        weights = g.mean(dim=1, keepdim=True)         # GAP градиентов по токенам -> (1,1,hidden)
        tok = F.relu((weights * a).sum(-1))[0]        # (seq,) важность токенов (Grad-CAM)
        patches = tok[2:]                             # убираем cls + distillation
        t_dim = patches.shape[0] // f_dim
        grid = patches[:f_dim * t_dim].reshape(f_dim, t_dim)   # (freq, time)
        grid = grid[None, None].detach()
        c0 = int(round((s / C.SR_AST) * C.DISPLAY_FPS))
        c1 = min(c0 + win_cols, t_full)
        width = max(1, c1 - c0)
        cam = F.interpolate(grid, size=(C.N_MELS, width),
                            mode="bilinear", align_corners=False)[0, 0].numpy()
        cam_full[:, c0:c1] += cam
        cnt[c0:c1] += 1.0
    h1.remove(); h2.remove()

    return mean_probs, mean_logits, _finalize_cam(cam_full, cnt), genres


# --------------------------------------------------------------------------- #
# публичная точка входа
# --------------------------------------------------------------------------- #
def analyze(path: str, model_name: str) -> dict:
    y22, y16, duration = A.load_audio(path)
    logmel_full = A.log_mel(y22)
    t_full = logmel_full.shape[1]

    if model_name == "cnn":
        probs, logits, cam_full, genres = analyze_cnn(logmel_full)
    elif model_name == "ast":
        probs, logits, cam_full, genres = analyze_ast(y16, t_full)
    else:
        raise ValueError(f"Неизвестная модель: {model_name}")

    mel_disp = A.normalize01(A.downsample_time(logmel_full, C.MAX_TIME_COLS))
    cam_disp = A.normalize01(A.downsample_time(cam_full, C.MAX_TIME_COLS))

    order = np.argsort(probs)[::-1]
    return {
        "model": model_name,
        "predicted_genre": genres[int(order[0])],
        "predicted_index": int(order[0]),
        "duration_sec": round(duration, 2),
        "classes": [
            {
                "genre": genres[i],
                "prob": float(probs[i]),
                "logit": float(logits[i]),
            }
            for i in order.tolist()
        ],
        "mel": _round2d(mel_disp),
        "gradcam": _round2d(cam_disp),
        "n_mels": C.N_MELS,
        "fmax": C.FMAX,
    }
