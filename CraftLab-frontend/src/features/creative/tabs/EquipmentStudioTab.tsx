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

const LAYER_CATEGORIES = [
  { id: 'humanoid', label: 'Humanoid', desc: 'Helmet, Chestplate, Boots' },
  { id: 'humanoid_leggings', label: 'Leggings', desc: 'Legs slot' },
  { id: 'wings', label: 'Wings', desc: 'Elytra / Glider' },
  { id: 'wolf_body', label: 'Wolf Body', desc: 'Wolf Armor' },
  { id: 'horse_body', label: 'Horse Body', desc: 'Horse Armor' },
  { id: 'llama_body', label: 'Llama Body', desc: 'Llama Carpet' },
]

const SLOTS = ['head', 'chest', 'legs', 'feet', 'body', 'mainhand', 'offhand', 'saddle']

export function EquipmentStudioTab() {
  const [models, setModels] = useState<EquipmentModelItem[]>([])
  const [selectedModel, setSelectedModel] = useState<EquipmentModelItem | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Namespace support
  const [namespace, setNamespace] = useState('craftlab')
  const [availableNamespaces, setAvailableNamespaces] = useState<string[]>(['craftlab'])

  // Form State
  const [modelId, setModelId] = useState('')
  const [targetSlot, setTargetSlot] = useState('chest')
  const [activeCategory, setActiveCategory] = useState('humanoid')
  const [layersMap, setLayersMap] = useState<Record<string, EquipmentLayer[]>>({
    humanoid: [{ texture: 'craftlab:paladin_set' }],
    humanoid_leggings: [{ texture: 'craftlab:paladin_set' }],
  })
  const [copied, setCopied] = useState(false)
  const [copiedLegacy, setCopiedLegacy] = useState(false)

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

    // Handle dictionary layers or fallback legacy list
    let normalized: Record<string, EquipmentLayer[]> = {}
    if (item.layers && typeof item.layers === 'object' && !Array.isArray(item.layers)) {
      normalized = { ...item.layers }
    } else if (Array.isArray(item.layers)) {
      item.layers.forEach((l: any) => {
        const cat = l.type || 'humanoid'
        if (!normalized[cat]) normalized[cat] = []
        normalized[cat].push({
          texture: l.texture,
          dyeable: l.dyeable,
          use_player_texture: l.use_player_texture,
        })
      })
    }

    if (Object.keys(normalized).length === 0) {
      normalized = { humanoid: [{ texture: `${item.namespace || 'craftlab'}:${item.id}` }] }
    }

    setLayersMap(normalized)
    const firstCat = Object.keys(normalized)[0] || 'humanoid'
    setActiveCategory(firstCat)
  }

  const resetForm = () => {
    setSelectedModel(null)
    setModelId('paladin_set')
    setNamespace('craftlab')
    setTargetSlot('chest')
    setLayersMap({
      humanoid: [
        { texture: 'craftlab:paladin_set' },
        { texture: 'craftlab:paladin_set_overlay', dyeable: { color_when_undyed: 10511680 } },
      ],
      humanoid_leggings: [
        { texture: 'craftlab:paladin_set' },
        { texture: 'craftlab:paladin_set_overlay', dyeable: { color_when_undyed: 10511680 } },
      ],
    })
    setActiveCategory('humanoid')
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

  const activeLayers = layersMap[activeCategory] || []

  const addLayerToActiveCategory = () => {
    const currentNs = namespace.trim() || 'craftlab'
    const newLayer: EquipmentLayer = {
      texture: `${currentNs}:${modelId || 'armor'}_layer_${activeLayers.length + 1}`,
    }
    setLayersMap({
      ...layersMap,
      [activeCategory]: [...activeLayers, newLayer],
    })
  }

  const updateActiveLayer = (idx: number, patch: Partial<EquipmentLayer>) => {
    const nextList = [...activeLayers]
    nextList[idx] = { ...nextList[idx], ...patch }
    setLayersMap({
      ...layersMap,
      [activeCategory]: nextList,
    })
  }

  const removeActiveLayer = (idx: number) => {
    const remaining = activeLayers.filter((_, i) => i !== idx)
    const nextMap = { ...layersMap }
    if (remaining.length === 0) {
      delete nextMap[activeCategory]
    } else {
      nextMap[activeCategory] = remaining
    }
    setLayersMap(nextMap)
  }

  const handleSave = async () => {
    if (!modelId.trim()) return
    const totalCount = Object.values(layersMap).reduce((acc, cur) => acc + cur.length, 0)
    if (totalCount === 0) {
      setErrorMsg('Equipment model must define at least one layer')
      return
    }

    setErrorMsg(null)
    const effectiveNs = namespace.trim() || 'craftlab'
    try {
      await saveEquipmentModel({
        id: modelId.trim(),
        layers: layersMap,
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
  const equippableSnippet = `"minecraft:equippable": { "slot": "${targetSlot}", "asset_id": "${effectiveNs}:${modelId}" }`

  const getTotalLayersCount = (item: EquipmentModelItem) => {
    if (!item.layers) return 0
    if (Array.isArray(item.layers)) return item.layers.length
    return Object.values(item.layers).reduce((acc, cur) => acc + (cur?.length || 0), 0)
  }

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
              const isSelected =
                selectedModel?.id === m.id &&
                (selectedModel?.namespace || 'craftlab') === (m.namespace || 'craftlab')
              const count = getTotalLayersCount(m)
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
                        <span className="text-blue-400 font-mono text-[11px]">
                          {m.namespace || 'craftlab'}:
                        </span>
                        {m.id}
                      </div>
                      <div className="flex items-center space-x-2 text-gray-500 text-[11px] font-mono">
                        <span>{count} layers</span>
                        {m.legacy_shader && (
                          <span className="px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 text-[10px]">
                            Shader #{m.legacy_shader.shader_id}
                          </span>
                        )}
                      </div>
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

            {/* Target Category Pills */}
            <div>
              <label className="block text-gray-400 mb-1 font-semibold">Layer Target Group</label>
              <div className="grid grid-cols-3 gap-1.5">
                {LAYER_CATEGORIES.map((cat) => {
                  const hasLayers = (layersMap[cat.id]?.length || 0) > 0
                  const isCurrent = activeCategory === cat.id
                  return (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => setActiveCategory(cat.id)}
                      className={`px-2 py-1.5 rounded-lg border text-left transition ${
                        isCurrent
                          ? 'bg-blue-600/20 border-blue-500 text-blue-300 font-medium'
                          : 'bg-[#1c1c22] border-[#2b2b35] text-gray-400 hover:text-gray-200'
                      }`}
                    >
                      <div className="font-semibold flex items-center justify-between">
                        <span>{cat.label}</span>
                        {hasLayers && (
                          <span className="text-[10px] bg-blue-500/20 px-1 rounded text-blue-300">
                            {layersMap[cat.id]?.length}
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-gray-500 truncate">{cat.desc}</div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Active Category Layers */}
            <div className="space-y-2 pt-1">
              <div className="flex items-center justify-between text-gray-400 font-semibold">
                <span className="capitalize">{activeCategory} Layers ({activeLayers.length})</span>
                <button
                  type="button"
                  onClick={addLayerToActiveCategory}
                  className="text-blue-400 hover:text-blue-300 text-xs font-medium"
                >
                  + Add Layer
                </button>
              </div>

              {activeLayers.length === 0 ? (
                <div className="p-3 bg-[#1c1c22]/50 border border-dashed border-[#2b2b35] rounded-lg text-center text-gray-500 text-[11px]">
                  No layers defined for <span className="font-mono text-gray-400">{activeCategory}</span>. Click "+ Add Layer" to add one.
                </div>
              ) : (
                activeLayers.map((layer, idx) => {
                  const isDyeable = Boolean(layer.dyeable)
                  const dyeableObj = typeof layer.dyeable === 'object' ? layer.dyeable : null
                  return (
                    <div key={idx} className="p-2.5 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-mono text-gray-400">
                          {activeCategory}[{idx}]
                        </span>
                        <button
                          type="button"
                          onClick={() => removeActiveLayer(idx)}
                          className="text-gray-500 hover:text-red-400"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>

                      <div>
                        <label className="block text-[10px] text-gray-400 mb-0.5">Texture Location</label>
                        <input
                          type="text"
                          value={layer.texture}
                          onChange={(e) => updateActiveLayer(idx, { texture: e.target.value })}
                          placeholder={`${effectiveNs}:${modelId || 'texture'}`}
                          className="w-full bg-[#141418] border border-[#2b2b35] rounded px-2 py-1 text-xs text-gray-100 font-mono"
                        />
                        <div className="text-[10px] text-gray-500 mt-0.5 font-mono truncate">
                          resolves: textures/entity/equipment/{activeCategory}/{layer.texture.split(':').pop()}.png
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-3 pt-1 border-t border-[#2b2b35]/60 text-[11px]">
                        <label className="flex items-center space-x-1.5 text-gray-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={isDyeable}
                            onChange={(e) => {
                              if (e.target.checked) {
                                updateActiveLayer(idx, { dyeable: { color_when_undyed: 10511680 } })
                              } else {
                                updateActiveLayer(idx, { dyeable: undefined })
                              }
                            }}
                            className="rounded border-[#2b2b35] bg-[#141418] text-blue-500"
                          />
                          <span>Dyeable</span>
                        </label>

                        {isDyeable && (
                          <div className="flex items-center space-x-1.5 text-[10px] text-gray-400">
                            <span>Undyed Tint:</span>
                            <input
                              type="number"
                              value={dyeableObj?.color_when_undyed ?? 10511680}
                              onChange={(e) =>
                                updateActiveLayer(idx, {
                                  dyeable: { color_when_undyed: parseInt(e.target.value, 10) || 0 },
                                })
                              }
                              className="w-20 bg-[#141418] border border-[#2b2b35] rounded px-1 py-0.5 text-right font-mono text-gray-200"
                            />
                          </div>
                        )}

                        {activeCategory === 'wings' && (
                          <label className="flex items-center space-x-1.5 text-gray-300 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={Boolean(layer.use_player_texture)}
                              onChange={(e) =>
                                updateActiveLayer(idx, { use_player_texture: e.target.checked })
                              }
                              className="rounded border-[#2b2b35] bg-[#141418] text-blue-500"
                            />
                            <span>Use Player Elytra Texture</span>
                          </label>
                        )}
                      </div>
                    </div>
                  )
                })
              )}
            </div>

            <button
              onClick={handleSave}
              disabled={loading}
              className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition mt-2"
            >
              {selectedModel ? 'Update Equipment Model' : 'Save Equipment Model'}
            </button>
          </div>

          {/* Mannequin Preview & Snippet */}
          <div className="space-y-3 text-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 font-semibold">1.21.4+ Paper Doll Preview</span>
                <span className="text-[10px] bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded font-mono">
                  {Object.keys(layersMap).length} targets configured
                </span>
              </div>
              <div className="h-56 bg-black/60 border border-white/5 rounded-xl flex items-center justify-center p-3 relative">
                <div className="flex flex-col items-center space-y-1">
                  <div className="w-10 h-10 bg-blue-900/40 border border-blue-400/80 rounded flex items-center justify-center text-[10px] text-blue-200 shadow">
                    Helmet
                  </div>
                  <div className="w-20 h-16 bg-blue-800/40 border border-blue-400/80 rounded flex items-center justify-center text-[10px] text-blue-200 shadow">
                    Chestplate
                  </div>
                  <div className="w-16 h-12 bg-blue-900/40 border border-blue-400/80 rounded flex items-center justify-center text-[10px] text-blue-200 shadow">
                    Leggings
                  </div>
                  <div className="w-16 h-6 bg-blue-950/60 border border-blue-400/80 rounded flex items-center justify-center text-[10px] text-blue-200 shadow">
                    Boots
                  </div>
                </div>
              </div>
            </div>

            <div className="p-3 bg-[#1c1c22] border border-[#2b2b35] rounded-lg space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-gray-400 font-medium">Item Component Tag (1.21.4+):</span>
                <span className="text-[10px] text-emerald-400 font-mono">asset_id</span>
              </div>
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

            {/* Multi-Version Diagnostics Box (< 1.21.2 Shader Fallback) */}
            <div className="p-3 bg-[#181822] border border-[#2b2b3d] rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
                  <span className="text-gray-300 font-semibold text-xs">
                    Legacy Core Shader Fallback (&lt; 1.21.2)
                  </span>
                </div>
                {selectedModel?.legacy_shader ? (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    Atlas Slot #{selectedModel.legacy_shader.slot_index} / {selectedModel.legacy_shader.total_layers}
                  </span>
                ) : (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                    Auto-Indexed on Save
                  </span>
                )}
              </div>

              {selectedModel?.legacy_shader ? (
                <div className="space-y-2 pt-1 text-[11px]">
                  <div className="grid grid-cols-3 gap-2">
                    <div className="p-2 rounded bg-[#101015] border border-[#23232f]">
                      <div className="text-gray-500 text-[10px]">Shader ID</div>
                      <div className="text-purple-300 font-mono font-bold mt-0.5">
                        #{selectedModel.legacy_shader.shader_id}
                      </div>
                    </div>
                    <div className="p-2 rounded bg-[#101015] border border-[#23232f]">
                      <div className="text-gray-500 text-[10px]">Atlas Tint (RGB)</div>
                      <div className="flex items-center space-x-1.5 mt-0.5">
                        <span
                          className="w-3.5 h-3.5 rounded border border-white/20 shrink-0"
                          style={{ backgroundColor: selectedModel.legacy_shader.hex }}
                        />
                        <span className="text-gray-200 font-mono text-[11px]">
                          {selectedModel.legacy_shader.hex}
                        </span>
                      </div>
                    </div>
                    <div className="p-2 rounded bg-[#101015] border border-[#23232f]">
                      <div className="text-gray-500 text-[10px]">Color Int</div>
                      <div className="text-cyan-300 font-mono mt-0.5">
                        {selectedModel.legacy_shader.color_rgb}
                      </div>
                    </div>
                  </div>

                  <div className="p-2 bg-[#101015] border border-[#23232f] rounded flex items-center justify-between font-mono text-[10px] text-purple-200">
                    <span className="truncate">
                      {`"minecraft:dyed_color": { "rgb": ${selectedModel.legacy_shader.color_rgb} }`}
                    </span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(
                          `"minecraft:dyed_color": { "rgb": ${selectedModel.legacy_shader?.color_rgb} }`
                        )
                        setCopiedLegacy(true)
                        setTimeout(() => setCopiedLegacy(false), 2000)
                      }}
                      className="text-gray-400 hover:text-gray-200 ml-2"
                      title="Copy Dyed Color Fallback"
                    >
                      {copiedLegacy ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-[11px] text-gray-500">
                  Save this model to automatically index it into the LessFancyPants vertical vertex atlas and generate its dyed_color fallback.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
