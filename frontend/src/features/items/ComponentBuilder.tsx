import { useState } from 'react'
import { Plus, Trash2, Zap, Shield, Sparkles, ChevronDown, ChevronRight } from 'lucide-react'

interface ComponentBuilderProps {
  components: Record<string, any>
  onChangeComponents: (components: Record<string, any>) => void
}

const COMMON_ATTRIBUTES = [
  { id: 'generic.attack_damage', label: 'Attack Damage' },
  { id: 'generic.attack_speed', label: 'Attack Speed' },
  { id: 'generic.movement_speed', label: 'Movement Speed' },
  { id: 'generic.max_health', label: 'Max Health' },
  { id: 'generic.armor', label: 'Armor' },
  { id: 'generic.armor_toughness', label: 'Armor Toughness' },
  { id: 'generic.knockback_resistance', label: 'Knockback Resistance' },
]

const EQUIPMENT_SLOTS = ['mainhand', 'offhand', 'head', 'chest', 'legs', 'feet', 'any']

const POPULAR_ENCHANTMENTS = [
  'sharpness',
  'smite',
  'fire_aspect',
  'looting',
  'unbreaking',
  'mending',
  'wind_burst',
  'density',
  'breach',
  'efficiency',
  'fortune',
  'silk_touch',
  'protection',
  'feather_falling',
  'power',
  'infinity',
  'riptide',
]

