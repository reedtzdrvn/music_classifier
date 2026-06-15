import { meta } from '../genres.js'

// Крупный блок с предсказанным жанром и уверенностью модели.
export default function GenreHero({ result }) {
  const top = result.classes[0]
  const m = meta(result.predicted_genre)
  const confidence = Math.round(top.prob * 100)

  return (
    <div className="hero card">
      <div className="hero-icon">{m.icon}</div>
      <div className="hero-body">
        <div className="hero-label">Предсказанный жанр</div>
        <div className="hero-genre">{result.predicted_genre}</div>
        <div className="hero-sub">{m.ru}</div>
      </div>
      <div className="hero-meta">
        <div className="hero-conf">
          <span className="hero-conf-val">{confidence}%</span>
          <span className="hero-conf-cap">уверенность</span>
        </div>
        <div className="hero-badges">
          <span className="badge badge-model">{result.model.toUpperCase()}</span>
          <span className="badge">{result.duration_sec}s</span>
        </div>
      </div>
    </div>
  )
}
