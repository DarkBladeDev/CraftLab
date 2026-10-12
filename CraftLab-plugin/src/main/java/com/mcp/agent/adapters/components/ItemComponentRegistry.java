package com.mcp.agent.adapters.components;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.util.Collection;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Extensible registry and dispatcher for Minecraft item data components.
 */
public class ItemComponentRegistry {
    private static final Logger LOGGER = Logger.getLogger(ItemComponentRegistry.class.getName());

    private final Map<String, ItemComponentApplier> appliers = new ConcurrentHashMap<>();

    public ItemComponentRegistry() {
    }

    /**
     * Registers a new component applier.
     */
    public void register(ItemComponentApplier applier) {
        if (applier != null && applier.getComponentKey() != null) {
            String key = normalizeKey(applier.getComponentKey());
            appliers.put(key, applier);
        }
    }

    /**
     * Unregisters an applier by component key.
     */
    public void unregister(String componentKey) {
        if (componentKey != null) {
            appliers.remove(normalizeKey(componentKey));
        }
    }

    /**
     * Returns the applier registered for the given component key, or null if none registered.
     */
    public ItemComponentApplier getApplier(String componentKey) {
        if (componentKey == null) return null;
        return appliers.get(normalizeKey(componentKey));
    }

    /**
     * Returns an unmodifiable collection of registered appliers.
     */
    public Collection<ItemComponentApplier> getAppliers() {
        return Collections.unmodifiableCollection(appliers.values());
    }

    /**
     * Iterates over all entries in the given components JSON object and delegates
     * each component to its registered, supported applier.
     *
     * @param stack the ItemStack being compiled
     * @param meta the ItemMeta being mutated
     * @param components the components JSON mapping (e.g. {"minecraft:equippable": {...}})
     */
    public void applyAll(ItemStack stack, ItemMeta meta, JsonObject components) {
        if (components == null || meta == null) {
            return;
        }

        for (Map.Entry<String, JsonElement> entry : components.entrySet()) {
            String rawKey = entry.getKey();
            String normalized = normalizeKey(rawKey);
            ItemComponentApplier applier = appliers.get(normalized);

            if (applier != null) {
                if (applier.isSupported()) {
                    try {
                        applier.apply(stack, meta, entry.getValue());
                    } catch (Exception e) {
                        LOGGER.log(Level.WARNING, "Failed to apply component '" + rawKey + "': " + e.getMessage(), e);
                    }
                } else {
                    LOGGER.log(Level.FINE, "Component applier for '" + rawKey + "' is not supported on this server runtime, skipping.");
                }
            } else {
                LOGGER.log(Level.FINE, "No component applier registered for '" + rawKey + "', ignoring.");
            }
        }
    }

    private static String normalizeKey(String key) {
        String clean = key.trim().toLowerCase();
        if (!clean.contains(":")) {
            return "minecraft:" + clean;
        }
        return clean;
    }
}
