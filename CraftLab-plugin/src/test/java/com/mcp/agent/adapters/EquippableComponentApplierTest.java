package com.mcp.agent.adapters;

import com.google.gson.JsonObject;
import com.mcp.agent.adapters.components.EquippableComponentApplier;
import org.bukkit.NamespacedKey;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.meta.ItemMeta;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Proxy;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.*;

public class EquippableComponentApplierTest {

    public interface MockEquippable {
        void setSlot(EquipmentSlot slot);
        void setModel(NamespacedKey model);
        void setCameraOverlay(NamespacedKey key);
        void setDispensable(boolean dispensable);
        void setSwappable(boolean swappable);
        void setDamageOnHurt(boolean damageOnHurt);
        void setCanBeSheared(boolean canBeSheared);
    }

    public interface MockItemMetaWithEquippable extends ItemMeta {
        MockEquippable getEquippable();
        void setEquippable(MockEquippable equippable);
    }

    @Test
    public void testSlotMapping() {
        assertEquals(EquipmentSlot.HEAD, EquippableComponentApplier.mapSlot("head"));
        assertEquals(EquipmentSlot.CHEST, EquippableComponentApplier.mapSlot("chest"));
        assertEquals(EquipmentSlot.LEGS, EquippableComponentApplier.mapSlot("legs"));
        assertEquals(EquipmentSlot.FEET, EquippableComponentApplier.mapSlot("feet"));
        assertEquals(EquipmentSlot.BODY, EquippableComponentApplier.mapSlot("body"));
        assertEquals(EquipmentSlot.HAND, EquippableComponentApplier.mapSlot("mainhand"));
        assertEquals(EquipmentSlot.OFF_HAND, EquippableComponentApplier.mapSlot("offhand"));
        assertNotNull(EquippableComponentApplier.mapSlot("saddle"));
        assertNull(EquippableComponentApplier.mapSlot(null));
        assertNull(EquippableComponentApplier.mapSlot("invalid_slot"));
    }

    @Test
    public void testNamespacedKeyParsing() {
        NamespacedKey key1 = EquippableComponentApplier.parseNamespacedKey("dev_studio:chocolate");
        assertNotNull(key1);
        assertEquals("dev_studio", key1.getNamespace());
        assertEquals("chocolate", key1.getKey());

        NamespacedKey key2 = EquippableComponentApplier.parseNamespacedKey("chocolate");
        assertNotNull(key2);
        assertEquals("minecraft", key2.getNamespace());
        assertEquals("chocolate", key2.getKey());

        assertNull(EquippableComponentApplier.parseNamespacedKey(null));
        assertNull(EquippableComponentApplier.parseNamespacedKey(""));
    }

    @Test
    public void testApplyFullEquippableComponent() {
        EquippableComponentApplier applier = new EquippableComponentApplier();

        AtomicReference<EquipmentSlot> capturedSlot = new AtomicReference<>();
        AtomicReference<NamespacedKey> capturedModel = new AtomicReference<>();
        AtomicReference<NamespacedKey> capturedOverlay = new AtomicReference<>();
        AtomicBoolean capturedDispensable = new AtomicBoolean();
        AtomicBoolean capturedSwappable = new AtomicBoolean();
        AtomicBoolean capturedDamageOnHurt = new AtomicBoolean();
        AtomicBoolean capturedCanBeSheared = new AtomicBoolean();
        AtomicBoolean appliedBackToMeta = new AtomicBoolean(false);

        MockEquippable mockEquippable = (MockEquippable) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{MockEquippable.class},
                (proxy, method, args) -> {
                    switch (method.getName()) {
                        case "setSlot":
                            capturedSlot.set((EquipmentSlot) args[0]);
                            break;
                        case "setModel":
                            capturedModel.set((NamespacedKey) args[0]);
                            break;
                        case "setCameraOverlay":
                            capturedOverlay.set((NamespacedKey) args[0]);
                            break;
                        case "setDispensable":
                            capturedDispensable.set((Boolean) args[0]);
                            break;
                        case "setSwappable":
                            capturedSwappable.set((Boolean) args[0]);
                            break;
                        case "setDamageOnHurt":
                            capturedDamageOnHurt.set((Boolean) args[0]);
                            break;
                        case "setCanBeSheared":
                            capturedCanBeSheared.set((Boolean) args[0]);
                            break;
                    }
                    return null;
                }
        );

