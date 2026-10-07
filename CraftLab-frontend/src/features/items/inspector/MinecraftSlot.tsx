import { useState } from 'react'
import { Sparkles, Shield, Wrench, Package } from 'lucide-react'

interface MinecraftSlotProps {
  material: string
  amount?: number
  customModelData?: number | null
  itemModel?: string | null
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function MinecraftSlot({
  material,
  amount = 1,
  customModelData,
  itemModel,
  size = 'md',
  className = '',
}: MinecraftSlotProps) {
  const [imgError, setImgError] = useState(false)

  const materialLower = (material || 'diamond_sword').trim().toLowerCase()

  // Standard public asset URL for Minecraft 1.21 vanilla item textures
  const primarySpriteUrl = `https://assets.mcasset.cloud/1.21.1/assets/minecraft/textures/item/${materialLower}.png`

  const sizeClasses = {
    sm: 'w-10 h-10',
    md: 'w-14 h-14',
    lg: 'w-16 h-16',
  }[size]

  const iconSizes = {
    sm: 'w-6 h-6',
    md: 'w-9 h-9',
    lg: 'w-11 h-11',
  }[size]

  return (
    <div
      className={`relative flex items-center justify-center select-none bg-[#8b8b8b] ${sizeClasses} ${className}`}
      style={{
        boxShadow:
          'inset 2px 2px 0px #373737, inset -2px -2px 0px #ffffff, inset 4px 4px 0px #222222, inset -4px -4px 0px #ffffff',
        border: '2px solid #181818',
      }}
      title={`${material} (Amount: ${amount}${customModelData ? `, CMD: ${customModelData}` : ''}${itemModel ? `, Model: ${itemModel}` : ''})`}
    >
      {/* Texture sprite or fallback icon */}
      {!imgError ? (
        <img
          key={materialLower}
          src={primarySpriteUrl}
          alt={material}
          onError={() => setImgError(true)}
          className={`${iconSizes} object-contain pointer-events-none drop-shadow-[0_2px_2px_rgba(0,0,0,0.4)]`}
          style={{
            imageRendering: 'pixelated',
          }}
        />
      ) : (
        <div className="flex items-center justify-center text-gray-800">
          {materialLower.includes('sword') || materialLower.includes('mace') ? (
            <Wrench className={`${iconSizes}`} />
          ) : materialLower.includes('shield') || materialLower.includes('chestplate') ? (
            <Shield className={`${iconSizes}`} />
          ) : (
            <Package className={`${iconSizes}`} />
          )}
        </div>
      )}

      {/* Stack Count Badge */}
      {amount > 1 && (
        <span
          className="absolute bottom-1 right-1 text-white font-bold leading-none pointer-events-none"
          style={{
            fontFamily: 'monospace',
            fontSize: size === 'sm' ? '10px' : '13px',
            textShadow: '2px 2px 0px #3f3f3f',
          }}
        >
          {amount}
        </span>
      )}

      {/* Custom Model Data Indicator Badge (1.21.1) */}
      {customModelData !== null && customModelData !== undefined && (
        <div
          className="absolute -top-1.5 -left-1.5 w-4 h-4 rounded-full bg-purple-600 border border-purple-300 flex items-center justify-center shadow-lg"
          title={`1.21.1 Custom Model Data: ${customModelData}`}
        >
          <Sparkles className="w-2.5 h-2.5 text-purple-100" />
        </div>
      )}

      {/* Modern Item Model Indicator Badge (1.21.2+) */}
      {itemModel && (
        <div
          className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-cyan-600 border border-cyan-300 flex items-center justify-center shadow-lg"
          title={`1.21.2+ Item Model: ${itemModel}`}
        >
          <Sparkles className="w-2.5 h-2.5 text-cyan-100" />
        </div>
      )}
    </div>
  )
}
