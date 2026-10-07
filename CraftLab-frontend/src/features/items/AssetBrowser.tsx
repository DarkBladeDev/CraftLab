import { useState, useEffect } from 'react'
import { Search, RefreshCw, GitFork, Package, Shield, Sparkles, Layers } from 'lucide-react'
import {
  Target,
  Item,
  VanillaItem,
  DiscoveredItem,
  fetchVanillaCatalog,
  fetchDiscoveredCatalog,
  syncTargetCatalog,
} from '../../api/client'

interface AssetBrowserProps {
  targets: Target[]
  platformItems: Item[]
  onForkItem: (template: Partial<Item>) => void
}

export function AssetBrowser({ targets, platformItems, onForkItem }: AssetBrowserProps) {
  const [activeTab, setActiveTab] = useState<'vanilla' | 'platform' | 'oraxen'>('vanilla')
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedTargetId, setSelectedTargetId] = useState<string>('')

  const [vanillaCategories, setVanillaCategories] = useState<string[]>([])
  const [vanillaItems, setVanillaItems] = useState<VanillaItem[]>([])
  const [discoveredItems, setDiscoveredItems] = useState<DiscoveredItem[]>([])
  const [loading, setLoading] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [syncStatus, setSyncStatus] = useState<string | null>(null)

  // Initialize selected target
  useEffect(() => {
    if (targets.length > 0 && !selectedTargetId) {
      const onlineTarget = targets.find((t) => t.status === 'online')
      setSelectedTargetId(onlineTarget ? onlineTarget.id : targets[0].id)
    }
  }, [targets, selectedTargetId])

  // Load vanilla catalog
  useEffect(() => {
    const loadVanilla = async () => {
      try {
        const data = await fetchVanillaCatalog(
          selectedCategory === 'all' ? undefined : selectedCategory,
          search || undefined
        )
        setVanillaCategories(['all', ...data.categories])
        setVanillaItems(data.items)
      } catch (err) {
        console.error('Error fetching vanilla catalog:', err)
      }
    }
    if (activeTab === 'vanilla') {
      loadVanilla()
    }
  }, [activeTab, selectedCategory, search])

  // Load discovered items
  useEffect(() => {
    const loadDiscovered = async () => {
      if (!selectedTargetId) return
      setLoading(true)
      try {
        const items = await fetchDiscoveredCatalog(selectedTargetId, 'oraxen', search || undefined)
        setDiscoveredItems(items)
      } catch (err) {
        console.error('Error fetching discovered catalog:', err)
      } finally {
        setLoading(false)
      }
    }
    if (activeTab === 'oraxen') {
      loadDiscovered()
    }
  }, [activeTab, selectedTargetId, search])

  const handleSync = async () => {
    if (!selectedTargetId) return
    setIsSyncing(true)
    setSyncStatus(null)
    try {
      await syncTargetCatalog(selectedTargetId)
      setSyncStatus('Catalog refreshed in live from server!')
      setTimeout(() => setSyncStatus(null), 3000)
      const items = await fetchDiscoveredCatalog(selectedTargetId, 'oraxen', search || undefined)
      setDiscoveredItems(items)
    } catch (err: any) {
      setSyncStatus(`Sync error: ${err.message}`)
      setTimeout(() => setSyncStatus(null), 4000)
    } finally {
      setIsSyncing(false)
    }
  }

  // Filter platform items locally
  const filteredPlatformItems = platformItems.filter(
    (it) =>
      it.id.toLowerCase().includes(search.toLowerCase()) ||
      it.material.toLowerCase().includes(search.toLowerCase()) ||
      it.display_name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="bg-[#141418] border border-[#27272e] rounded-xl p-5 shadow-xl mb-6">
      {/* Top Header & Navigation Tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-4 border-b border-[#24242c] gap-3">
        <div className="flex items-center space-x-2">
          <Package className="w-5 h-5 text-amber-400" />
          <h2 className="text-base font-semibold text-gray-100">Multi-Source Asset Browser</h2>
        </div>

        {/* Catalog Navigation Tabs */}
        <div className="flex items-center space-x-1.5 bg-[#1a1a20] p-1 rounded-lg border border-[#2d2d38]">
          <button
            onClick={() => setActiveTab('vanilla')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition ${
              activeTab === 'vanilla'
                ? 'bg-amber-500/20 text-amber-300 font-medium'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Shield className="w-3.5 h-3.5 text-blue-400" />
            <span>Vanilla 1.21 ({vanillaItems.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('platform')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition ${
              activeTab === 'platform'
                ? 'bg-emerald-500/20 text-emerald-300 font-medium'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            <span>Platform Drafts ({platformItems.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('oraxen')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition ${
              activeTab === 'oraxen'
                ? 'bg-purple-500/20 text-purple-300 font-medium'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>Oraxen Discovered ({discoveredItems.length})</span>
          </button>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-4">
        {/* Search Input */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search assets by name or ID..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#101014] border border-[#2d2d38] rounded-lg text-gray-200 focus:outline-none focus:border-amber-400"
          />
        </div>

        {/* Tab-specific Controls */}
        {activeTab === 'vanilla' && (
          <div className="flex flex-wrap gap-1">
            {vanillaCategories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`text-[11px] px-2.5 py-1 rounded-md capitalize transition ${
                  selectedCategory === cat
                    ? 'bg-blue-600 text-white font-medium'
                    : 'bg-[#1b1b22] text-gray-400 hover:text-gray-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        )}

        {activeTab === 'oraxen' && (
          <div className="flex items-center space-x-2">
            <select
              value={selectedTargetId}
              onChange={(e) => setSelectedTargetId(e.target.value)}
              className="text-xs bg-[#101014] border border-[#2d2d38] text-gray-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-purple-400"
            >
              {targets.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.status})
                </option>
              ))}
            </select>

            <button
              onClick={handleSync}
              disabled={isSyncing}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs bg-purple-600/20 text-purple-300 border border-purple-500/30 rounded-lg hover:bg-purple-600/30 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Syncing...' : 'Sync Live'}</span>
            </button>
          </div>
        )}
      </div>

      {syncStatus && (
        <div className="mb-3 p-2 bg-purple-950/40 border border-purple-800/40 rounded-lg text-xs text-purple-300">
          {syncStatus}
        </div>
      )}

      {/* Asset Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-72 overflow-y-auto pr-1">
        {/* Vanilla Items */}
        {activeTab === 'vanilla' &&
          vanillaItems.map((item) => (
            <div
              key={item.id}
              className="bg-[#17171d] border border-[#26262e] rounded-lg p-3 flex flex-col justify-between hover:border-gray-500 transition"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-gray-200">{item.name}</span>
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-950/50 text-blue-300 border border-blue-900/50">
                    {item.category}
                  </span>
                </div>
                <div className="text-[11px] text-gray-400 font-mono">{item.id}</div>
              </div>

              <div className="pt-2 mt-2 border-t border-[#22222a] flex items-center justify-between">
                <span className="text-[10px] text-gray-500">Stack: {item.stack_size}</span>
                <button
                  onClick={() =>
                    onForkItem({
                      material: item.id,
                      display_name: item.name,
                      id: item.id.toLowerCase(),
                    })
                  }
                  className="flex items-center space-x-1 px-2 py-1 text-[11px] bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 rounded border border-blue-500/20 transition"
                >
                  <GitFork className="w-3 h-3" />
                  <span>Fork as Base</span>
                </button>
              </div>
            </div>
          ))}

        {/* Platform Drafts */}
        {activeTab === 'platform' &&
          filteredPlatformItems.map((item) => (
            <div
              key={item.id}
              className="bg-[#17171d] border border-[#26262e] rounded-lg p-3 flex flex-col justify-between hover:border-emerald-600 transition"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-emerald-300 font-mono">{item.id}</span>
                  {item.custom_model_data && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/50 text-emerald-300 border border-emerald-900/50">
                      CMD {item.custom_model_data}
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-gray-300">{item.material}</div>
                <div className="text-[11px] text-gray-400 truncate">{item.display_name}</div>
              </div>

              <div className="pt-2 mt-2 border-t border-[#22222a] flex items-center justify-between">
                <span className="text-[10px] text-gray-500 uppercase">
                  {item.export_format || 'native'}
                </span>
                <button
                  onClick={() =>
                    onForkItem({
                      ...item,
                      id: `${item.id}_copy`,
                    })
                  }
                  className="flex items-center space-x-1 px-2 py-1 text-[11px] bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 rounded border border-emerald-500/20 transition"
                >
                  <GitFork className="w-3 h-3" />
                  <span>Fork as Base</span>
                </button>
              </div>
            </div>
          ))}

        {/* Oraxen Discovered Items */}
        {activeTab === 'oraxen' &&
          (loading ? (
            <div className="col-span-3 text-center py-8 text-xs text-gray-500">
              Loading discovered items from target...
            </div>
          ) : discoveredItems.length === 0 ? (
            <div className="col-span-3 text-center py-8 text-xs text-gray-500">
              No discovered Oraxen items found. Click 'Sync Live' when the server agent is connected.
            </div>
          ) : (
            discoveredItems.map((item) => (
              <div
                key={item.id}
                className="bg-[#17171d] border border-[#26262e] rounded-lg p-3 flex flex-col justify-between hover:border-purple-600 transition"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-purple-300 font-mono">
                      {item.item_id}
                    </span>
                    {item.custom_model_data && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-950/50 text-purple-300 border border-purple-900/50">
                        CMD {item.custom_model_data}
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-gray-300">{item.material}</div>
                  <div className="text-[11px] text-gray-400 truncate">
                    {item.display_name || item.item_id}
                  </div>
                </div>

                <div className="pt-2 mt-2 border-t border-[#22222a] flex items-center justify-between">
                  <span className="text-[10px] text-purple-400 font-mono">source: oraxen</span>
                  <button
                    onClick={() =>
                      onForkItem({
                        id: `${item.item_id}_custom`,
                        material: item.material,
                        display_name: item.display_name || item.item_id,
                        lore: item.lore || [],
                        custom_model_data: item.custom_model_data,
                        export_format: 'oraxen',
                        plugin_properties: item.raw_properties || {},
                      })
                    }
                    className="flex items-center space-x-1 px-2 py-1 text-[11px] bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 rounded border border-purple-500/20 transition"
                  >
                    <GitFork className="w-3 h-3" />
                    <span>Fork as Base</span>
                  </button>
                </div>
              </div>
            ))
          ))}
      </div>
    </div>
  )
}
