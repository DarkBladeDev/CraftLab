import React, { useState, useEffect } from 'react'
import {
  WorkspaceFileMetadata,
  fetchWorkspaceMetadata,
} from '../../api/client'
import {
  Compass,
  Copy,
  Check,
  Tag,
  Layers,
  FileCheck2,
  AlertTriangle,
  HardDrive,
  Maximize2,
  Link2,
} from 'lucide-react'

interface MetadataViewerProps {
  selectedFilePath: string | null
  onNavigateToPath?: (path: string) => void
}

export const MetadataViewer: React.FC<MetadataViewerProps> = ({
  selectedFilePath,
  onNavigateToPath,
}) => {
  const [metadata, setMetadata] = useState<WorkspaceFileMetadata | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  useEffect(() => {
    if (!selectedFilePath) {
      setMetadata(null)
      return
    }

    setLoading(true)
    fetchWorkspaceMetadata(selectedFilePath)
      .then((data) => setMetadata(data))
      .catch((err) => {
        console.error('Metadata fetch error:', err)
        setMetadata(null)
      })
      .finally(() => setLoading(false))
  }, [selectedFilePath])

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (!selectedFilePath) {
    return (
      <div className="h-full bg-[#121217] rounded-xl border border-[#23232b] p-4 flex items-center justify-center text-center text-xs text-gray-500">
        Select a file to inspect its Minecraft resource metadata.
      </div>
    )
  }

  if (loading) {
    return (
      <div className="h-full bg-[#121217] rounded-xl border border-[#23232b] p-4 flex items-center justify-center text-center text-xs text-gray-500">
        Loading metadata...
      </div>
    )
  }

  if (!metadata) {
    return (
      <div className="h-full bg-[#121217] rounded-xl border border-[#23232b] p-4 flex items-center justify-center text-center text-xs text-gray-500">
        No metadata available for this path.
      </div>
    )
  }

  const rl = metadata.resource_location
  const dims = metadata.diagnostics?.dimensions
  const missingTex = metadata.diagnostics?.missing_textures || []
  const referencingModels = metadata.diagnostics?.referenced_by_models || []

  return (
    <div className="h-full bg-[#121217] rounded-xl border border-[#23232b] p-4 flex flex-col justify-between overflow-y-auto space-y-4">
      {/* Top Section: Resource Location & Quick Copies */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#23232b] pb-2.5">
          <div className="flex items-center space-x-2">
            <Compass className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-bold text-gray-200 uppercase tracking-wider">
              Metadata & Resource Location
            </span>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 capitalize">
              {metadata.category}
            </span>
            {metadata.namespace && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                ns: {metadata.namespace}
              </span>
            )}
            {metadata.overlay && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                {metadata.overlay}
              </span>
            )}
          </div>
        </div>

        {/* Primary Resource Location Box */}
        {rl ? (
          <div className="p-3 rounded-xl bg-[#171720] border border-[#2a2a38] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5">
            <div>
              <div className="text-[10px] text-gray-400 uppercase font-semibold tracking-wider">
                Minecraft Resource Location
              </div>
              <div className="text-sm font-mono font-bold text-emerald-300 mt-0.5 selection:bg-emerald-500/30">
                {rl}
              </div>
            </div>

            <div className="flex items-center flex-wrap gap-1.5">
              <button
                onClick={() => handleCopy(rl, 'rl')}
                className="flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#232330] hover:bg-[#2c2c3d] text-gray-200 transition"
              >
                {copiedKey === 'rl' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>Copy RL</span>
              </button>

              {metadata.item_model_component && (
                <button
                  onClick={() => handleCopy(metadata.item_model_component!, 'im')}
                  title="Copy 1.21.2+ item_model component"
                  className="flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#232330] hover:bg-[#2c2c3d] text-gray-200 transition"
                >
                  {copiedKey === 'im' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Tag className="w-3.5 h-3.5 text-amber-400" />}
                  <span>item_model</span>
                </button>
              )}

              {metadata.json_layer_reference && (
                <button
                  onClick={() => handleCopy(metadata.json_layer_reference!, 'layer')}
                  title="Copy JSON layer reference"
                  className="flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#232330] hover:bg-[#2c2c3d] text-gray-200 transition"
                >
                  {copiedKey === 'layer' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Layers className="w-3.5 h-3.5 text-blue-400" />}
                  <span>layer0</span>
                </button>
              )}

              {metadata.give_command && (
                <button
                  onClick={() => handleCopy(metadata.give_command!, 'give')}
                  title="Copy /give command"
                  className="flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#232330] hover:bg-[#2c2c3d] text-gray-200 transition"
                >
                  {copiedKey === 'give' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-purple-400" />}
                  <span>/give</span>
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="p-3 rounded-xl bg-[#171720] border border-[#2a2a38] text-xs text-gray-400 font-mono">
            Direct file: {metadata.relative_path}
          </div>
        )}
      </div>

      {/* Middle Section: Specs & Diagnostics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <div className="p-2.5 rounded-xl bg-[#171720] border border-[#262634]">
          <div className="text-[10px] text-gray-400 flex items-center space-x-1">
            <HardDrive className="w-3 h-3 text-gray-500" />
            <span>File Size</span>
          </div>
          <div className="text-xs font-mono font-bold text-gray-200 mt-1">
            {formatBytes(metadata.size_bytes)}
          </div>
        </div>

        {dims && (
          <div className="p-2.5 rounded-xl bg-[#171720] border border-[#262634]">
            <div className="text-[10px] text-gray-400 flex items-center space-x-1">
              <Maximize2 className="w-3 h-3 text-emerald-500" />
              <span>Resolution</span>
            </div>
            <div className="text-xs font-mono font-bold text-gray-200 mt-1 flex items-center space-x-1.5">
              <span>{dims.width} × {dims.height} px</span>
              {metadata.diagnostics?.is_square && (
                <span className="text-[9px] px-1 rounded bg-emerald-500/10 text-emerald-400 font-semibold">1:1</span>
              )}
            </div>
          </div>
        )}

        <div className="p-2.5 rounded-xl bg-[#171720] border border-[#262634]">
          <div className="text-[10px] text-gray-400 flex items-center space-x-1">
            <FileCheck2 className="w-3 h-3 text-cyan-500" />
            <span>Relative Path</span>
          </div>
          <div className="text-xs font-mono text-gray-300 truncate mt-1" title={metadata.relative_path}>
            {metadata.file_name}
          </div>
        </div>

        <div className="p-2.5 rounded-xl bg-[#171720] border border-[#262634]">
          <div className="text-[10px] text-gray-400 flex items-center space-x-1">
            <Link2 className="w-3 h-3 text-purple-500" />
            <span>Referenced</span>
          </div>
          <div className="text-xs font-mono font-bold text-gray-200 mt-1">
            {referencingModels.length} models
          </div>
        </div>
      </div>

      {/* Bottom Section: Cross-Reference Details / Missing Textures Alert */}
      {missingTex.length > 0 && (
        <div className="p-3 rounded-xl bg-red-950/20 border border-red-500/30 text-xs text-red-300 space-y-1.5">
          <div className="flex items-center space-x-1.5 font-bold text-red-400">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>Missing Texture Warning ({missingTex.length})</span>
          </div>
          <div className="space-y-1 font-mono text-[11px] text-red-200/90 pl-5">
            {missingTex.map((m, idx) => (
              <div key={idx}>
                Slot <span className="text-amber-300 font-semibold">{m.slot}</span>: {m.texture_ref} (expected {m.expected_path})
              </div>
            ))}
          </div>
        </div>
      )}

      {referencingModels.length > 0 && (
        <div className="p-3 rounded-xl bg-[#171720] border border-[#2a2a38] text-xs space-y-1.5">
          <div className="text-[10px] text-gray-400 uppercase font-semibold tracking-wider flex items-center space-x-1.5">
            <Link2 className="w-3.5 h-3.5 text-purple-400" />
            <span>Referencing Models in Workspace</span>
          </div>
          <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
            {referencingModels.map((mPath) => (
              <button
                key={mPath}
                onClick={() => onNavigateToPath && onNavigateToPath(mPath)}
                className="px-2 py-0.5 rounded bg-[#232330] hover:bg-emerald-500/20 text-gray-300 hover:text-emerald-300 border border-white/5 transition"
              >
                {mPath}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
