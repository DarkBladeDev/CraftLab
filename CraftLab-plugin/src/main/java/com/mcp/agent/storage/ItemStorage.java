package com.mcp.agent.storage;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.reflect.TypeToken;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Type;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Logger;

public class ItemStorage {
    private final File storageFile;
    private final Logger logger;
    private final Gson gson = new GsonBuilder().setPrettyPrinting().create();
    private final Map<String, JsonObject> items = new ConcurrentHashMap<>();

    public ItemStorage(File dataFolder, Logger logger) {
        this.storageFile = new File(dataFolder, "items.json");
        this.logger = logger;
        if (!dataFolder.exists()) {
            dataFolder.mkdirs();
        }
        loadAll();
    }

    public synchronized void loadAll() {
        items.clear();
        if (!storageFile.exists()) {
            return;
        }

        try (FileReader reader = new FileReader(storageFile)) {
            Type type = new TypeToken<Map<String, JsonObject>>() {}.getType();
            Map<String, JsonObject> loaded = gson.fromJson(reader, type);
            if (loaded != null) {
                items.putAll(loaded);
            }
            logger.info("Loaded " + items.size() + " items from local storage.");
        } catch (IOException e) {
            logger.severe("Failed to load items.json: " + e.getMessage());
        }
    }

    public synchronized void saveItem(String id, JsonObject itemData) {
        items.put(id, itemData);
        flush();
    }

    public synchronized void removeItem(String id) {
        items.remove(id);
        flush();
    }

    public JsonObject getItem(String id) {
        return items.get(id);
    }

    public Map<String, JsonObject> getAllItems() {
        return Collections.unmodifiableMap(items);
    }

    private void flush() {
        try (FileWriter writer = new FileWriter(storageFile)) {
            gson.toJson(items, writer);
        } catch (IOException e) {
            logger.severe("Failed to write to items.json: " + e.getMessage());
        }
    }
}
