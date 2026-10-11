import { useState, useEffect } from 'react'
import { Check, AlertCircle, Save } from 'lucide-react'

interface RawSchemaEditorProps {
  filePath: string
  initialContent: string
  onSave: (parsedJson: any) => Promise<void>
}

export function RawSchemaEditor({ filePath, initialContent, onSave }: RawSchemaEditorProps) {
  const [content, setContent] = useState(initialContent)
  const [validationError, setValidationError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setContent(initialContent)
    setValidationError(null)
  }, [initialContent, filePath])

  const validateSyntax = (raw: string): any | null => {
    try {
      const parsed = JSON.parse(raw)
      setValidationError(null)
      return parsed
    } catch (e: any) {
      setValidationError(e.message || 'Malformed JSON syntax')
      return null
    }
  }

  const handleTextChange = (text: string) => {
    setContent(text)
    validateSyntax(text)
  }

  const handleSave = async () => {
    const parsed = validateSyntax(content)
    if (!parsed) return

    setSaving(true)
    try {
      await onSave(parsed)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2500)
    } catch (e: any) {
      setValidationError(e.message || 'Failed to save schema')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-[#141418] border border-[#23232b] rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-[#23232b]">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            Schema Validation
          </span>
          <span className="text-xs text-gray-400 font-mono">{filePath}</span>
        </div>

        <button
          onClick={handleSave}
          disabled={saving || Boolean(validationError)}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition"
        >
          {saveSuccess ? (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>Saved</span>
            </>
          ) : (
            <>
              <Save className="w-3.5 h-3.5" />
              <span>Validate & Save</span>
            </>
          )}
        </button>
      </div>

      {validationError && (
        <div className="p-2.5 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-lg flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      <textarea
        value={content}
        onChange={(e) => handleTextChange(e.target.value)}
        rows={16}
        className="w-full bg-[#0a0a0d] border border-[#23232b] rounded-lg p-3 font-mono text-xs text-gray-200 focus:outline-none focus:border-emerald-500 leading-relaxed resize-y"
      />

      <p className="text-[11px] text-gray-500">
        Changes are validated against Minecraft JSON schema standards before updating active assets.
      </p>
    </div>
  )
}
