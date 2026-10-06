import React, { useState, useEffect } from 'react'
import {
  WorkspaceFileNode,
  fetchWorkspaceTree,
  getWorkspaceRawFileUrl,
} from '../../api/client'
import {
  Folder,
  FolderOpen,
  Image,
  Box,
  Sparkles,
  ChevronRight,
  ChevronDown,
  X,
  Search,
  Check,
} from 'lucide-react'

interface AssetPickerModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectAsset: (resourceLocation: string, category: string, path: string) => void
  filterCategory?: 'all' | 'models' | 'textures'
  title?: string
}

export const AssetPickerModal: React.FC<AssetPickerModalProps> = ({
  isOpen,
  onClose,
  onSelectAsset,
  filterCategory = 'models',
  title = 'Select Asset from Workspace Pack',
}) => {
  const [tree, setTree] = useState<WorkspaceFileNode | null>(null)
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNode, setSelectedNode] = useState<WorkspaceFileNode | null>(null)
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(() => {
    const s = new Set<string>()
    s.add('')
    s.add('assets')
    s.add('assets/minecraft')
    return s
  })

  useEffect(() => {
    if (isOpen) {
      setLoading(true)
      fetchWorkspaceTree()
        .then((data) => setTree(data))
        .catch((err) => console.error(err))
        .finally(() => setLoading(false))
    }
  }, [isOpen])

  if (!isOpen) return null

  const toggleExpand = (path: string) => {
    setExpandedPaths((prev) => {
      const next = new Set(prev)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }

  // Filter tree
  const filterNode = (node: WorkspaceFileNode): WorkspaceFileNode | null => {
    if (node.type === 'file') {
      const matchesSearch =
        !searchQuery ||
        node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        node.path.toLowerCase().includes(searchQuery.toLowerCase())

      let matchesCat = true
      if (filterCategory === 'models') {
        matchesCat = node.category === 'model' || node.category === 'item_definition' || node.name.endsWith('.json')
      } else if (filterCategory === 'textures') {
        matchesCat = node.category === 'texture' || node.name.endsWith('.png')
      }

      return matchesSearch && matchesCat ? node : null
    }

    const filteredChildren = (node.children || [])
      .map(filterNode)
      .filter((n): n is WorkspaceFileNode => n !== null)

    if (filteredChildren.length > 0 || (!searchQuery && filterCategory === 'all')) {
      return {
        ...node,
        children: filteredChildren,
      }
    }
    return null
  }

  const filteredTree = tree ? filterNode(tree) : null

  const renderIcon = (node: WorkspaceFileNode, isExpanded: boolean) => {
    if (node.type === 'directory') {
      return isExpanded ? <FolderOpen className="w-4 h-4 text-amber-400 shrink-0" /> : <Folder className="w-4 h-4 text-amber-400 shrink-0" />
    }
    if (node.category === 'texture' || node.name.endsWith('.png')) return <Image className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
    if (node.category === 'item_definition') return <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
    return <Box className="w-3.5 h-3.5 text-blue-400 shrink-0" />
  }

  const renderTreeNode = (node: WorkspaceFileNode, depth: number = 0) => {
    const isExpanded = expandedPaths.has(node.path)
    const isSelected = selectedNode?.path === node.path

    return (
      <div key={node.path || 'root'} className="select-none">
        <div
          onClick={() => {
            if (node.type === 'directory') toggleExpand(node.path)
            else setSelectedNode(node)
          }}
          style={{ paddingLeft: `${depth * 14 + 8}px` }}
          className={`flex items-center justify-between py-1.5 pr-2.5 rounded-lg text-xs cursor-pointer transition ${
            isSelected
              ? 'bg-emerald-500/15 text-emerald-300 font-medium border-l-2 border-emerald-400'
              : 'text-gray-300 hover:bg-[#1f1f2a]'
          }`}
        >
          <div className="flex items-center space-x-2 truncate">
            {node.type === 'directory' ? (
              <span className="text-gray-500 p-0.5">
                {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </span>
            ) : (
              <span className="w-3.5" />
            )}
            {renderIcon(node, isExpanded)}
            <span className="truncate">{node.name}</span>
          </div>

          {node.resource_location && (
            <span className="text-[10px] font-mono text-gray-400 truncate max-w-[140px]">
              {node.resource_location}
            </span>
          )}
        </div>

        {node.type === 'directory' && isExpanded && node.children && (
          <div>{node.children.map((c) => renderTreeNode(c, depth + 1))}</div>
        )}
      </div>
    )
  }

  const handleConfirm = () => {
    if (!selectedNode || !selectedNode.resource_location) return
    onSelectAsset(selectedNode.resource_location, selectedNode.category || 'other', selectedNode.path)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#141418] border border-[#282834] rounded-2xl max-w-2xl w-full h-[520px] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-[#23232b] flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-100 flex items-center space-x-2">
            <Box className="w-4 h-4 text-emerald-400" />
            <span>{title}</span>
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Search */}
        <div className="p-3 border-b border-[#23232b] bg-[#181820]">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search assets by name or path..."
              className="w-full bg-[#121217] border border-[#2e2e3e] rounded-lg pl-8 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        {/* Tree & Preview Body */}
        <div className="flex-1 flex overflow-hidden">
          {/* Tree column */}
          <div className="flex-1 overflow-y-auto p-2 border-r border-[#23232b]">
            {loading ? (
              <div className="p-4 text-center text-xs text-gray-500">Loading workspace assets...</div>
            ) : filteredTree ? (
              renderTreeNode(filteredTree, 0)
            ) : (
              <div className="p-4 text-center text-xs text-gray-500">No assets match filter.</div>
            )}
          </div>

          {/* Selected Preview Column */}
          <div className="w-64 p-4 bg-[#121217] flex flex-col justify-between shrink-0">
            {selectedNode && selectedNode.type === 'file' ? (
              <div className="space-y-3">
                <div className="text-[10px] text-gray-400 uppercase font-semibold">Selected Asset</div>
                <div className="text-xs font-mono font-bold text-emerald-300 break-all">
                  {selectedNode.resource_location || selectedNode.path}
                </div>

                {selectedNode.category === 'texture' && (
                  <div className="p-2 rounded bg-black/40 border border-white/10 flex items-center justify-center">
                    <img
                      src={getWorkspaceRawFileUrl(selectedNode.path)}
                      alt="preview"
                      style={{ imageRendering: 'pixelated' }}
                      className="w-16 h-16 object-contain"
                    />
                  </div>
                )}

                <div className="text-[11px] text-gray-400 space-y-1">
                  <div>Type: <span className="text-gray-200 capitalize">{selectedNode.category}</span></div>
                  <div className="truncate">Path: <span className="text-gray-300 font-mono text-[10px]">{selectedNode.path}</span></div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-xs text-gray-500 text-center">
                Select an asset on the left to see details and apply.
              </div>
            )}

            <div className="flex items-center space-x-2 pt-3 border-t border-[#23232b]">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-400 hover:text-gray-200 bg-[#1c1c24]"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!selectedNode || !selectedNode.resource_location}
                onClick={handleConfirm}
                className={`flex-1 flex items-center justify-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  selectedNode && selectedNode.resource_location
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-950/40'
                    : 'bg-[#1e1e28] text-gray-500 cursor-not-allowed'
                }`}
              >
                <Check className="w-3.5 h-3.5" />
                <span>Apply</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
