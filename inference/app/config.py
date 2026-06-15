# -*- coding: utf-8 -*-
"""Конфигурация сервиса инференса."""
import os

# --- Пути к обученным моделям (монтируются в docker-compose) ---
MODELS_DIR = os.environ.get("MODELS_DIR", "/models")
CNN_CKPT = os.environ.get("CNN_CKPT", os.path.join(MODELS_DIR, "cnn", "best.pt"))
AST_DIR = os.environ.get("AST_DIR", os.path.join(MODELS_DIR, "ast", "best"))

# --- Параметры извлечения признаков (CNN, как в обучении) ---
SR_CNN = 22050
N_FFT = 2048
HOP = 512
N_MELS = 128
FMAX = 11025
WINDOW_FRAMES = 216           # ~5 секунд при HOP=512
DISPLAY_FPS = SR_CNN / HOP    # ~43.07 фреймов/с — ось времени отображаемой спектрограммы

# --- Параметры AST ---
SR_AST = 16000
AST_WINDOW_SEC = 10.0

# Ограничение числа окон при анализе (защита от очень длинных треков)
MAX_WINDOWS = int(os.environ.get("MAX_WINDOWS", "24"))

# Размер отдаваемой клиенту спектрограммы по оси времени (даунсемплинг)
MAX_TIME_COLS = int(os.environ.get("MAX_TIME_COLS", "512"))

# Порядок классов фиксирован обучением на FMA-small (отсортированные жанры)
GENRES = [
    "Electronic", "Experimental", "Folk", "Hip-Hop",
    "Instrumental", "International", "Pop", "Rock",
]
