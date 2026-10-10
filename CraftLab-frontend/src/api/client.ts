export interface Target {
  id: string
  name: string
  status: 'online' | 'offline' | 'stale'
  environment_metadata?: {
    agentVersion?: string
    minecraftVersion?: string
    paperVersion?: string
  }
  last_seen_at?: string
}

export interface Item {
  id: string
  material: string
  display_name: string
  lore: string[]
  custom_model_data?: number | null
  item_model?: string | null
  item_flags: string[]
  amount?: number
  components?: Record<string, any>
  export_format?: 'native' | 'oraxen' | 'nexo'
  plugin_properties?: Record<string, any>
  raw_extensions?: string
}

export interface VanillaItem {
  id: string
  name: string
  category: string
  stack_size: number
}

export interface DiscoveredItem {
  id: string
  target_id: string
  source: string
  item_id: string
  material: string
  display_name?: string
  lore?: string[]
  custom_model_data?: number | null
  item_flags?: string[]
  raw_properties?: Record<string, any>
  synced_at?: string
}

export interface PluginSchemaField {
  key: string
  label: string
  type: 'boolean' | 'string' | 'number' | 'select'
  default?: any
  placeholder?: string
  description?: string
  min?: number
  options?: string[]
}

export interface PluginSchemaSection {
  id: string
  title: string
  description?: string
  fields: PluginSchemaField[]
}

export interface PluginSchema {
  id: string
  plugin: string
  name: string
  version: string
  description?: string
  sections: PluginSchemaSection[]
  default_yaml_template?: string
}

export interface PropStateSound {
  key: string
  volume: number
  pitch: number
}

export interface PropState {
  name?: string
  block_model?: string | null
  light_level?: number
  sound?: PropStateSound | null
  hitbox_type?: 'solid' | 'passable' | null
  next_state?: string | null
}

export interface Block {
  id: string
  display_name: string
  mode: 'display_prop' | 'noteblock'
  item_model?: string | null
  block_model?: string | null
  scale: [number, number, number] | number[]
  translation: [number, number, number] | number[]
  hitbox_type: 'solid' | 'passable'
  hitbox_offsets: number[][]
  interaction_type?: string | null
  seat_height: number
  hardness: number
  tool_type: string
  drop_item_id?: string | null
  plugin_properties?: Record<string, any>
  default_state?: string
  states?: Record<string, PropState>
}

export interface Revision {
  id: string
  revision_number: number
  revision_hash: string
  items_count: number
  blocks_count?: number
  created_at: string
}

export interface DeploymentPlan {
  id: string
  plan_hash: string
  revision_id: string
  target_id: string
  status: 'draft' | 'approved' | 'applied' | 'failed'
  operations: Array<{
    operationId: string
    action: string
    resourceId: string
    payload: Item
  }>
}

const API_BASE = '/api'

export async function fetchTargets(): Promise<Target[]> {
  const res = await fetch(`${API_BASE}/targets`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Failed to fetch targets (${res.status}): ${text}`)
  }
  return res.json()
}

export async function registerTarget(id: string, name: string): Promise<any> {
  const res = await fetch(`${API_BASE}/targets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, name }),
  })
  return res.json()
}

export async function fetchItems(): Promise<Item[]> {
  const res = await fetch(`${API_BASE}/items`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Failed to fetch items (${res.status}): ${text}`)
  }
  return res.json()
}

export async function saveItem(item: Item): Promise<Item> {
  const res = await fetch(`${API_BASE}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail ? JSON.stringify(err.detail) : 'Failed to save item')
  }
  return res.json()
}

export async function deleteItem(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/items/${id}`, { method: 'DELETE' })
  return res.json()
}

export async function fetchRevisions(): Promise<Revision[]> {
  const res = await fetch(`${API_BASE}/revisions`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Failed to fetch revisions (${res.status}): ${text}`)
  }
  return res.json()
}

export async function createRevision(): Promise<Revision> {
  const res = await fetch(`${API_BASE}/revisions`, { method: 'POST' })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Failed to create revision')
  }
  return res.json()
}

