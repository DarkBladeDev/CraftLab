import { useState, useEffect } from 'react'
import {
  Box,
  Plus,
  Trash2,
  Armchair,
  Sparkles,
  RotateCcw,
  Sliders,
  Shield,
  Check,
  AlertCircle,
  Bed,
  Lightbulb,
  Volume2,
  ArrowRightLeft,
  Layers,
} from 'lucide-react'
import {
  Block,
  Item,
  PropState,
  fetchBlocks,
  saveBlock,
  deleteBlock,
  fetchItems,
  createRevision,
} from '../../api/client'

const DEFAULT_BLOCK: Block = {
  id: '',
  display_name: '',
  mode: 'display_prop',
  item_model: 'studio:furniture/custom_prop',
  block_model: 'studio:furniture/custom_prop',
  scale: [1.0, 1.0, 1.0],
  translation: [0.0, 0.0, 0.0],
  hitbox_type: 'solid',
  hitbox_offsets: [[0, 0, 0]],
  interaction_type: 'seat',
  seat_height: 0.45,
  hardness: 1.0,
  tool_type: 'AXE',
  drop_item_id: '',
  plugin_properties: {},
  default_state: 'default',
  states: {},
}

const PRESET_HITBOXES = [
  { label: '1x1 Single Block', offsets: [[0, 0, 0]] },
  { label: '1x2 High (Pillar/Cabinet)', offsets: [[0, 0, 0], [0, 1, 0]] },
  { label: '2x1 Long (Bench/Bed)', offsets: [[0, 0, 0], [1, 0, 0]] },
  { label: '2x2 Table/Platform', offsets: [[0, 0, 0], [1, 0, 0], [0, 0, 1], [1, 0, 1]] },
]

