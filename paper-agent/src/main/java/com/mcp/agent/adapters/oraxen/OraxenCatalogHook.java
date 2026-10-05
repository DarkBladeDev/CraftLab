package com.mcp.agent.adapters.oraxen;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import org.bukkit.Bukkit;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

public class OraxenCatalogHook {
    private final Logger logger;

    public OraxenCatalogHook(Logger logger) {
        this.logger = logger;
    }

    public boolean isOraxenEnabled() {
        return Bukkit.getPluginManager().isPluginEnabled("Oraxen");
    }

    public String getOraxenVersion() {
        if (!isOraxenEnabled()) {
            return "not_installed";
        }
        var plugin = Bukkit.getPluginManager().getPlugin("Oraxen");
        return plugin != null ? plugin.getDescription().getVersion() : "unknown";
    }

    /**
     * Inspects registered Oraxen items and returns a list of JSON representations.
     */
    public List<JsonObject> getDiscoveredItems() {
        List<JsonObject> items = new ArrayList<>();
        if (!isOraxenEnabled()) {
            return items;
        }

        try {
            // First attempt: Read configurations directly from plugins/Oraxen/items/
            File pluginsDir = Bukkit.getPluginManager().getPlugin("Oraxen").getDataFolder();
            File itemsDir = new File(pluginsDir, "items");
            if (itemsDir.exists() && itemsDir.isDirectory()) {
                scanItemsDirectory(itemsDir, items);
            }
        } catch (Exception e) {
            logger.warning("Error inspecting Oraxen items: " + e.getMessage());
        }

        return items;
    }

    private void scanItemsDirectory(File dir, List<JsonObject> items) {
        File[] files = dir.listFiles();
        if (files == null) return;

        for (File file : files) {
            if (file.isDirectory()) {
                scanItemsDirectory(file, items);
            } else if (file.getName().endsWith(".yml") || file.getName().endsWith(".yaml")) {
                parseOraxenYaml(file, items);
            }
        }
    }

    private void parseOraxenYaml(File file, List<JsonObject> items) {
        try {
            YamlConfiguration yaml = YamlConfiguration.loadConfiguration(file);
            for (String key : yaml.getKeys(false)) {
                ConfigurationSection sec = yaml.getConfigurationSection(key);
                if (sec == null) continue;

                JsonObject itemObj = new JsonObject();
                itemObj.addProperty("id", key);
                itemObj.addProperty("material", sec.getString("material", "DIAMOND_SWORD").toUpperCase());

                if (sec.contains("displayname")) {
                    itemObj.addProperty("displayName", sec.getString("displayname"));
                } else if (sec.contains("name")) {
                    itemObj.addProperty("displayName", sec.getString("name"));
                }

                if (sec.contains("lore")) {
                    JsonArray loreArr = new JsonArray();
                    List<String> loreLines = sec.getStringList("lore");
                    for (String line : loreLines) {
                        loreArr.add(line);
                    }
                    itemObj.add("lore", loreArr);
                }

                if (sec.contains("Pack.custom_model_data")) {
                    itemObj.addProperty("customModelData", sec.getInt("Pack.custom_model_data"));
                } else if (sec.contains("custom_model_data")) {
                    itemObj.addProperty("customModelData", sec.getInt("custom_model_data"));
                }

                // Collect raw properties
                JsonObject rawProps = new JsonObject();
                if (sec.contains("Pack")) {
                    JsonObject packObj = new JsonObject();
                    ConfigurationSection packSec = sec.getConfigurationSection("Pack");
                    if (packSec != null) {
                        for (String pKey : packSec.getKeys(false)) {
                            packObj.addProperty(pKey, packSec.getString(pKey));
                        }
                    }
                    rawProps.add("Pack", packObj);
                }
                if (sec.contains("Mechanics")) {
                    JsonObject mechObj = new JsonObject();
                    ConfigurationSection mechSec = sec.getConfigurationSection("Mechanics");
                    if (mechSec != null) {
                        for (String mKey : mechSec.getKeys(false)) {
                            mechObj.addProperty(mKey, mechSec.getString(mKey));
                        }
                    }
                    rawProps.add("Mechanics", mechObj);
                }
                itemObj.add("raw_properties", rawProps);

                items.add(itemObj);
            }
        } catch (Exception e) {
            logger.warning("Could not parse Oraxen yaml " + file.getName() + ": " + e.getMessage());
        }
    }
}
