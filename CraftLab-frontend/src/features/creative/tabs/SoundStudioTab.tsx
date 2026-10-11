import { useState, useEffect } from 'react'
import { Plus, Trash2, Volume2, AlertTriangle, Check, AlertCircle } from 'lucide-react'
import {
  fetchSoundEvents,
  saveSoundEvent,
  deleteSoundEvent,
  probeAudioFile,
  convertAudioToMono,
  fetchCreativeNamespaces,
  SoundEventItem,
  AudioProbeResult,
} from '../../../api/client'

const CATEGORIES = ['master', 'blocks', 'player', 'ambient', 'hostile', 'neutral', 'voice', 'music']

export function SoundStudioTab() {
  const [soundEvents, setSoundEvents] = useState<SoundEventItem[]>([])
  const [selectedEvent, setSelectedEvent] = useState<SoundEventItem | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Namespace support
  const [namespace, setNamespace] = useState('craftlab')
  const [availableNamespaces, setAvailableNamespaces] = useState<string[]>(['craftlab'])

  // Form
  const [eventId, setEventId] = useState('')
  const [category, setCategory] = useState('blocks')
  const [subtitle, setSubtitle] = useState('')
  const [sampleName, setSampleName] = useState('craftlab:prop/door_open_1')
  const [volume, setVolume] = useState(1.0)
  const [pitch, setPitch] = useState(1.0)

  // Audio Probe State
  const [probeResult, setProbeResult] = useState<AudioProbeResult | null>(null)
  const [probing, setProbing] = useState(false)
  const [converting, setConverting] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setErrorMsg(null)
    try {
      const [nsList, data] = await Promise.all([
        fetchCreativeNamespaces().catch(() => ['craftlab']),
        fetchSoundEvents(),
      ])
      if (nsList && nsList.length > 0) {
        setAvailableNamespaces(nsList)
      }
      setSoundEvents(data)
      if (data.length > 0 && !selectedEvent) {
        selectItem(data[0])
      } else if (data.length === 0) {
        resetForm()
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to load sound events')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const selectItem = (item: SoundEventItem) => {
    setSelectedEvent(item)
    setEventId(item.id)
    setNamespace(item.namespace || 'craftlab')
    setCategory(item.category || 'blocks')
    setSubtitle(item.subtitle || '')
    const firstSound = item.sounds[0]
    if (typeof firstSound === 'string') {
      setSampleName(firstSound)
      setVolume(1.0)
      setPitch(1.0)
    } else if (firstSound && typeof firstSound === 'object') {
      setSampleName(firstSound.name || '')
      setVolume(firstSound.volume ?? 1.0)
      setPitch(firstSound.pitch ?? 1.0)
    }
    setProbeResult(null)
  }

  const resetForm = () => {
    setSelectedEvent(null)
    setEventId('prop.mystic_door.open')
    setNamespace('craftlab')
    setCategory('blocks')
    setSubtitle('subtitles.craftlab.door_creak')
    setSampleName('craftlab:prop/door_open_1')
    setVolume(1.0)
    setPitch(1.0)
    setProbeResult(null)
  }

  const handleEventIdChange = (val: string) => {
    if (val.includes(':')) {
      const parts = val.split(':')
      if (parts[0].trim()) {
        const ns = parts[0].trim()
        setNamespace(ns)
        setSampleName(`${ns}:prop/${parts.slice(1).join(':')}_1`)
      }
      setEventId(parts.slice(1).join(':'))
    } else {
      setEventId(val)
    }
  }

  const handleProbe = async () => {
    if (!sampleName) return
    setProbing(true)
    setErrorMsg(null)
    const effectiveNs = namespace.trim() || 'craftlab'
    const parts = sampleName.split(':')
    const ns = parts.length > 1 ? parts[0] : effectiveNs
    const pathPart = parts.length > 1 ? parts[1] : parts[0]
    const relativePath = `assets/${ns}/sounds/${pathPart}.ogg`

    try {
      const res = await probeAudioFile(relativePath)
      setProbeResult(res)
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to probe audio file')
    } finally {
      setProbing(false)
    }
  }

  const handleConvertMono = async () => {
    if (!sampleName) return
    setConverting(true)
    setErrorMsg(null)
    const effectiveNs = namespace.trim() || 'craftlab'
    const parts = sampleName.split(':')
    const ns = parts.length > 1 ? parts[0] : effectiveNs
    const pathPart = parts.length > 1 ? parts[1] : parts[0]
    const relativePath = `assets/${ns}/sounds/${pathPart}.ogg`

    try {
      const res = await convertAudioToMono(relativePath)
      setProbeResult(res.probe)
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to convert audio to mono')
    } finally {
      setConverting(false)
    }
  }

  const handleSave = async () => {
    if (!eventId.trim() || !sampleName.trim()) return
    setErrorMsg(null)
    const effectiveNs = namespace.trim() || 'craftlab'
    try {
      await saveSoundEvent({
        id: eventId.trim(),
        category,
        subtitle: subtitle.trim() || undefined,
        sounds: [
          {
            name: sampleName.trim(),
            volume: Number(volume),
            pitch: Number(pitch),
          },
        ],
        namespace: effectiveNs,
      })
      await loadData()
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to save sound event')
    }
  }

  const handleDelete = async (id: string, ns?: string) => {
    const fullId = ns ? `${ns}:${id}` : id
    if (!confirm(`Delete sound event '${fullId}'?`)) return
    try {
      await deleteSoundEvent(id, ns)
      setSelectedEvent(null)
      await loadData()
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to delete sound event')
    }
  }

  const effectiveNs = namespace.trim() || 'craftlab'

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
      <datalist id="sound-namespaces-list">
        {availableNamespaces.map((ns) => (
          <option key={ns} value={ns} />
        ))}
      </datalist>

      {/* Sidebar List */}
      <div className="lg:col-span-4 bg-[#141418] border border-[#23232b] rounded-xl p-4 flex flex-col space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-[#23232b]">
          <span className="text-xs font-semibold text-gray-200">Sound Events ({soundEvents.length})</span>
          <button
            onClick={resetForm}
            className="flex items-center space-x-1 px-2.5 py-1 bg-purple-600/20 hover:bg-purple-600/30 text-purple-400 border border-purple-500/30 text-xs font-medium rounded-lg transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Event</span>
          </button>
        </div>

        <div className="space-y-1.5 overflow-y-auto max-h-[500px]">
          {soundEvents.length === 0 ? (
            <div className="text-xs text-gray-500 py-6 text-center">No sound events registered yet.</div>
          ) : (
            soundEvents.map((s) => {
              const isSelected = selectedEvent?.id === s.id && (selectedEvent?.namespace || 'craftlab') === (s.namespace || 'craftlab')
              return (
                <div
                  key={`${s.namespace || 'craftlab'}:${s.id}`}
                  onClick={() => selectItem(s)}
                  className={`flex items-center justify-between p-2.5 rounded-lg border cursor-pointer transition text-xs ${
                    isSelected
                      ? 'bg-purple-500/10 border-purple-500/40 text-gray-100'
                      : 'bg-[#1c1c22] border-[#2b2b35] hover:bg-[#252530] text-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2.5 min-w-0">
                    <Volume2 className="w-4 h-4 text-purple-400 shrink-0" />
                    <div className="truncate">
                      <div className="font-semibold truncate">
                        <span className="text-purple-400 font-mono text-[11px]">{s.namespace || 'craftlab'}:</span>
                        {s.id}
                      </div>
                      <div className="text-gray-500 text-[11px] font-mono">{s.category}</div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(s.id, s.namespace)
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

      {/* Editor & Diagnostic */}
      <div className="lg:col-span-8 space-y-4">
        {errorMsg && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-[#141418] border border-[#23232b] rounded-xl p-4">
          {/* Controls */}
          <div className="space-y-3 text-xs">
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-gray-400 mb-1">Namespace</label>
                <input
                  type="text"
                  list="sound-namespaces-list"
                  value={namespace}
                  onChange={(e) => setNamespace(e.target.value.toLowerCase().trim())}
                  placeholder="craftlab"
                  className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2 py-1.5 text-xs text-purple-300 font-mono focus:outline-none focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Event ID</label>
                <input
                  type="text"
                  value={eventId}
                  onChange={(e) => handleEventIdChange(e.target.value)}
                  placeholder="e.g. prop.door.open"
                  className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2 py-1.5 text-xs text-gray-100 focus:outline-none focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2 py-1.5 text-xs text-gray-100 focus:outline-none focus:border-purple-500"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-gray-400 mb-1">Subtitle Key</label>
              <input
                type="text"
                value={subtitle}
                onChange={(e) => setSubtitle(e.target.value)}
                placeholder="subtitles.craftlab.door_creak"
                className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2.5 py-1.5 text-xs text-gray-100 focus:outline-none focus:border-purple-500 font-mono"
              />
            </div>

            <div className="p-3 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-gray-400">Sample Audio Path (.ogg)</label>
                <button
                  onClick={handleProbe}
                  disabled={probing}
                  className="text-purple-400 hover:text-purple-300 text-[11px] font-medium"
                >
                  {probing ? 'Probing...' : 'Check Audio'}
                </button>
              </div>
              <input
                type="text"
                value={sampleName}
                onChange={(e) => {
                  setSampleName(e.target.value)
                  setProbeResult(null)
                }}
                placeholder="craftlab:prop/door_open_1"
                className="w-full bg-[#141418] border border-[#2b2b35] rounded px-2.5 py-1 text-xs text-gray-100 font-mono focus:outline-none focus:border-purple-500"
              />

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="block text-gray-400 mb-1">Volume ({volume})</label>
                  <input
                    type="range"
                    min="0.1"
                    max="2.0"
                    step="0.05"
                    value={volume}
                    onChange={(e) => setVolume(Number(e.target.value))}
                    className="w-full accent-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-400 mb-1">Pitch ({pitch})</label>
                  <input
                    type="range"
                    min="0.5"
                    max="2.0"
                    step="0.05"
                    value={pitch}
                    onChange={(e) => setPitch(Number(e.target.value))}
                    className="w-full accent-purple-500"
                  />
                </div>
              </div>
            </div>

            <button
              onClick={handleSave}
              disabled={loading}
              className="w-full py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition"
            >
              {selectedEvent ? 'Update Sound Event' : 'Save Sound Event'}
            </button>
          </div>

          {/* Spatial Diagnostic & Downmixing */}
          <div className="space-y-3 text-xs flex flex-col justify-between">
            <div className="space-y-2">
              <span className="text-gray-400 font-semibold block">Spatial Audio Diagnostic</span>

              <div className="p-3 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-2">
                {probeResult ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Audio Channels:</span>
                      <span
                        className={`font-mono font-bold px-2 py-0.5 rounded text-xs ${
                          probeResult.is_mono
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}
                      >
                        {probeResult.is_mono ? 'Mono (3D Spatial Ready)' : 'Stereo (2 Channels)'}
                      </span>
                    </div>

                    {!probeResult.is_mono && (
                      <div className="p-2.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] space-y-2">
                        <div className="flex items-start space-x-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                          <span>Stereo sounds bypass 3D distance attenuation in Minecraft.</span>
                        </div>
                        <button
                          onClick={handleConvertMono}
                          disabled={converting}
                          className="w-full py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold transition"
                        >
                          {converting ? 'Converting...' : 'Convert to Mono'}
                        </button>
                      </div>
                    )}

                    {probeResult.is_mono && (
                      <div className="text-[11px] text-emerald-400 flex items-center space-x-1">
                        <Check className="w-3.5 h-3.5" />
                        <span>Valid single-channel audio. 3D attenuation active.</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-gray-500 py-4 text-center text-xs">
                    Click "Check Audio" to inspect channel count and 3D distance attenuation readiness.
                  </div>
                )}
              </div>
            </div>

            <div className="p-3 bg-[#1c1c22]/50 border border-[#23232b] rounded-lg text-[11px] text-gray-400">
              Sound events are compiled into <code className="text-purple-400">assets/{effectiveNs}/sounds.json</code> and automatically linked with Block Studio prop states.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
