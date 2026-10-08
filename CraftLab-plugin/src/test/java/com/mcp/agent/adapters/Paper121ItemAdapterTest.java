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
}
