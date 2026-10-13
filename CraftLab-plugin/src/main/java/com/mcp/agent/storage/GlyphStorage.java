package com.mcp.agent.storage;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.reflect.TypeToken;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Logger;

public class GlyphStorage {
    private final File storageFile;
    private final Logger logger;
    private final Gson gson = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();

    // Indexed by "<namespace>:<id>" (lowercase)
    private final Map<String, JsonObject> byQualifiedId = new ConcurrentHashMap<>();
    // Indexed by unqualified "<id>" (lowercase), prioritizing "craftlab" namespace
    private final Map<String, JsonObject> byId = new ConcurrentHashMap<>();
    // Indexed by 4-digit uppercase hex (e.g. "E001")
    private final Map<String, JsonObject> byHex = new ConcurrentHashMap<>();

    public GlyphStorage(File dataFolder, Logger logger) {
        this.storageFile = new File(dataFolder, "glyphs.json");
        this.logger = logger;
        if (!dataFolder.exists()) {
            dataFolder.mkdirs();
        }
        loadAll();
    }

    public synchronized void loadAll() {
        byQualifiedId.clear();
        byId.clear();
        byHex.clear();

        if (!storageFile.exists()) {
            return;
        }

        try (FileReader reader = new FileReader(storageFile, StandardCharsets.UTF_8)) {
            Type listType = new TypeToken<List<JsonObject>>() {}.getType();
            List<JsonObject> loaded = gson.fromJson(reader, listType);
            if (loaded != null) {
                for (JsonObject glyph : loaded) {
                    indexGlyph(glyph);
                }
            }
            if (logger != null) {
                logger.info("Loaded " + byQualifiedId.size() + " glyphs from local storage.");
            }
        } catch (Exception e) {
            if (logger != null) {
                logger.severe("Failed to load glyphs.json: " + e.getMessage());
            }
        }
    }

    public synchronized void syncGlyphs(JsonArray glyphsArray) {
        byQualifiedId.clear();
        byId.clear();
        byHex.clear();

        if (glyphsArray != null) {
            for (JsonElement el : glyphsArray) {
                if (el != null && el.isJsonObject()) {
                    indexGlyph(el.getAsJsonObject());
                }
            }
        }
        flush();
        if (logger != null) {
            logger.info("Synchronized " + byQualifiedId.size() + " glyphs to local storage.");
        }
    }

    public synchronized void saveGlyph(JsonObject glyphData) {
        if (glyphData == null) return;
        indexGlyph(glyphData);
        flush();
    }

    private void indexGlyph(JsonObject glyph) {
        if (glyph == null || !glyph.has("id")) {
            return;
        }
        String rawId = glyph.get("id").getAsString().trim();
        if (rawId.isEmpty()) {
            return;
        }

        String namespace = "craftlab";
        if (glyph.has("namespace") && !glyph.get("namespace").isJsonNull()) {
            String nsVal = glyph.get("namespace").getAsString().trim().toLowerCase();
            if (!nsVal.isEmpty()) {
                namespace = nsVal;
            }
        }

        String idLower = rawId.toLowerCase();
        String qualifiedKey = namespace + ":" + idLower;

        String hexNorm = null;
        if (glyph.has("hex") && !glyph.get("hex").isJsonNull()) {
            hexNorm = normalizeHex(glyph.get("hex").getAsString());
        }

        // Ensure "character" is populated if "hex" is valid
        if ((!glyph.has("character") || glyph.get("character").isJsonNull() || glyph.get("character").getAsString().isEmpty())
                && hexNorm != null && hexNorm.length() == 4) {
            try {
                int cp = Integer.parseInt(hexNorm, 16);
                glyph.addProperty("character", String.valueOf((char) cp));
            } catch (NumberFormatException ignored) {
            }
        }

        byQualifiedId.put(qualifiedKey, glyph);

        // Prioritize "craftlab" namespace for unqualified lookup, or set if not yet present
        if ("craftlab".equals(namespace) || !byId.containsKey(idLower)) {
            byId.put(idLower, glyph);
        }

        if (hexNorm != null && !hexNorm.isEmpty()) {
            byHex.put(hexNorm, glyph);
        }
    }

    /**
     * Resolves a glyph by selector: either "<namespace>:<id>" or unqualified "<id>".
     */
    public JsonObject getGlyph(String selector) {
        if (selector == null || selector.isBlank()) {
            return null;
        }
        String clean = selector.trim().toLowerCase();
        if (clean.contains(":")) {
            return byQualifiedId.get(clean);
        }
        JsonObject defaultNsMatch = byQualifiedId.get("craftlab:" + clean);
        if (defaultNsMatch != null) {
            return defaultNsMatch;
        }
        return byId.get(clean);
    }

    /**
     * Resolves a glyph by its 4-digit PUA hexadecimal codepoint (e.g. "E001").
     */
    public JsonObject getGlyphByHex(String hex) {
        if (hex == null || hex.isBlank()) {
            return null;
        }
        return byHex.get(normalizeHex(hex));
    }

    public Map<String, JsonObject> getAllGlyphs() {
        return Collections.unmodifiableMap(new LinkedHashMap<>(byQualifiedId));
    }

    public static String normalizeHex(String hex) {
        if (hex == null) return "";
        return hex.trim()
                .replace("\\u", "")
                .replace("\\U", "")
                .replace("U+", "")
                .replace("u+", "")
                .toUpperCase();
    }

    public static String extractCharacter(JsonObject glyph) {
        if (glyph == null) return null;
        if (glyph.has("character") && !glyph.get("character").isJsonNull()) {
            String ch = glyph.get("character").getAsString();
            if (!ch.isEmpty()) {
                return ch;
            }
        }
        if (glyph.has("hex") && !glyph.get("hex").isJsonNull()) {
            String hex = normalizeHex(glyph.get("hex").getAsString());
            if (hex.length() == 4) {
                try {
                    int cp = Integer.parseInt(hex, 16);
                    return String.valueOf((char) cp);
                } catch (NumberFormatException ignored) {
                }
            }
        }
        return null;
    }

    private void flush() {
        try (FileWriter writer = new FileWriter(storageFile, StandardCharsets.UTF_8)) {
            List<JsonObject> list = new ArrayList<>(byQualifiedId.values());
            gson.toJson(list, writer);
        } catch (IOException e) {
            if (logger != null) {
                logger.severe("Failed to write to glyphs.json: " + e.getMessage());
            }
        }
    }
}
