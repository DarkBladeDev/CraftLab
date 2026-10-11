import { useState, useEffect } from 'react'
import { Plus, Trash2, Copy, Check, Shield, AlertCircle } from 'lucide-react'
import {
  fetchEquipmentModels,
  saveEquipmentModel,
  deleteEquipmentModel,
  fetchCreativeNamespaces,
  EquipmentModelItem,
  EquipmentLayer,
} from '../../../api/client'

const LAYER_TYPES = ['humanoid', 'humanoid_leggings', 'wings', 'horse', 'wolf', 'llama']
const SLOTS = ['head', 'chest', 'legs', 'feet', 'mainhand', 'offhand']

export function EquipmentStudioTab() {
  const [models, setModels] = useState<EquipmentModelItem[]>([])
  const [selectedModel, setSelectedModel] = useState<EquipmentModelItem | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Namespace support
  const [namespace, setNamespace] = useState('craftlab')
  const [availableNamespaces, setAvailableNamespaces] = useState<string[]>(['craftlab'])

  // Form
  const [modelId, setModelId] = useState('')
  const [targetSlot, setTargetSlot] = useState('chest')
  const [layers, setLayers] = useState<EquipmentLayer[]>([
    { texture: 'craftlab:paladin', type: 'humanoid' },
  ])
  const [copied, setCopied] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setErrorMsg(null)
    try {
      const [nsList, data] = await Promise.all([
        fetchCreativeNamespaces().catch(() => ['craftlab']),
        fetchEquipmentModels(),
      ])
      if (nsList && nsList.length > 0) {
        setAvailableNamespaces(nsList)
      }
      setModels(data)
      if (data.length > 0 && !selectedModel) {
        selectItem(data[0])
      } else if (data.length === 0) {
        resetForm()
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to load equipment models')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const selectItem = (item: EquipmentModelItem) => {
    setSelectedModel(item)
    setModelId(item.id)
    setNamespace(item.namespace || 'craftlab')
    setLayers(item.layers.length > 0 ? item.layers : [{ texture: `${item.namespace || 'craftlab'}:${item.id}`, type: 'humanoid' }])
  }

  const resetForm = () => {
    setSelectedModel(null)
    setModelId('paladin_set')
    setNamespace('craftlab')
    setTargetSlot('chest')
    setLayers([
      { texture: 'craftlab:paladin', type: 'humanoid' },
      { texture: 'craftlab:paladin_overlay', type: 'humanoid', dyeable: true },
    ])
  }

  const handleModelIdChange = (val: string) => {
    if (val.includes(':')) {
      const parts = val.split(':')
      if (parts[0].trim()) setNamespace(parts[0].trim())
      setModelId(parts.slice(1).join(':'))
    } else {
      setModelId(val)
    }
  }

  const addLayer = () => {
    const currentNs = namespace.trim() || 'craftlab'
    setLayers([...layers, { texture: `${currentNs}:layer_${layers.length + 1}`, type: 'humanoid' }])
  }

  const updateLayer = (idx: number, patch: Partial<EquipmentLayer>) => {
    const next = [...layers]
    next[idx] = { ...next[idx], ...patch }
    setLayers(next)
  }

  const removeLayer = (idx: number) => {
    if (layers.length <= 1) return
    setLayers(layers.filter((_, i) => i !== idx))
  }

  const handleSave = async () => {
    if (!modelId.trim() || layers.length === 0) return
    setErrorMsg(null)
    const effectiveNs = namespace.trim() || 'craftlab'
    try {
      await saveEquipmentModel({
        id: modelId.trim(),
        layers: layers,
        namespace: effectiveNs,
      })
      await loadData()
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to save equipment model')
    }
  }

  const handleDelete = async (id: string, ns?: string) => {
    const fullId = ns ? `${ns}:${id}` : id
    if (!confirm(`Delete equipment model '${fullId}'?`)) return
    try {
      await deleteEquipmentModel(id, ns)
      setSelectedModel(null)
      await loadData()
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to delete equipment model')
    }
  }

  const effectiveNs = namespace.trim() || 'craftlab'
  const equippableSnippet = `"minecraft:equippable": { "slot": "${targetSlot}", "model": "${effectiveNs}:${modelId}" }`

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
      <datalist id="equipment-namespaces-list">
        {availableNamespaces.map((ns) => (
          <option key={ns} value={ns} />
        ))}
      </datalist>

      {/* Sidebar List */}
      <div className="lg:col-span-4 bg-[#141418] border border-[#23232b] rounded-xl p-4 flex flex-col space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-[#23232b]">
          <span className="text-xs font-semibold text-gray-200">Equipment Models ({models.length})</span>
          <button
            onClick={resetForm}
            className="flex items-center space-x-1 px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 text-xs font-medium rounded-lg transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Model</span>
          </button>
        </div>

        <div className="space-y-1.5 overflow-y-auto max-h-[500px]">
          {models.length === 0 ? (
            <div className="text-xs text-gray-500 py-6 text-center">No equipment models found.</div>
          ) : (
            models.map((m) => {
              const isSelected = selectedModel?.id === m.id && (selectedModel?.namespace || 'craftlab') === (m.namespace || 'craftlab')
              return (
                <div
                  key={`${m.namespace || 'craftlab'}:${m.id}`}
                  onClick={() => selectItem(m)}
                  className={`flex items-center justify-between p-2.5 rounded-lg border cursor-pointer transition text-xs ${
                    isSelected
                      ? 'bg-blue-500/10 border-blue-500/40 text-gray-100'
                      : 'bg-[#1c1c22] border-[#2b2b35] hover:bg-[#252530] text-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2.5 min-w-0">
                    <Shield className="w-4 h-4 text-blue-400 shrink-0" />
                    <div className="truncate">
                      <div className="font-semibold truncate">
                        <span className="text-blue-400 font-mono text-[11px]">{m.namespace || 'craftlab'}:</span>
                        {m.id}
                      </div>
                      <div className="text-gray-500 text-[11px] font-mono">{m.layers.length} layers</div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(m.id, m.namespace)
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

      {/* Editor & Preview */}
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
                  list="equipment-namespaces-list"
                  value={namespace}
                  onChange={(e) => setNamespace(e.target.value.toLowerCase().trim())}
                  placeholder="craftlab"
                  className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2 py-1.5 text-xs text-blue-300 font-mono focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Model ID</label>
                <input
                  type="text"
                  value={modelId}
                  onChange={(e) => handleModelIdChange(e.target.value)}
                  placeholder="e.g. paladin_set"
                  className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2 py-1.5 text-xs text-gray-100 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Slot</label>
                <select
                  value={targetSlot}
                  onChange={(e) => setTargetSlot(e.target.value)}
                  className="w-full bg-[#1c1c22] border border-[#2b2b35] rounded-lg px-2 py-1.5 text-xs text-gray-100 focus:outline-none focus:border-blue-500"
                >
                  {SLOTS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Layers */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-gray-400 font-semibold">
                <span>Model Layers</span>
                <button onClick={addLayer} className="text-blue-400 hover:text-blue-300">
                  + Add Layer
                </button>
              </div>

              {layers.map((layer, idx) => (
                <div key={idx} className="p-2.5 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono text-gray-400">Layer {idx + 1}</span>
                    {layers.length > 1 && (
                      <button onClick={() => removeLayer(idx)} className="text-gray-500 hover:text-red-400">
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                  <div>
                    <input
                      type="text"
                      value={layer.texture}
                      onChange={(e) => updateLayer(idx, { texture: e.target.value })}
                      placeholder="craftlab:entity/equipment/paladin"
                      className="w-full bg-[#141418] border border-[#2b2b35] rounded px-2 py-1 text-xs text-gray-100 font-mono"
                    />
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <select
                      value={layer.type || 'humanoid'}
                      onChange={(e) => updateLayer(idx, { type: e.target.value })}
                      className="bg-[#141418] border border-[#2b2b35] rounded px-2 py-0.5 text-[11px] text-gray-300"
                    >
                      {LAYER_TYPES.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>

                    <label className="flex items-center space-x-1.5 text-[11px] text-gray-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={Boolean(layer.dyeable)}
                        onChange={(e) => updateLayer(idx, { dyeable: e.target.checked })}
                        className="rounded border-[#2b2b35] bg-[#141418] text-blue-500"
                      />
                      <span>Dyeable</span>
                    </label>
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={handleSave}
              disabled={loading}
              className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition"
            >
              {selectedModel ? 'Update Model' : 'Save Model'}
            </button>
          </div>

          {/* Mannequin Preview & Snippet */}
          <div className="space-y-3 text-xs flex flex-col justify-between">
            <div>
              <span className="text-gray-400 font-semibold block mb-2">Mannequin Preview</span>
              <div className="h-48 bg-black/60 border border-white/5 rounded-xl flex items-center justify-center p-3 relative">
                <div className="flex flex-col items-center space-y-1">
                  <div className="w-10 h-10 bg-blue-900/40 border border-blue-400 rounded flex items-center justify-center text-[10px] text-blue-200">
                    Helmet
                  </div>
                  <div className="w-20 h-16 bg-blue-800/40 border border-blue-400 rounded flex items-center justify-center text-[10px] text-blue-200">
                    Chestplate
                  </div>
                  <div className="w-16 h-12 bg-blue-900/40 border border-blue-400 rounded flex items-center justify-center text-[10px] text-blue-200">
                    Leggings
                  </div>
                  <div className="w-16 h-6 bg-blue-950/60 border border-blue-400 rounded flex items-center justify-center text-[10px] text-blue-200">
                    Boots
                  </div>
                </div>
              </div>
            </div>

            <div className="p-3 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-1.5">
              <span className="text-gray-400 font-medium">Item Component Tag:</span>
              <div className="flex items-center justify-between font-mono text-[11px] text-blue-300 bg-[#141418] p-2 rounded">
                <span className="truncate">{equippableSnippet}</span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(equippableSnippet)
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
