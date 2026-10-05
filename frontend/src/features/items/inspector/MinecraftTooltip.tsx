import { useMemo } from 'react'
import { parseMiniMessage } from '../minimessage/minimessage'

export interface ItemTooltipData {
  id?: string
  material: string
  displayName?: string
  lore?: string[]
  customModelData?: number | null
  itemFlags?: string[]
  amount?: number
  components?: Record<string, any>
}

const ROMAN_NUMERALS: [number, string][] = [
  [10, 'X'],
  [9, 'IX'],
  [5, 'V'],
  [4, 'IV'],
  [1, 'I'],
]

function toRoman(num: number): string {
  if (num <= 0) return num.toString()
  let result = ''
  let remaining = num
  for (const [val, roman] of ROMAN_NUMERALS) {
    while (remaining >= val) {
      result += roman
      remaining -= val
    }
  }
  return result || num.toString()
}

// Default base stats for Minecraft 1.21 combat gear
const VANILLA_BASE_STATS: Record<
  string,
  { slot: string; damage?: number; speed?: number; armor?: number; toughness?: number }
> = {
  NETHERITE_SWORD: { slot: 'Main Hand', damage: 8, speed: 1.6 },
  DIAMOND_SWORD: { slot: 'Main Hand', damage: 7, speed: 1.6 },
  IRON_SWORD: { slot: 'Main Hand', damage: 6, speed: 1.6 },
  STONE_SWORD: { slot: 'Main Hand', damage: 5, speed: 1.6 },
  WOODEN_SWORD: { slot: 'Main Hand', damage: 4, speed: 1.6 },
  GOLDEN_SWORD: { slot: 'Main Hand', damage: 4, speed: 1.6 },
  MACE: { slot: 'Main Hand', damage: 6, speed: 0.6 },
  NETHERITE_AXE: { slot: 'Main Hand', damage: 10, speed: 1.0 },
  DIAMOND_AXE: { slot: 'Main Hand', damage: 9, speed: 1.0 },
  IRON_AXE: { slot: 'Main Hand', damage: 9, speed: 0.9 },
  NETHERITE_CHESTPLATE: { slot: 'Body', armor: 8, toughness: 3 },
  DIAMOND_CHESTPLATE: { slot: 'Body', armor: 8, toughness: 2 },
  NETHERITE_HELMET: { slot: 'Head', armor: 3, toughness: 3 },
  DIAMOND_HELMET: { slot: 'Head', armor: 3, toughness: 2 },
}

