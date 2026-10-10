package com.mcp.agent.props;

import com.github.retrooper.packetevents.PacketEvents;
import com.github.retrooper.packetevents.protocol.entity.data.EntityData;
import com.github.retrooper.packetevents.protocol.entity.data.EntityDataTypes;
import com.github.retrooper.packetevents.protocol.entity.type.EntityTypes;
import com.github.retrooper.packetevents.util.Quaternion4f;
import com.github.retrooper.packetevents.util.Vector3d;
import com.github.retrooper.packetevents.util.Vector3f;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerDestroyEntities;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerEntityMetadata;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerSpawnEntity;
import io.github.retrooper.packetevents.util.SpigotConversionUtil;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Logger;

public class PropManager {
    public static final double TRACKING_RANGE = 32.0;

    // Minecraft 1.20.5+ / 1.21.x ItemDisplay entity data indices:
    // Display:
    //  11: translation (Vector3f)
    //  12: scale (Vector3f)
    //  13: rotation_left (Quaternionf)
    // ItemDisplay:
    //  23: item_stack (ItemStack)
    public static final int METADATA_INDEX_TRANSLATION = 11;
    public static final int METADATA_INDEX_SCALE = 12;
    public static final int METADATA_INDEX_ROTATION_LEFT = 13;
    public static final int METADATA_INDEX_ITEM_STACK = 23;
    public static final int METADATA_INDEX_ITEM_DISPLAY_CONTEXT = 24;

    private final PropStorage storage;
    private final com.mcp.agent.storage.ItemStorage itemStorage;
    private final Logger logger;
    private final Map<String, PropDefinition> definitions = new ConcurrentHashMap<>();
    private final Map<UUID, PropInstance> instancesById = new ConcurrentHashMap<>();
    private final Map<String, Map<Long, List<PropInstance>>> chunkSpatialIndex = new ConcurrentHashMap<>();
    private final Map<UUID, Integer> instanceToEntityId = new ConcurrentHashMap<>();
    private final Map<String, UUID> blockToInstance = new ConcurrentHashMap<>();
    private final Map<UUID, Set<UUID>> playersViewingProps = new ConcurrentHashMap<>();
    private final Map<UUID, Location> activeLightLocations = new ConcurrentHashMap<>();
    private final AtomicInteger nextEntityId = new AtomicInteger(2_000_000);

    public static String toBlockKey(String world, int x, int y, int z) {
        return world + ":" + x + ":" + y + ":" + z;
    }

    public PropManager(PropStorage storage, Logger logger) {
        this(storage, null, logger);
    }

    public PropManager(PropStorage storage, com.mcp.agent.storage.ItemStorage itemStorage, Logger logger) {
        this.storage = storage;
        this.itemStorage = itemStorage;
        this.logger = logger;
        loadAll();
    }

    public void loadAll() {
        definitions.clear();
        instancesById.clear();
        chunkSpatialIndex.clear();
        blockToInstance.clear();

        definitions.putAll(storage.getAllDefinitions());
        for (PropInstance instance : storage.getAllInstances()) {
            addInstanceToMemory(instance);
            applyPropLighting(instance);
        }
        logger.info("Loaded " + definitions.size() + " prop definitions and " + instancesById.size() + " placed props.");
    }

    public void registerDefinition(PropDefinition def) {
        definitions.put(def.getId(), def);
        storage.saveDefinition(def);
        for (PropInstance instance : instancesById.values()) {
            if (instance.getPropId().equals(def.getId())) {
                List<int[]> offsets = getRotatedOffsets(def, instance.getYaw());
                for (int[] off : offsets) {
                    String key = toBlockKey(instance.getWorld(), instance.getX() + off[0], instance.getY() + off[1], instance.getZ() + off[2]);
                    blockToInstance.put(key, instance.getInstanceId());
                }
            }
        }
    }

    public PropDefinition getDefinition(String id) {
        return definitions.get(id);
    }

    public Map<String, PropDefinition> getDefinitions() {
        return Collections.unmodifiableMap(definitions);
    }

    public synchronized void registerPlacedProp(PropInstance instance) {
        addInstanceToMemory(instance);
        storage.saveInstance(instance);
        applyPropLighting(instance);
    }

    public synchronized void removePlacedProp(UUID instanceId) {
        removePropLighting(instanceId);
        PropInstance instance = instancesById.remove(instanceId);
        if (instance != null) {
            removeInstanceFromSpatialIndex(instance);
            storage.removeInstance(instanceId);
            instanceToEntityId.remove(instanceId);
        }
    }

