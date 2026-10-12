package com.mcp.agent.adapters;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mcp.agent.adapters.components.AttributeModifiersComponentApplier;
import com.mcp.agent.adapters.components.EnchantmentsComponentApplier;
import com.mcp.agent.adapters.components.ItemComponentRegistry;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeModifier;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.meta.ItemMeta;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

public class ComponentAppliersTest {

    public interface MockMetaWithModifiers extends ItemMeta {
        boolean addAttributeModifier(Attribute attribute, AttributeModifier modifier);
        boolean addEnchant(Enchantment ench, int level, boolean ignoreLevelRestriction);
    }

    @Test
    public void testAttributeResolution() {
        assertEquals(Attribute.GENERIC_ATTACK_DAMAGE, AttributeModifiersComponentApplier.resolveAttribute("generic.attack_damage"));
        assertEquals(Attribute.GENERIC_ATTACK_DAMAGE, AttributeModifiersComponentApplier.resolveAttribute("attack_damage"));
        assertEquals(Attribute.GENERIC_ATTACK_DAMAGE, AttributeModifiersComponentApplier.resolveAttribute("minecraft:generic.attack_damage"));
        assertEquals(Attribute.GENERIC_MOVEMENT_SPEED, AttributeModifiersComponentApplier.resolveAttribute("generic.movement_speed"));
        assertEquals(Attribute.GENERIC_MAX_HEALTH, AttributeModifiersComponentApplier.resolveAttribute("generic.max_health"));
        assertNull(AttributeModifiersComponentApplier.resolveAttribute("non_existent_attribute_xyz"));
        assertNull(AttributeModifiersComponentApplier.resolveAttribute(null));
    }

    @Test
    public void testOperationMapping() {
        assertEquals(AttributeModifier.Operation.ADD_NUMBER, AttributeModifiersComponentApplier.mapOperation("add_value"));
        assertEquals(AttributeModifier.Operation.ADD_SCALAR, AttributeModifiersComponentApplier.mapOperation("add_multiplied_base"));
        assertEquals(AttributeModifier.Operation.MULTIPLY_SCALAR_1, AttributeModifiersComponentApplier.mapOperation("add_multiplied_total"));
        assertEquals(AttributeModifier.Operation.ADD_NUMBER, AttributeModifiersComponentApplier.mapOperation(null));
        assertEquals(AttributeModifier.Operation.ADD_NUMBER, AttributeModifiersComponentApplier.mapOperation("unknown_op"));
    }

    @Test
    public void testApplyAttributeModifiers() {
        AttributeModifiersComponentApplier applier = new AttributeModifiersComponentApplier();
        List<Attribute> capturedAttrs = new ArrayList<>();
        List<AttributeModifier> capturedModifiers = new ArrayList<>();

        MockMetaWithModifiers mockMeta = (MockMetaWithModifiers) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{MockMetaWithModifiers.class},
                (proxy, method, args) -> {
                    if ("addAttributeModifier".equals(method.getName())) {
                        capturedAttrs.add((Attribute) args[0]);
                        capturedModifiers.add((AttributeModifier) args[1]);
                        return true;
                    }
                    return false;
                }
        );

        JsonArray modifiers = new JsonArray();
        JsonObject mod1 = new JsonObject();
        mod1.addProperty("type", "generic.attack_damage");
        mod1.addProperty("amount", 14.5);
        mod1.addProperty("slot", "mainhand");
        mod1.addProperty("operation", "add_value");
        modifiers.add(mod1);

        JsonObject mod2 = new JsonObject();
        mod2.addProperty("type", "generic.movement_speed");
        mod2.addProperty("amount", 0.2);
        mod2.addProperty("slot", "feet");
        mod2.addProperty("operation", "add_multiplied_base");
        modifiers.add(mod2);

        applier.apply(null, mockMeta, modifiers);

        assertEquals(2, capturedAttrs.size());
        assertEquals(Attribute.GENERIC_ATTACK_DAMAGE, capturedAttrs.get(0));
        assertEquals(14.5, capturedModifiers.get(0).getAmount());
        assertEquals(EquipmentSlot.HAND.getGroup(), capturedModifiers.get(0).getSlotGroup());
        assertEquals(AttributeModifier.Operation.ADD_NUMBER, capturedModifiers.get(0).getOperation());

        assertEquals(Attribute.GENERIC_MOVEMENT_SPEED, capturedAttrs.get(1));
        assertEquals(0.2, capturedModifiers.get(1).getAmount());
        assertEquals(EquipmentSlot.FEET.getGroup(), capturedModifiers.get(1).getSlotGroup());
        assertEquals(AttributeModifier.Operation.ADD_SCALAR, capturedModifiers.get(1).getOperation());
    }

    @Test
    public void testApplyEnchantments() {
        EnchantmentsComponentApplier applier = new EnchantmentsComponentApplier();
        AtomicInteger appliedCount = new AtomicInteger(0);

        MockMetaWithModifiers mockMeta = (MockMetaWithModifiers) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{MockMetaWithModifiers.class},
                (proxy, method, args) -> {
                    if ("addEnchant".equals(method.getName())) {
                        appliedCount.incrementAndGet();
                        assertTrue((Boolean) args[2]); // ignoreLevelRestriction should be true
                        return true;
                    }
                    return false;
                }
        );

        JsonObject json = new JsonObject();
        json.addProperty("sharpness", 5);
        json.addProperty("unbreaking", 3);

        // Safely executes even in headless unit test without Paper server RegistryAccess
        assertDoesNotThrow(() -> applier.apply(null, mockMeta, json));
        assertNotNull(applier.getComponentKey());
        assertTrue(applier.isSupported());
    }

    @Test
    public void testDefaultRegistryRegistration() {
        ItemComponentRegistry registry = Paper121ItemAdapter.createDefaultRegistry();
        assertNotNull(registry.getApplier("minecraft:equippable"));
        assertNotNull(registry.getApplier("minecraft:attribute_modifiers"));
        assertNotNull(registry.getApplier("minecraft:enchantments"));
    }
}
