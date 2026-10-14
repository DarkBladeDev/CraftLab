package com.mcp.agent.adapters.components;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import org.bukkit.Color;
import org.bukkit.NamespacedKey;
import org.bukkit.Sound;
import org.bukkit.entity.EntityType;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.ItemFlag;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.inventory.meta.LeatherArmorMeta;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Applier for the Minecraft 1.21.2+ `minecraft:equippable` data component.
 * Uses reflection over Paper/Bukkit's EquippableComponent API to guarantee
 * multi-version runtime safety across Paper 1.21.0 to 1.21.4+.
 */
public class EquippableComponentApplier implements ItemComponentApplier {
    private static final Logger LOGGER = Logger.getLogger(EquippableComponentApplier.class.getName());

    public static final String COMPONENT_KEY = "minecraft:equippable";

    @Override
    public String getComponentKey() {
        return COMPONENT_KEY;
    }

    @Override
    public boolean isSupported() {
        return true;
    }

    /**
     * Checks if native 1.21.2+ EquippableComponent API is present on this server.
     */
    public boolean hasNativeSupport() {
        try {
            ItemMeta.class.getMethod("getEquippable");
            return true;
        } catch (NoSuchMethodException e) {
            return false;
        }
    }

    @Override
    public void apply(ItemStack stack, ItemMeta meta, JsonElement componentData) {
        if (componentData == null || !componentData.isJsonObject() || meta == null) {
            return;
        }

        JsonObject obj = componentData.getAsJsonObject();

        Method getEquippableMethod = findMethod(meta.getClass(), "getEquippable");
        if (getEquippableMethod == null) {
            LOGGER.log(Level.FINE, "ItemMeta does not support getEquippable on this server runtime, applying legacy fallback.");
            applyLegacyFallback(stack, meta, obj);
            return;
        }

        Object equippable;
        try {
            getEquippableMethod.setAccessible(true);
            equippable = getEquippableMethod.invoke(meta);
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Failed to invoke getEquippable: " + e.getMessage(), e);
            return;
        }

        if (equippable == null) {
            return;
        }

        // 1. Equipment Slot
        if (obj.has("slot") && !obj.get("slot").isJsonNull()) {
            String slotStr = obj.get("slot").getAsString();
            EquipmentSlot eqSlot = mapSlot(slotStr);
            if (eqSlot != null) {
                Method setSlotMethod = findMethod(equippable.getClass(), "setSlot", EquipmentSlot.class);
                if (setSlotMethod != null) {
                    try {
                        setSlotMethod.invoke(equippable, eqSlot);
                    } catch (Exception e) {
                        LOGGER.log(Level.FINE, "Failed to invoke setSlot: " + e.getMessage());
                    }
                }
            }
        }

        // 2. Asset ID / Model (support official 'asset_id' and fallback 'model')
        String assetId = null;
        if (obj.has("asset_id") && !obj.get("asset_id").isJsonNull()) {
            assetId = obj.get("asset_id").getAsString();
        } else if (obj.has("model") && !obj.get("model").isJsonNull()) {
            assetId = obj.get("model").getAsString();
        }

        if (assetId != null && !assetId.trim().isEmpty()) {
            NamespacedKey modelKey = parseNamespacedKey(assetId);
            if (modelKey != null) {
                Method setModelMethod = findMethod(equippable.getClass(), "setModel", NamespacedKey.class);
                if (setModelMethod != null) {
                    try {
                        setModelMethod.invoke(equippable, modelKey);
                    } catch (Exception e) {
                        LOGGER.log(Level.FINE, "Failed to invoke setModel on equippable: " + e.getMessage());
                    }
                }
            }
        }

        // 3. Camera Overlay
        if (obj.has("camera_overlay") && !obj.get("camera_overlay").isJsonNull()) {
            String overlayStr = obj.get("camera_overlay").getAsString();
            NamespacedKey overlayKey = parseNamespacedKey(overlayStr);
            if (overlayKey != null) {
                Method setCameraOverlayMethod = findMethod(equippable.getClass(), "setCameraOverlay", NamespacedKey.class);
                if (setCameraOverlayMethod != null) {
                    try {
                        setCameraOverlayMethod.invoke(equippable, overlayKey);
                    } catch (Exception e) {
                        LOGGER.log(Level.FINE, "Failed to invoke setCameraOverlay: " + e.getMessage());
                    }
                }
            }
        }

        // 4. Equip Sound
        if (obj.has("equip_sound") && !obj.get("equip_sound").isJsonNull()) {
            String soundStr = obj.get("equip_sound").getAsString();
            applyEquipSound(equippable, soundStr);
        }

        // 5. Allowed Entities
        if (obj.has("allowed_entities") && !obj.get("allowed_entities").isJsonNull()) {
            applyAllowedEntities(equippable, obj.get("allowed_entities"));
        }

        // 6. Boolean behavioral flags
        if (obj.has("dispensable") && !obj.get("dispensable").isJsonNull()) {
            invokeBooleanSetter(equippable, "setDispensable", obj.get("dispensable").getAsBoolean());
        }
        if (obj.has("swappable") && !obj.get("swappable").isJsonNull()) {
            invokeBooleanSetter(equippable, "setSwappable", obj.get("swappable").getAsBoolean());
        }
        if (obj.has("damage_on_hurt") && !obj.get("damage_on_hurt").isJsonNull()) {
            invokeBooleanSetter(equippable, "setDamageOnHurt", obj.get("damage_on_hurt").getAsBoolean());
        }
        if (obj.has("can_be_sheared") && !obj.get("can_be_sheared").isJsonNull()) {
            invokeBooleanSetter(equippable, "setCanBeSheared", obj.get("can_be_sheared").getAsBoolean());
        }

        // 7. Apply modified EquippableComponent snapshot back to ItemMeta
        try {
            for (Method m : meta.getClass().getMethods()) {
                if ("setEquippable".equals(m.getName()) && m.getParameterCount() == 1) {
                    m.setAccessible(true);
                    m.invoke(meta, equippable);
                    break;
                }
            }
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Failed to apply EquippableComponent back to ItemMeta: " + e.getMessage(), e);
        }
    }

