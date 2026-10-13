import { useState, useEffect } from 'react'
import { Plus, Trash2, Copy, Check, AlertCircle } from 'lucide-react'
import {
  fetchGlyphs,
  registerGlyph,
  deleteGlyph,
  validateGlyphHex,
  fetchCreativeNamespaces,
  GlyphItem,
} from '../../../api/client'

export function GlyphStudioTab() {
  const [glyphs, setGlyphs] = useState<GlyphItem[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedGlyph, setSelectedGlyph] = useState<GlyphItem | null>(null)

  // Namespace support
  const [namespace, setNamespace] = useState('craftlab')
  const [availableNamespaces, setAvailableNamespaces] = useState<string[]>(['craftlab'])

  // Form state
  const [glyphId, setGlyphId] = useState('')
  const [fileRef, setFileRef] = useState('')
  const [customHex, setCustomHex] = useState('')
  const [height, setHeight] = useState(8)
  const [ascent, setAscent] = useState(7)
  const [hexStatus, setHexStatus] = useState<{ valid: boolean; message?: string } | null>(null)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    setErrorMsg(null)
    try {
      const [nsList, data] = await Promise.all([
        fetchCreativeNamespaces().catch(() => ['craftlab']),
        fetchGlyphs(),
      ])
      if (nsList && nsList.length > 0) {
        setAvailableNamespaces(nsList)
      }
      setGlyphs(data.glyphs)
      if (data.glyphs.length > 0 && !selectedGlyph) {
        selectItem(data.glyphs[0])
      } else if (data.glyphs.length === 0) {
        resetForm(data.next_available_hex)
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to load glyphs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const selectItem = (item: GlyphItem) => {
    setSelectedGlyph(item)
    setGlyphId(item.id)
    setNamespace(item.namespace || 'craftlab')
    setFileRef(item.file)
    setCustomHex(item.hex)
    setHeight(item.height)
    setAscent(item.ascent)
    setHexStatus({ valid: true })
  }

  const resetForm = (nextHex: string = '') => {
    setSelectedGlyph(null)
    setGlyphId('new_icon')
    setNamespace('craftlab')
    setFileRef('craftlab:font/new_icon.png')
    setCustomHex(nextHex || 'E001')
    setHeight(8)
    setAscent(7)
    setHexStatus({ valid: true })
  }

  const handleGlyphIdChange = (val: string) => {
    if (val.includes(':')) {
      const parts = val.split(':')
      if (parts[0].trim()) {
        const ns = parts[0].trim()
        setNamespace(ns)
        setFileRef(`${ns}:font/${parts.slice(1).join(':')}.png`)
      }
      setGlyphId(parts.slice(1).join(':'))
    } else {
      setGlyphId(val)
    }
  }

  const handleHexChange = async (val: string) => {
    const clean = val.trim().toUpperCase()
    setCustomHex(clean)
    if (!clean) {
      setHexStatus(null)
      return
    }
    try {
      const res = await validateGlyphHex(clean)
      setHexStatus(res)
    } catch {
      setHexStatus({ valid: false, message: 'Invalid hex format' })
    }
  }

  const handleSave = async () => {
    if (!glyphId.trim() || !fileRef.trim()) return
    setErrorMsg(null)
    const effectiveNs = namespace.trim() || 'craftlab'
    try {
      const saved = await registerGlyph({
        id: glyphId.trim(),
        file: fileRef.trim(),
        hex: customHex.trim() || undefined,
        height: Number(height),
        ascent: Number(ascent),
        namespace: effectiveNs,
      })
      await loadData()
      selectItem(saved)
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to save glyph')
    }
  }

  const handleDelete = async (hex: string, ns?: string) => {
    if (!confirm(`Delete glyph with character \\u${hex}?`)) return
    try {
      await deleteGlyph(hex, ns)
      setSelectedGlyph(null)
      await loadData()
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to delete glyph')
    }
  }

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const currentPreviewChar = customHex ? String.fromCharCode(parseInt(customHex, 16)) : selectedGlyph?.character || '★'

  const effectiveNs = namespace.trim() || 'craftlab'
  const canonicalPapiToken =
    effectiveNs === 'craftlab'
      ? `%craftlab_glyph_${glyphId}%`
      : `%craftlab_glyph_${effectiveNs}:${glyphId}%`

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
      <datalist id="glyph-namespaces-list">
        {availableNamespaces.map((ns) => (
          <option key={ns} value={ns} />
        ))}
      </datalist>

      {/* Sidebar List */}
      <div className="lg:col-span-4 bg-[#141418] border border-[#23232b] rounded-xl p-4 flex flex-col space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-[#23232b]">
          <span className="text-xs font-semibold text-gray-200">Registered Glyphs ({glyphs.length})</span>
          <button
            onClick={() => resetForm()}
            className="flex items-center space-x-1 px-2.5 py-1 bg-pink-600/20 hover:bg-pink-600/30 text-pink-400 border border-pink-500/30 text-xs font-medium rounded-lg transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Glyph</span>
          </button>
        </div>

        <div className="space-y-1.5 overflow-y-auto max-h-[500px]">
          {glyphs.length === 0 ? (
            <div className="text-xs text-gray-500 py-6 text-center">No glyphs registered yet.</div>
          ) : (
            glyphs.map((g) => {
              const isSelected = selectedGlyph?.hex === g.hex && (selectedGlyph?.namespace || 'craftlab') === (g.namespace || 'craftlab')
              return (
                <div
                  key={`${g.namespace || 'craftlab'}:${g.hex}`}
                  onClick={() => selectItem(g)}
                  className={`flex items-center justify-between p-2.5 rounded-lg border cursor-pointer transition text-xs ${
                    isSelected
                      ? 'bg-pink-500/10 border-pink-500/40 text-gray-100'
                      : 'bg-[#1c1c22] border-[#2b2b35] hover:bg-[#252530] text-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2.5 min-w-0">
                    <span className="w-6 h-6 rounded bg-black/40 border border-white/10 flex items-center justify-center font-mono text-xs text-pink-400">
                      {g.character}
                    </span>
                    <div className="truncate">
                      <div className="font-semibold truncate">
                        <span className="text-pink-400 font-mono text-[11px]">{g.namespace || 'craftlab'}:</span>
                        {g.id}
                      </div>
                      <div className="text-gray-500 text-[11px] font-mono">\u{g.hex}</div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(g.hex, g.namespace)
                    }}
                    className="text-gray-500 hover:text-red-400 p-1 transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Editor & Controls */}
      <div className="lg:col-span-8 space-y-4">
        {errorMsg && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-[#141418] border border-[#23232b] rounded-xl p-4">
          {/* Inputs */}
          <div className="space-y-3 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-gray-400 mb-1">Namespace</label>
                <input
                  type="text"
                  list="glyph-namespaces-list"
                  value={namespace}
                  onChange={(e) => setNamespace(e.target.value.toLowerCase().trim())}
                  placeholder="craftlab"
                  className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2.5 py-1.5 text-xs text-pink-300 font-mono focus:outline-none focus:border-pink-500"
                />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Identifier</label>
                <input
                  type="text"
                  value={glyphId}
                  onChange={(e) => handleGlyphIdChange(e.target.value)}
                  placeholder="e.g. badge_vip"
                  className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2.5 py-1.5 text-xs text-gray-100 focus:outline-none focus:border-pink-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-gray-400 mb-1">Texture File Reference</label>
              <input
                type="text"
                value={fileRef}
                onChange={(e) => setFileRef(e.target.value)}
                placeholder="craftlab:font/badge_vip.png"
                className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2.5 py-1.5 text-xs text-gray-100 font-mono focus:outline-none focus:border-pink-500"
              />
            </div>

            <div className="p-3 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Unicode Codepoint (PUA)</span>
                {hexStatus && (
                  <span
                    className={`text-[11px] px-1.5 py-0.5 rounded font-mono ${
                      hexStatus.valid
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-red-500/10 text-red-400 border border-red-500/20'
                    }`}
                  >
                    {hexStatus.valid ? 'Available' : hexStatus.message || 'Invalid'}
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-gray-500 font-mono">\u</span>
                <input
                  type="text"
                  maxLength={4}
                  value={customHex}
                  onChange={(e) => handleHexChange(e.target.value)}
                  placeholder="E001"
                  className="w-24 bg-[#141418] border border-[#2b2b35] text-pink-400 font-mono font-bold px-2 py-1 rounded text-center text-xs focus:outline-none focus:border-pink-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-gray-400 mb-1">Height (px)</label>
                <input
                  type="number"
                  value={height}
                  onChange={(e) => setHeight(Number(e.target.value))}
                  className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded px-2 py-1 text-xs text-gray-100"
                />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Ascent (Baseline)</label>
                <input
                  type="number"
                  value={ascent}
                  onChange={(e) => setAscent(Number(e.target.value))}
                  className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded px-2 py-1 text-xs text-gray-100"
                />
              </div>
            </div>

            <button
              onClick={handleSave}
              disabled={Boolean(loading || (hexStatus && !hexStatus.valid))}
              className="w-full py-2 bg-pink-600 hover:bg-pink-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition"
            >
              {selectedGlyph ? 'Update Glyph' : 'Save Glyph'}
            </button>
          </div>

          {/* Integration Snippets */}
          <div className="space-y-3 text-xs flex flex-col justify-between">
            <div className="space-y-2">
              <span className="text-gray-400 font-semibold">Snippets</span>

              <div className="p-2.5 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-1">
                <span className="text-[11px] text-gray-400">MiniMessage Tag:</span>
                <div className="flex items-center justify-between font-mono text-[11px] text-pink-300">
                  <span className="truncate">&lt;font:{effectiveNs}:default&gt;\u{customHex}&lt;/font&gt;</span>
                  <button
                    onClick={() => copyToClipboard(`<font:${effectiveNs}:default>\\u${customHex}</font>`, 'mm')}
                    className="text-gray-400 hover:text-gray-200 ml-2"
                  >
                    {copiedKey === 'mm' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="p-2.5 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-1">
                <span className="text-[11px] text-gray-400">PlaceholderAPI / LuckPerms:</span>
                <div className="flex items-center justify-between font-mono text-[11px] text-pink-300">
                  <span className="truncate">{canonicalPapiToken}</span>
                  <button
                    onClick={() => copyToClipboard(canonicalPapiToken, 'papi')}
                    className="text-gray-400 hover:text-gray-200 ml-2"
                  >
                    {copiedKey === 'papi' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="p-3 bg-[#1c1c22]/50 border border-[#2b2b35] rounded-lg text-[11px] text-gray-400">
              Font providers are stored in <code className="text-pink-400">assets/{effectiveNs}/font/default.json</code>.
            </div>
          </div>
        </div>

        {/* Live Simulator Preview */}
        <div className="bg-[#0e0e11] border border-[#23232b] rounded-xl p-4 space-y-3 font-mono">
          <div className="flex items-center justify-between text-xs text-gray-400 font-sans">
            <span>In-Game Chat Simulator</span>
            <span className="text-[11px] text-gray-500">Minecraft UI</span>
          </div>

          <div className="bg-black/70 p-3 rounded-lg border border-white/5 space-y-2 text-xs text-white">
            <div className="flex items-center space-x-1.5">
              <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold">
                {currentPreviewChar} VIP
              </span>
              <span className="text-emerald-400 font-bold">PlayerOne</span>
              <span className="text-gray-400">:</span>
              <span>Welcome to the server!</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs font-bold">
                🛡 STAFF
              </span>
              <span className="text-cyan-400 font-bold">Admin</span>
              <span className="text-gray-400">:</span>
              <span>Font baseline alignment is live.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
