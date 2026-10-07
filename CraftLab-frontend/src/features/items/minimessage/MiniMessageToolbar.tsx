import { useState } from 'react'
import { Bold, Italic, Underline, Strikethrough, RotateCcw, Palette, Sparkles, ChevronDown } from 'lucide-react'
import { MINECRAFT_COLORS } from './minimessage'

interface MiniMessageToolbarProps {
  onWrapSelection: (openTag: string, closeTag: string) => void
  onInsertText: (text: string) => void
}

const GRADIENT_PRESETS = [
  { name: 'Flame (Fire)', start: '#ff2200', end: '#ffaa00' },
  { name: 'Frost (Ice)', start: '#00d2ff', end: '#e0ffff' },
  { name: 'Void (Nether)', start: '#8a2be2', end: '#ff1493' },
  { name: 'Emerald (Nature)', start: '#2ecc71', end: '#f1c40f' },
  { name: 'Amethyst (Mystic)', start: '#9b59b6', end: '#3498db' },
  { name: 'Gold Rush', start: '#e67e22', end: '#f39c12' },
]

export function MiniMessageToolbar({ onWrapSelection, onInsertText }: MiniMessageToolbarProps) {
  const [showColorPicker, setShowColorPicker] = useState(false)
  const [showGradientPicker, setShowGradientPicker] = useState(false)
  const [customStart, setCustomStart] = useState('#ff0055')
  const [customEnd, setCustomEnd] = useState('#ffaa00')

  return (
    <div className="flex flex-wrap items-center gap-1.5 p-1.5 bg-[#121217] border border-[#282833] rounded-lg text-xs mb-2 shadow-inner">
      {/* Basic Text Formatting */}
      <div className="flex items-center space-x-1 border-r border-[#2c2c38] pr-2 mr-1">
        <button
          type="button"
          onClick={() => onWrapSelection('<bold>', '</bold>')}
          title="Bold (<bold>...</bold>)"
          className="p-1.5 rounded hover:bg-[#202028] text-gray-300 hover:text-white transition"
        >
          <Bold className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={() => onWrapSelection('<italic>', '</italic>')}
          title="Italic (<italic>...</italic>)"
          className="p-1.5 rounded hover:bg-[#202028] text-gray-300 hover:text-white transition"
        >
          <Italic className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={() => onWrapSelection('<underlined>', '</underlined>')}
          title="Underline (<underlined>...</underlined>)"
          className="p-1.5 rounded hover:bg-[#202028] text-gray-300 hover:text-white transition"
        >
          <Underline className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={() => onWrapSelection('<strikethrough>', '</strikethrough>')}
          title="Strikethrough (<strikethrough>...</strikethrough>)"
          className="p-1.5 rounded hover:bg-[#202028] text-gray-300 hover:text-white transition"
        >
          <Strikethrough className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={() => onInsertText('<reset>')}
          title="Reset Formatting (<reset>)"
          className="p-1.5 rounded hover:bg-[#202028] text-gray-400 hover:text-red-400 transition"
        >
          <RotateCcw className="w-3 h-3" />
        </button>
      </div>

      {/* Minecraft 16 Colors Picker */}
      <div className="relative">
        <button
          type="button"
          onClick={() => {
            setShowColorPicker(!showColorPicker)
            setShowGradientPicker(false)
          }}
          className={`flex items-center space-x-1.5 px-2 py-1 rounded border text-[11px] transition ${
            showColorPicker
              ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
              : 'bg-[#181820] text-gray-300 border-[#2f2f3d] hover:bg-[#22222c]'
          }`}
        >
          <Palette className="w-3.5 h-3.5 text-amber-400" />
          <span>Colors</span>
          <ChevronDown className="w-3 h-3 text-gray-500" />
        </button>

        {showColorPicker && (
          <div className="absolute left-0 top-full mt-1.5 z-50 p-2.5 bg-[#171720] border border-[#303040] rounded-xl shadow-2xl grid grid-cols-4 gap-1.5 w-64 backdrop-blur-md">
            {Object.entries(MINECRAFT_COLORS).map(([colorName, colorData]) => (
              <button
                key={colorName}
                type="button"
                onClick={() => {
                  onWrapSelection(`<${colorName}>`, `</${colorName}>`)
                  setShowColorPicker(false)
                }}
                className="flex items-center space-x-1.5 p-1 rounded hover:bg-[#252535] transition text-left group"
                title={`${colorName} (${colorData.hex})`}
              >
                <span
                  className="w-3 h-3 rounded-full border border-black/50 shadow-sm flex-shrink-0"
                  style={{ backgroundColor: colorData.hex }}
                />
                <span className="text-[10px] text-gray-300 group-hover:text-white capitalize truncate">
                  {colorName.replace('_', ' ')}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* RPG Gradient Picker */}
      <div className="relative">
        <button
          type="button"
          onClick={() => {
            setShowGradientPicker(!showGradientPicker)
            setShowColorPicker(false)
          }}
          className={`flex items-center space-x-1.5 px-2 py-1 rounded border text-[11px] transition ${
            showGradientPicker
              ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
              : 'bg-[#181820] text-gray-300 border-[#2f2f3d] hover:bg-[#22222c]'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span>Gradients</span>
          <ChevronDown className="w-3 h-3 text-gray-500" />
        </button>

        {showGradientPicker && (
          <div className="absolute left-0 top-full mt-1.5 z-50 p-3 bg-[#171720] border border-[#303040] rounded-xl shadow-2xl w-72 space-y-2.5 backdrop-blur-md">
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-gray-400">
              RPG Gradient Presets
            </span>

            <div className="grid grid-cols-2 gap-1.5">
              {GRADIENT_PRESETS.map((p) => (
                <button
                  key={p.name}
                  type="button"
                  onClick={() => {
                    onWrapSelection(`<gradient:${p.start}:${p.end}>`, '</gradient>')
                    setShowGradientPicker(false)
                  }}
                  className="p-1.5 rounded bg-[#101016] border border-[#272736] hover:border-purple-500/50 transition flex items-center space-x-2 text-left"
                >
                  <span
                    className="w-3 h-3 rounded flex-shrink-0"
                    style={{
                      background: `linear-gradient(135deg, ${p.start}, ${p.end})`,
                    }}
                  />
                  <span className="text-[11px] text-gray-300 truncate">{p.name}</span>
                </button>
              ))}
            </div>

            <div className="pt-2 border-t border-[#262636] space-y-2">
              <span className="block text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                Custom Dual Stop
              </span>
              <div className="flex items-center space-x-2">
                <input
                  type="color"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                  className="w-7 h-7 rounded border border-[#3a3a4c] bg-transparent cursor-pointer"
                />
                <span className="text-[10px] text-gray-500 font-mono">to</span>
                <input
                  type="color"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                  className="w-7 h-7 rounded border border-[#3a3a4c] bg-transparent cursor-pointer"
                />
                <button
                  type="button"
                  onClick={() => {
                    onWrapSelection(`<gradient:${customStart}:${customEnd}>`, '</gradient>')
                    setShowGradientPicker(false)
                  }}
                  className="flex-1 py-1 px-2 text-[11px] bg-purple-600 hover:bg-purple-500 text-white rounded font-medium transition"
                >
                  Apply Gradient
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
