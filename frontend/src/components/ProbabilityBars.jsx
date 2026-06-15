import { meta } from '../genres.js'

// Логиты и вероятности по всем классам в виде анимированных полос.
export default function ProbabilityBars({ classes }) {
  return (
    <div className="card probs">
      <h3 className="section-title">Вероятности по классам</h3>
      <div className="probs-list">
        {classes.map((c, i) => {
          const pct = c.prob * 100
          const m = meta(c.genre)
          return (
            <div className={`prob-row${i === 0 ? ' prob-top' : ''}`} key={c.genre}>
              <div className="prob-name">
                <span className="prob-icon">{m.icon}</span>
                <span>{c.genre}</span>
              </div>
              <div className="prob-track">
                <div
                  className="prob-fill"
                  style={{ width: `${pct}%`, animationDelay: `${i * 60}ms` }}
                />
              </div>
              <div className="prob-vals">
                <span className="prob-pct">{pct.toFixed(1)}%</span>
                <span className="prob-logit">logit {c.logit.toFixed(2)}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
