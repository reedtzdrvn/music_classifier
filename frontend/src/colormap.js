// Простые перцептивные colormap'ы (интерполяция по опорным точкам).

function lerp(a, b, t) {
  return [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t,
  ]
}

function makeCmap(anchors) {
  const n = anchors.length - 1
  return (v) => {
    const t = Math.min(1, Math.max(0, v))
    const x = t * n
    const i = Math.min(n - 1, Math.floor(x))
    return lerp(anchors[i], anchors[i + 1], x - i)
  }
}

// Viridis — для самой спектрограммы
export const viridis = makeCmap([
  [68, 1, 84],
  [59, 82, 139],
  [33, 145, 140],
  [94, 201, 98],
  [253, 231, 37],
])

// Magma — тёмная база под Grad-CAM
export const magma = makeCmap([
  [0, 0, 4],
  [40, 11, 84],
  [101, 21, 110],
  [159, 42, 99],
  [212, 72, 66],
  [245, 125, 21],
  [252, 255, 164],
])

// «Тепловая» карта объяснения (Grad-CAM overlay): прозрачный -> жёлтый -> красный
export const heat = makeCmap([
  [69, 2, 86],
  [180, 30, 60],
  [240, 90, 40],
  [255, 200, 70],
  [255, 255, 200],
])
