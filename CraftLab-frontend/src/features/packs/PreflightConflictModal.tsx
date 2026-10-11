import React, { useState } from 'react'
import {
  AlertTriangle,
  ExternalLink,
  ShieldAlert,
  X,
  Zap,
  ImageOff,
  FileCode,
  Sparkles,
  Layers,
  CheckCircle2,
} from 'lucide-react'
import { PreflightReport, ConflictItem, PreflightConflict } from '../../api/client'

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

  const hasConflicts = report.conflicts && report.conflicts.length > 0
  const hasWarnings = report.warnings && report.warnings.length > 0
  const [activeTab, setActiveTab] = useState<'conflicts' | 'warnings'>(hasConflicts ? 'conflicts' : 'warnings')

  const itemsToDisplay = activeTab === 'conflicts' ? report.conflicts : (report.warnings || [])

  const renderBadge = (conflict: PreflightConflict) => {
    switch (conflict.type) {
      case 'missing_texture_reference':
        return (
          <span className="flex items-center space-x-1 text-[11px] font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
            <ImageOff className="w-3 h-3" />
            <span>Missing Texture Reference</span>
          </span>
        )
      case 'shader_collision':
        return (
          <span className="flex items-center space-x-1 text-[11px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
            <FileCode className="w-3 h-3" />
            <span>Shader Collision</span>
          </span>
        )
      case 'texture_dimension_anomaly':
        return (
          <span className="flex items-center space-x-1 text-[11px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
            <Sparkles className="w-3 h-3" />
            <span>Mipmap / Animation Safety</span>
          </span>
        )
      case 'item_model_collision':
        return (
          <span className="flex items-center space-x-1 text-[11px] font-semibold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
            <Layers className="w-3 h-3" />
            <span>item_model Collision</span>
          </span>
        )
      case 'custom_model_data_collision':
      default:
        return (
          <span className="flex items-center space-x-1 text-[11px] font-semibold text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
            <AlertTriangle className="w-3 h-3" />
            <span>CustomModelData Collision</span>
          </span>
        )
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div
        className={`bg-[#141418] border rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] ${
          !report.is_valid ? 'border-red-500/30' : 'border-amber-500/30'
        }`}
      >
        {/* Header */}
        <div
          className={`px-6 py-4 border-b flex items-center justify-between ${
            !report.is_valid ? 'bg-red-950/20 border-red-900/30' : 'bg-amber-950/20 border-amber-900/30'
          }`}
        >
          <div className="flex items-center space-x-3">
            <div
              className={`w-10 h-10 rounded-xl border flex items-center justify-center ${
                !report.is_valid
                  ? 'bg-red-500/10 border-red-500/30 text-red-400'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
              }`}
            >
              {!report.is_valid ? <ShieldAlert className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-100 flex items-center space-x-2">
                <span>{!report.is_valid ? 'Pre-Flight Validation Blocked' : 'Pre-Flight Advisory Warnings'}</span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                    !report.is_valid
                      ? 'bg-red-500/20 text-red-400 border-red-500/30'
                      : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                  }`}
                >
                  {!report.is_valid
                    ? `${report.conflicts.length} Critical Issue${report.conflicts.length === 1 ? '' : 's'}`
                    : `${report.warnings.length} Advisory Warning${report.warnings.length === 1 ? '' : 's'}`}
                </span>
              </h3>
              <p className="text-xs text-gray-400">
                {!report.is_valid
                  ? 'Missing textures or colliding model identifiers would break in-game rendering.'
                  : 'Shaders or assets have potential precedence overlaps or mipmap dimension warnings.'}
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

        {/* Tab switchers if both conflicts and warnings exist */}
        {hasConflicts && hasWarnings && (
          <div className="flex border-b border-[#23232b] bg-[#111116] px-6 pt-2">
            <button
              onClick={() => setActiveTab('conflicts')}
              className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition flex items-center space-x-1.5 ${
                activeTab === 'conflicts'
                  ? 'border-red-500 text-red-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              <span>Blocking Conflicts</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-red-500/20 text-red-400 font-mono">
                {report.conflicts.length}
              </span>
            </button>
            <button
              onClick={() => setActiveTab('warnings')}
              className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition flex items-center space-x-1.5 ${
                activeTab === 'warnings'
                  ? 'border-amber-500 text-amber-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              <span>Advisory Warnings</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-500/20 text-amber-400 font-mono">
                {report.warnings.length}
              </span>
            </button>
          </div>
        )}

        {/* Content list */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {itemsToDisplay.map((conflict, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl bg-[#1a1a22] border space-y-3 ${
                conflict.severity === 'error' ? 'border-red-500/20' : 'border-amber-500/20'
              }`}
            >
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                  {renderBadge(conflict)}

                  {conflict.material && (
                    <span className="text-xs font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                      {conflict.material}
                    </span>
                  )}
                  {conflict.custom_model_data !== undefined && conflict.custom_model_data !== null && (
                    <>
                      <span className="text-xs text-gray-400">CMD:</span>
                      <span className="text-xs font-mono font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                        #{conflict.custom_model_data}
                      </span>
                    </>
                  )}
                  {conflict.item_model && (
                    <>
                      <span className="text-xs text-gray-400">item_model:</span>
                      <span className="text-xs font-mono font-bold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                        {conflict.item_model}
                      </span>
                    </>
                  )}
                  {conflict.path && (
                    <span className="text-xs font-mono text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40 truncate max-w-xs">
                      {conflict.path}
                    </span>
                  )}
                </div>

                {conflict.items && conflict.items.length > 0 && (
                  <span className="text-[11px] text-gray-400">{conflict.items.length} conflicting sources</span>
                )}
              </div>

              {/* Explanatory Message */}
              {conflict.message && (
                <p className="text-xs text-gray-300 bg-[#121217] p-2.5 rounded-lg border border-[#22222d] font-mono leading-relaxed">
                  {conflict.message}
                </p>
              )}

              {/* Items grid if available */}
              {conflict.items && conflict.items.length > 0 && (
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
                          <span>Edit in Studio</span>
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-[#111116] border-t border-[#23232b] flex items-center justify-between">
          <div className="text-[11px] text-gray-500 flex items-center space-x-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>
              {!report.is_valid
                ? 'Fix missing textures or duplicate CMDs before compiling.'
                : 'Warnings are advisory; higher priority layers will overwrite lower layers.'}
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#22222a] hover:bg-[#2b2b36] text-gray-300 transition"
            >
              Close
            </button>
            <button
              onClick={() => {
                onForceBuild()
                onClose()
              }}
              className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition ${
                !report.is_valid
                  ? 'bg-red-600/80 hover:bg-red-600 text-white shadow-lg shadow-red-950/50'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-950/50'
              }`}
            >
              {!report.is_valid ? (
                <>
                  <Zap className="w-3.5 h-3.5" />
                  <span>Force Build Anyway</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Proceed with Build</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
