import { useState, useEffect } from 'react'
import { Server, RefreshCw, Plus } from 'lucide-react'
import { fetchTargets, registerTarget, Target } from '../../api/client'

export function TargetMonitor({ onSelectTarget, selectedTargetId }: {
  onSelectTarget?: (id: string) => void
  selectedTargetId?: string
}) {
  const [targets, setTargets] = useState<Target[]>([])
  const [loading, setLoading] = useState(false)
  const [newTargetId, setNewTargetId] = useState('')
  const [newTargetName, setNewTargetName] = useState('')
  const [showAdd, setShowAdd] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const data = await fetchTargets()
      setTargets(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const timer = setInterval(load, 5000)
    return () => clearInterval(timer)
  }, [])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTargetId) return
    await registerTarget(newTargetId, newTargetName || newTargetId)
    setNewTargetId('')
    setNewTargetName('')
    setShowAdd(false)
    load()
  }

  return (
    <div className="bg-[#16161a] border border-[#27272e] rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Server className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-gray-200">Server Fleet & Targets</h2>
          <span className="text-xs px-2 py-0.5 rounded-full bg-[#27272e] text-gray-400">
            {targets.length} registered
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => load()}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-[#27272e] transition"
            title="Refresh targets"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="flex items-center space-x-1 text-xs px-2.5 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Target</span>
          </button>
        </div>
      </div>

      {showAdd && (
        <form onSubmit={handleAdd} className="mb-4 p-3 bg-[#1e1e24] border border-[#2f2f38] rounded-lg space-y-3">
          <div className="text-xs font-medium text-gray-300">Enroll New Target Server</div>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="text"
              placeholder="Target ID (e.g. local-paper-server)"
              value={newTargetId}
              onChange={(e) => setNewTargetId(e.target.value)}
              className="px-3 py-1.5 text-xs bg-[#121215] border border-[#353540] rounded text-gray-200 focus:outline-none focus:border-emerald-500"
              required
            />
            <input
              type="text"
              placeholder="Display Name"
              value={newTargetName}
              onChange={(e) => setNewTargetName(e.target.value)}
              className="px-3 py-1.5 text-xs bg-[#121215] border border-[#353540] rounded text-gray-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setShowAdd(false)}
              className="text-xs px-3 py-1 rounded text-gray-400 hover:bg-[#27272e]"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="text-xs px-3 py-1 rounded bg-emerald-600 text-white font-medium hover:bg-emerald-500"
            >
              Save Target
            </button>
          </div>
        </form>
      )}

      {targets.length === 0 ? (
        <div className="py-6 text-center text-xs text-gray-500">
          No servers registered yet. Click &quot;Add Target&quot; or start Paper agent with targetId.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {targets.map((t) => {
            const isOnline = t.status === 'online'
            const isSelected = selectedTargetId === t.id
            return (
              <div
                key={t.id}
                onClick={() => onSelectTarget?.(t.id)}
                className={`p-3.5 rounded-lg border cursor-pointer transition flex items-start justify-between ${
                  isSelected
                    ? 'border-emerald-500 bg-emerald-950/20 shadow-md shadow-emerald-950/30'
                    : 'border-[#27272e] bg-[#1a1a20] hover:border-[#383842]'
                }`}
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-sm text-gray-200">{t.name}</span>
                    <span className="text-xs text-gray-500 font-mono">({t.id})</span>
                  </div>
                  <div className="mt-1 text-xs text-gray-400 space-y-0.5">
                    <div>
                      Paper:{' '}
                      <span className="text-gray-300 font-mono">
                        {t.environment_metadata?.minecraftVersion || '1.21.1'}
                      </span>
                    </div>
                    {t.last_seen_at && (
                      <div className="text-[11px] text-gray-500">
                        Heartbeat: {new Date(t.last_seen_at).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-1.5 pt-0.5">
                  <span
                    className={`inline-block w-2.5 h-2.5 rounded-full ${
                      isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'
                    }`}
                  />
                  <span
                    className={`text-xs font-semibold uppercase tracking-wider ${
                      isOnline ? 'text-emerald-400' : 'text-gray-500'
                    }`}
                  >
                    {isOnline ? 'Online' : 'Offline'}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
