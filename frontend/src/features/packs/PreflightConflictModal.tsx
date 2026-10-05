import React from 'react'
import { AlertTriangle, ExternalLink, ShieldAlert, X, Zap } from 'lucide-react'
import { PreflightReport, ConflictItem } from '../../api/client'

interface PreflightConflictModalProps {
  isOpen: boolean
  report: PreflightReport | null
  onClose: () => void
  onForceBuild: () => void
  onSelectStudioItem?: (itemId: string) => void
}

export const PreflightConflictModal: React.FC<PreflightConflictModalProps> = ({
  isOpen,
  report,
  onClose,
  onForceBuild,
  onSelectStudioItem,
}) => {
  if (!isOpen || !report) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#141418] border border-red-500/30 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 bg-red-950/20 border-b border-red-900/30 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-100 flex items-center space-x-2">
                <span>Pre-Flight Validation Blocked</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30">
                  {report.conflicts.length} Collisions Detected
                </span>
              </h3>
              <p className="text-xs text-gray-400">
                Multiple items share identical CustomModelData numbers on the same base Minecraft item.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/5 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {report.conflicts.map((conflict, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-[#1a1a22] border border-red-500/20 space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    {conflict.material}
                  </span>
                  <span className="text-xs text-gray-400">CustomModelData:</span>
                  <span className="text-xs font-mono font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                    #{conflict.custom_model_data}
                  </span>
                </div>
                <span className="text-[11px] text-gray-400">{conflict.items.length} conflicting sources</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                {conflict.items.map((it: ConflictItem, itIdx: number) => (
                  <div
                    key={itIdx}
                    className="p-3 rounded-lg bg-[#141418] border border-[#262633] flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-white/5 text-gray-300">
                          {it.source}
                        </span>
                        <span className="text-[10px] font-mono text-gray-500">{it.item_id}</span>
                      </div>
                      <div className="text-xs font-medium text-gray-200 truncate">
                        {it.display_name || it.item_id}
                      </div>
                    </div>

                    {it.source === 'Studio' && onSelectStudioItem && (
                      <button
                        onClick={() => {
                          onSelectStudioItem(it.item_id)
                          onClose()
                        }}
                        className="mt-3 flex items-center justify-center space-x-1.5 py-1 px-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[11px] font-medium transition"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span>Edit CMD in Studio</span>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-[#111116] border-t border-[#23232b] flex items-center justify-between">
          <div className="text-[11px] text-gray-500 flex items-center space-x-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Resolving CMDs prevents textures from overwriting in-game.</span>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#22222a] hover:bg-[#2b2b36] text-gray-300 transition"
            >
              Fix in Studio
            </button>
            <button
              onClick={() => {
                onForceBuild()
                onClose()
              }}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-red-600/80 hover:bg-red-600 text-white shadow-lg shadow-red-950/50 transition"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Force Build Anyway</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