    public PropStorage getStorage() {
        return storage;
    }

    public void updateInstanceState(UUID instanceId, String newState) {
        PropInstance instance = instancesById.get(instanceId);
        if (instance != null) {
            instance.setCurrentState(newState);
            storage.updateInstanceState(instanceId, newState);
        }
    }

    public PropInstance getInstance(UUID instanceId) {
        return instancesById.get(instanceId);
    }

    public PropInstance getInstanceAt(String world, int x, int y, int z) {
        String key = toBlockKey(world, x, y, z);
        UUID instanceId = blockToInstance.get(key);
        if (instanceId != null) {
            PropInstance instance = instancesById.get(instanceId);
            if (instance != null) {
                return instance;
            }
        }
        PropInstance dbInstance = storage.getInstanceAt(world, x, y, z);
        if (dbInstance != null) {
            addInstanceToMemory(dbInstance);
            return dbInstance;
        }
        return null;
    }

    public List<PropInstance> getAllInstances() {
        return new ArrayList<>(instancesById.values());
    }

    public List<int[]> getOccupiedBlocks(PropInstance instance) {
        PropDefinition def = definitions.get(instance.getPropId());
        List<int[]> offsets = getRotatedOffsets(def, instance.getYaw());
        List<int[]> result = new ArrayList<>();
        for (int[] off : offsets) {
            result.add(new int[]{
                    instance.getX() + off[0],
                    instance.getY() + off[1],
                    instance.getZ() + off[2]
            });
        }
        return result;
    }

    public int getEntityId(UUID instanceId) {
        return instanceToEntityId.getOrDefault(instanceId, -1);
    }

    public boolean isBlockOccupied(String world, int x, int y, int z) {
        return blockToInstance.containsKey(toBlockKey(world, x, y, z));
    }

    private void addInstanceToMemory(PropInstance instance) {
        instancesById.put(instance.getInstanceId(), instance);
        instanceToEntityId.computeIfAbsent(instance.getInstanceId(), k -> nextEntityId.incrementAndGet());

        long chunkKey = getChunkKey(instance.getX() >> 4, instance.getZ() >> 4);
        chunkSpatialIndex
                .computeIfAbsent(instance.getWorld(), w -> new ConcurrentHashMap<>())
                .computeIfAbsent(chunkKey, c -> Collections.synchronizedList(new ArrayList<>()))
                .add(instance);

        PropDefinition def = definitions.get(instance.getPropId());
        List<int[]> offsets = getRotatedOffsets(def, instance.getYaw());
        for (int[] off : offsets) {
            String key = toBlockKey(instance.getWorld(), instance.getX() + off[0], instance.getY() + off[1], instance.getZ() + off[2]);
            blockToInstance.put(key, instance.getInstanceId());
        }
    }

    private void removeInstanceFromSpatialIndex(PropInstance instance) {
        long chunkKey = getChunkKey(instance.getX() >> 4, instance.getZ() >> 4);
        Map<Long, List<PropInstance>> worldChunks = chunkSpatialIndex.get(instance.getWorld());
        if (worldChunks != null) {
            List<PropInstance> list = worldChunks.get(chunkKey);
            if (list != null) {
                list.remove(instance);
            }
        }

        PropDefinition def = definitions.get(instance.getPropId());
        List<int[]> offsets = getRotatedOffsets(def, instance.getYaw());
        for (int[] off : offsets) {
            String key = toBlockKey(instance.getWorld(), instance.getX() + off[0], instance.getY() + off[1], instance.getZ() + off[2]);
            blockToInstance.remove(key);
        }
    }

    public List<PropInstance> getPropsNear(String world, double x, double z, double maxDistance) {
        List<PropInstance> result = new ArrayList<>();
        int minChunkX = (int) Math.floor((x - maxDistance) / 16.0);
        int maxChunkX = (int) Math.floor((x + maxDistance) / 16.0);
        int minChunkZ = (int) Math.floor((z - maxDistance) / 16.0);
        int maxChunkZ = (int) Math.floor((z + maxDistance) / 16.0);

        Map<Long, List<PropInstance>> worldChunks = chunkSpatialIndex.get(world);
        if (worldChunks == null) return result;

        double maxDistSq = maxDistance * maxDistance;

        for (int cx = minChunkX; cx <= maxChunkX; cx++) {
            for (int cz = minChunkZ; cz <= maxChunkZ; cz++) {
                List<PropInstance> chunkProps = worldChunks.get(getChunkKey(cx, cz));
                if (chunkProps != null) {
                    synchronized (chunkProps) {
                        for (PropInstance p : chunkProps) {
                            double dx = (p.getX() + 0.5) - x;
                            double dz = (p.getZ() + 0.5) - z;
                            if ((dx * dx + dz * dz) <= maxDistSq) {
                                result.add(p);
                            }
                        }
                    }
                }
            }
        }
        return result;
    }