        MockItemMetaWithEquippable mockMeta = (MockItemMetaWithEquippable) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{MockItemMetaWithEquippable.class},
                (proxy, method, args) -> {
                    if ("getEquippable".equals(method.getName())) {
                        return mockEquippable;
                    }
                    if ("setEquippable".equals(method.getName())) {
                        appliedBackToMeta.set(true);
                        return null;
                    }
                    return null;
                }
        );

        JsonObject json = new JsonObject();
        json.addProperty("slot", "chest");
        json.addProperty("asset_id", "dev_studio:chocolate");
        json.addProperty("camera_overlay", "dev_studio:misc/blur");
        json.addProperty("dispensable", true);
        json.addProperty("swappable", true);
        json.addProperty("damage_on_hurt", false);
        json.addProperty("can_be_sheared", true);

        applier.apply(null, mockMeta, json);

        assertEquals(EquipmentSlot.CHEST, capturedSlot.get());
        assertNotNull(capturedModel.get());
        assertEquals("dev_studio", capturedModel.get().getNamespace());
        assertEquals("chocolate", capturedModel.get().getKey());
        assertNotNull(capturedOverlay.get());
        assertEquals("misc/blur", capturedOverlay.get().getKey());
        assertTrue(capturedDispensable.get());
        assertTrue(capturedSwappable.get());
        assertFalse(capturedDamageOnHurt.get());
        assertTrue(capturedCanBeSheared.get());
        assertTrue(appliedBackToMeta.get());
    }

    @Test
    public void testApplyLegacyModelKeyFallback() {
        EquippableComponentApplier applier = new EquippableComponentApplier();
        AtomicReference<NamespacedKey> capturedModel = new AtomicReference<>();

        MockEquippable mockEquippable = (MockEquippable) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{MockEquippable.class},
                (proxy, method, args) -> {
                    if ("setModel".equals(method.getName())) {
                        capturedModel.set((NamespacedKey) args[0]);
                    }
                    return null;
                }
        );

        MockItemMetaWithEquippable mockMeta = (MockItemMetaWithEquippable) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{MockItemMetaWithEquippable.class},
                (proxy, method, args) -> "getEquippable".equals(method.getName()) ? mockEquippable : null
        );

        JsonObject json = new JsonObject();
        json.addProperty("slot", "legs");
        json.addProperty("model", "custom:ruby_armor");

        applier.apply(null, mockMeta, json);

        assertNotNull(capturedModel.get());
        assertEquals("custom", capturedModel.get().getNamespace());
        assertEquals("ruby_armor", capturedModel.get().getKey());
    }

    @Test
    public void testSafeDegradationOnLegacyMeta() {
        EquippableComponentApplier applier = new EquippableComponentApplier();

        // Plain ItemMeta without getEquippable/setEquippable
        ItemMeta legacyMeta = (ItemMeta) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{ItemMeta.class},
                (proxy, method, args) -> null
        );

        JsonObject json = new JsonObject();
        json.addProperty("slot", "chest");
        json.addProperty("asset_id", "dev_studio:chocolate");

        // Must safely complete without throwing any exception
        assertDoesNotThrow(() -> applier.apply(null, legacyMeta, json));
    }

    @Test
    public void testLegacyFallbackOnLeatherMeta() {
        EquippableComponentApplier applier = new EquippableComponentApplier();

        AtomicReference<org.bukkit.Color> capturedColor = new AtomicReference<>();
        AtomicBoolean capturedHideDye = new AtomicBoolean(false);

        org.bukkit.inventory.meta.LeatherArmorMeta leatherMeta = (org.bukkit.inventory.meta.LeatherArmorMeta) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{org.bukkit.inventory.meta.LeatherArmorMeta.class},
                (proxy, method, args) -> {
                    if ("setColor".equals(method.getName())) {
                        capturedColor.set((org.bukkit.Color) args[0]);
                        return null;
                    }
                    if ("addItemFlags".equals(method.getName())) {
                        org.bukkit.inventory.ItemFlag[] flags = (org.bukkit.inventory.ItemFlag[]) args[0];
                        for (org.bukkit.inventory.ItemFlag f : flags) {
                            if (f == org.bukkit.inventory.ItemFlag.HIDE_DYE) {
                                capturedHideDye.set(true);
                            }
                        }
                        return null;
                    }
                    return null;
                }
        );

        JsonObject json = new JsonObject();
        json.addProperty("slot", "chest");
        json.addProperty("asset_id", "craftlab:ruby_armor");
        json.addProperty("color_rgb", 0x000001);

        applier.apply(null, leatherMeta, json);

        assertNotNull(capturedColor.get());
        assertEquals(0x000001, capturedColor.get().asRGB());
        assertTrue(capturedHideDye.get());
    }
}
