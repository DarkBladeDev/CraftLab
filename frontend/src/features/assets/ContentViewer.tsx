import React, { useState, useEffect } from 'react'
import {
  WorkspaceFileNode,
  fetchWorkspaceFileContent,
  saveWorkspaceFileContent,
  getWorkspaceRawFileUrl,
} from '../../api/client'
import {
  FileText,
  Save,
  CheckCircle2,
  AlertCircle,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Grid,
  Volume2,
  Code2,
} from 'lucide-react'

interface ContentViewerProps {
  selectedNode: WorkspaceFileNode | null
  onFileSaved?: () => void
}

export const ContentViewer: React.FC<ContentViewerProps> = ({
  selectedNode,
  onFileSaved,
}) => {
  // Image Viewer State
  const [zoomLevel, setZoomLevel] = useState<number>(4)
  const [showGrid, setShowGrid] = useState<boolean>(false)

  // JSON / Text Editor State
  const [textContent, setTextContent] = useState<string>('')
  const [originalContent, setOriginalContent] = useState<string>('')
  const [loadingContent, setLoadingContent] = useState<boolean>(false)
  const [saving, setSaving] = useState<boolean>(false)
  const [jsonSyntaxError, setJsonSyntaxError] = useState<string | null>(null)
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null)

  const isDirty = textContent !== originalContent
  const isImage = selectedNode?.extension?.toLowerCase() === '.png' || selectedNode?.category === 'texture'
  const isAudio = selectedNode?.extension?.toLowerCase() === '.ogg' || selectedNode?.category === 'sound'
  const isJson = selectedNode?.extension?.toLowerCase() === '.json' || selectedNode?.extension?.toLowerCase() === '.mcmeta'

  // Fetch text/json content when node changes
  useEffect(() => {
    if (!selectedNode || selectedNode.type === 'directory') {
      setTextContent('')
      setOriginalContent('')
      setJsonSyntaxError(null)
      return
    }

    if (isJson || (!isImage && !isAudio)) {
      setLoadingContent(true)
      fetchWorkspaceFileContent(selectedNode.path)
        .then((res) => {
          setTextContent(res.content)
          setOriginalContent(res.content)
          validateJson(res.content)
        })
        .catch((err) => {
          setTextContent(`// Failed to load file: ${err.message}`)
        })
        .finally(() => {
          setLoadingContent(false)
        })
    }
  }, [selectedNode?.path])

  const validateJson = (text: string) => {
    if (!isJson) {
      setJsonSyntaxError(null)
      return true
    }
    try {
      JSON.parse(text)
      setJsonSyntaxError(null)
      return true
    } catch (err: any) {
      setJsonSyntaxError(err.message)
      return false
    }
  }

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value
    setTextContent(val)
    validateJson(val)
  }

  const handleFormatJson = () => {
    try {
      const parsed = JSON.parse(textContent)
      const formatted = JSON.stringify(parsed, null, 2)
      setTextContent(formatted)
      setJsonSyntaxError(null)
    } catch (err: any) {
      setJsonSyntaxError(`Cannot format: ${err.message}`)
    }
  }

  const handleSave = async () => {
    if (!selectedNode || !isDirty || saving) return
    if (isJson && !validateJson(textContent)) return

    setSaving(true)
    setSaveSuccessMessage(null)
    try {
      await saveWorkspaceFileContent(selectedNode.path, textContent)
      setOriginalContent(textContent)
      setSaveSuccessMessage('Saved successfully')
      setTimeout(() => setSaveSuccessMessage(null), 2500)
      if (onFileSaved) onFileSaved()
    } catch (err: any) {
      alert(`Save error: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  // Handle Ctrl+S / Cmd+S
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        if (isDirty && !isImage && !isAudio) {
          e.preventDefault()
          handleSave()
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isDirty, textContent, selectedNode])

  if (!selectedNode) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-[#121217] rounded-xl border border-[#23232b] p-8 text-center">
        <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-gray-500 mb-3">
          <FileText className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-gray-300">No Asset Selected</h4>
        <p className="text-xs text-gray-500 mt-1 max-w-sm">
          Select a texture, JSON model, or sound file from the Resource Explorer on the left to preview or edit.
        </p>
      </div>
    )
  }

  const rawUrl = getWorkspaceRawFileUrl(selectedNode.path)

  return (
    <div className="flex flex-col h-full bg-[#121217] rounded-xl border border-[#23232b] overflow-hidden">
      {/* Top Action Bar */}
      <div className="p-3 border-b border-[#23232b] flex items-center justify-between gap-2 shrink-0">
        <div className="flex items-center space-x-2.5 truncate">
          <span className="text-xs font-bold text-gray-200 uppercase tracking-wider">
            Content Viewer
          </span>
          <span className="text-gray-600">/</span>
          <span className="text-xs font-mono text-emerald-400 truncate">
            {selectedNode.path}
          </span>
          {isDirty && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Unsaved Changes
            </span>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2 shrink-0">
          {isImage && (
            <div className="flex items-center space-x-1 bg-[#1a1a24] rounded-lg p-1 border border-[#282836]">
              <button
                onClick={() => setZoomLevel((z) => Math.max(1, z - 1))}
                title="Zoom Out"
                className="p-1 hover:bg-white/5 rounded text-gray-400 hover:text-gray-200"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="text-[10px] font-mono px-1.5 text-gray-300 font-semibold">
                {zoomLevel}x
              </span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(16, z + 1))}
                title="Zoom In"
                className="p-1 hover:bg-white/5 rounded text-gray-400 hover:text-gray-200"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setZoomLevel(4)}
                title="Reset Zoom"
                className="p-1 hover:bg-white/5 rounded text-gray-400 hover:text-gray-200 ml-1 border-l border-white/10"
              >
                <RotateCcw className="w-3 h-3" />
              </button>
              <button
                onClick={() => setShowGrid((g) => !g)}
                title="Toggle Pixel Grid"
                className={`p-1 rounded transition ml-1 ${
                  showGrid ? 'bg-emerald-500/20 text-emerald-400' : 'text-gray-400 hover:bg-white/5'
                }`}
              >
                <Grid className="w-3 h-3" />
              </button>
            </div>
          )}

          {isJson && (
            <>
              <button
                onClick={handleFormatJson}
                className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-[#1a1a24] hover:bg-[#252532] text-gray-300 border border-[#2e2e3e] transition"
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>Format</span>
              </button>
              <button
                onClick={handleSave}
                disabled={!isDirty || saving || !!jsonSyntaxError}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  isDirty && !jsonSyntaxError
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-950/40'
                    : 'bg-[#1e1e28] text-gray-500 border border-[#2b2b3a] cursor-not-allowed'
                }`}
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? 'Saving...' : 'Save (Ctrl+S)'}</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Main Body Area */}
      <div className="flex-1 overflow-auto relative">
        {/* IMAGE PREVIEW */}
        {isImage && (
          <div className="w-full h-full min-h-[300px] flex items-center justify-center p-6 bg-[#0a0a0d] overflow-auto">
            <div
              className="relative rounded-lg shadow-2xl p-2 border border-white/10"
              style={{
                backgroundImage: `
                  linear-gradient(45deg, #181820 25%, transparent 25%), 
                  linear-gradient(-45deg, #181820 25%, transparent 25%), 
                  linear-gradient(45deg, transparent 75%, #181820 75%), 
                  linear-gradient(-45deg, transparent 75%, #181820 75%)
                `,
                backgroundSize: '16px 16px',
                backgroundPosition: '0 0, 0 8px, 8px -8px, -8px 0px',
                backgroundColor: '#101015',
              }}
            >
              <img
                src={rawUrl}
                alt={selectedNode.name}
                style={{
                  imageRendering: 'pixelated',
                  transform: `scale(${zoomLevel})`,
                  transformOrigin: 'center center',
                  margin: `${(zoomLevel - 1) * 20}px`,
                }}
                className={`transition-transform duration-100 ${
                  showGrid ? 'outline outline-1 outline-emerald-500/40' : ''
                }`}
              />
            </div>
          </div>
        )}

        {/* AUDIO PLAYER */}
        {isAudio && (
          <div className="w-full h-full min-h-[250px] flex flex-col items-center justify-center p-8 space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 shadow-lg shadow-rose-950/20">
              <Volume2 className="w-8 h-8" />
            </div>
            <div className="text-center">
              <h4 className="text-sm font-bold text-gray-200">{selectedNode.name}</h4>
              <p className="text-xs text-gray-500 font-mono mt-0.5">{selectedNode.path}</p>
            </div>
            <audio controls src={rawUrl} className="w-full max-w-md mt-2" />
          </div>
        )}

        {/* JSON / TEXT CODE EDITOR */}
        {!isImage && !isAudio && (
          <div className="w-full h-full flex flex-col">
            {loadingContent ? (
              <div className="flex-1 flex items-center justify-center text-xs text-gray-500">
                Loading file content...
              </div>
            ) : (
              <textarea
                value={textContent}
                onChange={handleTextChange}
                spellCheck={false}
                className="flex-1 w-full p-4 bg-[#0d0d12] text-gray-200 font-mono text-xs leading-relaxed resize-none focus:outline-none selection:bg-emerald-500/30"
              />
            )}

            {/* Validation / Status Banner */}
            {jsonSyntaxError && (
              <div className="p-2.5 bg-red-950/40 border-t border-red-500/30 text-red-400 text-xs flex items-center space-x-2 shrink-0">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span className="font-mono truncate">{jsonSyntaxError}</span>
              </div>
            )}
            {saveSuccessMessage && (
              <div className="p-2.5 bg-emerald-950/40 border-t border-emerald-500/30 text-emerald-400 text-xs flex items-center space-x-2 shrink-0">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{saveSuccessMessage}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