    public static EquipmentSlot mapSlot(String slotStr) {
        if (slotStr == null) return null;
        String clean = slotStr.trim().toLowerCase();
        switch (clean) {
            case "head":
                return EquipmentSlot.HEAD;
            case "chest":
                return EquipmentSlot.CHEST;
            case "legs":
                return EquipmentSlot.LEGS;
            case "feet":
                return EquipmentSlot.FEET;
            case "body":
                return EquipmentSlot.BODY;
            case "mainhand":
                return EquipmentSlot.HAND;
            case "offhand":
                return EquipmentSlot.OFF_HAND;
            case "saddle":
                try {
                    return EquipmentSlot.valueOf("SADDLE");
                } catch (IllegalArgumentException ignored) {
                    return EquipmentSlot.BODY;
                }
            default:
                try {
                    return EquipmentSlot.valueOf(clean.toUpperCase());
                } catch (IllegalArgumentException ignored) {
                    return null;
                }
        }
    }

    public static NamespacedKey parseNamespacedKey(String raw) {
        if (raw == null || raw.trim().isEmpty()) return null;
        String clean = raw.trim().toLowerCase();
        try {
            if (clean.contains(":")) {
                return NamespacedKey.fromString(clean);
            } else {
                return NamespacedKey.minecraft(clean);
            }
        } catch (Exception e) {
            return null;
        }
    }

    private static void applyEquipSound(Object equippable, String soundStr) {
        if (soundStr == null || soundStr.trim().isEmpty()) return;

        // Try mapping to Bukkit Sound enum
        String cleanEnum = soundStr.trim().toUpperCase().replace("MINECRAFT:", "").replace(".", "_");
        try {
            Sound sound = Sound.valueOf(cleanEnum);
            for (Method m : equippable.getClass().getMethods()) {
                if ("setEquipSound".equals(m.getName()) && m.getParameterCount() == 1
                        && Sound.class.isAssignableFrom(m.getParameterTypes()[0])) {
                    m.invoke(equippable, sound);
                    return;
                }
            }
        } catch (Exception ignored) {
        }

        // Try NamespacedKey if overload exists in runtime
        NamespacedKey soundKey = parseNamespacedKey(soundStr);
        if (soundKey != null) {
            for (Method m : equippable.getClass().getMethods()) {
                if ("setEquipSound".equals(m.getName()) && m.getParameterCount() == 1
                        && NamespacedKey.class.isAssignableFrom(m.getParameterTypes()[0])) {
                    try {
                        m.invoke(equippable, soundKey);
                        return;
                    } catch (Exception ignored) {
                    }
                }
            }
        }
    }

