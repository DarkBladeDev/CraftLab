import React from 'react'

export interface MinecraftColor {
  hex: string
  shadow: string
}

export const MINECRAFT_COLORS: Record<string, MinecraftColor> = {
  black: { hex: '#000000', shadow: '#000000' },
  dark_blue: { hex: '#0000AA', shadow: '#00002A' },
  dark_green: { hex: '#00AA00', shadow: '#002A00' },
  dark_aqua: { hex: '#00AAAA', shadow: '#002A2A' },
  dark_red: { hex: '#AA0000', shadow: '#2A0000' },
  dark_purple: { hex: '#AA00AA', shadow: '#2A002A' },
  gold: { hex: '#FFAA00', shadow: '#2A2A00' },
  gray: { hex: '#AAAAAA', shadow: '#2A2A2A' },
  dark_gray: { hex: '#555555', shadow: '#151515' },
  blue: { hex: '#5555FF', shadow: '#15153F' },
  green: { hex: '#55FF55', shadow: '#153F15' },
  aqua: { hex: '#55FFFF', shadow: '#153F3F' },
  red: { hex: '#FF5555', shadow: '#3F1515' },
  light_purple: { hex: '#FF55FF', shadow: '#3F153F' },
  yellow: { hex: '#FFFF55', shadow: '#3F3F15' },
  white: { hex: '#FFFFFF', shadow: '#3F3F3F' },
}

export const LEGACY_COLOR_MAP: Record<string, string> = {
  '0': 'black',
  '1': 'dark_blue',
  '2': 'dark_green',
  '3': 'dark_aqua',
  '4': 'dark_red',
  '5': 'dark_purple',
  '6': 'gold',
  '7': 'gray',
  '8': 'dark_gray',
  '9': 'blue',
  'a': 'green',
  'b': 'aqua',
  'c': 'red',
  'd': 'light_purple',
  'e': 'yellow',
  'f': 'white',
}

export const LEGACY_DECORATION_MAP: Record<string, string> = {
  k: 'obfuscated',
  l: 'bold',
  m: 'strikethrough',
  n: 'underlined',
  o: 'italic',
  r: 'reset',
}

export function hexToRgb(hex: string): [number, number, number] {
  let cleaned = hex.replace('#', '').trim()
  if (cleaned.length === 3) {
    cleaned = cleaned
      .split('')
      .map((c) => c + c)
      .join('')
  }
  const num = parseInt(cleaned, 16)
  if (isNaN(num)) return [255, 255, 255]
  return [(num >> 16) & 255, (num >> 8) & 255, num & 255]
}

export function rgbToHex(r: number, g: number, b: number): string {
  const clamp = (val: number) => Math.max(0, Math.min(255, Math.round(val)))
  return `#${((1 << 24) + (clamp(r) << 16) + (clamp(g) << 8) + clamp(b))
    .toString(16)
    .slice(1)}`
}

export function getDarkenedShadow(hex: string): string {
  const [r, g, b] = hexToRgb(hex)
  return rgbToHex(r * 0.25, g * 0.25, b * 0.25)
}

export function resolveColor(colorNameOrHex: string): { hex: string; shadow: string } {
  const lower = colorNameOrHex.toLowerCase().trim()
  if (MINECRAFT_COLORS[lower]) {
    return MINECRAFT_COLORS[lower]
  }
  if (lower.startsWith('#')) {
    return {
      hex: lower,
      shadow: getDarkenedShadow(lower),
    }
  }
  if (/^[0-9a-f]{6}$/i.test(lower)) {
    const fullHex = `#${lower}`
    return { hex: fullHex, shadow: getDarkenedShadow(fullHex) }
  }
  return MINECRAFT_COLORS.white
}

export function interpolateColor(colorA: string, colorB: string, factor: number): string {
  const [r1, g1, b1] = hexToRgb(colorA)
  const [r2, g2, b2] = hexToRgb(colorB)
  const r = r1 + (r2 - r1) * factor
  const g = g1 + (g2 - g1) * factor
  const b = b1 + (b2 - b1) * factor
  return rgbToHex(r, g, b)
}

export function interpolateMultiStop(stops: string[], factor: number): string {
  if (stops.length === 0) return '#ffffff'
  if (stops.length === 1) return stops[0]
  if (factor <= 0) return stops[0]
  if (factor >= 1) return stops[stops.length - 1]

  const totalSegments = stops.length - 1
  const scaled = factor * totalSegments
  const index = Math.floor(scaled)
  const segmentFactor = scaled - index
  const startColor = stops[index]
  const endColor = stops[Math.min(index + 1, stops.length - 1)]
  return interpolateColor(startColor, endColor, segmentFactor)
}

export function stripMiniMessage(text: string): string {
  if (!text) return ''
  let clean = text.replace(/[&§][0-9a-fk-or]/gi, '')
  clean = clean.replace(/<[^>]+>/g, '')
  return clean
}

export function translateLegacyToMiniMessage(text: string): string {
  if (!text) return ''
  return text.replace(/[&§]([0-9a-fk-or])/gi, (_, code) => {
    const lower = code.toLowerCase()
    if (LEGACY_COLOR_MAP[lower]) {
      return `<${LEGACY_COLOR_MAP[lower]}>`
    }
    if (LEGACY_DECORATION_MAP[lower]) {
      const dec = LEGACY_DECORATION_MAP[lower]
      return dec === 'reset' ? '<reset>' : `<${dec}>`
    }
    return ''
  })
}

