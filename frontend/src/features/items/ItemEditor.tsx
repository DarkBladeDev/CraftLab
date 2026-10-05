import { useState, useEffect } from 'react'
import { Sparkles, Trash2, PackageCheck, Eye, Layers } from 'lucide-react'
import { fetchItems, saveItem, deleteItem, createRevision, Item, Revision, fetchRevisions } from '../../api/client'

const POPULAR_MATERIALS = [
  'DIAMOND_SWORD',
  'NETHERITE_SWORD',
  'BOW',
  'CROSSBOW',
  'DIAMOND_PICKAXE',
  'NETHERITE_PICKAXE',
  'FEATHER',
  'STICK',
  'EMERALD',
  'BLAZE_ROD',
  'NETHERITE_CHESTPLATE',
  'SHIELD'
]

const AVAILABLE_FLAGS = [
  'HIDE_ATTRIBUTES',
  'HIDE_ENCHANTS',
  'HIDE_UNBREAKABLE',
  'HIDE_DESTROYS',
  'HIDE_PLACED_ON',
  'HIDE_ADDITIONAL_TOOLTIP'
]

export function ItemEditor({ onRevisionCreated }: { onRevisionCreated?: () => void }) {
  const [items, setItems] = useState<Item[]>([])
  const [revisions, setRevisions] = useState<Revision[]>([])
  const [revMessage, setRevMessage] = useState<string | null>(null)

  // Form State
  const [id, setId] = useState('ruby_sword')
  const [material, setMaterial] = useState('DIAMOND_SWORD')
  const [displayName, setDisplayName] = useState('<red><bold>Ruby Sword</bold></red>')
  const [loreText, setLoreText] = useState('<gray>Forged in ancient magma chambers.</gray>\n<dark_red>Attack Damage: +12</dark_red>')
  const [customModelData, setCustomModelData] = useState<string>('10001')
  const [selectedFlags, setSelectedFlags] = useState<string[]>(['HIDE_ATTRIBUTES'])
  const [formError, setFormError] = useState<string | null>(null)

  const loadData = async () => {
    try {
      const [itms, revs] = await Promise.all([fetchItems(), fetchRevisions()])
      setItems(itms)
      setRevisions(revs)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    const loreArray = loreText
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 0)

    const cmdNum = customModelData ? parseInt(customModelData, 10) : null

    try {
      await saveItem({
        id: id.trim(),
        material: material.trim().toUpperCase(),
        display_name: displayName.trim(),
        lore: loreArray,
        custom_model_data: isNaN(cmdNum as number) ? null : cmdNum,
        item_flags: selectedFlags,
        amount: 1,
      })
      await loadData()
    } catch (err: any) {
      setFormError(err.message || 'Error saving item')
    }
  }

  const handleDelete = async (itemId: string) => {
    await deleteItem(itemId)
    await loadData()
  }

  const handleCreateRevision = async () => {
    try {
      const rev = await createRevision()
      setRevMessage(`Revision #${rev.revision_number} snapshotted (${rev.revision_hash.slice(0, 10)}...)`)
      setTimeout(() => setRevMessage(null), 4000)
      await loadData()
      onRevisionCreated?.()
    } catch (e: any) {
      setFormError(e.message)
    }
  }

  // Mini preview helper
  const renderPreviewName = (text: string) => {
    // Basic regex replacement for simple visualization
    return text.replace(/<[^>]+>/g, '')
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Editor Form */}
      <div className="lg:col-span-7 bg-[#16161a] border border-[#27272e] rounded-xl p-5 shadow-lg">
        <div className="flex items-center space-x-2 mb-4 pb-3 border-b border-[#27272e]">
          <Sparkles className="w-5 h-5 text-amber-400" />
          <h2 className="text-base font-semibold text-gray-200">Item Definition Editor (Paper 1.21)</h2>
        </div>

        {formError && (
          <div className="mb-4 p-3 bg-red-950/40 border border-red-800/50 rounded-lg text-xs text-red-300">
            {formError}
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Item Identifier (Slug)</label>
              <input
                type="text"
                value={id}
                onChange={(e) => setId(e.target.value)}
                placeholder="e.g. ruby_sword"
                className="w-full px-3 py-2 text-xs bg-[#111114] border border-[#30303a] rounded-lg text-gray-200 focus:outline-none focus:border-amber-400 font-mono"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Vanilla Material</label>
              <input
                list="materials"
                value={material}
                onChange={(e) => setMaterial(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-[#111114] border border-[#30303a] rounded-lg text-gray-200 focus:outline-none focus:border-amber-400 font-mono"
                required
              />
              <datalist id="materials">
                {POPULAR_MATERIALS.map((m) => (
                  <option key={m} value={m} />
                ))}
              </datalist>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">
              Display Name <span className="text-[11px] text-gray-500">(Supports Adventure MiniMessage)</span>
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="<gold>Excalibur</gold>"
              className="w-full px-3 py-2 text-xs bg-[#111114] border border-[#30303a] rounded-lg text-gray-200 focus:outline-none focus:border-amber-400 font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">
              Lore Lines <span className="text-[11px] text-gray-500">(One line per entry)</span>
            </label>
            <textarea
              rows={3}
              value={loreText}
              onChange={(e) => setLoreText(e.target.value)}
              placeholder="<gray>First line</gray>&#10;<red>Second line</red>"
              className="w-full px-3 py-2 text-xs bg-[#111114] border border-[#30303a] rounded-lg text-gray-200 focus:outline-none focus:border-amber-400 font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">
                Custom Model Data <span className="text-[11px] text-gray-500">(Resource packs)</span>
              </label>
              <input
                type="number"
                value={customModelData}
                onChange={(e) => setCustomModelData(e.target.value)}
                placeholder="10001"
                min="0"
                className="w-full px-3 py-2 text-xs bg-[#111114] border border-[#30303a] rounded-lg text-gray-200 focus:outline-none focus:border-amber-400 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Item Flags</label>
              <div className="flex flex-wrap gap-1.5 mt-1">
                {AVAILABLE_FLAGS.slice(0, 3).map((flag) => {
                  const checked = selectedFlags.includes(flag)
                  return (
                    <button
                      key={flag}
                      type="button"
                      onClick={() => {
                        setSelectedFlags(
                          checked ? selectedFlags.filter((f) => f !== flag) : [...selectedFlags, flag]
                        )
                      }}
                      className={`text-[11px] px-2 py-1 rounded border transition ${
                        checked
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                          : 'bg-[#1e1e24] text-gray-400 border-[#30303a]'
                      }`}
                    >
                      {flag}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          <div className="pt-2 flex justify-between items-center">
            {/* Live In-Game Preview Box */}
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-[#0f0f13] border border-[#2b2b35] rounded-lg text-xs">
              <Eye className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-gray-400">Preview:</span>
              <span className="font-semibold text-amber-300">{renderPreviewName(displayName)}</span>
            </div>

            <button
              type="submit"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-lg shadow transition"
            >
              Save Definition
            </button>
          </div>
        </form>
      </div>

      {/* Items & Revisions Side Column */}
      <div className="lg:col-span-5 space-y-4">
        {/* Current Draft Items */}
        <div className="bg-[#16161a] border border-[#27272e] rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-[#27272e]">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-gray-200">Draft Content ({items.length})</h3>
            </div>
            {items.length > 0 && (
              <button
                onClick={handleCreateRevision}
                className="flex items-center space-x-1 px-2.5 py-1 text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-lg hover:bg-emerald-500/30 transition"
              >
                <PackageCheck className="w-3.5 h-3.5" />
                <span>Create Revision</span>
              </button>
            )}
          </div>

          {revMessage && (
            <div className="mb-3 p-2 bg-emerald-950/40 border border-emerald-800/50 rounded text-xs text-emerald-300">
              {revMessage}
            </div>
          )}

          {items.length === 0 ? (
            <div className="py-8 text-center text-xs text-gray-500">
              No items in current draft. Fill out the editor form and click Save.
            </div>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {items.map((it) => (
                <div
                  key={it.id}
                  className="p-2.5 bg-[#1b1b22] border border-[#2e2e38] rounded-lg flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-medium text-gray-200 font-mono">{it.id}</div>
                    <div className="text-[11px] text-gray-400">
                      {it.material} {it.custom_model_data ? `• CMD ${it.custom_model_data}` : ''}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        setId(it.id)
                        setMaterial(it.material)
                        setDisplayName(it.display_name)
                        setLoreText((it.lore || []).join('\n'))
                        setCustomModelData(it.custom_model_data ? it.custom_model_data.toString() : '')
                        setSelectedFlags(it.item_flags || [])
                      }}
                      className="text-[11px] text-amber-400 hover:underline"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(it.id)}
                      className="p-1 text-gray-500 hover:text-red-400 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Revisions History */}
        <div className="bg-[#16161a] border border-[#27272e] rounded-xl p-4 shadow-lg">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
            Immutable Revision History
          </h4>
          {revisions.length === 0 ? (
            <div className="text-xs text-gray-500 py-2">No revisions created yet.</div>
          ) : (
            <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1 text-xs font-mono">
              {revisions.map((r) => (
                <div
                  key={r.id}
                  className="flex items-center justify-between p-2 rounded bg-[#131317] border border-[#24242c]"
                >
                  <span className="text-emerald-400 font-semibold">Rev #{r.revision_number}</span>
                  <span className="text-gray-500">{r.revision_hash.slice(0, 12)}...</span>
                  <span className="text-gray-400">{r.items_count} items</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
