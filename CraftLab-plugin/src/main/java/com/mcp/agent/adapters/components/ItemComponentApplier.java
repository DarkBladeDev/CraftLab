package com.mcp.agent.adapters.components;

import com.google.gson.JsonElement;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

/**
 * Strategy interface for translating and applying a specific Minecraft Data Component
 * to an ItemStack / ItemMeta.
 */
public interface ItemComponentApplier {

    /**
     * The canonical Minecraft component identifier, e.g. "minecraft:equippable".
     */
    String getComponentKey();

    /**
     * Checks if this component applier is supported on the current Paper server runtime.
     * Appliers targeting 1.21.2+ components (like Equippable) can reflectively check
     * API presence to prevent linkage or runtime errors on older 1.21.0 - 1.21.1 runtimes.
     */
    boolean isSupported();

    /**
     * Applies the JSON component payload to the target ItemStack and/or ItemMeta.
     *
     * @param stack the target item stack
     * @param meta the active item meta being configured
     * @param componentData the JSON payload for this component
     */
    void apply(ItemStack stack, ItemMeta meta, JsonElement componentData);
}
