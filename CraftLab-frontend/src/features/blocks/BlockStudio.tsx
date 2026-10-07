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
} from 'lucide-react'
import {
  Block,
  Item,
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

  useEffect(() => {
    loadData()
  }, [])

  const handleSelectBlock = (block: Block) => {
    setSelectedBlock({ ...block })
    setIsEditing(true)
    setStatusMessage(null)
  }

  const handleNewBlock = () => {
    setSelectedBlock({
      ...DEFAULT_BLOCK,
      id: `prop_${Date.now().toString().slice(-4)}`,
      display_name: '<yellow>New Prop</yellow>',
    })
    setIsEditing(false)
    setStatusMessage(null)
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedBlock.id.trim()) {
      setStatusMessage('ID is required')
      return
    }

    try {
      const saved = await saveBlock(selectedBlock)
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

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Item Model Identifier (1.21.2+ / RP Model)
              </label>
              <input
                type="text"
                value={selectedBlock.item_model || ''}
                onChange={(e) => setSelectedBlock({ ...selectedBlock, item_model: e.target.value })}
                placeholder="studio:furniture/oak_chair"
                className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 font-mono focus:border-emerald-500 outline-none"
              />
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
                  value={selectedBlock.hardness}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, hardness: parseFloat(e.target.value) || 1.0 })}
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Optimal Tool</label>
                <select
                  value={selectedBlock.tool_type}
                  onChange={(e) => setSelectedBlock({ ...selectedBlock, tool_type: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 focus:border-emerald-500 outline-none"
                >
                  <option value="AXE">Axe (Wood/Furniture)</option>
                  <option value="PICKAXE">Pickaxe (Stone/Metal)</option>
                  <option value="SHOVEL">Shovel (Dirt/Gravel)</option>
                  <option value="SHEARS">Shears (Foliage)</option>
                  <option value="HAND">Hand (Any Tool)</option>
                </select>
              </div>
            </div>

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
                  <option value="none">None (Static Decoration)</option>
                  <option value="container">Storage Container</option>
                  <option value="custom">Custom Plugin Trigger</option>
                </select>
              </div>

              {selectedBlock.interaction_type === 'seat' && (
                <div>
                  <div className="flex justify-between text-xs font-medium text-gray-300 mb-1">
                    <span>Seat Height (Y Offset)</span>
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
                    Height above the floor where the player's model sits. Typical chairs: 0.40 - 0.50m.
                  </p>
                </div>
              )}
            </div>
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
