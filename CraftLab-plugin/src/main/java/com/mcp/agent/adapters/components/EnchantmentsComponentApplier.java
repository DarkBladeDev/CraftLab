package com.mcp.agent.adapters.components;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import org.bukkit.NamespacedKey;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Applier for the Minecraft 1.20.5+ / 1.21+ `minecraft:enchantments` data component.
 */
public class EnchantmentsComponentApplier implements ItemComponentApplier {
    private static final Logger LOGGER = Logger.getLogger(EnchantmentsComponentApplier.class.getName());

    public static final String COMPONENT_KEY = "minecraft:enchantments";

    @Override
    public String getComponentKey() {
        return COMPONENT_KEY;
    }

    @Override
    public boolean isSupported() {
        return true;
    }

    @Override
    public void apply(ItemStack stack, ItemMeta meta, JsonElement componentData) {
        if (componentData == null || meta == null) {
            return;
        }

        if (componentData.isJsonObject()) {
            JsonObject obj = componentData.getAsJsonObject();
            JsonObject levelsObj = (obj.has("levels") && obj.get("levels").isJsonObject())
                    ? obj.getAsJsonObject("levels") : obj;

            for (Map.Entry<String, JsonElement> entry : levelsObj.entrySet()) {
                String enchantName = entry.getKey();
                if ("show_in_tooltip".equals(enchantName)) {
                    continue; // Skip component boolean flag
                }

                int level = 1;
                try {
                    level = entry.getValue().getAsInt();
                } catch (Exception ignored) {
                    continue;
                }

                applySingleEnchantment(meta, enchantName, level);
            }
        } else if (componentData.isJsonArray()) {
            for (JsonElement el : componentData.getAsJsonArray()) {
                if (!el.isJsonObject()) continue;
                JsonObject o = el.getAsJsonObject();
                String id = o.has("id") && !o.get("id").isJsonNull() ? o.get("id").getAsString() : null;
                int lvl = 1;
                if (o.has("lvl") && !o.get("lvl").isJsonNull()) {
                    lvl = o.get("lvl").getAsInt();
                } else if (o.has("level") && !o.get("level").isJsonNull()) {
                    lvl = o.get("level").getAsInt();
                }
                if (id != null) {
                    applySingleEnchantment(meta, id, lvl);
                }
            }
        }
    }

    private void applySingleEnchantment(ItemMeta meta, String rawName, int level) {
        Enchantment enchantment = resolveEnchantment(rawName);
        if (enchantment == null) {
            LOGGER.log(Level.FINE, "Unknown enchantment: " + rawName);
            return;
        }
        try {
            // Apply with unrestricted levels (ignoreLevelRestriction = true)
            meta.addEnchant(enchantment, level, true);
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Failed to apply enchantment " + rawName + " at level " + level + ": " + e.getMessage(), e);
        }
    }

    public static Enchantment resolveEnchantment(String raw) {
        if (raw == null || raw.trim().isEmpty()) return null;
        NamespacedKey key = EquippableComponentApplier.parseNamespacedKey(raw);
        if (key != null) {
            try {
                Enchantment ench = Enchantment.getByKey(key);
                if (ench != null) return ench;
            } catch (Throwable ignored) {}
        }
        String clean = raw.trim().toLowerCase().replace("minecraft:", "");
        try {
            Enchantment ench = Enchantment.getByName(clean.toUpperCase());
            if (ench != null) return ench;
        } catch (Throwable ignored) {}
        return null;
    }
}
