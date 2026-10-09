import React, { useState, useMemo } from 'react'
import {
  Folder,
  FolderOpen,
  File,
  Image,
  Box,
  Music,
  Sparkles,
  FileCode,
  ChevronRight,
  ChevronDown,
  Search,
  Plus,
  Upload,
  RefreshCw,
  Trash2,
  AlertCircle,
  X,
  Edit2,
} from 'lucide-react'
import {
  WorkspaceFileNode,
  createWorkspaceDirectory,
  uploadWorkspaceFile,
  deleteWorkspaceFile,
  renameWorkspacePath,
} from '../../api/client'

interface ResourceExplorerProps {
  tree: WorkspaceFileNode | null
  selectedFilePath: string | null
  onSelectFile: (fileNode: WorkspaceFileNode) => void
  onRefresh: () => void
  loading?: boolean
}

type CategoryFilter = 'all' | 'textures' | 'models' | 'sounds'

export const ResourceExplorer: React.FC<ResourceExplorerProps> = ({
  tree,
  selectedFilePath,
  onSelectFile,
  onRefresh,
  loading = false,
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all')
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(() => {
    const initial = new Set<string>()
    initial.add('')
    initial.add('assets')
    initial.add('assets/minecraft')
    return initial
  })

  // Modal states
  const [isNewFolderOpen, setIsNewFolderOpen] = useState(false)
  const [newFolderTarget, setNewFolderTarget] = useState('assets/minecraft')
  const [newFolderName, setNewFolderName] = useState('')
  const [folderError, setFolderError] = useState<string | null>(null)
  const [creatingFolder, setCreatingFolder] = useState(false)

  const [isRenameOpen, setIsRenameOpen] = useState(false)
  const [renameTargetNode, setRenameTargetNode] = useState<WorkspaceFileNode | null>(null)
  const [renameNewName, setRenameNewName] = useState('')
  const [renameError, setRenameError] = useState<string | null>(null)
  const [renaming, setRenaming] = useState(false)

  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [uploadTargetDir, setUploadTargetDir] = useState('assets/minecraft/textures/item')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const toggleExpand = (path: string) => {
    setExpandedPaths((prev) => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }

  // Collect all directories in the tree for the folder/upload target dropdowns
  const allDirectories = useMemo(() => {
    const dirs: string[] = []
    const traverse = (node: WorkspaceFileNode) => {
      if (node.type === 'directory') {
        dirs.push(node.path || '')
        if (node.children) {
          node.children.forEach(traverse)
        }
      }
    }
    if (tree) traverse(tree)
    return dirs
  }, [tree])

  // Filter tree nodes based on search & category
  const filterNode = (node: WorkspaceFileNode): WorkspaceFileNode | null => {
    if (node.type === 'file') {
      const matchesSearch =
        !searchQuery ||
        node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        node.path.toLowerCase().includes(searchQuery.toLowerCase())

      let matchesCategory = true
      if (categoryFilter === 'textures') matchesCategory = node.category === 'texture' || node.name.endsWith('.png')
      else if (categoryFilter === 'models')
        matchesCategory = node.category === 'model' || node.category === 'item_definition' || node.name.endsWith('.json')
      else if (categoryFilter === 'sounds') matchesCategory = node.category === 'sound' || node.name.endsWith('.ogg')

      return matchesSearch && matchesCategory ? node : null
    }

    // Directory
    const filteredChildren = (node.children || [])
      .map(filterNode)
      .filter((n): n is WorkspaceFileNode => n !== null)

    const matchesSearch = !searchQuery || node.name.toLowerCase().includes(searchQuery.toLowerCase())

    if (filteredChildren.length > 0 || (matchesSearch && categoryFilter === 'all')) {
      return {
        ...node,
        children: filteredChildren,
      }
    }

    return null
  }

  const filteredTree = useMemo(() => {
    if (!tree) return null
    if (!searchQuery && categoryFilter === 'all') return tree
    return filterNode(tree)
  }, [tree, searchQuery, categoryFilter])

  const handleCreateFolder = async (e: React.FormEvent) => {
    e.preventDefault()
    setFolderError(null)

    const name = newFolderName.trim().toLowerCase()
    if (!/^[a-z0-9_.-]+$/.test(name)) {
      setFolderError('Folder name must be lowercase and contain only a-z, 0-9, _, -, or .')
      return
    }

    setCreatingFolder(true)
    try {
      const fullPath = newFolderTarget ? `${newFolderTarget}/${name}` : name
      await createWorkspaceDirectory(fullPath)
      setExpandedPaths((prev) => new Set([...prev, newFolderTarget, fullPath]))
      setIsNewFolderOpen(false)
      setNewFolderName('')
      onRefresh()
    } catch (err: any) {
      setFolderError(err.message || 'Failed to create directory')
    } finally {
      setCreatingFolder(false)
    }
  }

  const handleUploadFile = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!uploadFile) return
    setUploadError(null)

    const stem = uploadFile.name.split('.')[0]
    if (!/^[a-z0-9_.-]+$/.test(stem)) {
      setUploadError(`File name stem '${stem}' must be lowercase and match ^[a-z0-9_.-]+$`)
      return
    }

    setUploading(true)
    try {
      await uploadWorkspaceFile(uploadFile, uploadTargetDir)
      setExpandedPaths((prev) => new Set([...prev, uploadTargetDir]))
      setIsUploadOpen(false)
      setUploadFile(null)
      onRefresh()
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleStartRename = (e: React.MouseEvent, node: WorkspaceFileNode) => {
    e.stopPropagation()
    setRenameTargetNode(node)
    setRenameNewName(node.name)
    setRenameError(null)
    setIsRenameOpen(true)
  }

  const handleRename = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!renameTargetNode) return
    setRenameError(null)
    const newName = renameNewName.trim().toLowerCase()
    if (!newName) {
      setRenameError('Name cannot be empty')
      return
    }

    const parentDir = renameTargetNode.path.includes('/')
      ? renameTargetNode.path.substring(0, renameTargetNode.path.lastIndexOf('/'))
      : ''
    const newPath = parentDir ? `${parentDir}/${newName}` : newName

    if (newPath === renameTargetNode.path) {
      setIsRenameOpen(false)
      return
    }

    setRenaming(true)
    try {
      await renameWorkspacePath(renameTargetNode.path, newPath)
      setIsRenameOpen(false)
      setRenameTargetNode(null)
      onRefresh()
    } catch (err: any) {
      setRenameError(err.message || 'Failed to rename')
    } finally {
      setRenaming(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent, node: WorkspaceFileNode) => {
    e.stopPropagation()
    const label = node.type === 'directory' ? `folder '${node.name}' and all its contents` : `file '${node.name}'`
    if (!window.confirm(`Delete ${label}?`)) return

    try {
      await deleteWorkspaceFile(node.path)
      onRefresh()
    } catch (err: any) {
      alert(`Delete error: ${err.message}`)
    }
  }

  const renderIcon = (node: WorkspaceFileNode, isExpanded: boolean) => {
    if (node.type === 'directory') {
      return isExpanded ? (
        <FolderOpen className="w-4 h-4 text-amber-400 shrink-0" />
      ) : (
        <Folder className="w-4 h-4 text-amber-400/80 shrink-0" />
      )
    }

    switch (node.category) {
      case 'texture':
        return <Image className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
      case 'model':
        return <Box className="w-3.5 h-3.5 text-blue-400 shrink-0" />
      case 'item_definition':
        return <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
      case 'sound':
        return <Music className="w-3.5 h-3.5 text-rose-400 shrink-0" />
      case 'manifest':
        return <FileCode className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
      default:
        return <File className="w-3.5 h-3.5 text-gray-400 shrink-0" />
    }
  }

  const renderTreeNode = (node: WorkspaceFileNode, depth: number = 0) => {
    const isExpanded = expandedPaths.has(node.path)
    const isSelected = selectedFilePath === node.path

    return (
      <div key={node.path || 'root'} className="select-none">
        <div
          onClick={() => {
            if (node.type === 'directory') {
              toggleExpand(node.path)
            } else {
              onSelectFile(node)
            }
          }}
          style={{ paddingLeft: `${depth * 14 + 8}px` }}
          className={`group flex items-center justify-between py-1.5 pr-2.5 rounded-lg text-xs cursor-pointer transition ${
            isSelected
              ? 'bg-emerald-500/15 text-emerald-300 font-medium border-l-2 border-emerald-400'
              : 'text-gray-300 hover:bg-[#1a1a22] hover:text-gray-100'
          }`}
        >
          <div className="flex items-center space-x-2 truncate">
            {node.type === 'directory' ? (
              <span
                onClick={(e) => {
                  e.stopPropagation()
                  toggleExpand(node.path)
                }}
                className="text-gray-500 hover:text-gray-300 p-0.5 rounded cursor-pointer"
              >
                {isExpanded ? (
                  <ChevronDown className="w-3.5 h-3.5" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5" />
                )}
              </span>
            ) : (
              <span className="w-3.5" />
            )}

            {renderIcon(node, isExpanded)}

            <span className="truncate">{node.name || 'workspace'}</span>

            {node.category === 'item_definition' && (
              <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                1.21.2+
              </span>
            )}
          </div>

          <div className="opacity-0 group-hover:opacity-100 flex items-center space-x-1 shrink-0">
            {node.path && (
              <>
                <button
                  onClick={(e) => handleStartRename(e, node)}
                  title={node.type === 'directory' ? 'Rename folder' : 'Rename file'}
                  className="p-1 hover:bg-blue-500/20 hover:text-blue-400 rounded text-gray-500 transition"
                >
                  <Edit2 className="w-3 h-3" />
                </button>
                <button
                  onClick={(e) => handleDelete(e, node)}
                  title={node.type === 'directory' ? 'Delete folder and contents' : 'Delete file'}
                  className="p-1 hover:bg-red-500/20 hover:text-red-400 rounded text-gray-500 transition"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </>
            )}
          </div>
        </div>

        {node.type === 'directory' && isExpanded && node.children && (
          <div>
            {node.children.map((child) => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-[#121217] rounded-xl border border-[#23232b] overflow-hidden">
      {/* Header & Controls */}
      <div className="p-3 border-b border-[#23232b] space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-gray-200 uppercase tracking-wider">
              Resource Explorer
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Workspace
            </span>
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={onRefresh}
              title="Refresh Tree"
              className="p-1.5 hover:bg-white/5 rounded-lg text-gray-400 hover:text-gray-200 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setIsNewFolderOpen(true)}
              title="New Folder"
              className="p-1.5 hover:bg-white/5 rounded-lg text-gray-400 hover:text-gray-200 transition"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setIsUploadOpen(true)}
              title="Upload Asset"
              className="p-1.5 hover:bg-emerald-500/20 rounded-lg text-emerald-400 transition"
            >
              <Upload className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-gray-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search assets..."
            className="w-full bg-[#181820] border border-[#2a2a36] rounded-lg pl-8 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-500"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-2 text-gray-500 hover:text-gray-300"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center space-x-1 text-[11px]">
          {(['all', 'textures', 'models', 'sounds'] as CategoryFilter[]).map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-2 py-0.5 rounded-md font-medium capitalize transition ${
                categoryFilter === cat
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5 font-mono text-xs">
        {filteredTree ? (
          renderTreeNode(filteredTree, 0)
        ) : (
          <div className="p-4 text-center text-xs text-gray-500">
            {loading ? 'Loading workspace...' : 'No assets found.'}
          </div>
        )}
      </div>

      {/* New Folder Modal */}
      {isNewFolderOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#141418] border border-[#282834] rounded-2xl p-5 max-w-sm w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-100 flex items-center space-x-2">
                <Folder className="w-4 h-4 text-amber-400" />
                <span>New Folder</span>
              </h3>
              <button
                onClick={() => setIsNewFolderOpen(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateFolder} className="space-y-3">
              <div>
                <label className="block text-[11px] text-gray-400 mb-1">Target Directory</label>
                <select
                  value={newFolderTarget}
                  onChange={(e) => setNewFolderTarget(e.target.value)}
                  className="w-full bg-[#1a1a24] border border-[#2e2e3e] rounded-lg px-3 py-1.5 text-xs text-gray-200"
                >
                  <option value="">Root (workspace/)</option>
                  {allDirectories.filter(Boolean).map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-gray-400 mb-1">
                  Folder Name <span className="text-gray-500 font-mono">(^[a-z0-9_.-]+$)</span>
                </label>
                <input
                  type="text"
                  required
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value.toLowerCase())}
                  placeholder="e.g. ruby_weapons"
                  className="w-full bg-[#1a1a24] border border-[#2e2e3e] rounded-lg px-3 py-1.5 text-xs text-gray-200 font-mono"
                />
              </div>

              {folderError && (
                <div className="p-2 rounded bg-red-950/30 border border-red-500/30 text-red-400 text-xs flex items-center space-x-1.5">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>{folderError}</span>
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsNewFolderOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-400 hover:text-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingFolder}
                  className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white"
                >
                  {creatingFolder ? 'Creating...' : 'Create Folder'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#141418] border border-[#282834] rounded-2xl p-5 max-w-sm w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-100 flex items-center space-x-2">
                <Upload className="w-4 h-4 text-emerald-400" />
                <span>Upload Asset</span>
              </h3>
              <button
                onClick={() => setIsUploadOpen(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUploadFile} className="space-y-3">
              <div>
                <label className="block text-[11px] text-gray-400 mb-1">Target Directory</label>
                <select
                  value={uploadTargetDir}
                  onChange={(e) => setUploadTargetDir(e.target.value)}
                  className="w-full bg-[#1a1a24] border border-[#2e2e3e] rounded-lg px-3 py-1.5 text-xs text-gray-200"
                >
                  <option value="">Root (workspace/)</option>
                  {allDirectories.filter(Boolean).map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-gray-400 mb-1">File (.png, .json, .ogg)</label>
                <input
                  type="file"
                  required
                  accept=".png,.json,.ogg,.mcmeta"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-gray-300 file:mr-2 file:py-1 file:px-2.5 file:rounded-lg file:border-0 file:text-xs file:bg-[#252532] file:text-gray-200 hover:file:bg-[#2e2e3e]"
                />
              </div>

              {uploadError && (
                <div className="p-2 rounded bg-red-950/30 border border-red-500/30 text-red-400 text-xs flex items-center space-x-1.5">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsUploadOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-400 hover:text-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white"
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {isRenameOpen && renameTargetNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#141418] border border-[#2b2b38] rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden p-5 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#23232b]">
              <div className="flex items-center space-x-2">
                <Edit2 className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-bold text-gray-100">
                  Rename {renameTargetNode.type === 'directory' ? 'Folder' : 'File'}
                </h3>
              </div>
              <button
                onClick={() => setIsRenameOpen(false)}
                className="text-gray-500 hover:text-gray-300 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleRename} className="space-y-3.5">
              <div>
                <label className="block text-[11px] text-gray-400 mb-1">Current Path</label>
                <div className="px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs font-mono text-gray-400 truncate">
                  {renameTargetNode.path}
                </div>
              </div>

              <div>
                <label className="block text-[11px] text-gray-400 mb-1">New Name</label>
                <input
                  type="text"
                  required
                  value={renameNewName}
                  onChange={(e) => setRenameNewName(e.target.value)}
                  placeholder="new_name"
                  className="w-full px-3 py-2 bg-[#0e0e11] border border-[#23232b] rounded-lg text-xs text-gray-200 font-mono focus:border-blue-500 outline-none"
                  autoFocus
                />
                <p className="text-[10px] text-gray-500 mt-1">
                  Lowercase letters, digits, _, -, or . only.
                </p>
              </div>

              {renameError && (
                <div className="p-2 rounded bg-red-950/30 border border-red-500/30 text-red-400 text-xs flex items-center space-x-1.5">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>{renameError}</span>
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsRenameOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-400 hover:text-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={renaming || !renameNewName.trim()}
                  className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white"
                >
                  {renaming ? 'Renaming...' : 'Rename'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