    private static void applyAllowedEntities(Object equippable, JsonElement el) {
        List<EntityType> entities = new ArrayList<>();
        if (el.isJsonArray()) {
            for (JsonElement item : el.getAsJsonArray()) {
                String name = item.getAsString().trim().toUpperCase().replace("MINECRAFT:", "");
                try {
                    entities.add(EntityType.valueOf(name));
                } catch (IllegalArgumentException ignored) {
                }
            }
        } else if (el.isJsonPrimitive()) {
            String name = el.getAsString().trim().toUpperCase().replace("MINECRAFT:", "");
            try {
                entities.add(EntityType.valueOf(name));
            } catch (IllegalArgumentException ignored) {
            }
        }

        if (!entities.isEmpty()) {
            for (Method m : equippable.getClass().getMethods()) {
                if ("setAllowedEntities".equals(m.getName()) && m.getParameterCount() == 1
                        && Collection.class.isAssignableFrom(m.getParameterTypes()[0])) {
                    try {
                        m.invoke(equippable, entities);
                        return;
                    } catch (Exception ignored) {
                    }
                }
            }
        }
    }

    private static void invokeBooleanSetter(Object target, String methodName, boolean value) {
        try {
            for (Method m : target.getClass().getMethods()) {
                if (methodName.equals(m.getName()) && m.getParameterCount() == 1
                        && (m.getParameterTypes()[0].equals(boolean.class) || m.getParameterTypes()[0].equals(Boolean.class))) {
                    m.invoke(target, value);
                    return;
                }
            }
        } catch (Exception ignored) {
        }
    }

    public static Method findMethod(Class<?> clazz, String name, Class<?>... paramTypes) {
        if (clazz == null || name == null) return null;
        try {
            Method m = clazz.getMethod(name, paramTypes);
            m.setAccessible(true);
            return m;
        } catch (NoSuchMethodException ignored) {
        }
        for (Method m : clazz.getMethods()) {
            if (m.getName().equals(name)) {
                if (paramTypes.length == 0 && m.getParameterCount() == 0) {
                    m.setAccessible(true);
                    return m;
                }
                if (paramTypes.length == m.getParameterCount()) {
                    boolean match = true;
                    for (int i = 0; i < paramTypes.length; i++) {
                        if (!m.getParameterTypes()[i].isAssignableFrom(paramTypes[i])) {
                            match = false;
                            break;
                        }
                    }
                    if (match) {
                        m.setAccessible(true);
                        return m;
                    }
                }
            }
        }
        return null;
    }

    private void applyLegacyFallback(ItemStack stack, ItemMeta meta, JsonObject obj) {
        if (meta instanceof LeatherArmorMeta) {
            LeatherArmorMeta leatherMeta = (LeatherArmorMeta) meta;
            Integer colorRgb = null;
            if (obj.has("color_rgb") && !obj.get("color_rgb").isJsonNull()) {
                colorRgb = obj.get("color_rgb").getAsInt();
            } else if (obj.has("legacy_color_rgb") && !obj.get("legacy_color_rgb").isJsonNull()) {
                colorRgb = obj.get("legacy_color_rgb").getAsInt();
            } else if (obj.has("dyed_color") && !obj.get("dyed_color").isJsonNull()) {
                if (obj.get("dyed_color").isJsonObject()) {
                    JsonObject dObj = obj.getAsJsonObject("dyed_color");
                    if (dObj.has("rgb") && !dObj.get("rgb").isJsonNull()) {
                        colorRgb = dObj.get("rgb").getAsInt();
                    }
                } else if (obj.get("dyed_color").isJsonPrimitive()) {
                    colorRgb = obj.get("dyed_color").getAsInt();
                }
            } else if (obj.has("legacy_shader") && obj.get("legacy_shader").isJsonObject()) {
                JsonObject lObj = obj.getAsJsonObject("legacy_shader");
                if (lObj.has("color_rgb") && !lObj.get("color_rgb").isJsonNull()) {
                    colorRgb = lObj.get("color_rgb").getAsInt();
                }
            }

            if (colorRgb != null) {
                leatherMeta.setColor(Color.fromRGB(colorRgb & 0xFFFFFF));
                leatherMeta.addItemFlags(ItemFlag.HIDE_DYE);
            }
        }

        if (obj.has("custom_model_data") && !obj.get("custom_model_data").isJsonNull()) {
            int cmd = obj.get("custom_model_data").getAsInt();
            if (!meta.hasCustomModelData()) {
                meta.setCustomModelData(cmd);
            }
        }
    }
}
