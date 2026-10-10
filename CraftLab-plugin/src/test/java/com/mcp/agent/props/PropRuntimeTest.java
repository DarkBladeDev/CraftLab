package com.mcp.agent.props;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.util.*;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.*;

public class PropRuntimeTest {

    @Test
    public void testPropManagerStateTransitionsAndPersistence(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("PropRuntimeTest");
        PropStorage storage = new PropStorage(tempDir, logger);
        PropManager manager = new PropManager(storage, logger);

        // 1. Register lamp prop definition
        PropDefinition lamp = new PropDefinition("lamp", "Lamp", "studio:item/lamp", "studio:props/lamp_off");
        lamp.setDefaultState("off");

        Map<String, PropDefinition.PropState> states = new LinkedHashMap<>();
        PropDefinition.PropState offState = new PropDefinition.PropState();
        offState.setName("Off");
        offState.setBlockModel("studio:props/lamp_off");
        offState.setLightLevel(0);
        offState.setNextState("on");
        states.put("off", offState);

        PropDefinition.PropState onState = new PropDefinition.PropState();
        onState.setName("On");
        onState.setBlockModel("studio:props/lamp_on");
        onState.setLightLevel(15);
        onState.setNextState("off");
        states.put("on", onState);

        lamp.setStates(states);
        manager.registerDefinition(lamp);

        assertEquals("studio:props/lamp_off", lamp.getBlockModelForState("off"));
        assertEquals("studio:props/lamp_on", lamp.getBlockModelForState("on"));

        // 2. Register placed instance in default state
        UUID instanceId = UUID.randomUUID();
        PropInstance instance = new PropInstance(
                instanceId,
                "lamp",
                "world",
                12, 65, -8,
                0.0f,
                System.currentTimeMillis(),
                "off"
        );
        manager.registerPlacedProp(instance);

        PropInstance retrieved = manager.getInstance(instanceId);
        assertNotNull(retrieved);
        assertEquals("off", retrieved.getCurrentState());

        // 3. Update state in manager & verify persistence
        manager.updateInstanceState(instanceId, "on");
        assertEquals("on", manager.getInstance(instanceId).getCurrentState());

        PropInstance fromDb = storage.getInstanceAt("world", 12, 65, -8);
        assertNotNull(fromDb);
        assertEquals("on", fromDb.getCurrentState());

        // 4. Reload manager from storage and verify state preserved
        PropManager reloadedManager = new PropManager(storage, logger);
        PropInstance reloadedInstance = reloadedManager.getInstance(instanceId);
        assertNotNull(reloadedInstance);
        assertEquals("on", reloadedInstance.getCurrentState());
    }

    @Test
    public void testHitboxOffsetRotations() {
        int[] original = new int[]{1, 0, 2};

        // Yaw 0 (SOUTH): offset remains (1, 0, 2)
        int[] rot0 = PropManager.rotateOffset(original, 0.0f);
        assertArrayEquals(new int[]{1, 0, 2}, rot0);

        // Yaw 90 (WEST): (dz, dy, -dx) -> (2, 0, -1)
        int[] rot90 = PropManager.rotateOffset(original, 90.0f);
        assertArrayEquals(new int[]{2, 0, -1}, rot90);

        // Yaw 180 (NORTH): (-dx, dy, -dz) -> (-1, 0, -2)
        int[] rot180 = PropManager.rotateOffset(original, 180.0f);
        assertArrayEquals(new int[]{-1, 0, -2}, rot180);

        // Yaw 270 (EAST): (-dz, dy, dx) -> (-2, 0, 1)
        int[] rot270 = PropManager.rotateOffset(original, 270.0f);
        assertArrayEquals(new int[]{-2, 0, 1}, rot270);
    }

    @Test
    public void testCardinalYawNormalization() {
        assertEquals(0.0f, PropManager.normalizeToCardinalYaw(0.0f));
        assertEquals(0.0f, PropManager.normalizeToCardinalYaw(30.0f));
        assertEquals(90.0f, PropManager.normalizeToCardinalYaw(90.0f));
        assertEquals(90.0f, PropManager.normalizeToCardinalYaw(85.0f));
        assertEquals(180.0f, PropManager.normalizeToCardinalYaw(180.0f));
        assertEquals(270.0f, PropManager.normalizeToCardinalYaw(270.0f));
        assertEquals(0.0f, PropManager.normalizeToCardinalYaw(350.0f));
    }

    @Test
    public void testCyclicStateTransitions() {
        PropDefinition def = new PropDefinition("traffic_light", "Traffic Light", "studio:item/light");
        Map<String, PropDefinition.PropState> states = new LinkedHashMap<>();

        PropDefinition.PropState red = new PropDefinition.PropState();
        red.setName("Red");
        states.put("red", red);

        PropDefinition.PropState yellow = new PropDefinition.PropState();
        yellow.setName("Yellow");
        states.put("yellow", yellow);

        PropDefinition.PropState green = new PropDefinition.PropState();
        green.setName("Green");
        states.put("green", green);

        def.setStates(states);

        List<String> keys = new ArrayList<>(def.getStates().keySet());
        assertEquals("red", keys.get(0));
        assertEquals("yellow", keys.get(1));
        assertEquals("green", keys.get(2));

        // Cyclic progression without next_state:
        int nextFromRed = (keys.indexOf("red") + 1) % keys.size();
        assertEquals("yellow", keys.get(nextFromRed));

        int nextFromYellow = (keys.indexOf("yellow") + 1) % keys.size();
        assertEquals("green", keys.get(nextFromYellow));

        int nextFromGreen = (keys.indexOf("green") + 1) % keys.size();
        assertEquals("red", keys.get(nextFromGreen));
    }
}
