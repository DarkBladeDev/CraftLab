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
  item_flags: string[]
  amount?: number
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

export interface Revision {
  id: string
  revision_number: number
  revision_hash: string
  items_count: number
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
