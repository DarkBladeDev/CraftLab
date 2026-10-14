package com.mcp.agent.adapters.components;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import org.bukkit.Color;
import org.bukkit.inventory.ItemFlag;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.inventory.meta.LeatherArmorMeta;

/**
 * Applier for the `minecraft:dyed_color` data component.
 * Applies the 24-bit RGB tint to LeatherArmorMeta and appends ItemFlag.HIDE_DYE
 * so that raw color metadata does not leak into item tooltips.
 */
public class DyedColorComponentApplier implements ItemComponentApplier {
    public static final String COMPONENT_KEY = "minecraft:dyed_color";

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

        if (meta instanceof LeatherArmorMeta) {
            LeatherArmorMeta leatherMeta = (LeatherArmorMeta) meta;
            Integer rgb = null;
            if (componentData.isJsonObject()) {
                JsonObject obj = componentData.getAsJsonObject();
                if (obj.has("rgb") && !obj.get("rgb").isJsonNull()) {
                    rgb = obj.get("rgb").getAsInt();
                }
            } else if (componentData.isJsonPrimitive()) {
                rgb = componentData.getAsInt();
            }

            if (rgb != null) {
                leatherMeta.setColor(Color.fromRGB(rgb & 0xFFFFFF));
                leatherMeta.addItemFlags(ItemFlag.HIDE_DYE);
            }
        }
    }
}