export function ComponentBuilder({ components, onChangeComponents }: ComponentBuilderProps) {
  const [activeSection, setActiveSection] = useState<'attributes' | 'enchantments' | null>(
    'attributes'
  )

  // Attribute Form state
  const [selectedAttr, setSelectedAttr] = useState(COMMON_ATTRIBUTES[0].id)
  const [selectedSlot, setSelectedSlot] = useState('mainhand')
  const [attrAmount, setAttrAmount] = useState('12.0')

  // Enchantment Form state
  const [selectedEnch, setSelectedEnch] = useState(POPULAR_ENCHANTMENTS[0])
  const [enchLevel, setEnchLevel] = useState('5')

  const attributeModifiers: Array<{ type: string; amount: number; slot: string }> =
    components['minecraft:attribute_modifiers'] || []

  const enchantments: Record<string, number> = components['minecraft:enchantments'] || {}

  const handleAddAttribute = () => {
    const val = parseFloat(attrAmount)
    if (isNaN(val)) return

    const updatedModifiers = [
      ...attributeModifiers,
      {
        type: selectedAttr,
        amount: val,
        slot: selectedSlot,
      },
    ]

    onChangeComponents({
      ...components,
      'minecraft:attribute_modifiers': updatedModifiers,
    })
  }

  const handleRemoveAttribute = (index: number) => {
    const updated = attributeModifiers.filter((_, i) => i !== index)
    const next = { ...components }
    if (updated.length > 0) {
      next['minecraft:attribute_modifiers'] = updated
    } else {
      delete next['minecraft:attribute_modifiers']
    }
    onChangeComponents(next)
  }

  const handleAddEnchantment = () => {
    const lvl = parseInt(enchLevel, 10)
    if (isNaN(lvl) || lvl <= 0) return

    const updatedEnchants = {
      ...enchantments,
      [selectedEnch]: lvl,
    }

    onChangeComponents({
      ...components,
      'minecraft:enchantments': updatedEnchants,
    })
  }

  const handleRemoveEnchantment = (enchKey: string) => {
    const nextEnchants = { ...enchantments }
    delete nextEnchants[enchKey]
    const next = { ...components }
    if (Object.keys(nextEnchants).length > 0) {
      next['minecraft:enchantments'] = nextEnchants
    } else {
      delete next['minecraft:enchantments']
    }
    onChangeComponents(next)
  }

  return (
    <div className="bg-[#121217] border border-[#272733] rounded-xl p-4 mt-3 space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-[#242430]">
        <div className="flex items-center space-x-2">
          <Zap className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-semibold text-gray-200">
            Minecraft 1.21 Data Components
          </h3>
        </div>
        <span className="text-[10px] text-gray-500 font-mono">Mojang Component API</span>
      </div>

      {/* 1. Attribute Modifiers Accordion */}
      <div className="border border-[#23232f] rounded-lg overflow-hidden bg-[#16161d]">
        <button
          type="button"
          onClick={() =>
            setActiveSection(activeSection === 'attributes' ? null : 'attributes')
          }
          className="w-full flex items-center justify-between p-2.5 text-left text-xs font-medium text-gray-300 hover:text-white transition"
        >
          <div className="flex items-center space-x-2">
            <Shield className="w-3.5 h-3.5 text-blue-400" />
            <span>Attribute Modifiers ({attributeModifiers.length})</span>
          </div>
          {activeSection === 'attributes' ? (
            <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
          )}
        </button>

        {activeSection === 'attributes' && (
          <div className="p-3 border-t border-[#23232f] space-y-3 bg-[#13131a]">
            {/* Active List */}
            {attributeModifiers.length > 0 && (
              <div className="space-y-1.5">
                {attributeModifiers.map((mod, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 rounded bg-[#1a1a24] border border-[#2b2b3a] text-xs font-mono"
                  >
                    <div>
                      <span className="text-emerald-400 font-semibold">
                        {mod.amount >= 0 ? `+${mod.amount}` : mod.amount}
                      </span>
                      <span className="text-gray-300 ml-1.5">
                        {mod.type.replace('generic.', '')}
                      </span>
                      <span className="text-gray-500 ml-1 text-[11px]">({mod.slot})</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveAttribute(idx)}
                      className="text-gray-500 hover:text-red-400 transition"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Add Attribute Row */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-2 pt-1">
              <div className="md:col-span-5">
                <select
                  value={selectedAttr}
                  onChange={(e) => setSelectedAttr(e.target.value)}
                  className="w-full px-2 py-1.5 text-xs bg-[#1a1a24] border border-[#303040] rounded text-gray-200"
                >
                  {COMMON_ATTRIBUTES.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-3">
                <select
                  value={selectedSlot}
                  onChange={(e) => setSelectedSlot(e.target.value)}
                  className="w-full px-2 py-1.5 text-xs bg-[#1a1a24] border border-[#303040] rounded text-gray-200 capitalize"
                >
                  {EQUIPMENT_SLOTS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-2">
                <input
                  type="number"
                  step="0.1"
                  value={attrAmount}
                  onChange={(e) => setAttrAmount(e.target.value)}
                  className="w-full px-2 py-1.5 text-xs bg-[#1a1a24] border border-[#303040] rounded text-gray-200"
                  placeholder="+10.0"
                />
              </div>

              <div className="md:col-span-2">
                <button
                  type="button"
                  onClick={handleAddAttribute}
                  className="w-full py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs flex items-center justify-center space-x-1 font-medium transition"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 2. Enchantments Accordion */}
      <div className="border border-[#23232f] rounded-lg overflow-hidden bg-[#16161d]">
        <button
          type="button"
          onClick={() =>
            setActiveSection(activeSection === 'enchantments' ? null : 'enchantments')
          }
          className="w-full flex items-center justify-between p-2.5 text-left text-xs font-medium text-gray-300 hover:text-white transition"
        >
          <div className="flex items-center space-x-2">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>Enchantments ({Object.keys(enchantments).length})</span>
          </div>
          {activeSection === 'enchantments' ? (
            <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
          )}
        </button>

        {activeSection === 'enchantments' && (
          <div className="p-3 border-t border-[#23232f] space-y-3 bg-[#13131a]">
            {/* Active List */}
            {Object.keys(enchantments).length > 0 && (
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(enchantments).map(([k, lvl]) => (
                  <div
                    key={k}
                    className="flex items-center justify-between p-2 rounded bg-[#1a1a24] border border-[#2b2b3a] text-xs font-mono"
                  >
                    <div className="truncate">
                      <span className="text-purple-300 capitalize">
                        {k.replace(/_/g, ' ')}
                      </span>
                      <span className="text-amber-400 ml-1.5 font-bold">lvl {lvl}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveEnchantment(k)}
                      className="text-gray-500 hover:text-red-400 transition ml-2"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Add Enchantment Row */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-2 pt-1">
              <div className="md:col-span-7">
                <select
                  value={selectedEnch}
                  onChange={(e) => setSelectedEnch(e.target.value)}
                  className="w-full px-2 py-1.5 text-xs bg-[#1a1a24] border border-[#303040] rounded text-gray-200 capitalize"
                >
                  {POPULAR_ENCHANTMENTS.map((ench) => (
                    <option key={ench} value={ench}>
                      {ench.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-3">
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={enchLevel}
                  onChange={(e) => setEnchLevel(e.target.value)}
                  className="w-full px-2 py-1.5 text-xs bg-[#1a1a24] border border-[#303040] rounded text-gray-200"
                  placeholder="Lvl 1-10"
                />
              </div>

              <div className="md:col-span-2">
                <button
                  type="button"
                  onClick={handleAddEnchantment}
                  className="w-full py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs flex items-center justify-center space-x-1 font-medium transition"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