export async function createDeploymentPlan(revisionId: string, targetId: string): Promise<DeploymentPlan> {
  const res = await fetch(`${API_BASE}/deployments/plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ revision_id: revisionId, target_id: targetId }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Failed to create plan')
  }
  return res.json()
}

export async function approveDeploymentPlan(planId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/deployments/plans/${planId}/approve`, {
    method: 'POST',
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Failed to approve plan')
  }
  return res.json()
}

export async function executeDeploymentPlan(planId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/deployments/plans/${planId}/execute`, {
    method: 'POST',
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Failed to execute plan')
  }
  return res.json()
}

export async function fetchVanillaCatalog(category?: string, search?: string): Promise<{ categories: string[]; count: number; items: VanillaItem[] }> {
  const params = new URLSearchParams()
  if (category) params.append('category', category)
  if (search) params.append('search', search)
  const res = await fetch(`${API_BASE}/catalogs/vanilla?${params.toString()}`)
  return res.json()
}

export async function fetchDiscoveredCatalog(targetId: string, source?: string, search?: string): Promise<DiscoveredItem[]> {
  const params = new URLSearchParams()
  if (source) params.append('source', source)
  if (search) params.append('search', search)
  const res = await fetch(`${API_BASE}/catalogs/targets/${targetId}/items?${params.toString()}`)
  return res.json()
}

export async function syncTargetCatalog(targetId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/catalogs/targets/${targetId}/sync`, { method: 'POST' })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Failed to sync target catalog')
  }
  return res.json()
}

export async function fetchPluginSchema(schemaId: string): Promise<PluginSchema> {
  const res = await fetch(`${API_BASE}/catalogs/schemas/${schemaId}`)
  if (!res.ok) {
    throw new Error(`Failed to load schema '${schemaId}'`)
  }
  return res.json()
}

export interface PackSource {
  id: string
  target_id?: string
  name: string
  source_type: 'studio' | 'upload' | 'agent'
  plugin?: string
  layer_priority: number
  storage_path: string
  sha1_hash?: string
  meta_info?: Record<string, any>
  is_active: boolean
  updated_at?: string
}

export interface ConflictItem {
  source: string
  item_id: string
  display_name: string
  material: string
  custom_model_data?: number | null
  item_model?: string | null
  link?: string
}

export interface PreflightConflict {
  type: string
  severity: string
  material?: string
  custom_model_data?: number | null
  item_model?: string | null
  items: ConflictItem[]
  message: string
}


export interface PreflightReport {
  is_valid: boolean
  has_warnings: boolean
  conflicts: PreflightConflict[]
  warnings: PreflightConflict[]
  summary: Record<string, any>
}

export interface CompiledPackInfo {
  pack_id: string
  target_id?: string
  pack_name: string
  sha1_hash: string
  file_size: number
  download_url: string
  build_summary?: Record<string, any>
}

export async function fetchPackSources(targetId?: string): Promise<PackSource[]> {
  const params = new URLSearchParams()
  if (targetId) params.append('target_id', targetId)
  const res = await fetch(`/api/v1/packs/sources?${params.toString()}`)
  return res.json()
}

export async function uploadPackSource(formData: FormData): Promise<any> {
  const res = await fetch('/api/v1/packs/sources/upload', {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Failed to upload source')
  }
  return res.json()
}

export async function deletePackSource(sourceId: string): Promise<any> {
  const res = await fetch(`/api/v1/packs/sources/${sourceId}`, {
    method: 'DELETE',
  })
  return res.json()
}

export async function updatePackSource(
  sourceId: string,
  data: { name?: string; layer_priority?: number; is_active?: boolean }
): Promise<any> {
  const res = await fetch(`/api/v1/packs/sources/${sourceId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to update pack source (${res.status})`)
  }
  return res.json()
}

export interface WorkspaceConfig {
  description: string
  pack_format: number
  min_inclusive: number
  max_inclusive: number
}

export async function fetchWorkspaceConfig(): Promise<WorkspaceConfig> {
  const res = await fetch(`${API_BASE}/v1/packs/workspace/config`)
  if (!res.ok) throw new Error(`Failed to fetch workspace config (${res.status})`)
  return res.json()
}

export async function updateWorkspaceConfig(cfg: WorkspaceConfig): Promise<WorkspaceConfig> {
  const res = await fetch(`${API_BASE}/v1/packs/workspace/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cfg),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to update workspace config (${res.status})`)
  }
  return res.json()
}

export async function runPackPreflight(targetId?: string): Promise<PreflightReport> {
  const params = new URLSearchParams()
  if (targetId) params.append('target_id', targetId)
  const res = await fetch(`/api/v1/packs/preflight?${params.toString()}`, {
    method: 'POST',
  })
  return res.json()
}

export async function buildResourcePack(targetId?: string, force = false): Promise<CompiledPackInfo> {
  const res = await fetch('/api/v1/packs/build', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_id: targetId, force }),
  })
  if (res.status === 409) {
    const report: PreflightReport = await res.json()
    const err: any = new Error('Pre-flight validation failed with conflicts')
    err.report = report
    throw err
  }
  if (!res.ok) {
    let errMsg = `Failed to build resource pack (${res.status})`
    try {
      const err = await res.json()
      errMsg = err.detail || errMsg
    } catch {
      // Body is not JSON
    }
    throw new Error(errMsg)
  }
  return res.json()
}

