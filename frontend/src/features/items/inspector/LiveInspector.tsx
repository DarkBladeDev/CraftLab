import { useState } from 'react'
import { Eye, Code, Layers } from 'lucide-react'
import { MinecraftSlot } from './MinecraftSlot'
import { MinecraftTooltip, ItemTooltipData } from './MinecraftTooltip'

interface LiveInspectorProps {
  itemData: ItemTooltipData
}

export function LiveInspector({ itemData }: LiveInspectorProps) {
  const [tab, setTab] = useState<'visual' | 'json'>('visual')

  return (
    <div className="bg-[#15151a] border border-[#272733] rounded-xl p-4 shadow-xl sticky top-4">
      {/* Inspector Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#242430]">
        <div className="flex items-center space-x-2">
          <Eye className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
            Live Item Inspector (1.21)
          </h3>
        </div>

        {/* View mode toggle */}
        <div className="flex items-center bg-[#1c1c24] rounded-lg p-0.5 border border-[#2e2e3c]">
          <button
            type="button"
            onClick={() => setTab('visual')}
            className={`flex items-center space-x-1 px-2 py-0.5 text-[11px] rounded transition ${
              tab === 'visual'
                ? 'bg-amber-500/20 text-amber-300 font-medium'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Layers className="w-3 h-3" />
            <span>HUD</span>
          </button>
          <button
            type="button"
            onClick={() => setTab('json')}
            className={`flex items-center space-x-1 px-2 py-0.5 text-[11px] rounded transition ${
              tab === 'json'
                ? 'bg-purple-600/30 text-purple-300 font-medium'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Code className="w-3 h-3" />
            <span>Components</span>
          </button>
        </div>
      </div>

      {tab === 'visual' ? (
        <div className="space-y-4">
          {/* Minecraft 3D Slot Showcase */}
          <div className="p-4 rounded-xl bg-[#0f0f14] border border-[#22222c] flex flex-col items-center justify-center space-y-2">
            <span className="text-[10px] uppercase font-semibold tracking-wider text-gray-400">
              Inventory Slot View
            </span>
            <MinecraftSlot
              material={itemData.material}
              amount={itemData.amount || 1}
              customModelData={itemData.customModelData}
              size="lg"
            />
            <div className="text-[11px] font-mono text-gray-400 text-center">
              {itemData.material}
              {itemData.customModelData ? ` • CMD #${itemData.customModelData}` : ''}
            </div>
          </div>

          {/* Minecraft Pixel Tooltip Showcase */}
          <div className="p-4 rounded-xl bg-[#0b0b0e] border border-[#1f1f28] flex flex-col items-center justify-center">
            <div className="w-full flex justify-between items-center mb-2">
              <span className="text-[10px] uppercase font-semibold tracking-wider text-gray-400">
                In-Game Tooltip Preview
              </span>
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/40">
                Real-Time
              </span>
            </div>

            <div className="w-full flex justify-center py-2">
              <MinecraftTooltip {...itemData} />
            </div>
          </div>
        </div>
      ) : (
        /* Raw Components JSON View */
        <div className="space-y-2">
          <div className="flex justify-between items-center text-[10px] text-gray-400 font-semibold uppercase">
            <span>Canonical Data Components</span>
            <span>{Object.keys(itemData.components || {}).length} active</span>
          </div>
          <pre className="p-3 bg-[#0c0c10] border border-[#22222d] rounded-lg text-[11px] font-mono text-purple-300 overflow-x-auto max-h-96">
            {JSON.stringify(itemData.components || {}, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
