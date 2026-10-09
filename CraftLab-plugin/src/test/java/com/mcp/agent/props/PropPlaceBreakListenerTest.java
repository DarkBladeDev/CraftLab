package com.mcp.agent.props;

import org.bukkit.Material;
import org.bukkit.block.Block;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Proxy;

import static org.junit.jupiter.api.Assertions.*;

public class PropPlaceBreakListenerTest {

    private Block createMockBlock(Material material, boolean isReplaceable) {
        return (Block) Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{Block.class},
                (proxy, method, args) -> {
                    if ("getType".equals(method.getName())) {
                        return material;
                    }
                    if ("isReplaceable".equals(method.getName())) {
                        return isReplaceable;
                    }
                    return null;
                }
        );
    }

    @Test
    public void testIsClearForPlacementValidation() {
        // Null block is never clear
        assertFalse(PropPlaceBreakListener.isClearForPlacement(null));

        // Air is clear
        Block airBlock = createMockBlock(Material.AIR, false);
        assertTrue(PropPlaceBreakListener.isClearForPlacement(airBlock));

        // Structure void is clear
        Block voidBlock = createMockBlock(Material.STRUCTURE_VOID, false);
        assertTrue(PropPlaceBreakListener.isClearForPlacement(voidBlock));

        // Replaceable grass/fern/tall grass is clear even if material is not air
        Block tallGrass = createMockBlock(Material.TALL_GRASS, true);
        assertTrue(PropPlaceBreakListener.isClearForPlacement(tallGrass));

        // Solid non-replaceable block (stone, obsidian) is obstructed
        Block stone = createMockBlock(Material.STONE, false);
        assertFalse(PropPlaceBreakListener.isClearForPlacement(stone));

        Block oakPlanks = createMockBlock(Material.OAK_PLANKS, false);
        assertFalse(PropPlaceBreakListener.isClearForPlacement(oakPlanks));
    }
}
