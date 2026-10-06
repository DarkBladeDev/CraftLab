import React, { useState, useEffect, useCallback } from 'react'
import {
  WorkspaceFileNode,
  fetchWorkspaceTree,
} from '../../api/client'
import { ResourceExplorer } from './ResourceExplorer'
import { ContentViewer } from './ContentViewer'
import { MetadataViewer } from './MetadataViewer'

export const AssetWorkspaceView: React.FC = () => {
  const [tree, setTree] = useState<WorkspaceFileNode | null>(null)
  const [selectedNode, setSelectedNode] = useState<WorkspaceFileNode | null>(null)
  const [loading, setLoading] = useState(false)

  const loadTree = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchWorkspaceTree()
      setTree(data)
    } catch (err) {
      console.error('Failed to load workspace tree:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadTree()
  }, [loadTree])

  // Helper to find a node by path in the tree
  const findNodeByPath = (node: WorkspaceFileNode, targetPath: string): WorkspaceFileNode | null => {
    if (node.path === targetPath) return node
    if (node.children) {
      for (const child of node.children) {
        const found = findNodeByPath(child, targetPath)
        if (found) return found
      }
    }
    return null
  }

  const handleNavigateToPath = (path: string) => {
    if (tree) {
      const found = findNodeByPath(tree, path)
      if (found) {
        setSelectedNode(found)
        return
      }
    }
    // Fallback node if not deeply found
    setSelectedNode({
      name: path.split('/').pop() || path,
      path: path,
      type: 'file',
    })
  }

  return (
    <div className="flex flex-col lg:flex-row gap-5 h-[calc(100vh-14rem)] min-h-[640px]">
      {/* LEFT COLUMN: Resource Explorer (Wireframe: RESOURCE EXPLORER) */}
      <div className="w-full lg:w-80 xl:w-96 shrink-0 h-full">
        <ResourceExplorer
          tree={tree}
          selectedFilePath={selectedNode?.path || null}
          onSelectFile={(node) => setSelectedNode(node)}
          onRefresh={loadTree}
          loading={loading}
        />
      </div>

      {/* RIGHT COLUMN: Top = Content Viewer, Bottom = Metadata Viewer */}
      <div className="flex-1 flex flex-col gap-4 h-full min-w-0">
        {/* Top: CONTENT VIEWER (Wireframe: CONTENT VIEWER) */}
        <div className="flex-1 min-h-[340px]">
          <ContentViewer
            selectedNode={selectedNode}
            onFileSaved={loadTree}
          />
        </div>

        {/* Bottom: METADATA VIEWER (Wireframe: METADATA VIEWER) */}
        <div className="h-64 lg:h-72 shrink-0">
          <MetadataViewer
            selectedFilePath={selectedNode?.path || null}
            onNavigateToPath={handleNavigateToPath}
          />
        </div>
      </div>
    </div>
  )
}