    public void updatePlayerView(Player player) {
        if (!player.isOnline()) return;

        Location loc = player.getLocation();
        String world = loc.getWorld().getName();
        double px = loc.getX();
        double pz = loc.getZ();

        List<PropInstance> nearby = getPropsNear(world, px, pz, TRACKING_RANGE);
        Set<UUID> nearbyIds = new HashSet<>();
        for (PropInstance p : nearby) {
            nearbyIds.add(p.getInstanceId());
        }

        Set<UUID> currentlyViewing = playersViewingProps.computeIfAbsent(player.getUniqueId(), k -> ConcurrentHashMap.newKeySet());

        // Spawn newly visible
        for (PropInstance prop : nearby) {
            if (!currentlyViewing.contains(prop.getInstanceId())) {
                spawnPropForPlayer(player, prop);
                currentlyViewing.add(prop.getInstanceId());
            }
        }

        // Destroy out-of-range
        Iterator<UUID> iter = currentlyViewing.iterator();
        while (iter.hasNext()) {
            UUID propId = iter.next();
            if (!nearbyIds.contains(propId)) {
                PropInstance instance = instancesById.get(propId);
                if (instance != null) {
                    destroyPropForPlayer(player, instance);
                } else {
                    int entityId = instanceToEntityId.getOrDefault(propId, -1);
                    if (entityId != -1) {
                        sendPacket(player, new WrapperPlayServerDestroyEntities(entityId));
                    }
                }
                iter.remove();
            }
        }
    }

    public void spawnPropForPlayer(Player player, PropInstance prop) {
        int entityId = instanceToEntityId.computeIfAbsent(prop.getInstanceId(), k -> nextEntityId.incrementAndGet());
        PropDefinition def = definitions.get(prop.getPropId());

        // 1. Spawn ITEM_DISPLAY entity at anchor coordinate centered
        double spawnX = prop.getX() + 0.5;
        double spawnY = prop.getY();
        double spawnZ = prop.getZ() + 0.5;

        WrapperPlayServerSpawnEntity spawnPacket = new WrapperPlayServerSpawnEntity(
                entityId,
                Optional.of(UUID.randomUUID()),
                EntityTypes.ITEM_DISPLAY,
                new Vector3d(spawnX, spawnY, spawnZ),
                0.0f,
                prop.getYaw(),
                prop.getYaw(),
                0,
                Optional.empty()
        );
        sendPacket(player, spawnPacket);

        // 2. Set Entity Metadata (Translation, Scale, Rotation quaternion, Item display)
        List<EntityData<?>> metadata = new ArrayList<>();

        // Translation (Index 11 in MC 1.20.5+)
        float tx = 0.0f, ty = 0.0f, tz = 0.0f;
        if (def != null && def.getTranslation() != null && def.getTranslation().size() >= 3) {
            tx = def.getTranslation().get(0);
            ty = def.getTranslation().get(1);
            tz = def.getTranslation().get(2);
        }
        metadata.add(new EntityData<>(METADATA_INDEX_TRANSLATION, EntityDataTypes.VECTOR3F, new Vector3f(tx, ty, tz)));

        // Scale (Index 12 in MC 1.20.5+)
        float sx = 1.0f, sy = 1.0f, sz = 1.0f;
        if (def != null && def.getScale() != null && def.getScale().size() >= 3) {
            sx = def.getScale().get(0);
            sy = def.getScale().get(1);
            sz = def.getScale().get(2);
        }
        metadata.add(new EntityData<>(METADATA_INDEX_SCALE, EntityDataTypes.VECTOR3F, new Vector3f(sx, sy, sz)));

        // Rotation Quaternion (Rotation Left - Index 13 in MC 1.20.5+)
        Quaternion4f rotQuaternion = calculateRotationQuaternion(prop.getYaw());
        metadata.add(new EntityData<>(METADATA_INDEX_ROTATION_LEFT, EntityDataTypes.QUATERNION, rotQuaternion));

        // Display Item (Index 23 in MC 1.20.5+)
        com.github.retrooper.packetevents.protocol.item.ItemStack peItem = createPacketEventsItemStack(def, prop.getCurrentState());
        if (peItem != null) {
            metadata.add(new EntityData<>(METADATA_INDEX_ITEM_STACK, EntityDataTypes.ITEMSTACK, peItem));
        }

        // Item Display Context (Index 24 in MC 1.20.5+: byte 8 = FIXED)
        metadata.add(new EntityData<>(METADATA_INDEX_ITEM_DISPLAY_CONTEXT, EntityDataTypes.BYTE, (byte) 8));

        WrapperPlayServerEntityMetadata metaPacket = new WrapperPlayServerEntityMetadata(entityId, metadata);
        sendPacket(player, metaPacket);
    }

