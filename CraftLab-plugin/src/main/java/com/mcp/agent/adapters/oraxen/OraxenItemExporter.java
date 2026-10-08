package com.mcp.agent.adapters.oraxen;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import org.bukkit.Bukkit;
import org.bukkit.configuration.file.YamlConfiguration;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

public class OraxenItemExporter {
    private final File oraxenItemsFolder;
    private final Logger logger;

    public OraxenItemExporter(File oraxenItemsFolder, Logger logger) {
        this.oraxenItemsFolder = oraxenItemsFolder;
        this.logger = logger;
    }

    /**
     * Exports a canonical JSON item definition into Oraxen YAML configuration format.
     */
    public boolean exportItem(JsonObject itemData) {
        String itemId = itemData.get("id").getAsString();
        String material = itemData.has("material") ? itemData.get("material").getAsString() : "DIAMOND_SWORD";
        String displayName = itemData.has("display_name") ? itemData.get("display_name").getAsString() : itemId;

        if (!oraxenItemsFolder.exists()) {
            oraxenItemsFolder.mkdirs();
        }

        File targetFile = new File(oraxenItemsFolder, "platform_items.yml");
        YamlConfiguration yaml = YamlConfiguration.loadConfiguration(targetFile);

        // Populate Oraxen section for this item
        yaml.set(itemId + ".material", material.toUpperCase());
        yaml.set(itemId + ".displayname", displayName);

        if (itemData.has("lore") && itemData.get("lore").isJsonArray()) {
            JsonArray loreArray = itemData.getAsJsonArray("lore");
            List<String> loreList = new ArrayList<>();
            for (JsonElement el : loreArray) {
                loreList.add(el.getAsString());
            }
            yaml.set(itemId + ".lore", loreList);
        }

        if (itemData.has("custom_model_data") && !itemData.get("custom_model_data").isJsonNull()) {
            int cmd = itemData.get("custom_model_data").getAsInt();
            yaml.set(itemId + ".Pack.custom_model_data", cmd);
        }

        // Apply structured plugin properties if present
        if (itemData.has("plugin_properties") && itemData.get("plugin_properties").isJsonObject()) {
            JsonObject props = itemData.getAsJsonObject("plugin_properties");
            for (String key : props.keySet()) {
                JsonElement elem = props.get(key);
                if (elem.isJsonObject()) {
                    JsonObject sub = elem.getAsJsonObject();
                    for (String subKey : sub.keySet()) {
                        yaml.set(itemId + "." + key + "." + subKey, sub.get(subKey).getAsString());
                    }
                } else if (elem.isJsonPrimitive()) {
                    yaml.set(itemId + "." + key, elem.getAsString());
                }
            }
        }

        try {
            yaml.save(targetFile);
            logger.info("Exported item '" + itemId + "' to Oraxen file: " + targetFile.getAbsolutePath());

            // Trigger Oraxen reload if server is running
            try {
                if (Bukkit.getPluginManager() != null && Bukkit.getPluginManager().isPluginEnabled("Oraxen")) {
                    Bukkit.dispatchCommand(Bukkit.getConsoleSender(), "oraxen reload");
                    logger.info("Triggered 'oraxen reload' command after item export.");
                }
            } catch (Throwable t) {
                // In mock test environment or non-Bukkit context
            }

            return true;
        } catch (IOException e) {
            logger.severe("Failed to save Oraxen YAML configuration: " + e.getMessage());
            return false;
        }
    }
}
