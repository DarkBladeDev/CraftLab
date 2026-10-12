package com.mcp.agent.adapters.components;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import org.bukkit.NamespacedKey;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeModifier;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.util.UUID;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Applier for the Minecraft 1.20.5+ / 1.21+ `minecraft:attribute_modifiers` data component.
 */
public class AttributeModifiersComponentApplier implements ItemComponentApplier {
    private static final Logger LOGGER = Logger.getLogger(AttributeModifiersComponentApplier.class.getName());

    public static final String COMPONENT_KEY = "minecraft:attribute_modifiers";

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

        JsonArray modifiersArray = null;
        if (componentData.isJsonArray()) {
            modifiersArray = componentData.getAsJsonArray();
        } else if (componentData.isJsonObject()) {
            JsonObject obj = componentData.getAsJsonObject();
            if (obj.has("modifiers") && obj.get("modifiers").isJsonArray()) {
                modifiersArray = obj.getAsJsonArray("modifiers");
            }
        }

        if (modifiersArray == null || modifiersArray.isEmpty()) {
            return;
        }

        for (JsonElement el : modifiersArray) {
            if (!el.isJsonObject()) continue;
            JsonObject modObj = el.getAsJsonObject();

            String typeStr = null;
            if (modObj.has("type") && !modObj.get("type").isJsonNull()) {
                typeStr = modObj.get("type").getAsString();
            } else if (modObj.has("attribute") && !modObj.get("attribute").isJsonNull()) {
                typeStr = modObj.get("attribute").getAsString();
            }

            if (typeStr == null || typeStr.trim().isEmpty()) {
                continue;
            }

            Attribute attribute = resolveAttribute(typeStr);
            if (attribute == null) {
                LOGGER.log(Level.FINE, "Unknown attribute type: " + typeStr);
                continue;
            }

            double amount = 0.0;
            if (modObj.has("amount") && !modObj.get("amount").isJsonNull()) {
                try {
                    amount = modObj.get("amount").getAsDouble();
                } catch (Exception ignored) {
                    continue;
                }
            }

            String slotStr = modObj.has("slot") && !modObj.get("slot").isJsonNull()
                    ? modObj.get("slot").getAsString() : null;
            EquipmentSlot eqSlot = "any".equalsIgnoreCase(slotStr) ? null : EquippableComponentApplier.mapSlot(slotStr);

            String opStr = modObj.has("operation") && !modObj.get("operation").isJsonNull()
                    ? modObj.get("operation").getAsString() : "add_value";
            AttributeModifier.Operation operation = mapOperation(opStr);

            String name = modObj.has("name") && !modObj.get("name").isJsonNull()
                    ? modObj.get("name").getAsString() : (attribute.name() + "_modifier");

            UUID uuid;
            if (modObj.has("uuid") && !modObj.get("uuid").isJsonNull()) {
                try {
                    uuid = UUID.fromString(modObj.get("uuid").getAsString());
                } catch (IllegalArgumentException e) {
                    uuid = UUID.nameUUIDFromBytes(name.getBytes());
                }
            } else if (modObj.has("id") && !modObj.get("id").isJsonNull()) {
                uuid = UUID.nameUUIDFromBytes(modObj.get("id").getAsString().getBytes());
            } else {
                uuid = UUID.nameUUIDFromBytes((name + "_" + (slotStr != null ? slotStr : "any")).getBytes());
            }

            try {
                NamespacedKey modKey = parseModifierKey(modObj, name);
                org.bukkit.inventory.EquipmentSlotGroup slotGroup = eqSlot != null ? eqSlot.getGroup() : org.bukkit.inventory.EquipmentSlotGroup.ANY;
                AttributeModifier modifier = new AttributeModifier(modKey, amount, operation, slotGroup);
                meta.addAttributeModifier(attribute, modifier);
            } catch (Throwable t) {
                try {
                    AttributeModifier modifier = eqSlot != null
                            ? new AttributeModifier(uuid, name, amount, operation, eqSlot)
                            : new AttributeModifier(uuid, name, amount, operation);
                    meta.addAttributeModifier(attribute, modifier);
                } catch (Exception e) {
                    LOGGER.log(Level.WARNING, "Failed to apply attribute modifier " + name + ": " + e.getMessage(), e);
                }
            }
        }
    }

    public static NamespacedKey parseModifierKey(JsonObject modObj, String fallbackName) {
        String rawKey = null;
        if (modObj.has("id") && !modObj.get("id").isJsonNull()) {
            rawKey = modObj.get("id").getAsString();
        } else if (modObj.has("name") && !modObj.get("name").isJsonNull()) {
            rawKey = modObj.get("name").getAsString();
        }
        if (rawKey == null || rawKey.trim().isEmpty()) {
            rawKey = fallbackName;
        }
        String clean = rawKey.trim().toLowerCase().replaceAll("[^a-z0-9/._-]", "_");
        if (clean.isEmpty()) clean = "modifier";
        if (clean.contains(":")) {
            NamespacedKey key = NamespacedKey.fromString(clean);
            if (key != null) return key;
        }
        return NamespacedKey.minecraft(clean);
    }

    public static Attribute resolveAttribute(String raw) {
        if (raw == null || raw.trim().isEmpty()) return null;
        String clean = raw.trim().toLowerCase().replace("minecraft:", "");

        for (Attribute attr : Attribute.values()) {
            if (attr.getKey() != null) {
                String keyPath = attr.getKey().getKey().toLowerCase();
                if (keyPath.equals(clean) || keyPath.equals("generic." + clean) || clean.equals("generic." + keyPath)) {
                    return attr;
                }
                if (attr.getKey().toString().equalsIgnoreCase(raw.trim())) {
                    return attr;
                }
            }
            String enumName = attr.name().toLowerCase().replace("_", ".");
            if (enumName.equals(clean) || enumName.equals("generic." + clean) || clean.equals("generic." + enumName)) {
                return attr;
            }
            if (attr.name().equalsIgnoreCase(clean.replace(".", "_"))) {
                return attr;
            }
        }
        return null;
    }

    public static AttributeModifier.Operation mapOperation(String opStr) {
        if (opStr == null) return AttributeModifier.Operation.ADD_NUMBER;
        String clean = opStr.trim().toLowerCase();
        switch (clean) {
            case "add_multiplied_base":
            case "add_scalar":
                return AttributeModifier.Operation.ADD_SCALAR;
            case "add_multiplied_total":
            case "multiply_scalar_1":
                return AttributeModifier.Operation.MULTIPLY_SCALAR_1;
            case "add_value":
            case "add_number":
            default:
                return AttributeModifier.Operation.ADD_NUMBER;
        }
    }
}