    public void destroyPropForPlayer(Player player, PropInstance prop) {
        int entityId = instanceToEntityId.getOrDefault(prop.getInstanceId(), -1);
        if (entityId != -1) {
            WrapperPlayServerDestroyEntities destroyPacket = new WrapperPlayServerDestroyEntities(entityId);
            sendPacket(player, destroyPacket);
        }
    }

    public void broadcastSpawn(PropInstance instance) {
        for (Player player : org.bukkit.Bukkit.getOnlinePlayers()) {
            if (player.getWorld().getName().equals(instance.getWorld())) {
                double distSq = player.getLocation().distanceSquared(new Location(player.getWorld(), instance.getX() + 0.5, instance.getY(), instance.getZ() + 0.5));
                if (distSq <= (TRACKING_RANGE * TRACKING_RANGE)) {
                    spawnPropForPlayer(player, instance);
                    Set<UUID> viewing = playersViewingProps.computeIfAbsent(player.getUniqueId(), k -> ConcurrentHashMap.newKeySet());
                    viewing.add(instance.getInstanceId());
                }
            }
        }
    }

    public void broadcastDestroy(PropInstance instance) {
        int entityId = instanceToEntityId.getOrDefault(instance.getInstanceId(), -1);
        if (entityId == -1) return;

        WrapperPlayServerDestroyEntities destroyPacket = new WrapperPlayServerDestroyEntities(entityId);
        for (Player player : org.bukkit.Bukkit.getOnlinePlayers()) {
            boolean wasViewing = false;
            Set<UUID> viewing = playersViewingProps.get(player.getUniqueId());
            if (viewing != null && viewing.remove(instance.getInstanceId())) {
                wasViewing = true;
            }
            if (player.getWorld().getName().equals(instance.getWorld())) {
                double distSq = player.getLocation().distanceSquared(new Location(player.getWorld(), instance.getX() + 0.5, instance.getY(), instance.getZ() + 0.5));
                if (distSq <= (TRACKING_RANGE * TRACKING_RANGE)) {
                    wasViewing = true;
                }
            }
            if (wasViewing) {
                sendPacket(player, destroyPacket);
            }
        }
    }

    public void onPlayerQuit(Player player) {
        playersViewingProps.remove(player.getUniqueId());
    }

    private void sendPacket(Player player, com.github.retrooper.packetevents.wrapper.PacketWrapper<?> packet) {
        try {
            PacketEvents.getAPI().getPlayerManager().sendPacket(player, packet);
        } catch (Exception e) {
            // PacketEvents might not be active in mock unit test environments
            logger.fine("Failed to send packet to " + player.getName() + ": " + e.getMessage());
        }
    }

    public void broadcastStateUpdate(PropInstance prop) {
        int entityId = instanceToEntityId.getOrDefault(prop.getInstanceId(), -1);
        if (entityId == -1) return;

        PropDefinition def = definitions.get(prop.getPropId());
        com.github.retrooper.packetevents.protocol.item.ItemStack peItem = createPacketEventsItemStack(def, prop.getCurrentState());
        if (peItem == null) return;

        List<EntityData<?>> metadata = new ArrayList<>();
        metadata.add(new EntityData<>(METADATA_INDEX_ITEM_STACK, EntityDataTypes.ITEMSTACK, peItem));
        WrapperPlayServerEntityMetadata metaPacket = new WrapperPlayServerEntityMetadata(entityId, metadata);

        try {
            for (Player player : org.bukkit.Bukkit.getOnlinePlayers()) {
                Set<UUID> viewing = playersViewingProps.get(player.getUniqueId());
                boolean isNear = player.getWorld().getName().equals(prop.getWorld()) &&
                        player.getLocation().distanceSquared(new Location(player.getWorld(), prop.getX() + 0.5, prop.getY(), prop.getZ() + 0.5)) <= (TRACKING_RANGE * TRACKING_RANGE);
                if ((viewing != null && viewing.contains(prop.getInstanceId())) || isNear) {
                    sendPacket(player, metaPacket);
                }
            }
        } catch (Throwable t) {
            logger.fine("Failed to broadcast state update: " + t.getMessage());
        }
    }

