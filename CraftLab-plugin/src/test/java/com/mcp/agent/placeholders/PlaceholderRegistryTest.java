package com.mcp.agent.placeholders;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mcp.agent.storage.GlyphStorage;
import org.bukkit.OfflinePlayer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.*;

public class PlaceholderRegistryTest {

    @Test
    public void testRouterDispatchesToRegisteredDomainProviders() {
        PlaceholderRegistry registry = new PlaceholderRegistry();
        registry.register(new PlaceholderProvider() {
            @Override
            public String getKey() {
                return "prop";
            }

            @Override
            public String resolve(OfflinePlayer player, String params) {
                return "prop_value:" + params;
            }
        });

        assertEquals("prop_value:chair_01_state", registry.resolve(null, "prop_chair_01_state"));
        assertNull(registry.resolve(null, "unknown_foo"));
        assertNull(registry.resolve(null, ""));
        assertNull(registry.resolve(null, null));
    }

    @Test
    public void testGlyphPlaceholderProviderResolutions(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("PlaceholderTest");
        GlyphStorage glyphStorage = new GlyphStorage(tempDir, logger);

        JsonArray glyphs = new JsonArray();

        JsonObject vipGlyph = new JsonObject();
        vipGlyph.addProperty("id", "badge_vip");
        vipGlyph.addProperty("namespace", "craftlab");
        vipGlyph.addProperty("hex", "E001");
        vipGlyph.addProperty("font_file", "default.json");
        glyphs.add(vipGlyph);

        JsonObject rankVipGlyph = new JsonObject();
        rankVipGlyph.addProperty("id", "badge_vip");
        rankVipGlyph.addProperty("namespace", "ranks");
        rankVipGlyph.addProperty("hex", "E002");
        rankVipGlyph.addProperty("font_file", "default.json");
        glyphs.add(rankVipGlyph);

        JsonObject customOnlyGlyph = new JsonObject();
        customOnlyGlyph.addProperty("id", "ruby_icon");
        customOnlyGlyph.addProperty("namespace", "economy");
        customOnlyGlyph.addProperty("hex", "E055");
        customOnlyGlyph.addProperty("font_file", "hud.json");
        glyphs.add(customOnlyGlyph);

        glyphStorage.syncGlyphs(glyphs);

        PlaceholderRegistry registry = new PlaceholderRegistry();
        registry.register(new GlyphPlaceholderProvider(glyphStorage));

        // 1. Resolve by unqualified ID (prioritizes craftlab namespace)
        assertEquals("\uE001", registry.resolve(null, "glyph_badge_vip"));

        // 2. Resolve by explicit namespace and ID
        assertEquals("\uE002", registry.resolve(null, "glyph_ranks:badge_vip"));
        assertEquals("\uE001", registry.resolve(null, "glyph_craftlab:badge_vip"));

        // 3. Fallback unqualified ID when only present in a custom namespace
        assertEquals("\uE055", registry.resolve(null, "glyph_ruby_icon"));

        // 4. Resolve by hexadecimal codepoint
        assertEquals("\uE001", registry.resolve(null, "glyph_hex_E001"));
        assertEquals("\uE002", registry.resolve(null, "glyph_hex_e002"));

        // 5. Resolve in MiniMessage format
        assertEquals("<font:craftlab:default>\uE001</font>", registry.resolve(null, "glyph_mm_badge_vip"));
        assertEquals("<font:ranks:default>\uE002</font>", registry.resolve(null, "glyph_mm_ranks:badge_vip"));
        assertEquals("<font:economy:hud>\uE055</font>", registry.resolve(null, "glyph_mm_economy:ruby_icon"));

        // 6. Unknown glyphs return null
        assertNull(registry.resolve(null, "glyph_non_existent"));
        assertNull(registry.resolve(null, "glyph_hex_E999"));
        assertNull(registry.resolve(null, "glyph_mm_non_existent"));
    }

    @Test
    public void testCraftLabPlaceholderExpansionMetadataAndDelegation(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("PlaceholderTest");
        GlyphStorage glyphStorage = new GlyphStorage(tempDir, logger);

        JsonObject glyph = new JsonObject();
        glyph.addProperty("id", "star");
        glyph.addProperty("namespace", "craftlab");
        glyph.addProperty("hex", "E009");
        glyphStorage.saveGlyph(glyph);

        PlaceholderRegistry registry = new PlaceholderRegistry();
        registry.register(new GlyphPlaceholderProvider(glyphStorage));

        CraftLabPlaceholderExpansion expansion = new CraftLabPlaceholderExpansion("0.11.3", registry);
        assertEquals("craftlab", expansion.getIdentifier());
        assertEquals("MinecraftContentPlatform", expansion.getAuthor());
        assertEquals("0.11.3", expansion.getVersion());
        assertTrue(expansion.persist());
        assertTrue(expansion.canRegister());
        assertEquals("\uE009", expansion.onRequest(null, "glyph_star"));
    }

    @Test
    public void testPlaceholderApiHookGracefulFallbackWithoutServer() {
        Logger logger = Logger.getLogger("PlaceholderTest");
        PlaceholderApiHook hook = new PlaceholderApiHook(logger);
        PlaceholderRegistry registry = new PlaceholderRegistry();

        assertFalse(hook.isPlaceholderApiEnabled());
        assertEquals("not_installed", hook.getPlaceholderApiVersion());
        assertFalse(hook.registerExpansion(null, registry));
    }
}