export function MinecraftTooltip({
  material,
  displayName,
  lore = [],
  customModelData,
  itemFlags = [],
  components = {},
}: ItemTooltipData) {
  const upperMat = (material || 'DIAMOND_SWORD').toUpperCase().trim()

  const hideAttributes = itemFlags.includes('HIDE_ATTRIBUTES')
  const hideEnchants = itemFlags.includes('HIDE_ENCHANTS')

  // Parse title
  const renderedTitle = useMemo(() => {
    const raw = displayName || `<white>${upperMat.replace(/_/g, ' ')}</white>`
    return parseMiniMessage(raw)
  }, [displayName, upperMat])

  // Parse lore lines
  const renderedLore = useMemo(() => {
    return (lore || []).map((line, idx) => ({
      id: idx,
      nodes: parseMiniMessage(line),
    }))
  }, [lore])

  // Extract enchantments
  const enchantments = useMemo(() => {
    if (hideEnchants) return []
    const rawEnchants = components['minecraft:enchantments'] || {}
    return Object.entries(rawEnchants).map(([k, v]) => {
      const formattedName = k
        .replace('minecraft:', '')
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase())
      const level = typeof v === 'number' ? toRoman(v) : v
      return `${formattedName} ${level}`
    })
  }, [components, hideEnchants])

  // Extract / Calculate attributes
  const attributes = useMemo(() => {
    if (hideAttributes) return null

    const customModifiers: Array<{ type: string; amount: number; slot?: string }> =
      components['minecraft:attribute_modifiers'] || []

    const base = VANILLA_BASE_STATS[upperMat]

    // Calculate total damage
    let damage = base?.damage
    let speed = base?.speed
    const otherModifiers: string[] = []

    for (const mod of customModifiers) {
      if (mod.type?.includes('attack_damage')) {
        damage = (damage || 1) + mod.amount
      } else if (mod.type?.includes('attack_speed')) {
        speed = mod.amount
      } else {
        const cleanName = mod.type
          .replace('generic.', '')
          .replace('minecraft:', '')
          .replace(/_/g, ' ')
          .replace(/\b\w/g, (c) => c.toUpperCase())
        const prefix = mod.amount >= 0 ? `+${mod.amount}` : `${mod.amount}`
        otherModifiers.push(`${prefix} ${cleanName}`)
      }
    }

    if (!damage && !speed && otherModifiers.length === 0 && !base?.armor) {
      return null
    }

    return {
      slot: base?.slot || 'Main Hand',
      damage,
      speed,
      armor: base?.armor,
      toughness: base?.toughness,
      otherModifiers,
    }
  }, [components, upperMat, hideAttributes])

  return (
    <div
      className="inline-block p-2.5 rounded text-xs select-none max-w-sm font-mono shadow-2xl"
      style={{
        backgroundColor: 'rgba(16, 0, 16, 0.94)',
        border: '2px solid #100010',
        outline: '2px solid #28007f',
        boxShadow: '0 0 0 2px #5000ff inset',
      }}
    >
      {/* 1. Item Display Name */}
      <div className="text-sm font-bold leading-tight mb-1 text-white">{renderedTitle}</div>

      {/* 2. Enchantments */}
      {enchantments.length > 0 && (
        <div className="space-y-0.5 mb-1.5">
          {enchantments.map((ench, i) => (
            <div
              key={i}
              className="text-[#AAAAAA] text-xs leading-tight"
              style={{ textShadow: '1px 1px 0px #2A2A2A' }}
            >
              {ench}
            </div>
          ))}
        </div>
      )}

      {/* 3. Lore Lines */}
      {renderedLore.length > 0 && (
        <div className="space-y-0.5 mb-2">
          {renderedLore.map((line) => (
            <div key={line.id} className="text-xs leading-snug">
              {line.nodes}
            </div>
          ))}
        </div>
      )}

      {/* 4. Attribute Modifiers (1.21 Style) */}
      {attributes && (
        <div className="pt-1 border-t border-[#2a1a3a] space-y-0.5 mb-2">
          <div
            className="text-[#5555FF] text-[11px] leading-tight"
            style={{ textShadow: '1px 1px 0px #15153F' }}
          >
            When in {attributes.slot}:
          </div>

          {attributes.damage !== undefined && (
            <div
              className="text-[#55FFFF] text-[11px] leading-tight"
              style={{ textShadow: '1px 1px 0px #153F3F' }}
            >
              &nbsp;+{attributes.damage} Attack Damage
            </div>
          )}

          {attributes.speed !== undefined && (
            <div
              className="text-[#55FFFF] text-[11px] leading-tight"
              style={{ textShadow: '1px 1px 0px #153F3F' }}
            >
              &nbsp;{attributes.speed} Attack Speed
            </div>
          )}

          {attributes.armor !== undefined && (
            <div
              className="text-[#55FFFF] text-[11px] leading-tight"
              style={{ textShadow: '1px 1px 0px #153F3F' }}
            >
              &nbsp;+{attributes.armor} Armor
            </div>
          )}

          {attributes.toughness !== undefined && (
            <div
              className="text-[#55FFFF] text-[11px] leading-tight"
              style={{ textShadow: '1px 1px 0px #153F3F' }}
            >
              &nbsp;+{attributes.toughness} Armor Toughness
            </div>
          )}

          {attributes.otherModifiers.map((mod, idx) => (
            <div
              key={idx}
              className="text-[#55FFFF] text-[11px] leading-tight"
              style={{ textShadow: '1px 1px 0px #153F3F' }}
            >
              &nbsp;{mod}
            </div>
          ))}
        </div>
      )}

      {/* 5. Advanced Info (F3+H Footer) */}
      <div className="pt-1.5 border-t border-[#22102f] space-y-0.5 text-[10px]">
        <div className="text-[#555555] font-mono leading-tight">
          minecraft:{upperMat.toLowerCase()}
        </div>
        {customModelData !== null && customModelData !== undefined && (
          <div className="text-[#555555] font-mono leading-tight">
            CustomModelData: {customModelData}
          </div>
        )}
      </div>
    </div>
  )
}
