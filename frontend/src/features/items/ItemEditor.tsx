import { useState, useEffect, useRef } from 'react'
import {
  Sparkles,
  Trash2,
  PackageCheck,
  Layers,
  Wrench,
  Flame,
  Plus,
  RotateCcw,
} from 'lucide-react'
import {
  fetchItems,
  saveItem,
  deleteItem,
  createRevision,
  Item,
  Revision,
  fetchRevisions,
  Target,
  fetchTargets,
  PluginSchema,
  fetchPluginSchema,
} from '../../api/client'
import { AssetBrowser } from './AssetBrowser'
import { ConfigSchemaEngine } from './ConfigSchemaEngine'
import { MiniMessageToolbar } from './minimessage/MiniMessageToolbar'
import { ComponentBuilder } from './ComponentBuilder'
import { LiveInspector } from './inspector/LiveInspector'

const POPULAR_MATERIALS = [
  'DIAMOND_SWORD',
  'NETHERITE_SWORD',
  'MACE',
  'BOW',
  'CROSSBOW',
  'TRIDENT',
  'DIAMOND_PICKAXE',
  'NETHERITE_PICKAXE',
  'NETHERITE_CHESTPLATE',
  'DIAMOND_CHESTPLATE',
  'SHIELD',
  'WIND_CHARGE',
  'FEATHER',
  'STICK',
  'EMERALD',
  'BLAZE_ROD',
]

const AVAILABLE_FLAGS = [
  'HIDE_ATTRIBUTES',
  'HIDE_ENCHANTS',
  'HIDE_UNBREAKABLE',
  'HIDE_DESTROYS',
  'HIDE_PLACED_ON',
  'HIDE_ADDITIONAL_TOOLTIP',
]

