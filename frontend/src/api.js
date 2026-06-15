// Отправка аудиофайла на backend с отслеживанием прогресса загрузки.
export function analyzeTrack(file, model, onProgress) {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    form.append('file', file)
    form.append('model', model)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/analyze')

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }

    xhr.onload = () => {
      let body
      try {
        body = JSON.parse(xhr.responseText)
      } catch {
        body = null
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body)
      } else {
        reject(new Error(body?.detail || `Ошибка сервера (${xhr.status})`))
      }
    }
    xhr.onerror = () => reject(new Error('Сеть недоступна'))
    xhr.send(form)
  })
}
