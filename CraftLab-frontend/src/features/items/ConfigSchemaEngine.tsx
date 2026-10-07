import { useState } from 'react'
import { Code, Sliders, Info } from 'lucide-react'
import { PluginSchema } from '../../api/client'

interface ConfigSchemaEngineProps {
  schema: PluginSchema | null
  properties: Record<string, any>
  onChangeProperties: (props: Record<string, any>) => void
  rawYaml: string
  onChangeRawYaml: (yaml: string) => void
}

export function ConfigSchemaEngine({
  schema,
  properties,
  onChangeProperties,
  rawYaml,
  onChangeRawYaml,
}: ConfigSchemaEngineProps) {
  const [viewMode, setViewMode] = useState<'form' | 'raw'>('form')

  const getNestedValue = (obj: Record<string, any>, path: string): any => {
    const parts = path.split('.')
    let current = obj
    for (const part of parts) {
      if (current === undefined || current === null) return undefined
      current = current[part]
    }
    return current
  }

  const setNestedValue = (path: string, val: any) => {
    const parts = path.split('.')
    const updated = JSON.parse(JSON.stringify(properties || {}))
    let current = updated
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i]
      if (!current[part] || typeof current[part] !== 'object') {
        current[part] = {}
      }
      current = current[part]
    }
    current[parts[parts.length - 1]] = val
    onChangeProperties(updated)

    // Auto update raw yaml representation
    syncToYaml(updated)
  }

  const syncToYaml = (propsObj: Record<string, any>) => {
    // Generate simple YAML representation
    const lines: string[] = []
    for (const [secKey, secVal] of Object.entries(propsObj)) {
      if (typeof secVal === 'object' && secVal !== null) {
        lines.push(`${secKey}:`)
        for (const [k, v] of Object.entries(secVal)) {
          lines.push(`  ${k}: ${v}`)
        }
      } else {
        lines.push(`${secKey}: ${secVal}`)
      }
    }
    onChangeRawYaml(lines.join('\n'))
  }

  return (
    <div className="bg-[#121216] border border-[#26262e] rounded-xl p-4 mt-3">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#24242c]">
        <div className="flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-semibold text-gray-200">
            {schema ? `${schema.name} (${schema.version})` : 'Plugin Configuration Extensions'}
          </span>
        </div>

        {/* Form vs Raw Mode Toggle */}
        <div className="flex items-center bg-[#1a1a22] rounded-lg p-0.5 border border-[#30303c]">
          <button
            type="button"
            onClick={() => setViewMode('form')}
            className={`flex items-center space-x-1 px-2.5 py-1 text-[11px] rounded-md transition ${
              viewMode === 'form'
                ? 'bg-purple-600/30 text-purple-300 font-medium'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Sliders className="w-3 h-3" />
            <span>Form</span>
          </button>
          <button
            type="button"
            onClick={() => setViewMode('raw')}
            className={`flex items-center space-x-1 px-2.5 py-1 text-[11px] rounded-md transition ${
              viewMode === 'raw'
                ? 'bg-purple-600/30 text-purple-300 font-medium'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Code className="w-3 h-3" />
            <span>Raw YAML</span>
          </button>
        </div>
      </div>

      {viewMode === 'form' && schema ? (
        <div className="space-y-4">
          {schema.sections.map((section) => (
            <div key={section.id} className="bg-[#17171d] border border-[#272733] rounded-lg p-3">
              <div className="mb-2">
                <div className="text-xs font-medium text-purple-300">{section.title}</div>
                {section.description && (
                  <div className="text-[10px] text-gray-500">{section.description}</div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                {section.fields.map((field) => {
                  const val = getNestedValue(properties, field.key)
                  const currentVal = val !== undefined ? val : (field.default ?? '')

                  return (
                    <div key={field.key} className="space-y-1">
                      <label className="block text-[11px] text-gray-300 flex items-center justify-between">
                        <span>{field.label}</span>
                        {field.description && (
                          <span title={field.description}>
                            <Info className="w-3 h-3 text-gray-500 hover:text-gray-400" />
                          </span>
                        )}
                      </label>

                      {field.type === 'boolean' ? (
                        <div className="flex items-center space-x-2 pt-0.5">
                          <input
                            type="checkbox"
                            checked={Boolean(currentVal)}
                            onChange={(e) => setNestedValue(field.key, e.target.checked)}
                            className="w-4 h-4 rounded bg-[#101014] border-gray-600 text-purple-600 focus:ring-purple-500 focus:ring-offset-0"
                          />
                          <span className="text-[11px] text-gray-400">
                            {currentVal ? 'Enabled' : 'Disabled'}
                          </span>
                        </div>
                      ) : field.type === 'select' ? (
                        <select
                          value={currentVal}
                          onChange={(e) => setNestedValue(field.key, e.target.value)}
                          className="w-full px-2.5 py-1.5 text-xs bg-[#101014] border border-[#30303e] rounded-md text-gray-200 focus:outline-none focus:border-purple-400 font-mono"
                        >
                          {(field.options || []).map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type={field.type === 'number' ? 'number' : 'text'}
                          value={currentVal}
                          min={field.min}
                          placeholder={field.placeholder}
                          onChange={(e) =>
                            setNestedValue(
                              field.key,
                              field.type === 'number'
                                ? (e.target.value ? parseInt(e.target.value, 10) : null)
                                : e.target.value
                            )
                          }
                          className="w-full px-2.5 py-1.5 text-xs bg-[#101014] border border-[#30303e] rounded-md text-gray-200 focus:outline-none focus:border-purple-400 font-mono"
                        />
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div>
          <label className="block text-[11px] text-gray-400 mb-1">
            Raw YAML Configuration Block <span className="text-gray-500">(Directly exported to plugin config)</span>
          </label>
          <textarea
            rows={6}
            value={rawYaml}
            onChange={(e) => onChangeRawYaml(e.target.value)}
            placeholder="Pack:&#10;  model: custom/weapons/example&#10;Mechanics:&#10;  custom_durability: 1000"
            className="w-full px-3 py-2 text-xs bg-[#0e0e12] border border-[#2c2c38] rounded-lg text-purple-200 focus:outline-none focus:border-purple-400 font-mono"
          />
        </div>
      )}
    </div>
  )
}
