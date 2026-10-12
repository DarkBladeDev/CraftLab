package com.mcp.agent.adapters;

import org.bukkit.NamespacedKey;
import org.bukkit.inventory.meta.ItemMeta;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Proxy;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.*;

public class Paper121ItemAdapterTest {

    interface ModernItemMetaWithItemModel extends ItemMeta {
        void setItemModel(NamespacedKey key);
    }

    @Test
    public void testVersionSupport() {
        Paper121ItemAdapter adapter = new Paper121ItemAdapter();
        assertTrue(adapter.supports("1.21"));
        assertTrue(adapter.supports("1.21.1"));
        assertTrue(adapter.supports("1.21.4"));
        assertTrue(adapter.supports("1.21.11"));
        assertFalse(adapter.supports("1.20.4"));
    }

    @Test
    public void testApplyItemModelInvokesModernMethod() {
        Paper121ItemAdapter adapter = new Paper121ItemAdapter();
        AtomicReference<NamespacedKey> capturedKey = new AtomicReference<>();

        ModernItemMetaWithItemModel mockMeta = (ModernItemMetaWithItemModel) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{ModernItemMetaWithItemModel.class},
                (proxy, method, args) -> {
                    if ("setItemModel".equals(method.getName()) && args != null && args.length == 1) {
                        capturedKey.set((NamespacedKey) args[0]);
                        return null;
                    }
                    return null;
                }
        );

        adapter.applyItemModel(mockMeta, "studio:items/celestial_sword");
        assertNotNull(capturedKey.get());
        assertEquals("studio", capturedKey.get().getNamespace());
        assertEquals("items/celestial_sword", capturedKey.get().getKey());
    }

    @Test
    public void testApplyItemModelGracefulFallbackOnLegacyMeta() {
        Paper121ItemAdapter adapter = new Paper121ItemAdapter();

        ItemMeta legacyMeta = (ItemMeta) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{ItemMeta.class},
                (proxy, method, args) -> null
        );

        // Does not have setItemModel; must safely complete without throwing exception
        assertDoesNotThrow(() -> adapter.applyItemModel(legacyMeta, "studio:items/celestial_sword"));
    }

    @Test
    public void testApplyItemModelInfersMinecraftNamespace() {
        Paper121ItemAdapter adapter = new Paper121ItemAdapter();
        AtomicReference<NamespacedKey> capturedKey = new AtomicReference<>();

        ModernItemMetaWithItemModel mockMeta = (ModernItemMetaWithItemModel) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{ModernItemMetaWithItemModel.class},
                (proxy, method, args) -> {
                    if ("setItemModel".equals(method.getName()) && args != null && args.length == 1) {
                        capturedKey.set((NamespacedKey) args[0]);
                        return null;
                    }
                    return null;
                }
        );

        adapter.applyItemModel(mockMeta, "custom_prop");
        assertNotNull(capturedKey.get());
        assertEquals("minecraft", capturedKey.get().getNamespace());
        assertEquals("custom_prop", capturedKey.get().getKey());
    }

    @Test
    public void testApplyItemModelNullEmptySafe() {
        Paper121ItemAdapter adapter = new Paper121ItemAdapter();
        assertDoesNotThrow(() -> adapter.applyItemModel(null, "studio:items/test"));
        assertDoesNotThrow(() -> adapter.applyItemModel(null, null));
    }

    @Test
    public void testComponentRegistryDispatch() {
        com.mcp.agent.adapters.components.ItemComponentRegistry registry = new com.mcp.agent.adapters.components.ItemComponentRegistry();
        AtomicReference<String> dispatchedKey = new AtomicReference<>();

        registry.register(new com.mcp.agent.adapters.components.ItemComponentApplier() {
            @Override
            public String getComponentKey() {
                return "minecraft:custom_test";
            }

            @Override
            public boolean isSupported() {
                return true;
            }

            @Override
            public void apply(org.bukkit.inventory.ItemStack stack, ItemMeta meta, com.google.gson.JsonElement componentData) {
                dispatchedKey.set(componentData.getAsJsonObject().get("value").getAsString());
            }
        });

        Paper121ItemAdapter adapter = new Paper121ItemAdapter(registry);
        com.google.gson.JsonObject itemJson = new com.google.gson.JsonObject();
        itemJson.addProperty("material", "DIAMOND");
        com.google.gson.JsonObject components = new com.google.gson.JsonObject();
        com.google.gson.JsonObject testComp = new com.google.gson.JsonObject();
        testComp.addProperty("value", "hello_world");
        components.add("minecraft:custom_test", testComp);
        itemJson.add("components", components);

        // In unit test without Bukkit.getItemFactory initialized, test with proxy ItemMeta
        ItemMeta dummyMeta = (ItemMeta) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{ItemMeta.class},
                (proxy, method, args) -> null
        );
        registry.applyAll(null, dummyMeta, components);
        assertEquals("hello_world", dispatchedKey.get());
    }
}