export function ItemEditor({ onRevisionCreated }: { onRevisionCreated?: () => void }) {
  const [items, setItems] = useState<Item[]>([])
  const [revisions, setRevisions] = useState<Revision[]>([])
  const [targets, setTargets] = useState<Target[]>([])
  const [oraxenSchema, setOraxenSchema] = useState<PluginSchema | null>(null)
  const [revMessage, setRevMessage] = useState<string | null>(null)

  // Form State
  const [id, setId] = useState('ruby_sword')
  const [material, setMaterial] = useState('NETHERITE_SWORD')
  const [displayName, setDisplayName] = useState('<gradient:#ff2a2a:#ffaa00><bold>Ruby Broadsword</bold></gradient>')
  const [loreText, setLoreText] = useState(
    '<gray>Forged in ancient magma chambers.</gray>\n<dark_red>Attack Damage: +14</dark_red>'
  )
  const [customModelData, setCustomModelData] = useState<string>('10001')
  const [itemModel, setItemModel] = useState<string>('')
  const [selectedFlags, setSelectedFlags] = useState<string[]>(['HIDE_ATTRIBUTES'])
  const [exportFormat, setExportFormat] = useState<'native' | 'oraxen'>('native')
  const [components, setComponents] = useState<Record<string, any>>({
    'minecraft:attribute_modifiers': [
      { type: 'generic.attack_damage', amount: 14.0, slot: 'mainhand' },
      { type: 'generic.attack_speed', amount: 1.6, slot: 'mainhand' },
    ],
    'minecraft:enchantments': {
      sharpness: 5,
      unbreaking: 3,
    },
  })
  const [pluginProperties, setPluginProperties] = useState<Record<string, any>>({})
  const [rawYaml, setRawYaml] = useState<string>('')
  const [formError, setFormError] = useState<string | null>(null)

  // Input tracking for Toolbar
  const displayNameRef = useRef<HTMLInputElement>(null)
  const loreRef = useRef<HTMLTextAreaElement>(null)
  const [activeInput, setActiveInput] = useState<'displayName' | 'lore'>('displayName')

  const loadData = async () => {
    try {
      const [itms, revs, tgts, schema] = await Promise.all([
        fetchItems(),
        fetchRevisions(),
        fetchTargets(),
        fetchPluginSchema('oraxen-item-v1').catch(() => null),
      ])
      setItems(itms)
      setRevisions(revs)
      setTargets(tgts)
      if (schema) setOraxenSchema(schema)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleForkItem = (template: Partial<Item>) => {
    if (template.id) setId(template.id)
    if (template.material) setMaterial(template.material)
    if (template.display_name) setDisplayName(template.display_name)
    if (template.lore) setLoreText(template.lore.join('\n'))
    if (template.custom_model_data !== undefined) {
      setCustomModelData(template.custom_model_data ? template.custom_model_data.toString() : '')
    }
    if (template.item_model !== undefined) {
      setItemModel(template.item_model || '')
    }
    if (template.export_format) {
      setExportFormat(template.export_format as 'native' | 'oraxen')
    }
    if (template.components) {
      setComponents(template.components)
    }
    if (template.plugin_properties) {
      setPluginProperties(template.plugin_properties)
    }
    if (template.raw_extensions) {
      setRawYaml(template.raw_extensions)
    }
  }

  const handleSelectDraft = (it: Item) => {
    setId(it.id)
    setMaterial(it.material)
    setDisplayName(it.display_name)
    setLoreText((it.lore || []).join('\n'))
    setCustomModelData(it.custom_model_data ? it.custom_model_data.toString() : '')
    setItemModel(it.item_model || '')
    setSelectedFlags(it.item_flags || [])
    setComponents(it.components || {})
    setExportFormat((it.export_format as 'native' | 'oraxen') || 'native')
    setPluginProperties(it.plugin_properties || {})
    setRawYaml(it.raw_extensions || '')
  }

  const handleNewDraft = () => {
    setId('')
    setMaterial('DIAMOND_SWORD')
    setDisplayName('')
    setLoreText('')
    setCustomModelData('')
    setItemModel('')
    setSelectedFlags([])
    setComponents({})
    setPluginProperties({})
    setRawYaml('')
  }

  const handleWrapSelection = (openTag: string, closeTag: string) => {
    if (activeInput === 'displayName') {
      const el = displayNameRef.current
      if (!el) return
      const start = el.selectionStart || 0
      const end = el.selectionEnd || 0
      const sel = displayName.substring(start, end)
      const replacement = `${openTag}${sel || 'Item Name'}${closeTag}`
      const next = displayName.substring(0, start) + replacement + displayName.substring(end)
      setDisplayName(next)
      setTimeout(() => {
        el.focus()
        el.setSelectionRange(start + openTag.length, start + openTag.length + (sel || 'Item Name').length)
      }, 10)
    } else {
      const el = loreRef.current
      if (!el) return
      const start = el.selectionStart || 0
      const end = el.selectionEnd || 0
      const sel = loreText.substring(start, end)
      const replacement = `${openTag}${sel || 'Lore Line'}${closeTag}`
      const next = loreText.substring(0, start) + replacement + loreText.substring(end)
      setLoreText(next)
      setTimeout(() => {
        el.focus()
        el.setSelectionRange(start + openTag.length, start + openTag.length + (sel || 'Lore Line').length)
      }, 10)
    }
  }

  const handleInsertText = (text: string) => {
    if (activeInput === 'displayName') {
      const el = displayNameRef.current
      const start = el?.selectionStart || displayName.length
      const next = displayName.substring(0, start) + text + displayName.substring(start)
      setDisplayName(next)
    } else {
      const el = loreRef.current
      const start = el?.selectionStart || loreText.length
      const next = loreText.substring(0, start) + text + loreText.substring(start)
      setLoreText(next)
    }
  }

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
        item_model: itemModel.trim() ? itemModel.trim() : null,
        item_flags: selectedFlags,
        amount: 1,
        components,
        export_format: exportFormat,
        plugin_properties: pluginProperties,
        raw_extensions: rawYaml,
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

  return (
    <div className="space-y-6">
      {/* 1. Multi-Source Asset Browser Component */}
      <AssetBrowser
        targets={targets}
        platformItems={items}
        onForkItem={handleForkItem}
      />

      {/* 2. 3-Column Studio Workspace */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
        {/* COLUMN 1: DRAFTS & REVISIONS (~25% / xl:col-span-3) */}
        <div className="xl:col-span-3 space-y-4">
          {/* Draft Items List */}
          <div className="bg-[#16161a] border border-[#27272e] rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-[#27272e]">
              <div className="flex items-center space-x-2">
                <Layers className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
                  Draft Items ({items.length})
                </h3>
              </div>
              <button
                type="button"
                onClick={handleNewDraft}
                className="flex items-center space-x-1 px-2 py-1 text-[11px] font-medium bg-[#1e1e26] hover:bg-[#282834] text-emerald-300 border border-emerald-500/30 rounded transition"
                title="Create New Draft"
              >
                <Plus className="w-3 h-3" />
                <span>New</span>
              </button>
            </div>

            {items.length === 0 ? (
              <div className="py-6 text-center text-xs text-gray-500">
                No items in draft. Use New to create one.
              </div>
            ) : (
              <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
                {items.map((it) => {
                  const isSelected = it.id === id
                  return (
                    <div
                      key={it.id}
                      onClick={() => handleSelectDraft(it)}
                      className={`p-2.5 rounded-lg border transition cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? 'bg-[#1e1e28] border-amber-500/50 shadow-sm'
                          : 'bg-[#15151c] border-[#252530] hover:bg-[#1a1a22]'
                      }`}
                    >
                      <div className="truncate">
                        <div className="flex items-center space-x-1.5">
                          <span className="text-xs font-medium text-gray-200 font-mono truncate">
                            {it.id}
                          </span>
                          {it.export_format === 'oraxen' && (
                            <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-purple-950/60 text-purple-300 border border-purple-800/50">
                              oraxen
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-gray-400 truncate flex items-center space-x-1.5">
                          <span>{it.material}</span>
                          {it.custom_model_data ? <span>• CMD {it.custom_model_data}</span> : null}
                          {it.item_model ? (
                            <span className="text-cyan-400 font-mono text-[10px]">
                              • {it.item_model}
                            </span>
                          ) : null}
                        </div>
                      </div>
                      <div className="flex items-center space-x-1 ml-2">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(it.id)
                          }}
                          className="p-1 text-gray-500 hover:text-red-400 transition"
                          title="Delete draft item"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {items.length > 0 && (
              <div className="mt-3 pt-3 border-t border-[#252530]">
                <button
                  type="button"
                  onClick={handleCreateRevision}
                  className="w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 text-xs font-medium bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 rounded-lg transition"
                >
                  <PackageCheck className="w-3.5 h-3.5" />
                  <span>Snapshot Revision</span>
                </button>
              </div>
            )}

            {revMessage && (
              <div className="mt-2 p-2 bg-emerald-950/40 border border-emerald-800/50 rounded text-xs text-emerald-300">
                {revMessage}
              </div>
            )}
          </div>

          {/* Immutable Revisions List */}
          <div className="bg-[#16161a] border border-[#27272e] rounded-xl p-4 shadow-lg">
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-2">
              Revision History
            </h4>
            {revisions.length === 0 ? (
              <div className="text-xs text-gray-500 py-2">No revisions snapshot yet.</div>
            ) : (
              <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1 text-xs font-mono">
                {revisions.map((r) => (
                  <div
                    key={r.id}
                    className="flex items-center justify-between p-2 rounded bg-[#131317] border border-[#24242c]"
                  >
                    <span className="text-emerald-400 font-semibold">Rev #{r.revision_number}</span>
                    <span className="text-gray-500">{r.revision_hash.slice(0, 10)}...</span>
                    <span className="text-gray-400">{r.items_count} items</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* COLUMN 2: ITEM DEFINITION EDITOR & BUILDERS (~45% / xl:col-span-5) */}
        <div className="xl:col-span-5 bg-[#16161a] border border-[#27272e] rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#27272e]">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-amber-400" />
              <h2 className="text-sm font-semibold text-gray-200">
                Item Editor
              </h2>
            </div>

            {/* Target Exporter Selector */}
            <div className="flex items-center space-x-1.5 bg-[#101014] p-1 rounded-lg border border-[#282833]">
              <button
                type="button"
                onClick={() => setExportFormat('native')}
                className={`flex items-center space-x-1 px-2 py-0.5 text-xs rounded transition ${
                  exportFormat === 'native'
                    ? 'bg-emerald-600/30 text-emerald-300 font-medium'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                <Wrench className="w-3 h-3" />
                <span>Native</span>
              </button>

              <button
                type="button"
                onClick={() => setExportFormat('oraxen')}
                className={`flex items-center space-x-1 px-2 py-0.5 text-xs rounded transition ${
                  exportFormat === 'oraxen'
                    ? 'bg-purple-600/30 text-purple-300 font-medium'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                <Flame className="w-3 h-3 text-purple-400" />
                <span>Oraxen</span>
              </button>
            </div>
          </div>

          {formError && (
            <div className="p-3 bg-red-950/40 border border-red-800/50 rounded-lg text-xs text-red-300">
              {formError}
            </div>
          )}

          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">
                  Item Identifier (Slug)
                </label>
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
                <label className="block text-xs font-medium text-gray-400 mb-1">
                  Vanilla Material
                </label>
                <input
                  list="materials"
                  value={material}
                  onChange={(e) => setMaterial(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-[#111114] border border-[#30303a] rounded-lg text-gray-200 focus:outline-none focus:border-amber-400 font-mono uppercase"
                  required
                />
                <datalist id="materials">
                  {POPULAR_MATERIALS.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              </div>
            </div>

            {/* MiniMessage Toolbar & Display Name */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-medium text-gray-400">
                  Display Name <span className="text-[11px] text-gray-500">(Adventure MiniMessage)</span>
                </label>
                <span className="text-[10px] text-amber-400 font-mono">
                  {activeInput === 'displayName' ? 'Active in Toolbar' : ''}
                </span>
              </div>

              <MiniMessageToolbar
                onWrapSelection={handleWrapSelection}
                onInsertText={handleInsertText}
              />

              <input
                ref={displayNameRef}
                type="text"
                value={displayName}
                onFocus={() => setActiveInput('displayName')}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="<gradient:#ff0000:#ffaa00>Ruby Sword</gradient>"
                className="w-full px-3 py-2 text-xs bg-[#111114] border border-[#30303a] rounded-lg text-gray-200 focus:outline-none focus:border-amber-400 font-mono"
                required
              />
            </div>

            {/* Lore Lines */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">
                Lore Lines <span className="text-[11px] text-gray-500">(One line per entry)</span>
              </label>
              <textarea
                ref={loreRef}
                rows={3}
                value={loreText}
                onFocus={() => setActiveInput('lore')}
                onChange={(e) => setLoreText(e.target.value)}
                placeholder="<gray>First line</gray>&#10;<red>Second line</red>"
                className="w-full px-3 py-2 text-xs bg-[#111114] border border-[#30303a] rounded-lg text-gray-200 focus:outline-none focus:border-amber-400 font-mono"
              />
            </div>

            {/* Multi-Version Model Identifiers: CMD (1.21.1) and Item Model (1.21.2+) */}
            <div className="p-3.5 rounded-xl bg-[#121216] border border-[#262632] space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-[#20202a]">
                <div className="flex items-center space-x-2">
                  <Layers className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="text-xs font-semibold text-gray-200">
                    Multi-Version Model Configuration
                  </span>
                </div>
                <span className="text-[10px] text-gray-400">
                  Universal Hybrid (1.21.1 – 1.21.11)
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {/* 1.21.1 CMD */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-medium text-gray-300">
                      Legacy CMD <span className="text-[10px] text-purple-400">(1.21.1)</span>
                    </label>
                  </div>
                  <input
                    type="number"
                    value={customModelData}
                    onChange={(e) => setCustomModelData(e.target.value)}
                    placeholder="10001"
                    min="0"
                    className="w-full px-3 py-2 text-xs bg-[#17171f] border border-[#30303e] rounded-lg text-gray-200 focus:outline-none focus:border-purple-400 font-mono"
                  />
                  <span className="text-[10px] text-gray-500 block mt-1">
                    Used by 1.21.1 via models/item override
                  </span>
                </div>

                {/* 1.21.2+ item_model */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-medium text-gray-300">
                      Item Model Key <span className="text-[10px] text-cyan-400">(1.21.2+)</span>
                    </label>
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded font-mono ${
                        itemModel.trim()
                          ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                          : 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20'
                      }`}
                    >
                      {itemModel.trim() ? 'Custom' : 'Auto-Derived'}
                    </span>
                  </div>
                  <input
                    type="text"
                    value={itemModel}
                    onChange={(e) => setItemModel(e.target.value)}
                    placeholder={id.trim() ? `studio:${id.trim()}` : 'studio:<id>'}
                    className="w-full px-3 py-2 text-xs bg-[#17171f] border border-[#30303e] rounded-lg text-gray-200 focus:outline-none focus:border-cyan-400 font-mono"
                  />
                  <span className="text-[10px] text-gray-500 block mt-1 truncate">
                    {itemModel.trim() ? (
                      <span className="text-amber-400/80">Explicit: {itemModel.trim()}</span>
                    ) : (
                      <span>
                        Auto-derives as <code className="text-cyan-400">studio:{id.trim() || 'id'}</code>
                      </span>
                    )}
                  </span>
                </div>
              </div>
            </div>

            {/* Item Flags */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">
                Item Flags
              </label>
              <div className="flex flex-wrap gap-1.5">
                {AVAILABLE_FLAGS.slice(0, 4).map((flag) => {
                  const checked = selectedFlags.includes(flag)
                  return (
                    <button
                      key={flag}
                      type="button"
                      onClick={() => {
                        setSelectedFlags(
                          checked
                            ? selectedFlags.filter((f) => f !== flag)
                            : [...selectedFlags, flag]
                        )
                      }}
                      className={`text-[10px] px-2.5 py-1 rounded-md border transition ${
                        checked
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                          : 'bg-[#1e1e24] text-gray-400 border-[#30303a]'
                      }`}
                    >
                      {flag.replace('HIDE_', '')}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* 1.21 Data Components Visual Builder */}
            <ComponentBuilder
              components={components}
              onChangeComponents={setComponents}
            />

            {/* Oraxen Schema Engine Block */}
            {exportFormat === 'oraxen' && (
              <ConfigSchemaEngine
                schema={oraxenSchema}
                properties={pluginProperties}
                onChangeProperties={setPluginProperties}
                rawYaml={rawYaml}
                onChangeRawYaml={setRawYaml}
              />
            )}

            <div className="pt-3 border-t border-[#252530] flex justify-between items-center">
              <button
                type="button"
                onClick={handleNewDraft}
                className="flex items-center space-x-1 px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200 border border-[#2f2f3d] rounded-lg transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset</span>
              </button>

              <button
                type="submit"
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-lg transition"
              >
                Save Item Definition
              </button>
            </div>
          </form>
        </div>

        {/* COLUMN 3: STICKY LIVE INSPECTOR (~30% / xl:col-span-4) */}
        <div className="xl:col-span-4">
          <LiveInspector
            itemData={{
              id,
              material,
              displayName,
              lore: loreText
                .split('\n')
                .map((l) => l.trim())
                .filter((l) => l.length > 0),
              customModelData: customModelData ? parseInt(customModelData, 10) : null,
              itemModel: itemModel.trim() || (id.trim() ? `studio:${id.trim()}` : null),
              itemFlags: selectedFlags,
              amount: 1,
              components,
            }}
          />
        </div>
      </div>
    </div>
  )
}
