package com.mcp.agent.storage;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.*;

public class GlyphStorageTest {

    @Test
    public void testSyncLookupAndReloadGlyphs(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("GlyphStorageTest");
        GlyphStorage storage = new GlyphStorage(tempDir, logger);

        JsonArray arr = new JsonArray();

        JsonObject g1 = new JsonObject();
        g1.addProperty("id", "badge_vip");
        g1.addProperty("namespace", "craftlab");
        g1.addProperty("hex", "E001");
        g1.addProperty("character", "\uE001");
        g1.addProperty("font_file", "default.json");
        arr.add(g1);

        JsonObject g2 = new JsonObject();
        g2.addProperty("id", "badge_vip");
        g2.addProperty("namespace", "ranks");
        g2.addProperty("hex", "E002");
        g2.addProperty("character", "\uE002");
        g2.addProperty("font_file", "default.json");
        arr.add(g2);

        JsonObject g3 = new JsonObject();
        g3.addProperty("id", "crown_gold");
        g3.addProperty("namespace", "ranks");
        g3.addProperty("hex", "E003");
        arr.add(g3);

        storage.syncGlyphs(arr);

        assertEquals(3, storage.getAllGlyphs().size());

        // Unqualified lookup prioritizes "craftlab" namespace when duplicate IDs exist
        assertEquals("E001", storage.getGlyph("badge_vip").get("hex").getAsString());
        // Explicit namespace lookup resolves "ranks:badge_vip"
        assertEquals("E002", storage.getGlyph("ranks:badge_vip").get("hex").getAsString());
        // Unqualified lookup falls back to custom namespace when unambiguous
        assertEquals("E003", storage.getGlyph("crown_gold").get("hex").getAsString());
        assertEquals("\uE003", GlyphStorage.extractCharacter(storage.getGlyph("crown_gold")));

        // Hex lookup
        assertNotNull(storage.getGlyphByHex("E002"));
        assertEquals("ranks", storage.getGlyphByHex("\\uE002").get("namespace").getAsString());

        // Reload from disk (plugins/McpAgent/glyphs.json)
        GlyphStorage reloaded = new GlyphStorage(tempDir, logger);
        assertEquals(3, reloaded.getAllGlyphs().size());
        assertEquals("\uE001", GlyphStorage.extractCharacter(reloaded.getGlyph("badge_vip")));
        assertEquals("\uE002", GlyphStorage.extractCharacter(reloaded.getGlyph("ranks:badge_vip")));
        assertEquals("\uE003", GlyphStorage.extractCharacter(reloaded.getGlyphByHex("E003")));
    }
}