    public void applyPropLighting(PropInstance instance) {
        if (instance == null) return;
        PropDefinition def = definitions.get(instance.getPropId());
        String currentState = instance.getCurrentState();
        PropDefinition.PropState state = def != null ? def.getState(currentState) : null;
        int lightLevel = state != null ? state.getLightLevel() : 0;

        if (lightLevel <= 0) {
            removePropLighting(instance.getInstanceId());
            return;
        }

        try {
            org.bukkit.World world = org.bukkit.Bukkit.getWorld(instance.getWorld());
            if (world == null) return;

            Block baseBlock = world.getBlockAt(instance.getX(), instance.getY(), instance.getZ());
            String hitbox = (state != null && state.getHitboxType() != null)
                    ? state.getHitboxType()
                    : (def != null ? def.getHitboxType() : "solid");

            Block targetBlock;
            if ("passable".equalsIgnoreCase(hitbox) && (baseBlock.getType() == Material.AIR || baseBlock.getType() == Material.STRUCTURE_VOID || baseBlock.getType() == Material.LIGHT)) {
                targetBlock = baseBlock;
            } else {
                Block above = baseBlock.getRelative(0, 1, 0);
                if (above.getType() == Material.AIR || above.getType() == Material.LIGHT) {
                    targetBlock = above;
                } else {
                    targetBlock = baseBlock;
                }
            }

            Location oldLoc = activeLightLocations.get(instance.getInstanceId());
            if (oldLoc != null && !oldLoc.equals(targetBlock.getLocation())) {
                Block oldBlock = oldLoc.getBlock();
                if (oldBlock.getType() == Material.LIGHT) {
                    oldBlock.setType(Material.AIR);
                }
            }

            targetBlock.setType(Material.LIGHT);
            if (targetBlock.getBlockData() instanceof org.bukkit.block.data.type.Light lightData) {
                lightData.setLevel(Math.min(15, Math.max(0, lightLevel)));
                targetBlock.setBlockData(lightData);
            } else if (targetBlock.getBlockData() instanceof org.bukkit.block.data.Levelled levelled) {
                levelled.setLevel(Math.min(15, Math.max(0, lightLevel)));
                targetBlock.setBlockData(levelled);
            }
            activeLightLocations.put(instance.getInstanceId(), targetBlock.getLocation());
        } catch (Throwable t) {
            logger.fine("Failed to apply lighting for prop " + instance.getInstanceId() + ": " + t.getMessage());
        }
    }

    public void removePropLighting(UUID instanceId) {
        Location loc = activeLightLocations.remove(instanceId);
        if (loc != null) {
            try {
                org.bukkit.World world = loc.getWorld();
                if (world != null) {
                    Block b = loc.getBlock();
                    if (b.getType() == Material.LIGHT) {
                        b.setType(Material.AIR);
                    }
                }
            } catch (Throwable t) {
                logger.fine("Failed to remove lighting for prop " + instanceId + ": " + t.getMessage());
            }
        }
    }

    public void cleanupLighting() {
        for (UUID id : new ArrayList<>(activeLightLocations.keySet())) {
            removePropLighting(id);
        }
    }

    public Map<UUID, Location> getActiveLightLocations() {
        return Collections.unmodifiableMap(activeLightLocations);
    }

    public Location getActiveLightLocation(UUID instanceId) {
        return activeLightLocations.get(instanceId);
    }

    public ItemStack createDisplayItemStack(PropDefinition def) {
        return createDisplayItemStack(def, null);
    }

