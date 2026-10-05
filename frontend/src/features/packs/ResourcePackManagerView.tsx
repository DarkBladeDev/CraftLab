import React, { useState, useEffect } from 'react'
import {
  Package,
  Layers,
  Upload,
  Download,
  Copy,
  Check,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Trash2,
  Hash,
  ExternalLink,
} from 'lucide-react'
import {
  PackSource,
  CompiledPackInfo,
  PreflightReport,
  fetchPackSources,
  uploadPackSource,
  deletePackSource,
  runPackPreflight,
  buildResourcePack,
  fetchLatestPack,
} from '../../api/client'
import { PreflightConflictModal } from './PreflightConflictModal'

interface ResourcePackManagerViewProps {
  selectedTargetId: string
  onSelectStudioItem?: (itemId: string) => void
}

export const ResourcePackManagerView: React.FC<ResourcePackManagerViewProps> = ({
  selectedTargetId,
  onSelectStudioItem,
}) => {
  const [sources, setSources] = useState<PackSource[]>([])
  const [latestPack, setLatestPack] = useState<CompiledPackInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [building, setBuilding] = useState(false)
  const [copiedHash, setCopiedHash] = useState(false)
  const [copiedUrl, setCopiedUrl] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // Pre-flight modal state
  const [isConflictModalOpen, setIsConflictModalOpen] = useState(false)
  const [conflictReport, setConflictReport] = useState<PreflightReport | null>(null)

  // Upload modal state
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [uploadName, setUploadName] = useState('')
  const [uploadPriority, setUploadPriority] = useState(15)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const [srcs, latest] = await Promise.all([
        fetchPackSources(selectedTargetId),
        fetchLatestPack(selectedTargetId),
      ])
      setSources(srcs)
      if (latest) {
        setLatestPack(latest)
      }
    } catch (err: any) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [selectedTargetId])

  const handleCopy = (text: string, type: 'hash' | 'url') => {
    navigator.clipboard.writeText(text)
    if (type === 'hash') {
      setCopiedHash(true)
      setTimeout(() => setCopiedHash(false), 2000)
    } else {
      setCopiedUrl(true)
      setTimeout(() => setCopiedUrl(false), 2000)
    }
  }

  const handlePreflight = async () => {
    setLoading(true)
    setStatusMessage(null)
    try {
      const report = await runPackPreflight(selectedTargetId)
      if (!report.is_valid) {
        setConflictReport(report)
        setIsConflictModalOpen(true)
      } else {
        setStatusMessage({
          type: 'success',
          text: `Pre-flight passed! ${report.summary.total_cmd_indexed || 0} models checked, 0 collisions.`,
        })
      }
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message || 'Preflight check failed' })
    } finally {
      setLoading(false)
    }
  }

  const handleBuild = async (force = false) => {
    setBuilding(true)
    setStatusMessage(null)
    try {
      const compiled = await buildResourcePack(selectedTargetId, force)
      setLatestPack(compiled)
      setStatusMessage({
        type: 'success',
        text: `Resource pack successfully compiled! SHA-1: ${compiled.sha1_hash.slice(0, 10)}...`,
      })
      await loadData()
    } catch (err: any) {
      if (err.report) {
        setConflictReport(err.report)
        setIsConflictModalOpen(true)
      } else {
        setStatusMessage({ type: 'error', text: err.message || 'Build failed' })
      }
    } finally {
      setBuilding(false)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!uploadFile || !uploadName) return

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      formData.append('name', uploadName)
      formData.append('layer_priority', uploadPriority.toString())
      if (selectedTargetId) {
        formData.append('target_id', selectedTargetId)
      }

      await uploadPackSource(formData)
      setIsUploadOpen(false)
      setUploadFile(null)
      setUploadName('')
      setStatusMessage({ type: 'success', text: `Source pack '${uploadName}' uploaded and registered.` })
      await loadData()
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message || 'Upload failed' })
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteSource = async (sourceId: string) => {
    if (!window.confirm('Remove this pack source?')) return
    try {
      await deletePackSource(sourceId)
      await loadData()
    } catch (err: any) {
      console.error(err)
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Control Bar */}
      <div className="p-5 rounded-2xl bg-[#141418] border border-[#23232b] shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-11 h-11 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <Package className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-gray-100 flex items-center space-x-2">
              <span>Resource Pack Pipeline & Merger</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                1.21 Ready
              </span>
            </h2>
            <p className="text-xs text-gray-400">
              Automated multi-layer packaging, deterministic bit-for-bit SHA-1 hashing, and HTTP distribution.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5 w-full md:w-auto">
          <button
            onClick={handlePreflight}
            disabled={loading || building}
            className="flex-1 md:flex-initial flex items-center justify-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#1c1c24] hover:bg-[#252530] border border-[#2e2e3d] text-gray-200 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Pre-Flight Check</span>
          </button>

          <button
            onClick={() => setIsUploadOpen(true)}
            className="flex-1 md:flex-initial flex items-center justify-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#1c1c24] hover:bg-[#252530] border border-[#2e2e3d] text-gray-200 transition"
          >
            <Upload className="w-3.5 h-3.5 text-purple-400" />
            <span>Add Source .zip</span>
          </button>

          <button
            onClick={() => handleBuild(false)}
            disabled={building}
            className="flex-1 md:flex-initial flex items-center justify-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-950/40 transition active:scale-95"
          >
            <Package className={`w-3.5 h-3.5 ${building ? 'animate-spin' : ''}`} />
            <span>{building ? 'Building Pack...' : 'Build & Publish Pack'}</span>
          </button>
        </div>
      </div>

      {/* Status Messages */}
      {statusMessage && (
        <div
          className={`p-4 rounded-xl flex items-center space-x-2.5 text-xs font-medium border ${
            statusMessage.type === 'success'
              ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-400'
              : 'bg-red-950/20 border-red-500/30 text-red-400'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" />
          )}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Active Pack Status Card */}
      {latestPack && (
        <div className="p-5 rounded-2xl bg-[#141418] border border-[#23232b] space-y-4">
          <div className="flex items-center justify-between border-b border-[#23232b] pb-3">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-bold text-gray-200">Active Published Pack</span>
              <span className="text-[11px] font-mono text-gray-500">{latestPack.pack_name}</span>
            </div>
            <span className="text-xs font-mono text-gray-400">{formatBytes(latestPack.file_size)}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* SHA-1 Box */}
            <div className="p-3.5 rounded-xl bg-[#0f0f13] border border-[#22222b] flex items-center justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold flex items-center space-x-1">
                  <Hash className="w-3 h-3 text-purple-400" />
                  <span>SHA-1 Checksum</span>
                </div>
                <div className="text-xs font-mono text-gray-200 mt-1 select-all">
                  {latestPack.sha1_hash}
                </div>
              </div>
              <button
                onClick={() => handleCopy(latestPack.sha1_hash, 'hash')}
                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition"
                title="Copy SHA-1"
              >
                {copiedHash ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>

            {/* Download URL Box */}
            <div className="p-3.5 rounded-xl bg-[#0f0f13] border border-[#22222b] flex items-center justify-between">
              <div className="overflow-hidden">
                <div className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold flex items-center space-x-1">
                  <Download className="w-3 h-3 text-indigo-400" />
                  <span>HTTP Distribution Endpoint</span>
                </div>
                <div className="text-xs font-mono text-indigo-300 mt-1 truncate select-all">
                  {latestPack.download_url || `/api/v1/packs/${selectedTargetId}/download`}
                </div>
              </div>
              <div className="flex items-center space-x-1 shrink-0 ml-2">
                <button
                  onClick={() =>
                    handleCopy(
                      latestPack.download_url || `${window.location.origin}/api/v1/packs/${selectedTargetId}/download`,
                      'url'
                    )
                  }
                  className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition"
                  title="Copy URL"
                >
                  {copiedUrl ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>
                <a
                  href={`/api/v1/packs/${selectedTargetId}/download`}
                  download={latestPack.pack_name}
                  className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition"
                  title="Direct Download"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Layer Priority Stack / Sources Table */}
      <div className="p-5 rounded-2xl bg-[#141418] border border-[#23232b] space-y-4">
        <div className="flex items-center justify-between border-b border-[#23232b] pb-3">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-bold text-gray-200">Pack Layer Precedence</h3>
          </div>
          <span className="text-[11px] text-gray-500">Higher priority layers overwrite lower layers upon conflict</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#202028] text-gray-500 font-semibold">
                <th className="py-2.5 px-3">Priority</th>
                <th className="py-2.5 px-3">Source Name</th>
                <th className="py-2.5 px-3">Origin</th>
                <th className="py-2.5 px-3">Plugin / Type</th>
                <th className="py-2.5 px-3">Source SHA-1</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1c1c24]">
              {/* Virtual Studio Layer Entry (Top Priority) */}
              <tr className="bg-purple-950/10">
                <td className="py-3 px-3">
                  <span className="font-mono font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    100
                  </span>
                </td>
                <td className="py-3 px-3 font-semibold text-gray-200">Studio Items & Custom Overrides</td>
                <td className="py-3 px-3">
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-purple-500/20 text-purple-400">
                    Studio Core
                  </span>
                </td>
                <td className="py-3 px-3 text-gray-400">Native Platform Items</td>
                <td className="py-3 px-3 font-mono text-gray-500">Live Workspace</td>
                <td className="py-3 px-3 text-right text-gray-500 italic text-[11px]">Master Layer</td>
              </tr>

              {/* Registered External Sources */}
              {sources.map((src) => (
                <tr key={src.id} className="hover:bg-white/[0.02] transition">
                  <td className="py-3 px-3">
                    <span className="font-mono font-semibold px-2 py-0.5 rounded bg-white/5 text-gray-300 border border-[#2b2b36]">
                      {src.layer_priority}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-medium text-gray-200">{src.name}</td>
                  <td className="py-3 px-3">
                    <span
                      className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                        src.source_type === 'agent'
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      }`}
                    >
                      {src.source_type}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-gray-400">{src.plugin ? src.plugin.toUpperCase() : 'Zip Archive'}</td>
                  <td className="py-3 px-3 font-mono text-gray-500">
                    {src.sha1_hash ? `${src.sha1_hash.slice(0, 8)}...` : 'N/A'}
                  </td>
                  <td className="py-3 px-3 text-right">
                    {src.source_type === 'upload' && (
                      <button
                        onClick={() => handleDeleteSource(src.id)}
                        className="p-1 rounded text-gray-500 hover:text-red-400 transition"
                        title="Delete Source"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload Source Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#141418] border border-[#2b2b38] rounded-2xl w-full max-w-md shadow-2xl overflow-hidden p-6 space-y-4">
            <h3 className="text-sm font-bold text-gray-100 flex items-center space-x-2">
              <Upload className="w-4 h-4 text-purple-400" />
              <span>Upload Third-Party Resource Pack</span>
            </h3>

            <form onSubmit={handleUpload} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-400 mb-1 font-medium">Source Display Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Server GUI Base Pack"
                  value={uploadName}
                  onChange={(e) => setUploadName(e.target.value)}
                  className="w-full bg-[#1b1b24] border border-[#2a2a38] rounded-xl px-3 py-2 text-gray-200 focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-gray-400 mb-1 font-medium">Layer Priority</label>
                <input
                  type="number"
                  required
                  value={uploadPriority}
                  onChange={(e) => setUploadPriority(parseInt(e.target.value) || 10)}
                  className="w-full bg-[#1b1b24] border border-[#2a2a38] rounded-xl px-3 py-2 text-gray-200 focus:outline-none focus:border-purple-500"
                />
                <span className="text-[10px] text-gray-500">Recommended: 10 (base), 20 (plugins)</span>
              </div>

              <div>
                <label className="block text-gray-400 mb-1 font-medium">Pack Zip File (.zip)</label>
                <input
                  type="file"
                  required
                  accept=".zip"
                  onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsUploadOpen(false)}
                  className="px-3.5 py-2 rounded-xl bg-[#22222a] hover:bg-[#2b2b36] text-gray-300 font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold transition"
                >
                  {uploading ? 'Extracting...' : 'Upload & Register'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Pre-Flight Conflict Resolution Modal */}
      <PreflightConflictModal
        isOpen={isConflictModalOpen}
        report={conflictReport}
        onClose={() => setIsConflictModalOpen(false)}
        onForceBuild={() => handleBuild(true)}
        onSelectStudioItem={onSelectStudioItem}
      />
    </div>
  )
}
