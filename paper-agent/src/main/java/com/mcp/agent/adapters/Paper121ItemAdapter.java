package com.mcp.agent.adapters;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.minimessage.MiniMessage;
import org.bukkit.Material;
import org.bukkit.inventory.ItemFlag;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.util.ArrayList;
import java.util.List;

public class Paper121ItemAdapter implements ItemAdapter {
    private final MiniMessage miniMessage = MiniMessage.miniMessage();

    @Override
    public ItemStack compile(JsonObject itemJson) {
        String materialName = itemJson.has("material") ? itemJson.get("material").getAsString() : "STONE";
        Material material = Material.matchMaterial(materialName);
        if (material == null) {
            material = Material.STONE;
        }

        int amount = itemJson.has("amount") ? itemJson.get("amount").getAsInt() : 1;
        ItemStack stack = new ItemStack(material, Math.max(1, Math.min(amount, 64)));

        ItemMeta meta = stack.getItemMeta();
        if (meta == null) {
            return stack;
        }

        // Display Name (Adventure MiniMessage)
        if (itemJson.has("display_name") && !itemJson.get("display_name").isJsonNull()) {
            String displayName = itemJson.get("display_name").getAsString();
            meta.displayName(miniMessage.deserialize(displayName));
        }

        // Lore
        if (itemJson.has("lore") && itemJson.get("lore").isJsonArray()) {
            JsonArray loreArray = itemJson.getAsJsonArray("lore");
            List<Component> loreComponents = new ArrayList<>();
            for (JsonElement el : loreArray) {
                loreComponents.add(miniMessage.deserialize(el.getAsString()));
            }
            meta.lore(loreComponents);
        }

        // Custom Model Data
        if (itemJson.has("custom_model_data") && !itemJson.get("custom_model_data").isJsonNull()) {
            int cmd = itemJson.get("custom_model_data").getAsInt();
            meta.setCustomModelData(cmd);
        }

        // Modern 1.21.2+ Item Model Component (reflective invocation for multi-version server compatibility)
        if (itemJson.has("item_model") && !itemJson.get("item_model").isJsonNull()) {
            String itemModelKey = itemJson.get("item_model").getAsString();
            applyItemModel(meta, itemModelKey);
        }

        // Item Flags
        if (itemJson.has("item_flags") && itemJson.get("item_flags").isJsonArray()) {
            JsonArray flagsArray = itemJson.getAsJsonArray("item_flags");
            for (JsonElement el : flagsArray) {
                try {
                    ItemFlag flag = ItemFlag.valueOf(el.getAsString());
                    meta.addItemFlags(flag);
                } catch (IllegalArgumentException ignored) {
                    // Ignore unrecognized flag
                }
            }
        }

        stack.setItemMeta(meta);
        return stack;
    }

    void applyItemModel(ItemMeta meta, String itemModelStr) {
        if (itemModelStr == null || itemModelStr.trim().isEmpty()) {
            return;
        }
        try {
            org.bukkit.NamespacedKey key = org.bukkit.NamespacedKey.fromString(itemModelStr.trim().toLowerCase());
            if (key != null) {
                // In Paper 1.21.2+, meta.setItemModel(NamespacedKey) is present
                java.lang.reflect.Method method = meta.getClass().getMethod("setItemModel", org.bukkit.NamespacedKey.class);
                method.invoke(meta, key);
            }
        } catch (NoSuchMethodException ignored) {
            // Server runtime is Paper 1.21.0 - 1.21.1 where setItemModel does not exist yet; safe fallback
        } catch (Exception ignored) {
            // Reflective error or unsupported mock environment
        }
    }

    @Override
    public boolean supports(String minecraftVersion) {
        return minecraftVersion != null && minecraftVersion.contains("1.21");
    }
}