export function BlockStudio({ onRevisionCreated }: { onRevisionCreated?: () => void }) {
  const [blocks, setBlocks] = useState<Block[]>([])
  const [items, setItems] = useState<Item[]>([])
  const [selectedBlock, setSelectedBlock] = useState<Block>(DEFAULT_BLOCK)
  const [isEditing, setIsEditing] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [loadedBlocks, loadedItems] = await Promise.all([
        fetchBlocks(),
        fetchItems().catch(() => []),
      ])
      setBlocks(loadedBlocks)
      setItems(loadedItems)
      if (loadedBlocks.length > 0 && !isEditing) {
        setSelectedBlock(loadedBlocks[0])
      }
    } catch (err: any) {
      console.error(err)
      setStatusMessage('Error loading blocks: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const [activeStateKey, setActiveStateKey] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const currentStates = selectedBlock.states || {}
  const stateKeys = Object.keys(currentStates)

  const handleSelectBlock = (block: Block) => {
    const states = block.states || {}
    const defaultState = block.default_state || 'default'
    setSelectedBlock({
      ...DEFAULT_BLOCK,
      ...block,
      default_state: defaultState,
      states,
    })
    const keys = Object.keys(states)
    setActiveStateKey(keys.includes(defaultState) ? defaultState : (keys[0] || null))
    setIsEditing(true)
    setStatusMessage(null)
  }

  const handleNewBlock = () => {
    setSelectedBlock({
      ...DEFAULT_BLOCK,
      id: `prop_${Date.now().toString().slice(-4)}`,
      display_name: '<yellow>New Prop</yellow>',
    })
    setActiveStateKey(null)
    setIsEditing(false)
    setStatusMessage(null)
  }

  const handleAddState = () => {
    const key = prompt('Enter unique state identifier (e.g. "on", "off", "open"):')?.trim().toLowerCase()
    if (!key) return
    if (currentStates[key]) {
      alert(`State "${key}" already exists!`)
      return
    }
    const updatedStates = {
      ...currentStates,
      [key]: {
        name: key.charAt(0).toUpperCase() + key.slice(1),
        block_model: selectedBlock.block_model || '',
        light_level: 0,
        sound: null,
        hitbox_type: null,
        next_state: null,
      },
    }
    setSelectedBlock({
      ...selectedBlock,
      states: updatedStates,
      default_state: selectedBlock.default_state && currentStates[selectedBlock.default_state] ? selectedBlock.default_state : key,
    })
    setActiveStateKey(key)
  }

  const handleRemoveState = (keyToRemove: string) => {
    const { [keyToRemove]: _, ...rest } = currentStates
    const remainingKeys = Object.keys(rest)
    const newDefault = selectedBlock.default_state === keyToRemove ? (remainingKeys[0] || 'default') : (selectedBlock.default_state || 'default')
    setSelectedBlock({
      ...selectedBlock,
      states: rest,
      default_state: newDefault,
    })
    if (activeStateKey === keyToRemove) {
      setActiveStateKey(remainingKeys[0] || null)
    }
  }

  const handleUpdateCurrentState = (partial: Partial<PropState>) => {
    if (!activeStateKey || !currentStates[activeStateKey]) return
    setSelectedBlock({
      ...selectedBlock,
      states: {
        ...currentStates,
        [activeStateKey]: {
          ...currentStates[activeStateKey],
          ...partial,
        },
      },
    })
  }

  const handleApplyLampPreset = () => {
    const baseModel = selectedBlock.block_model || 'studio:props/custom_prop'
    setSelectedBlock({
      ...selectedBlock,
      default_state: 'off',
      states: {
        off: {
          name: 'Apagada',
          block_model: baseModel.replace(/_on$/, '') + '_off',
          light_level: 0,
          sound: { key: 'block.wooden_button.click_off', volume: 0.8, pitch: 1.0 },
          hitbox_type: null,
          next_state: 'on',
        },
        on: {
          name: 'Encendida',
          block_model: baseModel.replace(/_off$/, '') + '_on',
          light_level: 14,
          sound: { key: 'block.wooden_button.click_on', volume: 0.8, pitch: 1.0 },
          hitbox_type: null,
          next_state: 'off',
        },
      },
    })
    setActiveStateKey('off')
  }

  const handleApplyDoorPreset = () => {
    const baseModel = selectedBlock.block_model || 'studio:props/custom_prop'
    setSelectedBlock({
      ...selectedBlock,
      default_state: 'closed',
      states: {
        closed: {
          name: 'Cerrada',
          block_model: baseModel.replace(/_open$/, '') + '_closed',
          light_level: 0,
          sound: { key: 'block.wooden_door.close', volume: 1.0, pitch: 1.0 },
          hitbox_type: 'solid',
          next_state: 'open',
        },
        open: {
          name: 'Abierta',
          block_model: baseModel.replace(/_closed$/, '') + '_open',
          light_level: 0,
          sound: { key: 'block.wooden_door.open', volume: 1.0, pitch: 1.0 },
          hitbox_type: 'passable',
          next_state: 'closed',
        },
      },
    })
    setActiveStateKey('closed')
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedBlock.id.trim()) {
      setStatusMessage('ID is required')
      return
    }

    try {
      const payload: Block = {
        ...selectedBlock,
        block_model: selectedBlock.block_model?.trim() || selectedBlock.item_model?.trim() || null,
        item_model: selectedBlock.item_model?.trim() || selectedBlock.block_model?.trim() || null,
        default_state: selectedBlock.default_state?.trim() || 'default',
        states: selectedBlock.states || {},
      }
      const saved = await saveBlock(payload)
      setStatusMessage(`Saved block "${saved.id}" successfully!`)
      await loadData()
      setSelectedBlock(saved)
      setIsEditing(true)
    } catch (err: any) {
      setStatusMessage('Failed to save block: ' + err.message)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(`Are you sure you want to delete block "${id}"?`)) return
    try {
      await deleteBlock(id)
      setStatusMessage(`Block "${id}" deleted.`)
      await loadData()
      if (blocks.length > 1) {
        setSelectedBlock(blocks.find((b) => b.id !== id) || DEFAULT_BLOCK)
      } else {
        setSelectedBlock(DEFAULT_BLOCK)
        setIsEditing(false)
      }
    } catch (err: any) {
      setStatusMessage('Failed to delete block: ' + err.message)
    }
  }

  const handleCreateRevision = async () => {
    try {
      const rev = await createRevision()
      setStatusMessage(`Revision #${rev.revision_number} created with hash ${rev.revision_hash.slice(0, 8)}...`)
      if (onRevisionCreated) onRevisionCreated()
    } catch (err: any) {
      setStatusMessage('Failed to create revision: ' + err.message)
    }
  }

  const updateScale = (axisIndex: number, val: number) => {
    const newScale = [...selectedBlock.scale] as [number, number, number]
    newScale[axisIndex] = Math.max(0.01, val)
    setSelectedBlock({ ...selectedBlock, scale: newScale })
  }

  const updateTranslation = (axisIndex: number, val: number) => {
    const newTrans = [...selectedBlock.translation] as [number, number, number]
    newTrans[axisIndex] = val
    setSelectedBlock({ ...selectedBlock, translation: newTrans })
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Column: Blocks List */}
      <div className="lg:col-span-4 space-y-4">
        <div className="p-4 rounded-xl bg-[#141418] border border-[#23232b] flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-gray-100 flex items-center space-x-2">
              <Box className="w-4 h-4 text-emerald-400" />
              <span>Blocks & Props</span>
              {isLoading && <span className="text-[10px] text-gray-500 animate-pulse font-mono">Loading...</span>}
            </h2>
            <p className="text-xs text-gray-400">PacketEvents Virtual Display Props</p>
          </div>
          <button
            onClick={handleNewBlock}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow transition transform active:scale-95"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Prop</span>
          </button>
        </div>

        {/* List of blocks */}
        <div className="space-y-2 max-h-[620px] overflow-y-auto pr-1">
          {blocks.length === 0 ? (
            <div className="p-8 text-center bg-[#141418] rounded-xl border border-[#23232b] text-gray-500 text-xs">
              No custom blocks created yet. Click "New Prop" to get started.
            </div>
          ) : (
            blocks.map((block) => {
              const isSelected = selectedBlock.id === block.id
              return (
                <div
                  key={block.id}
                  onClick={() => handleSelectBlock(block)}
                  className={`p-3 rounded-xl border transition cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? 'bg-[#1e1e26] border-emerald-500/50 shadow-md shadow-emerald-950/20'
                      : 'bg-[#141418] border-[#23232b] hover:border-[#353542]'
                  }`}
                >
                  <div className="flex items-center space-x-3 overflow-hidden">
                    <div className="w-8 h-8 rounded-lg bg-[#0e0e11] border border-[#23232b] flex items-center justify-center flex-shrink-0 text-emerald-400">
                      {block.interaction_type === 'seat' ? (
                        <Armchair className="w-4 h-4" />
                      ) : block.interaction_type === 'lay' ? (
                        <Bed className="w-4 h-4 text-purple-400" />
                      ) : (
                        <Box className="w-4 h-4" />
                      )}
                    </div>
                    <div className="truncate">
                      <div className="text-xs font-bold text-gray-200 truncate">
                        {block.display_name.replace(/<[^>]*>/g, '') || block.id}
                      </div>
                      <div className="text-[10px] font-mono text-gray-500 truncate">{block.id}</div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#23232b] text-gray-300 font-mono">
                      {block.mode === 'display_prop' ? 'Virtual Prop' : 'NoteBlock'}
                    </span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(block.id)
                      }}
                      className="p-1 hover:text-red-400 text-gray-500 rounded transition"
                      title="Delete block"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* Revisions trigger card */}
        <div className="p-4 rounded-xl bg-[#141418] border border-[#23232b] flex items-center justify-between">
          <div className="text-xs text-gray-400">
            <span>Snapshot project state into revision</span>
          </div>
          <button
            onClick={handleCreateRevision}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#1f1f27] hover:bg-[#282833] border border-[#2f2f3d] text-gray-200 rounded-lg text-xs font-semibold transition"
          >
            <RotateCcw className="w-3.5 h-3.5 text-emerald-400" />
            <span>Create Revision</span>
          </button>
        </div>
      </div>

      {/* Right Column: Block Details & 3D Transform Editor */}
      <div className="lg:col-span-8">
        <form onSubmit={handleSave} className="space-y-5">
          {statusMessage && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center space-x-2">
              <Sparkles className="w-4 h-4 flex-shrink-0" />
              <span>{statusMessage}</span>
            </div>
          )}

          {/* Section 1: General Info */}
          <div className="p-5 rounded-xl bg-[#141418] border border-[#23232b] space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center space-x-2">
              <Box className="w-4 h-4 text-emerald-400" />
              <span>Identity & Implementation Mode</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Identifier (slug)
                </label>
                <input
                  type="text"
                  required
                  disabled={isEditing}
                  value={selectedBlock.id}
                  onChange={(e) =>
                    setSelectedBlock({ ...selectedBlock, id: e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, '') })
                  }
                  placeholder="e.g. oak_chair"
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 font-mono focus:border-emerald-500 outline-none disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Display Name (MiniMessage / Text)
                </label>
                <input
                  type="text"
                  required
                  value={selectedBlock.display_name}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, display_name: e.target.value })}
                  placeholder="<yellow>Oak Chair</yellow>"
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-[#1e1e26]">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Engine Mode</label>
                <select
                  value={selectedBlock.mode}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, mode: e.target.value as any })}
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none"
                >
                  <option value="display_prop">Display Prop (PacketEvents Virtual Entities)</option>
                  <option value="noteblock">NoteBlock (Vanilla / Oraxen Blockstate)</option>
                </select>
                <p className="text-[11px] text-gray-500 mt-1">
                  {selectedBlock.mode === 'display_prop'
                    ? 'Renders client-side with 0 server tick lag and barrier collision anchors.'
                    : 'Overwrites note block instrument/pitch states via resource pack.'}
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Drop Item on Break</label>
                <select
                  value={selectedBlock.drop_item_id || ''}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, drop_item_id: e.target.value || null })}
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none"
                >
                  <option value="">None (No drop reward)</option>
                  {items.map((i) => (
                    <option key={i.id} value={i.id}>
                      {i.display_name.replace(/<[^>]*>/g, '') || i.id} ({i.id})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Section 2: 3D Transform Controls */}
          <div className="p-5 rounded-xl bg-[#141418] border border-[#23232b] space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <span>Model & 3D Display Transformations</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Block Model Identifier (Placed 3D Display)
                </label>
                <input
                  type="text"
                  value={selectedBlock.block_model ?? selectedBlock.item_model ?? ''}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, block_model: e.target.value })}
                  placeholder="studio:furniture/oak_chair_display"
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 font-mono focus:border-emerald-500 outline-none"
                />
                <p className="text-[11px] text-gray-500 mt-1">
                  Model displayed by the PacketEvents ItemDisplay entity in the world.
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Item Model Identifier (Handheld / Inventory)
                </label>
                <input
                  type="text"
                  value={selectedBlock.item_model ?? ''}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, item_model: e.target.value })}
                  placeholder="studio:furniture/oak_chair"
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 font-mono focus:border-emerald-500 outline-none"
                />
                <p className="text-[11px] text-gray-500 mt-1">
                  Model shown in player hands, hotbar, and dropped item stacks.
                </p>
              </div>
            </div>

            {/* Scale Sliders */}
            <div className="space-y-2 pt-2 border-t border-[#1e1e26]">
              <span className="text-xs font-semibold text-gray-300">Scale Factors [X, Y, Z]</span>
              <div className="grid grid-cols-3 gap-3">
                {['X', 'Y', 'Z'].map((axis, idx) => (
                  <div key={axis} className="p-3 rounded-lg bg-[#0e0e11] border border-[#23232b] space-y-1">
                    <div className="flex justify-between text-[11px] text-gray-400 font-mono">
                      <span>Axis {axis}</span>
                      <span className="text-emerald-400 font-bold">{selectedBlock.scale[idx].toFixed(2)}x</span>
                    </div>
                    <input
                      type="range"
                      min="0.1"
                      max="3.0"
                      step="0.05"
                      value={selectedBlock.scale[idx]}
                      onChange={(e) => updateScale(idx, parseFloat(e.target.value))}
                      className="w-full accent-emerald-500 cursor-pointer"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Translation Offsets */}
            <div className="space-y-2 pt-2 border-t border-[#1e1e26]">
              <span className="text-xs font-semibold text-gray-300">Anchor Translation Offsets [X, Y, Z]</span>
              <div className="grid grid-cols-3 gap-3">
                {['X', 'Y', 'Z'].map((axis, idx) => (
                  <div key={axis} className="p-3 rounded-lg bg-[#0e0e11] border border-[#23232b] space-y-1">
                    <div className="flex justify-between text-[11px] text-gray-400 font-mono">
                      <span>Offset {axis}</span>
                      <span className="text-blue-400 font-bold">{selectedBlock.translation[idx].toFixed(2)}m</span>
                    </div>
                    <input
                      type="range"
                      min="-1.5"
                      max="1.5"
                      step="0.05"
                      value={selectedBlock.translation[idx]}
                      onChange={(e) => updateTranslation(idx, parseFloat(e.target.value))}
                      className="w-full accent-blue-500 cursor-pointer"
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Section 3: Hitbox & Collision Grid */}
          <div className="p-5 rounded-xl bg-[#141418] border border-[#23232b] space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center space-x-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span>Collision Hitbox & Mechanics</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Hitbox Type</label>
                <select
                  value={selectedBlock.hitbox_type}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, hitbox_type: e.target.value as any })}
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none"
                >
                  <option value="solid">Solid Barrier (Impassable)</option>
                  <option value="passable">Passable (Structure Void)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Hardness (Break Speed)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  disabled={selectedBlock.hitbox_type === 'solid'}
                  value={selectedBlock.hardness}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, hardness: parseFloat(e.target.value) || 1.0 })}
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none disabled:opacity-40 disabled:cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Optimal Tool</label>
                <select
                  disabled={selectedBlock.hitbox_type === 'solid'}
                  value={selectedBlock.tool_type}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, tool_type: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <option value="AXE">Axe (Wood/Furniture)</option>
                  <option value="PICKAXE">Pickaxe (Stone/Metal)</option>
                  <option value="SHOVEL">Shovel (Dirt/Gravel)</option>
                  <option value="SHEARS">Shears (Foliage)</option>
                  <option value="HAND">Hand (Any Tool)</option>
                </select>
              </div>
            </div>

            {selectedBlock.hitbox_type === 'solid' && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>Solid Barrier is unbreakable in survival mode (Hardness & Optimal Tool are disabled).</span>
              </div>
            )}

            {/* Hitbox Presets */}
            <div className="space-y-2 pt-2 border-t border-[#1e1e26]">
              <label className="block text-xs font-medium text-gray-300">Hitbox Dimension Preset</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {PRESET_HITBOXES.map((preset) => {
                  const isActive = JSON.stringify(selectedBlock.hitbox_offsets) === JSON.stringify(preset.offsets)
                  return (
                    <button
                      key={preset.label}
                      type="button"
                      onClick={() => setSelectedBlock({ ...selectedBlock, hitbox_offsets: preset.offsets })}
                      className={`px-3 py-2 rounded-lg text-xs text-left border transition ${
                        isActive
                          ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400 font-semibold'
                          : 'bg-[#0e0e11] border-[#23232b] text-gray-400 hover:text-gray-200'
                      }`}
                    >
                      {preset.label}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Section 4: Interactive Behaviors & Seat Mechanics */}
          <div className="p-5 rounded-xl bg-[#141418] border border-[#23232b] space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center space-x-2">
              <Armchair className="w-4 h-4 text-emerald-400" />
              <span>Interactions & Seat Mechanics</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Interaction Behavior</label>
                <select
                  value={selectedBlock.interaction_type || 'none'}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, interaction_type: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none"
                >
                  <option value="seat">Seat (Mount player on right-click)</option>
                  <option value="lay">Lie Down (Lay back in the block on right-click)</option>
                  <option value="none">None (Static Decoration)</option>
                  <option value="container">Storage Container</option>
                  <option value="custom">Custom Plugin Trigger</option>
                </select>
              </div>

              {(selectedBlock.interaction_type === 'seat' || selectedBlock.interaction_type === 'lay') && (
                <div>
                  <div className="flex justify-between text-xs font-medium text-gray-300 mb-1">
                    <span>{selectedBlock.interaction_type === 'lay' ? 'Lay Height Offset' : 'Seat Height (Y Offset)'}</span>
                    <span className="text-emerald-400 font-bold">{selectedBlock.seat_height.toFixed(2)}m</span>
                  </div>
                  <input
                    type="range"
                    min="0.1"
                    max="1.5"
                    step="0.05"
                    value={selectedBlock.seat_height}
                    onChange={(e) => setSelectedBlock({ ...selectedBlock, seat_height: parseFloat(e.target.value) || 0.45 })}
                    className="w-full accent-emerald-500 cursor-pointer"
                  />
                  <p className="text-[11px] text-gray-500 mt-1">
                    {selectedBlock.interaction_type === 'lay'
                      ? 'Height above the floor where the player lies down. Typical beds/couches: 0.30 - 0.45m.'
                      : "Height above the floor where the player's model sits. Typical chairs: 0.40 - 0.50m."}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Section 5: States, Lighting & Variants */}
          <div className="p-5 rounded-xl bg-[#141418] border border-[#23232b] space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center space-x-2">
                <Layers className="w-4 h-4 text-emerald-400" />
                <span>States, Lighting & Variants</span>
                {stateKeys.length > 0 && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {stateKeys.length} {stateKeys.length === 1 ? 'state' : 'states'}
                  </span>
                )}
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={handleApplyLampPreset}
                  className="px-2.5 py-1 text-[11px] rounded bg-[#1c1c22] hover:bg-[#252530] text-gray-300 border border-[#2b2b35] transition flex items-center space-x-1"
                >
                  <Lightbulb className="w-3 h-3 text-amber-400" />
                  <span>Preset: Lamp</span>
                </button>
                <button
                  type="button"
                  onClick={handleApplyDoorPreset}
                  className="px-2.5 py-1 text-[11px] rounded bg-[#1c1c22] hover:bg-[#252530] text-gray-300 border border-[#2b2b35] transition flex items-center space-x-1"
                >
                  <ArrowRightLeft className="w-3 h-3 text-emerald-400" />
                  <span>Preset: Door/Gate</span>
                </button>
                <button
                  type="button"
                  onClick={handleAddState}
                  className="px-2.5 py-1 text-[11px] rounded bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 transition flex items-center space-x-1"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add State</span>
                </button>
              </div>
            </div>

            {stateKeys.length === 0 ? (
              <div className="p-4 rounded-lg bg-[#0e0e11] border border-[#23232b] text-center text-xs text-gray-400">
                <p>This prop currently has no custom states (behaves as a single static model).</p>
                <p className="text-[11px] text-gray-500 mt-1">Use a preset above or click "Add State" to create interactive toggleable variants.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* State Tabs */}
                <div className="flex flex-wrap items-center gap-1.5 p-1 bg-[#0e0e11] rounded-lg border border-[#23232b]">
                  {stateKeys.map((key) => {
                    const isDefault = selectedBlock.default_state === key
                    const isSelected = activeStateKey === key
                    return (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setActiveStateKey(key)}
                        className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center space-x-1.5 transition ${
                          isSelected
                            ? 'bg-emerald-600 text-white shadow-sm'
                            : 'bg-transparent text-gray-400 hover:text-gray-200 hover:bg-[#1a1a22]'
                        }`}
                      >
                        <span>{currentStates[key]?.name || key}</span>
                        <span className={`text-[10px] px-1 rounded ${isSelected ? 'bg-emerald-700 text-emerald-100' : 'bg-[#23232b] text-gray-400'}`}>
                          {key}
                        </span>
                        {isDefault && (
                          <span className="text-[9px] px-1 rounded bg-amber-400/20 text-amber-300 font-bold">
                            DEFAULT
                          </span>
                        )}
                      </button>
                    )
                  })}
                </div>

                {/* Active State Form Card */}
                {activeStateKey && currentStates[activeStateKey] && (
                  <div className="p-4 rounded-xl bg-[#0e0e11] border border-[#23232b] space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-[#1e1e26]">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-gray-200">Configuring State:</span>
                        <span className="px-2 py-0.5 rounded text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {activeStateKey}
                        </span>
                        {selectedBlock.default_state !== activeStateKey && (
                          <button
                            type="button"
                            onClick={() => setSelectedBlock({ ...selectedBlock, default_state: activeStateKey })}
                            className="text-[10px] text-gray-400 hover:text-amber-300 underline"
                          >
                            Set as Default State
                          </button>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveState(activeStateKey)}
                        className="text-xs text-red-400 hover:text-red-300 flex items-center space-x-1 transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        <span>Delete State</span>
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-300 mb-1">State Display Label</label>
                        <input
                          type="text"
                          value={currentStates[activeStateKey]?.name || ''}
                          onChange={(e) => handleUpdateCurrentState({ name: e.target.value })}
                          placeholder="e.g. Encendida, Open, High Speed"
                          className="w-full px-3 py-2 bg-[#141418] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-300 mb-1">Target Next State (on right-click)</label>
                        <select
                          value={currentStates[activeStateKey]?.next_state || ''}
                          onChange={(e) => handleUpdateCurrentState({ next_state: e.target.value || null })}
                          className="w-full px-3 py-2 bg-[#141418] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none"
                        >
                          <option value="">None (Does not transition)</option>
                          {stateKeys.map((sk) => (
                            <option key={sk} value={sk}>
                              {currentStates[sk]?.name ? `${currentStates[sk].name} (${sk})` : sk}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-xs font-medium text-gray-300 mb-1">Block Model Override for this State</label>
                        <input
                          type="text"
                          value={currentStates[activeStateKey]?.block_model || ''}
                          onChange={(e) => handleUpdateCurrentState({ block_model: e.target.value || null })}
                          placeholder={selectedBlock.block_model || 'namespace:props/model'}
                          className="w-full px-3 py-2 bg-[#141418] border border-[#23232b] rounded-lg text-xs font-mono text-gray-200 focus:border-emerald-500 outline-none"
                        />
                        <p className="text-[11px] text-gray-500 mt-1">
                          Leave empty to inherit the prop's primary block model.
                        </p>
                      </div>

                      {/* Light Level Setting */}
                      <div>
                        <div className="flex justify-between text-xs font-medium text-gray-300 mb-1">
                          <span className="flex items-center space-x-1.5">
                            <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                            <span>Emitted Light Level</span>
                          </span>
                          <span className="text-amber-400 font-bold">{currentStates[activeStateKey]?.light_level || 0} / 15</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="15"
                          step="1"
                          value={currentStates[activeStateKey]?.light_level || 0}
                          onChange={(e) => handleUpdateCurrentState({ light_level: parseInt(e.target.value, 10) || 0 })}
                          className="w-full accent-amber-500 cursor-pointer"
                        />
                        <p className="text-[11px] text-gray-500 mt-1">
                          0 = No light, 15 = Full glow (managed automatically via Paper 1.21 Material.LIGHT).
                        </p>
                      </div>

                      {/* Collision Override */}
                      <div>
                        <label className="block text-xs font-medium text-gray-300 mb-1">Hitbox Collision in this State</label>
                        <select
                          value={currentStates[activeStateKey]?.hitbox_type || ''}
                          onChange={(e) => handleUpdateCurrentState({ hitbox_type: (e.target.value as 'solid' | 'passable') || null })}
                          className="w-full px-3 py-2 bg-[#141418] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none"
                        >
                          <option value="">Inherit Prop Hitbox ({selectedBlock.hitbox_type})</option>
                          <option value="solid">Solid Barrier (Blocks movement)</option>
                          <option value="passable">Passable Structure Void (Walk through)</option>
                        </select>
                        <p className="text-[11px] text-gray-500 mt-1">
                          Use "Passable" for open doors/gates to allow players to walk through freely.
                        </p>
                      </div>

                      {/* Sound Setting */}
                      <div className="md:col-span-2 pt-2 border-t border-[#1e1e26] space-y-3">
                        <label className="text-xs font-medium text-gray-300 flex items-center space-x-1.5">
                          <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Entry Sound Effect</span>
                        </label>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                          <div className="sm:col-span-2">
                            <input
                              type="text"
                              value={currentStates[activeStateKey]?.sound?.key || ''}
                              onChange={(e) => {
                                const keyVal = e.target.value.trim()
                                if (!keyVal) {
                                  handleUpdateCurrentState({ sound: null })
                                } else {
                                  handleUpdateCurrentState({
                                    sound: {
                                      key: keyVal,
                                      volume: currentStates[activeStateKey]?.sound?.volume ?? 1.0,
                                      pitch: currentStates[activeStateKey]?.sound?.pitch ?? 1.0,
                                    },
                                  })
                                }
                              }}
                              placeholder="e.g. block.wooden_button.click_on, block.wooden_door.open"
                              className="w-full px-3 py-2 bg-[#141418] border border-[#23232b] rounded-lg text-xs font-mono text-gray-200 focus:border-emerald-500 outline-none"
                            />
                          </div>
                          <div className="flex items-center space-x-2">
                            <div className="flex-1">
                              <span className="block text-[10px] text-gray-400 mb-0.5">Pitch ({currentStates[activeStateKey]?.sound?.pitch ?? 1.0})</span>
                              <input
                                type="range"
                                min="0.5"
                                max="2.0"
                                step="0.1"
                                disabled={!currentStates[activeStateKey]?.sound}
                                value={currentStates[activeStateKey]?.sound?.pitch ?? 1.0}
                                onChange={(e) => {
                                  if (currentStates[activeStateKey]?.sound) {
                                    handleUpdateCurrentState({
                                      sound: {
                                        ...currentStates[activeStateKey]!.sound!,
                                        pitch: parseFloat(e.target.value) || 1.0,
                                      },
                                    })
                                  }
                                }}
                                className="w-full accent-emerald-500 cursor-pointer disabled:opacity-40"
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Save Action Bar */}
          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              type="submit"
              className="flex items-center space-x-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-950/40 transition transform active:scale-95"
            >
              <Check className="w-4 h-4" />
              <span>Save Prop Definition</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
