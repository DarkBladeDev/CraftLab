import { useState } from 'react'
import { Sparkles, Code2, Sliders } from 'lucide-react'
import { GlyphStudioTab } from './tabs/GlyphStudioTab'
import { EquipmentStudioTab } from './tabs/EquipmentStudioTab'
import { SoundStudioTab } from './tabs/SoundStudioTab'
import { ParticleStudioTab } from './tabs/ParticleStudioTab'
import { RawSchemaEditor } from './components/RawSchemaEditor'

type CreativeModule = 'glyphs' | 'equipment' | 'sounds' | 'particles'
type ViewMode = 'visual' | 'raw'

export function CreativeAssetsLabView() {
  const [activeModule, setActiveModule] = useState<CreativeModule>('glyphs')
  const [viewMode, setViewMode] = useState<ViewMode>('visual')

  const sampleSchemas: Record<CreativeModule, { path: string; json: string }> = {
    glyphs: {
      path: 'assets/craftlab/font/default.json',
      json: JSON.stringify(
        {
          providers: [
            {
              type: 'bitmap',
              file: 'craftlab:font/badge_vip.png',
              ascent: 7,
              height: 8,
              chars: ['\uE001'],
            },
          ],
        },
        null,
        2
      ),
    },
    equipment: {
      path: 'assets/craftlab/models/equipment/paladin_set.json',
      json: JSON.stringify(
        {
          layers: [
            { texture: 'craftlab:entity/equipment/paladin', type: 'humanoid' },
            { texture: 'craftlab:entity/equipment/paladin_tint', dyeable: true },
          ],
        },
        null,
        2
      ),
    },
    sounds: {
      path: 'assets/craftlab/sounds.json',
      json: JSON.stringify(
        {
          'prop.mystic_door.open': {
            category: 'blocks',
            subtitle: 'subtitles.craftlab.door_creak',
            sounds: [
              { name: 'craftlab:prop/door_open_1', volume: 1.0, pitch: 1.0 },
            ],
          },
        },
        null,
        2
      ),
    },
    particles: {
      path: 'assets/craftlab/particles/mystic_spark.json',
      json: JSON.stringify(
        {
          textures: ['craftlab:particle/spark'],
        },
        null,
        2
      ),
    },
  }

  const handleRawSave = async (parsedJson: any) => {
    // In raw mode, changes can be submitted to corresponding endpoint
    console.log('Saved raw schema:', parsedJson)
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#23232b]">
        <div>
          <h2 className="text-base font-bold text-gray-100 flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-rose-400" />
            <span>Creative Assets</span>
          </h2>
          <p className="text-xs text-gray-400">
            Author and inspect Minecraft 1.21.2+ equipment models, glyphs, sound events, and particles.
          </p>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center space-x-1.5 bg-[#141418] p-1 rounded-xl border border-[#23232b]">
          <button
            onClick={() => setViewMode('visual')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              viewMode === 'visual'
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Visual Editor</span>
          </button>
          <button
            onClick={() => setViewMode('raw')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              viewMode === 'raw'
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Schema & JSON</span>
          </button>
        </div>
      </div>

      {/* Sub-module Pills */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
        <button
          onClick={() => setActiveModule('glyphs')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl font-semibold transition whitespace-nowrap ${
            activeModule === 'glyphs'
              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
              : 'text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent'
          }`}
        >
          <span>Glyphs & Font</span>
        </button>
        <button
          onClick={() => setActiveModule('equipment')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl font-semibold transition whitespace-nowrap ${
            activeModule === 'equipment'
              ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
              : 'text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent'
          }`}
        >
          <span>Equipment Models (1.21.2+)</span>
        </button>
        <button
          onClick={() => setActiveModule('sounds')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl font-semibold transition whitespace-nowrap ${
            activeModule === 'sounds'
              ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
              : 'text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent'
          }`}
        >
          <span>Sound Events (SFX)</span>
        </button>
        <button
          onClick={() => setActiveModule('particles')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl font-semibold transition whitespace-nowrap ${
            activeModule === 'particles'
              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
              : 'text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent'
          }`}
        >
          <span>Particles & VFX</span>
        </button>
      </div>

      {/* Main Workspace Display */}
      {viewMode === 'visual' ? (
        <div>
          {activeModule === 'glyphs' && <GlyphStudioTab />}
          {activeModule === 'equipment' && <EquipmentStudioTab />}
          {activeModule === 'sounds' && <SoundStudioTab />}
          {activeModule === 'particles' && <ParticleStudioTab />}
        </div>
      ) : (
        <RawSchemaEditor
          filePath={sampleSchemas[activeModule].path}
          initialContent={sampleSchemas[activeModule].json}
          onSave={handleRawSave}
        />
      )}
    </div>
  )
}
