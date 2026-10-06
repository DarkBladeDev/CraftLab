import { useState, useEffect } from 'react'
import { Box, Rocket, ShieldCheck, Terminal, Package, Wrench, Armchair, FolderGit2 } from 'lucide-react'
import { TargetMonitor } from './features/targets/TargetMonitor'
import { ItemEditor } from './features/items/ItemEditor'
import { BlockStudio } from './features/blocks/BlockStudio'
import { DeployModal } from './features/deployments/DeployModal'
import { ResourcePackManagerView } from './features/packs/ResourcePackManagerView'
import { AssetWorkspaceView } from './features/assets/AssetWorkspaceView'
import { fetchRevisions, fetchTargets } from './api/client'

export default function App() {
  const [selectedTargetId, setSelectedTargetId] = useState<string>('local-paper-server')
  const [latestRevisionId, setLatestRevisionId] = useState<string | undefined>(undefined)
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'studio' | 'blocks' | 'packs' | 'assets'>('studio')

  const refreshLatestRevision = async () => {
    try {
      const revs = await fetchRevisions()
      if (revs.length > 0) {
        setLatestRevisionId(revs[0].id)
      }
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    refreshLatestRevision()
    fetchTargets().then((targets) => {
      if (targets.length > 0 && !selectedTargetId) {
        setSelectedTargetId(targets[0].id)
      }
    })
  }, [])

  return (
    <div className="min-h-screen bg-[#0e0e11] text-gray-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-[#23232b] bg-[#141418]/80 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-green-400 flex items-center justify-center shadow-lg shadow-emerald-950/40">
              <Box className="w-5 h-5 text-gray-950" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight text-gray-100 flex items-center space-x-1.5">
                <span>Minecraft Content Platform</span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  v1.0 Paper 1.21
                </span>
              </div>
              <div className="text-[11px] text-gray-400">Canonical Content & Real-time Release Engine</div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center space-x-2 text-xs px-3 py-1.5 rounded-lg bg-[#1c1c22] border border-[#2b2b35] text-gray-300">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Allowlisted Protocol: Strict</span>
            </div>

            <button
              onClick={async () => {
                await refreshLatestRevision()
                setIsDeployModalOpen(true)
              }}
              className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white text-xs font-semibold rounded-xl shadow-lg shadow-emerald-950/50 transition transform active:scale-95"
            >
              <Rocket className="w-4 h-4" />
              <span>Publish & Deploy</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6 space-y-6">
        {/* Fleet Monitor */}
        <section>
          <TargetMonitor
            selectedTargetId={selectedTargetId}
            onSelectTarget={(id) => setSelectedTargetId(id)}
          />
        </section>

        {/* Tab Selector */}
        <div className="flex items-center space-x-2 border-b border-[#23232b] pb-2">
          <button
            onClick={() => setActiveTab('studio')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              activeTab === 'studio'
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
            }`}
          >
            <Wrench className="w-3.5 h-3.5" />
            <span>Items Studio</span>
          </button>
          <button
            onClick={() => setActiveTab('blocks')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              activeTab === 'blocks'
                ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
            }`}
          >
            <Armchair className="w-3.5 h-3.5" />
            <span>Blocks & Props</span>
          </button>
          <button
            onClick={() => setActiveTab('packs')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              activeTab === 'packs'
                ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
            }`}
          >
            <Package className="w-3.5 h-3.5" />
            <span>Resource Packs</span>
          </button>
          <button
            onClick={() => setActiveTab('assets')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              activeTab === 'assets'
                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
            }`}
          >
            <FolderGit2 className="w-3.5 h-3.5" />
            <span>Asset Explorer</span>
          </button>
        </div>

        {/* Workspace Views */}
        {activeTab === 'studio' && (
          <section>
            <ItemEditor onRevisionCreated={refreshLatestRevision} />
          </section>
        )}
        {activeTab === 'blocks' && (
          <section>
            <BlockStudio onRevisionCreated={refreshLatestRevision} />
          </section>
        )}
        {activeTab === 'packs' && (
          <section>
            <ResourcePackManagerView
              selectedTargetId={selectedTargetId}
              onSelectStudioItem={() => {
                setActiveTab('studio')
              }}
            />
          </section>
        )}
        {activeTab === 'assets' && (
          <section>
            <AssetWorkspaceView />
          </section>
        )}

        {/* Quick In-Game Help Footer Card */}
        <div className="p-4 rounded-xl bg-[#141418] border border-[#23232b] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-gray-400">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-gray-500" />
              <span>Give Item:</span>
              <code className="text-emerald-400 bg-[#0e0e11] px-2 py-0.5 rounded border border-[#22222a]">
                /mcp give &lt;player&gt; &lt;item_id&gt;
              </code>
            </div>
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-purple-400" />
              <span>Reload Pack:</span>
              <code className="text-purple-300 bg-[#0e0e11] px-2 py-0.5 rounded border border-[#22222a]">
                /mcp reloadpack [all]
              </code>
            </div>
          </div>
          <span className="text-gray-500 text-[11px]">Paper 1.21 Resource Pipeline Active</span>
        </div>
      </main>

      {/* Deploy Modal */}
      <DeployModal
        isOpen={isDeployModalOpen}
        onClose={() => setIsDeployModalOpen(false)}
        revisionId={latestRevisionId}
        targetId={selectedTargetId}
      />
    </div>
  )
}
