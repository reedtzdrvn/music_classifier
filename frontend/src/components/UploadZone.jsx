import { useRef, useState } from 'react'

const ACCEPT = '.mp3,.wav,.flac,.ogg,.m4a,.aac'

// Зона загрузки трека: drag&drop + выбор файла + переключатель модели.
export default function UploadZone({ model, onModel, onFile, disabled }) {
  const inputRef = useRef(null)
  const [drag, setDrag] = useState(false)

  const pick = (files) => {
    if (files && files[0]) onFile(files[0])
  }

  return (
    <div className="card upload">
      <div className="model-toggle">
        <button
          className={`seg ${model === 'ast' ? 'seg-on' : ''}`}
          onClick={() => onModel('ast')}
          disabled={disabled}
        >
          AST <small>трансформер</small>
        </button>
        <button
          className={`seg ${model === 'cnn' ? 'seg-on' : ''}`}
          onClick={() => onModel('cnn')}
          disabled={disabled}
        >
          CNN <small>свёрточная</small>
        </button>
      </div>

      <div
        className={`dropzone${drag ? ' dropzone-active' : ''}${disabled ? ' dropzone-off' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDrag(false)
          if (!disabled) pick(e.dataTransfer.files)
        }}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <div className="drop-icon">🎵</div>
        <div className="drop-title">Перетащите аудиотрек сюда</div>
        <div className="drop-sub">или нажмите, чтобы выбрать файл</div>
        <div className="drop-formats">MP3 · WAV · FLAC · OGG · M4A — до 30 МБ</div>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          hidden
          onChange={(e) => pick(e.target.files)}
        />
      </div>
    </div>
  )
}