    public ItemStack createDisplayItemStack(PropDefinition def, String currentState) {
        String activeModel = (def != null) ? def.getBlockModelForState(currentState) : null;
        Material mat = (activeModel != null && !activeModel.isEmpty())
                ? Material.WHITE_WOOL
                : Material.PAPER;
        if (def != null && def.getDropItemId() != null && itemStorage != null) {
            com.google.gson.JsonObject dropJson = itemStorage.getItem(def.getDropItemId());
            if (dropJson != null && dropJson.has("material")) {
                Material m = Material.matchMaterial(dropJson.get("material").getAsString());
                if (m != null) {
                    mat = m;
                }
            }
        }

        ItemStack item = new ItemStack(mat);
        ItemMeta meta = item.getItemMeta();
        if (meta != null) {
            if (def != null && def.getDisplayName() != null) {
                meta.setDisplayName(def.getDisplayName());
            }
            if (activeModel != null && !activeModel.isEmpty()) {
                com.mcp.agent.adapters.Paper121ItemAdapter.applyItemModel(meta, activeModel);
            }
            item.setItemMeta(meta);
        }
        return item;
    }

    public com.github.retrooper.packetevents.protocol.item.ItemStack createPacketEventsItemStack(PropDefinition def, String currentState) {
        ItemStack displayItem = createDisplayItemStack(def, currentState);
        if (displayItem == null) return null;

        com.github.retrooper.packetevents.protocol.item.ItemStack peItem =
                SpigotConversionUtil.fromBukkitItemStack(displayItem);

        String activeModel = (def != null) ? def.getBlockModelForState(currentState) : null;
        if (activeModel != null && !activeModel.isEmpty()) {
            String model = activeModel.trim().toLowerCase();
            String ns = "minecraft";
            String path = model;
            if (model.contains(":")) {
                String[] parts = model.split(":", 2);
                ns = parts[0];
                path = parts[1];
            }
            try {
                peItem.setComponent(
                        com.github.retrooper.packetevents.protocol.component.ComponentTypes.ITEM_MODEL,
                        new com.github.retrooper.packetevents.protocol.component.builtin.item.ItemModel(
                                new com.github.retrooper.packetevents.resources.ResourceLocation(ns, path)
                        )
                );
            } catch (Throwable t) {
                logger.warning("Failed to set PacketEvents ITEM_MODEL: " + t.getMessage());
            }
        }
        return peItem;
    }

    public static Quaternion4f calculateRotationQuaternion(float yaw) {
        float normalizedYaw = normalizeToCardinalYaw(yaw);
        double rad = Math.toRadians(normalizedYaw);
        float y = (float) Math.sin(rad / 2.0);
        float w = (float) Math.cos(rad / 2.0);
        return new Quaternion4f(0.0f, y, 0.0f, w);
    }

    public static float normalizeToCardinalYaw(float yaw) {
        float normalized = (yaw % 360.0f + 360.0f) % 360.0f;
        if (normalized >= 45.0f && normalized < 135.0f) {
            return 90.0f; // WEST
        } else if (normalized >= 135.0f && normalized < 225.0f) {
            return 180.0f; // NORTH
        } else if (normalized >= 225.0f && normalized < 315.0f) {
            return 270.0f; // EAST
        } else {
            return 0.0f; // SOUTH
        }
    }

    public static int[] rotateOffset(int dx, int dy, int dz, float yaw) {
        float normalizedYaw = normalizeToCardinalYaw(yaw);
        int cardinal = Math.round(normalizedYaw);
        return switch (cardinal) {
            case 90 -> new int[]{dz, dy, -dx};
            case 180 -> new int[]{-dx, dy, -dz};
            case 270 -> new int[]{-dz, dy, dx};
            default -> new int[]{dx, dy, dz};
        };
    }

    public static int[] rotateOffset(int[] offset, float yaw) {
        if (offset == null || offset.length < 3) {
            return new int[]{0, 0, 0};
        }
        return rotateOffset(offset[0], offset[1], offset[2], yaw);
    }

    public static List<int[]> getRotatedOffsets(PropDefinition def, float yaw) {
        List<int[]> result = new ArrayList<>();
        if (def == null || def.getHitboxOffsets() == null || def.getHitboxOffsets().isEmpty()) {
            result.add(new int[]{0, 0, 0});
            return result;
        }
        for (int[] offset : def.getHitboxOffsets()) {
            result.add(rotateOffset(offset, yaw));
        }
        return result;
    }

    public static long getChunkKey(int chunkX, int chunkZ) {
        return (((long) chunkX) << 32) | (((long) chunkZ) & 0xFFFFFFFFL);
    }
}
