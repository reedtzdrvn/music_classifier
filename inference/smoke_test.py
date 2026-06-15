# -*- coding: utf-8 -*-
"""Локальная проверка инференса + Grad-CAM (без Docker).

Запуск из каталога inference/ с venv проекта:
    set CNN_CKPT=...\\runs\\cnn\\best.pt
    set AST_DIR=...\\runs\\ast\\best
    python smoke_test.py path\\to\\track.mp3
"""
import sys
import numpy as np

from app.models import BUNDLE
from app import predictor


def main():
    audio = sys.argv[1]
    print("Загрузка моделей...")
    BUNDLE.load()
    print("CNN жанры:", BUNDLE.cnn_genres)
    print("AST жанры:", BUNDLE.ast_genres)

    for model_name in ("cnn", "ast"):
        print(f"\n===== {model_name.upper()} =====")
        r = predictor.analyze(audio, model_name)
        mel = np.array(r["mel"])
        cam = np.array(r["gradcam"])
        print("predicted:", r["predicted_genre"], "| duration:", r["duration_sec"], "s")
        print("mel shape:", mel.shape, "range", round(mel.min(), 3), round(mel.max(), 3))
        print("cam shape:", cam.shape, "range", round(cam.min(), 3), round(cam.max(), 3))
        for c in r["classes"][:3]:
            print(f"  {c['genre']:>13s}  p={c['prob']:.3f}  logit={c['logit']:.2f}")
        assert mel.shape == cam.shape, "mel и gradcam должны совпадать по форме"
    print("\nOK")


if __name__ == "__main__":
    main()
