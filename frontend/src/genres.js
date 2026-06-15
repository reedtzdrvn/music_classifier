// Метаданные жанров FMA-small: русское название и эмодзи для оформления.
export const GENRE_META = {
  Electronic: { ru: 'Электроника', icon: '🎛️' },
  Experimental: { ru: 'Экспериментальная', icon: '🌀' },
  Folk: { ru: 'Фолк', icon: '🪕' },
  'Hip-Hop': { ru: 'Хип-хоп', icon: '🎤' },
  Instrumental: { ru: 'Инструментальная', icon: '🎻' },
  International: { ru: 'Этническая', icon: '🌍' },
  Pop: { ru: 'Поп', icon: '✨' },
  Rock: { ru: 'Рок', icon: '🎸' },
}

export function meta(genre) {
  return GENRE_META[genre] || { ru: genre, icon: '🎵' }
}
