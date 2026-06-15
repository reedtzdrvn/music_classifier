import { useEffect, useRef } from 'react'
import { viridis, magma, heat } from '../colormap.js'

// data: 2D массив [freq][time] значений 0..1 (row 0 — низкие частоты).
// overlay: опциональная Grad-CAM карта той же формы (0..1) для подсветки.
export default function Spectrogram({ data, overlay = null, duration = 0, fmax = 11025 }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    if (!data || !data.length) return
    const rows = data.length
    const cols = data[0].length
    const canvas = canvasRef.current

    // offscreen в нативном разрешении (cols x rows), затем растягиваем со сглаживанием
    const off = document.createElement('canvas')
    off.width = cols
    off.height = rows
    const octx = off.getContext('2d')
    const img = octx.createImageData(cols, rows)

    for (let y = 0; y < rows; y++) {
      const srcRow = rows - 1 - y // верх канваса = высокие частоты
      for (let x = 0; x < cols; x++) {
        const v = data[srcRow][x]
        let r, g, b
        if (overlay) {
          // тёмная база + раскалённая подсветка важных областей
          const base = magma(v * 0.85)
          const cam = overlay[srcRow][x]
          const a = Math.pow(cam, 1.4) * 0.9 // нелинейность — выделяем сильные зоны
          const hc = heat(cam)
          r = base[0] * (1 - a) + hc[0] * a
          g = base[1] * (1 - a) + hc[1] * a
          b = base[2] * (1 - a) + hc[2] * a
        } else {
          ;[r, g, b] = viridis(v)
        }
        const idx = (y * cols + x) * 4
        img.data[idx] = r
        img.data[idx + 1] = g
        img.data[idx + 2] = b
        img.data[idx + 3] = 255
      }
    }
    octx.putImageData(img, 0, 0)

    const ctx = canvas.getContext('2d')
    ctx.imageSmoothingEnabled = true
    ctx.imageSmoothingQuality = 'high'
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(off, 0, 0, canvas.width, canvas.height)
  }, [data, overlay])

  // подписи осей
  const timeTicks = duration
    ? [0, 0.25, 0.5, 0.75, 1].map((f) => ({
        left: `${f * 100}%`,
        label: fmt(f * duration),
      }))
    : []
  const freqTicks = [fmax, fmax * 0.75, fmax * 0.5, fmax * 0.25, 0].map((hz) => ({
    label: `${Math.round(hz / 100) / 10}k`,
  }))

  return (
    <div className="spec-wrap">
      <div className="spec-yaxis">
        {freqTicks.map((t, i) => (
          <span key={i}>{t.label}</span>
        ))}
      </div>
      <div className="spec-main">
        <canvas ref={canvasRef} width={900} height={320} className="spec-canvas" />
        <div className="spec-xaxis">
          {timeTicks.map((t, i) => (
            <span key={i} style={{ left: t.left }}>
              {t.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

function fmt(sec) {
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