export async function fetchLatestPack(targetId: string): Promise<any> {
  const res = await fetch(`/api/v1/packs/${targetId}/latest`)
  if (!res.ok) return null
  return res.json()
}

export async function fetchBlocks(): Promise<Block[]> {
  const res = await fetch(`${API_BASE}/v1/blocks`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Failed to fetch blocks (${res.status}): ${text}`)
  }
  return res.json()
}

export async function saveBlock(block: Block): Promise<Block> {
  const res = await fetch(`${API_BASE}/v1/blocks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(block),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Failed to save block (${res.status}): ${text}`)
  }
  return res.json()
}

export async function deleteBlock(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/v1/blocks/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Failed to delete block (${res.status}): ${text}`)
  }
  return res.json()
}

// ----------------------------------------------------------------------
// Workspace Pack Explorer API
// ----------------------------------------------------------------------

export interface WorkspaceFileNode {
  name: string
  path: string
  type: 'directory' | 'file'
  size?: number
  extension?: string
  category?: 'texture' | 'model' | 'item_definition' | 'sound' | 'manifest' | 'font' | 'lang' | 'other'
  resource_location?: string | null
  children?: WorkspaceFileNode[]
}

export interface WorkspaceMetadataDiagnostics {
  dimensions?: { width: number; height: number } | null
  is_square?: boolean | null
  is_power_of_two?: boolean | null
  missing_textures: Array<{ slot: string; texture_ref: string; expected_path: string }>
  referenced_by_models: string[]
}

export interface WorkspaceFileMetadata {
  file_name: string
  relative_path: string
  size_bytes: number
  modified_at: number
  category: string
  namespace?: string | null
  resource_location?: string | null
  overlay?: string | null
  item_model_component?: string | null
  json_layer_reference?: string | null
  give_command?: string | null
  diagnostics: WorkspaceMetadataDiagnostics
}

export async function fetchWorkspaceTree(): Promise<WorkspaceFileNode> {
  const res = await fetch(`${API_BASE}/v1/packs/workspace/tree`)
  if (!res.ok) throw new Error(`Failed to fetch workspace tree (${res.status})`)
  return res.json()
}

export async function fetchWorkspaceFileContent(path: string): Promise<{ path: string; content: string }> {
  const res = await fetch(`${API_BASE}/v1/packs/workspace/file?path=${encodeURIComponent(path)}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch file (${res.status})`)
  }
  return res.json()
}

export async function saveWorkspaceFileContent(path: string, content: string): Promise<{ success: boolean; path: string; size: number }> {
  const res = await fetch(`${API_BASE}/v1/packs/workspace/file`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, content }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to save file (${res.status})`)
  }
  return res.json()
}

export async function createWorkspaceDirectory(path: string): Promise<{ success: boolean; path: string }> {
  const res = await fetch(`${API_BASE}/v1/packs/workspace/directory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to create directory (${res.status})`)
  }
  return res.json()
}

export async function uploadWorkspaceFile(file: File, directory: string): Promise<{ success: boolean; path: string; filename: string }> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('directory', directory)

  const res = await fetch(`${API_BASE}/v1/packs/workspace/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to upload file (${res.status})`)
  }
  return res.json()
}

export async function deleteWorkspaceFile(path: string): Promise<{ success: boolean; path: string }> {
  const res = await fetch(`${API_BASE}/v1/packs/workspace/file?path=${encodeURIComponent(path)}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to delete file (${res.status})`)
  }
  return res.json()
}

export async function renameWorkspacePath(
  oldPath: string,
  newPath: string
): Promise<{ success: boolean; old_path: string; new_path: string }> {
  const res = await fetch(`${API_BASE}/v1/packs/workspace/rename`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ old_path: oldPath, new_path: newPath }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to rename path (${res.status})`)
  }
  return res.json()
}

export async function fetchWorkspaceMetadata(path: string): Promise<WorkspaceFileMetadata> {
  const res = await fetch(`${API_BASE}/v1/packs/workspace/metadata?path=${encodeURIComponent(path)}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch metadata (${res.status})`)
  }
  return res.json()
}

export function getWorkspaceRawFileUrl(path: string): string {
  return `${API_BASE}/v1/packs/workspace/file?path=${encodeURIComponent(path)}&raw=true`
}


