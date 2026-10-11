import { useState, useEffect, useRef } from 'react'
import { Plus, Trash2, Sparkles, Copy, Check, AlertCircle } from 'lucide-react'
import {
  fetchParticles,
  saveParticle,
  deleteParticle,
  ParticleItem,
} from '../../../api/client'

export function ParticleStudioTab() {
  const [particles, setParticles] = useState<ParticleItem[]>([])
  const [selectedParticle, setSelectedParticle] = useState<ParticleItem | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Form State
  const [particleId, setParticleId] = useState('')
  const [textureRef, setTextureRef] = useState('craftlab:particle/spark')
  const [speed, setSpeed] = useState(4)
  const [spread, setSpread] = useState(5)
  const [rate, setRate] = useState(8)
  const [copied, setCopied] = useState(false)

  // Canvas Emitter Ref
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  const loadData = async () => {
    setLoading(true)
    setErrorMsg(null)
    try {
      const data = await fetchParticles()
      setParticles(data)
      if (data.length > 0 && !selectedParticle) {
        selectItem(data[0])
      } else if (data.length === 0) {
        resetForm()
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to load particles')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const selectItem = (item: ParticleItem) => {
    setSelectedParticle(item)
    setParticleId(item.id)
    setTextureRef(item.textures[0] || `craftlab:particle/${item.id}`)
    if (item.emitter) {
      setSpeed(item.emitter.speed ?? 4)
      setSpread(item.emitter.spread ?? 5)
      setRate(item.emitter.rate ?? 8)
    }
  }

  const resetForm = () => {
    setSelectedParticle(null)
    setParticleId('mystic_spark')
    setTextureRef('craftlab:particle/spark')
    setSpeed(4)
    setSpread(5)
    setRate(8)
  }

  const handleSave = async () => {
    if (!particleId.trim() || !textureRef.trim()) return
    setErrorMsg(null)
    try {
      await saveParticle({
        id: particleId.trim(),
        textures: [textureRef.trim()],
        emitter: { speed, spread, rate },
        namespace: 'craftlab',
      })
      await loadData()
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to save particle')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(`Delete particle definition '${id}'?`)) return
    try {
      await deleteParticle(id)
      setSelectedParticle(null)
      await loadData()
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to delete particle')
    }
  }

  // 60 FPS HTML5 Canvas Animation
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animFrame: number
    const activeParticles: Array<{
      x: number
      y: number
      vx: number
      vy: number
      alpha: number
      size: number
      color: string
    }> = []

    const spawn = () => {
      const sp = Number(spread)
      const spd = Number(speed)
      activeParticles.push({
        x: canvas.width / 2 + (Math.random() - 0.5) * sp * 18,
        y: canvas.height - 20,
        vx: (Math.random() - 0.5) * (sp * 0.7),
        vy: -(Math.random() * 2 + spd * 0.35),
        alpha: 1.0,
        size: Math.random() * 3 + 2,
        color: Math.random() > 0.4 ? '#f59e0b' : '#f43f5e',
      })
    }

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Spawner base pad
      ctx.fillStyle = '#222'
      ctx.fillRect(canvas.width / 2 - 12, canvas.height - 10, 24, 6)

      const spawnRate = Number(rate)
      if (Math.random() * 15 < spawnRate) {
        spawn()
      }

      for (let i = activeParticles.length - 1; i >= 0; i--) {
        const p = activeParticles[i]
        p.x += p.vx
        p.y += p.vy
        p.alpha -= 0.015

        if (p.alpha <= 0 || p.y < 0) {
          activeParticles.splice(i, 1)
          continue
        }

        ctx.save()
        ctx.globalAlpha = p.alpha
        ctx.fillStyle = p.color
        ctx.shadowColor = p.color
        ctx.shadowBlur = 6
        ctx.fillRect(p.x, p.y, p.size, p.size)
        ctx.restore()
      }

      animFrame = requestAnimationFrame(render)
    }

    render()

    return () => {
      cancelAnimationFrame(animFrame)
    }
  }, [speed, spread, rate])

  const command = `/particle craftlab:${particleId || 'spark'} ~ ~1 ~ 0.3 0.5 0.3 0.05 15`

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
      {/* Sidebar List */}
      <div className="lg:col-span-4 bg-[#141418] border border-[#23232b] rounded-xl p-4 flex flex-col space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-[#23232b]">
          <span className="text-xs font-semibold text-gray-200">Particles ({particles.length})</span>
          <button
            onClick={resetForm}
            className="flex items-center space-x-1 px-2.5 py-1 bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-500/30 text-xs font-medium rounded-lg transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Particle</span>
          </button>
        </div>

        <div className="space-y-1.5 overflow-y-auto max-h-[500px]">
          {particles.length === 0 ? (
            <div className="text-xs text-gray-500 py-6 text-center">No particles registered yet.</div>
          ) : (
            particles.map((p) => {
              const isSelected = selectedParticle?.id === p.id
              return (
                <div
                  key={p.id}
                  onClick={() => selectItem(p)}
                  className={`flex items-center justify-between p-2.5 rounded-lg border cursor-pointer transition text-xs ${
                    isSelected
                      ? 'bg-amber-500/10 border-amber-500/40 text-gray-100'
                      : 'bg-[#1c1c22] border-[#2b2b35] hover:bg-[#252530] text-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2.5 min-w-0">
                    <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
                    <div className="truncate">
                      <div className="font-semibold truncate">{p.id}</div>
                      <div className="text-gray-500 text-[11px] font-mono">{p.textures[0]}</div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(p.id)
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

      {/* Editor & Canvas Simulator */}
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
            <div>
              <label className="block text-gray-400 mb-1">Particle Identifier</label>
              <input
                type="text"
                value={particleId}
                onChange={(e) => setParticleId(e.target.value)}
                placeholder="e.g. mystic_spark"
                className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2.5 py-1.5 text-xs text-gray-100 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-gray-400 mb-1">Texture Sprite Path</label>
              <input
                type="text"
                value={textureRef}
                onChange={(e) => setTextureRef(e.target.value)}
                placeholder="craftlab:particle/spark"
                className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2.5 py-1.5 text-xs text-gray-100 font-mono focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="p-3 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-2.5">
              <span className="text-gray-400 font-medium block">Emitter Simulation Parameters</span>

              <div>
                <div className="flex justify-between text-[11px] text-gray-400 mb-1">
                  <span>Upward Velocity</span>
                  <span>{speed}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={speed}
                  onChange={(e) => setSpeed(Number(e.target.value))}
                  className="w-full accent-amber-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-gray-400 mb-1">
                  <span>Spread Dispersion</span>
                  <span>{spread}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={spread}
                  onChange={(e) => setSpread(Number(e.target.value))}
                  className="w-full accent-amber-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-gray-400 mb-1">
                  <span>Spawn Rate</span>
                  <span>{rate}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={rate}
                  onChange={(e) => setRate(Number(e.target.value))}
                  className="w-full accent-amber-500"
                />
              </div>
            </div>

            <button
              onClick={handleSave}
              disabled={loading}
              className="w-full py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition"
            >
              {selectedParticle ? 'Update Particle' : 'Save Particle'}
            </button>
          </div>

          {/* Canvas Emitter Simulator & Command */}
          <div className="space-y-3 text-xs flex flex-col justify-between">
            <div>
              <span className="text-gray-400 font-semibold block mb-2">Live Emitter Preview</span>
              <div className="h-48 bg-black/70 border border-white/5 rounded-xl flex items-center justify-center relative overflow-hidden">
                <canvas ref={canvasRef} width={380} height={190} className="w-full h-full" />
              </div>
            </div>

            <div className="p-3 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-1.5">
              <span className="text-gray-400 font-medium">In-Game Command:</span>
              <div className="flex items-center justify-between font-mono text-[11px] text-amber-300 bg-[#141418] p-2 rounded">
                <span className="truncate">{command}</span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(command)
                    setCopied(true)
                    setTimeout(() => setCopied(false), 2000)
                  }}
                  className="text-gray-400 hover:text-gray-200 ml-2"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
