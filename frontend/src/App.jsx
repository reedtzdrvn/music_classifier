import { useState, useCallback } from 'react'
import { analyzeTrack } from './api.js'
import UploadZone from './components/UploadZone.jsx'
import GenreHero from './components/GenreHero.jsx'
import ProbabilityBars from './components/ProbabilityBars.jsx'
import Spectrogram from './components/Spectrogram.jsx'

export default function App() {
  const [model, setModel] = useState('ast')
  const [file, setFile] = useState(null)
  const [phase, setPhase] = useState('idle') // idle | uploading | analyzing | done | error
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const run = useCallback(async (f, mdl) => {
    setFile(f)
    setError(null)
    setResult(null)
    setProgress(0)
    setPhase('uploading')
    try {
      const data = await analyzeTrack(f, mdl, (pct) => {
        setProgress(pct)
        if (pct >= 100) setPhase('analyzing')
      })
      // Сохраняем исходное имя файла: берём из ответа бэкенда, а если его
      // там нет — из самого загруженного файла.
      setResult({ ...data, filename: data.filename || f.name })
      setPhase('done')
    } catch (e) {
      setError(e.message)
      setPhase('error')
    }
  }, [])

  const onFile = (f) => run(f, model)

  const onModel = (m) => {
    setModel(m)
    if (file && phase !== 'uploading' && phase !== 'analyzing') run(file, m)
  }

  const busy = phase === 'uploading' || phase === 'analyzing'

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-dot" />
          <span>GenreScope</span>
        </div>
        <div className="brand-sub">Классификация музыкальных жанров · AST / CNN · Grad-CAM</div>
      </header>

      <main className="container">
        <section className="landing">
          <div className="intro">
            <h1>
              Определите жанр трека <span className="grad">и&nbsp;поймите почему</span>
            </h1>
            <p>
              Загрузите аудио — нейросеть предскажет жанр, покажет вероятности всех классов,
              мел-спектрограмму и подсветит фрагменты, на которые она опиралась.
            </p>
          </div>

          <UploadZone model={model} onModel={onModel} onFile={onFile} disabled={busy} />
        </section>

        {busy && (
          <ProgressCard phase={phase} progress={progress} name={file?.name} />
        )}

        {phase === 'error' && (
          <div className="card error-card">
            <span className="error-icon">⚠️</span>
            <div>
              <div className="error-title">Не удалось обработать трек</div>
              <div className="error-msg">{error}</div>
            </div>
          </div>
        )}

        {phase === 'done' && result && (
          <div className="results">
            <div className="results-top">
              <GenreHero result={result} />
              <ProbabilityBars classes={result.classes} />
            </div>

            <div className="card spec-card">
              <h3 className="section-title">Мел-спектрограмма</h3>
              <p className="section-hint">
                Частотно-временное представление сигнала — то, что «видит» модель.
              </p>
              <Spectrogram
                data={result.mel}
                duration={result.duration_sec}
                fmax={result.fmax}
              />
            </div>

            <div className="card spec-card">
              <h3 className="section-title">
                Почему модель так решила · <span className="grad">Grad-CAM</span>
              </h3>
              <p className="section-hint">
                Подсвечены области спектрограммы, сильнее всего повлиявшие на выбор жанра
                «{result.predicted_genre}».
              </p>
              <Spectrogram
                data={result.mel}
                overlay={result.gradcam}
                duration={result.duration_sec}
                fmax={result.fmax}
              />
              <div className="legend">
                <span>слабое влияние</span>
                <div className="legend-bar" />
                <span>сильное влияние</span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function ProgressCard({ phase, progress, name }) {
  return (
    <div className="card progress-card">
      <div className="progress-head">
        <span className="spinner" />
        <span className="progress-name">{name}</span>
      </div>
      {phase === 'uploading' ? (
        <>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <div className="progress-label">Загрузка трека… {progress}%</div>
        </>
      ) : (
        <div className="progress-label analyzing">
          Анализ аудио и построение Grad-CAM…
        </div>
      )}
    </div>
  )
}
