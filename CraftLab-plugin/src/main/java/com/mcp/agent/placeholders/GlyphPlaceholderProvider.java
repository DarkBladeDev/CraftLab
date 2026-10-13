package com.mcp.agent.placeholders;

import com.google.gson.JsonObject;
import com.mcp.agent.storage.GlyphStorage;
import org.bukkit.OfflinePlayer;

public class GlyphPlaceholderProvider implements PlaceholderProvider {
    private final GlyphStorage glyphStorage;

    public GlyphPlaceholderProvider(GlyphStorage glyphStorage) {
        this.glyphStorage = glyphStorage;
    }

    @Override
    public String getKey() {
        return "glyph";
    }

    @Override
    public String resolve(OfflinePlayer player, String params) {
        if (glyphStorage == null || params == null || params.isBlank()) {
            return null;
        }

        String trimmed = params.trim();

        // 1. MiniMessage format: mm_<selector>
        if (trimmed.regionMatches(true, 0, "mm_", 0, 3)) {
            String selector = trimmed.substring(3).trim();
            if (selector.isEmpty()) {
                return null;
            }
            JsonObject glyph = glyphStorage.getGlyph(selector);
            if (glyph == null && selector.regionMatches(true, 0, "hex_", 0, 4)) {
                glyph = glyphStorage.getGlyphByHex(selector.substring(4));
            }
            if (glyph == null) {
                return null;
            }
            String ch = GlyphStorage.extractCharacter(glyph);
            if (ch == null || ch.isEmpty()) {
                return null;
            }
            String namespace = "craftlab";
            if (glyph.has("namespace") && !glyph.get("namespace").isJsonNull()) {
                String ns = glyph.get("namespace").getAsString().trim().toLowerCase();
                if (!ns.isEmpty()) {
                    namespace = ns;
                }
            }
            String fontName = "default";
            if (glyph.has("font_file") && !glyph.get("font_file").isJsonNull()) {
                String ff = glyph.get("font_file").getAsString().trim();
                if (ff.endsWith(".json")) {
                    ff = ff.substring(0, ff.length() - 5);
                }
                if (!ff.isEmpty()) {
                    fontName = ff;
                }
            }
            return "<font:" + namespace + ":" + fontName + ">" + ch + "</font>";
        }

        // 2. Hexadecimal codepoint lookup: hex_<hex>
        if (trimmed.regionMatches(true, 0, "hex_", 0, 4)) {
            String hex = trimmed.substring(4).trim();
            if (hex.isEmpty()) {
                return null;
            }
            JsonObject glyph = glyphStorage.getGlyphByHex(hex);
            return GlyphStorage.extractCharacter(glyph);
        }

        // 3. Qualified (<namespace>:<id>) or unqualified (<id>) lookup
        JsonObject glyph = glyphStorage.getGlyph(trimmed);
        return GlyphStorage.extractCharacter(glyph);
    }
}