interface FormatState {
  color?: string
  gradientStops?: string[]
  bold: boolean
  italic: boolean
  underlined: boolean
  strikethrough: boolean
  obfuscated: boolean
}

export function parseMiniMessage(input: string): React.ReactNode[] {
  if (!input) return []

  const normalized = translateLegacyToMiniMessage(input)
  const elements: React.ReactNode[] = []

  const tagRegex = /<(\/?[a-zA-Z0-9_#:]+)(?::([a-zA-Z0-9_#:]+))*>/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  const stateStack: FormatState[] = [
    {
      color: '#FFFFFF',
      bold: false,
      italic: false,
      underlined: false,
      strikethrough: false,
      obfuscated: false,
    },
  ]

  const getCurrentState = (): FormatState => {
    return { ...stateStack[stateStack.length - 1] }
  }

  const renderTextSegment = (text: string, state: FormatState, keyPrefix: string) => {
    if (!text) return null

    if (state.gradientStops && state.gradientStops.length >= 2) {
      const chars = Array.from(text)
      const count = chars.length
      return (
        <span key={keyPrefix} className="inline">
          {chars.map((char, charIdx) => {
            const factor = count > 1 ? charIdx / (count - 1) : 0
            const charHex = interpolateMultiStop(state.gradientStops!, factor)
            const charShadow = getDarkenedShadow(charHex)
            return (
              <span
                key={`${keyPrefix}-c-${charIdx}`}
                style={{
                  color: charHex,
                  textShadow: `1px 1px 0px ${charShadow}`,
                  fontWeight: state.bold ? 'bold' : 'normal',
                  fontStyle: state.italic ? 'italic' : 'normal',
                  textDecoration:
                    [
                      state.underlined ? 'underline' : '',
                      state.strikethrough ? 'line-through' : '',
                    ]
                      .filter(Boolean)
                      .join(' ') || undefined,
                }}
              >
                {char}
              </span>
            )
          })}
        </span>
      )
    }

    const resolved = resolveColor(state.color || '#FFFFFF')
    return (
      <span
        key={keyPrefix}
        style={{
          color: resolved.hex,
          textShadow: `1px 1px 0px ${resolved.shadow}`,
          fontWeight: state.bold ? 'bold' : 'normal',
          fontStyle: state.italic ? 'italic' : 'normal',
          textDecoration:
            [
              state.underlined ? 'underline' : '',
              state.strikethrough ? 'line-through' : '',
            ]
              .filter(Boolean)
              .join(' ') || undefined,
        }}
      >
        {text}
      </span>
    )
  }

  let elementCounter = 0

  while ((match = tagRegex.exec(normalized)) !== null) {
    const textBefore = normalized.slice(lastIndex, match.index)
    if (textBefore) {
      const seg = renderTextSegment(textBefore, getCurrentState(), `elem-${elementCounter++}`)
      if (seg) elements.push(seg)
    }

    const fullTag = match[0]
    const tagName = match[1]
    const rawTag = fullTag.slice(1, -1)

    lastIndex = match.index + fullTag.length

    if (tagName.startsWith('/')) {
      const closing = tagName.slice(1).toLowerCase()
      if (stateStack.length > 1) {
        stateStack.pop()
      } else {
        const base = getCurrentState()
        if (closing === 'b' || closing === 'bold') base.bold = false
        if (closing === 'i' || closing === 'italic' || closing === 'em') base.italic = false
        if (closing === 'u' || closing === 'underlined') base.underlined = false
        if (closing === 'st' || closing === 'strikethrough') base.strikethrough = false
        if (closing === 'gradient') base.gradientStops = undefined
        stateStack[0] = base
      }
      continue
    }

    const nextState = getCurrentState()

    if (rawTag === 'reset' || rawTag === 'r') {
      stateStack.push({
        color: '#FFFFFF',
        bold: false,
        italic: false,
        underlined: false,
        strikethrough: false,
        obfuscated: false,
      })
      continue
    }

    if (rawTag === 'bold' || rawTag === 'b') {
      nextState.bold = true
      stateStack.push(nextState)
      continue
    }

    if (rawTag === 'italic' || rawTag === 'i' || rawTag === 'em') {
      nextState.italic = true
      stateStack.push(nextState)
      continue
    }

    if (rawTag === 'underlined' || rawTag === 'u') {
      nextState.underlined = true
      stateStack.push(nextState)
      continue
    }

    if (rawTag === 'strikethrough' || rawTag === 'st') {
      nextState.strikethrough = true
      stateStack.push(nextState)
      continue
    }

    if (rawTag === 'obfuscated' || rawTag === 'obf') {
      nextState.obfuscated = true
      stateStack.push(nextState)
      continue
    }

    if (rawTag.startsWith('gradient:') || rawTag.startsWith('gradient')) {
      const parts = rawTag.split(':').slice(1)
      if (parts.length >= 2) {
        const hexStops = parts.map((p) => resolveColor(p).hex)
        nextState.gradientStops = hexStops
        nextState.color = hexStops[0]
        stateStack.push(nextState)
        continue
      }
    }

    let colorCandidate = rawTag
    if (colorCandidate.startsWith('color:')) {
      colorCandidate = colorCandidate.slice(6)
    }

    const resolved = resolveColor(colorCandidate)
    if (resolved) {
      nextState.color = resolved.hex
      nextState.gradientStops = undefined
      stateStack.push(nextState)
    }
  }

  const trailing = normalized.slice(lastIndex)
  if (trailing) {
    const seg = renderTextSegment(trailing, getCurrentState(), `elem-${elementCounter++}`)
    if (seg) elements.push(seg)
  }

  return elements
}
