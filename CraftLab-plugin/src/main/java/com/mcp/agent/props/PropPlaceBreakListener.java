package com.mcp.agent.props;

import org.bukkit.*;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.Action;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataContainer;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;

import com.google.gson.JsonObject;
import com.mcp.agent.adapters.ItemAdapter;
import com.mcp.agent.adapters.Paper121ItemAdapter;
import com.mcp.agent.storage.ItemStorage;
import java.util.List;
import java.util.UUID;
import java.util.logging.Logger;

public class PropPlaceBreakListener implements Listener {
    public static final NamespacedKey PROP_ID_KEY = NamespacedKey.fromString("mcp:prop_id");

    private final Plugin plugin;
    private final PropManager propManager;
    private final ItemStorage itemStorage;
    private final ItemAdapter itemAdapter;
    private final Logger logger;

    public PropPlaceBreakListener(Plugin plugin, PropManager propManager, Logger logger) {
        this(plugin, propManager, null, null, logger);
    }

    public PropPlaceBreakListener(Plugin plugin, PropManager propManager, ItemStorage itemStorage, ItemAdapter itemAdapter, Logger logger) {
        this.plugin = plugin;
        this.propManager = propManager;
        this.itemStorage = itemStorage;
        this.itemAdapter = itemAdapter;
        this.logger = logger;
    }

    public static boolean isClearForPlacement(Block block) {
        if (block == null) return false;
        try {
            if (block.isReplaceable()) return true;
        } catch (Throwable ignored) {
        }
        Material type = block.getType();
        if (type == null) return false;
        return type == Material.AIR || type == Material.CAVE_AIR || type == Material.VOID_AIR || type == Material.STRUCTURE_VOID || type == Material.LIGHT;
    }

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onPlayerPlaceProp(PlayerInteractEvent event) {
        if (event.getAction() != Action.RIGHT_CLICK_BLOCK) return;
        if (event.getHand() != EquipmentSlot.HAND) return;

        Block clickedBlock = event.getClickedBlock();
        if (clickedBlock == null) return;

        ItemStack item = event.getItem();
        if (item == null || !item.hasItemMeta()) return;

        ItemMeta meta = item.getItemMeta();
        PersistentDataContainer pdc = meta.getPersistentDataContainer();
        String propId = pdc.get(PROP_ID_KEY, PersistentDataType.STRING);

        // Fallback: Check if item display name or type matches a registered prop definition
        if (propId == null && meta.hasDisplayName()) {
            for (PropDefinition def : propManager.getDefinitions().values()) {
                if (meta.getDisplayName().contains(def.getId()) || meta.getDisplayName().equals(def.getDisplayName())) {
                    propId = def.getId();
                    break;
                }
            }
        }

        if (propId == null) return;

        PropDefinition propDef = propManager.getDefinition(propId);
        if (propDef == null) return;

        Player player = event.getPlayer();
        BlockFace face = event.getBlockFace();
        Block anchorBlock = clickedBlock.getRelative(face);

        // 1. Calculate cardinal facing (0, 90, 180, 270)
        float cardinalYaw = PropManager.normalizeToCardinalYaw(player.getLocation().getYaw());

        // 2. Pre-placement clearance check across all rotated hitbox offsets
        List<int[]> offsets = PropManager.getRotatedOffsets(propDef, cardinalYaw);
        for (int[] off : offsets) {
            Block target = anchorBlock.getRelative(off[0], off[1], off[2]);
            if (!isClearForPlacement(target)) {
                event.setCancelled(true);
                player.sendMessage(net.kyori.adventure.text.Component.text("Cannot place prop here: area is obstructed.", net.kyori.adventure.text.format.NamedTextColor.RED));
                return;
            }
        }

        event.setCancelled(true);

        // 3. Place collision blocks (BARRIER for solid or STRUCTURE_VOID for passable) across all rotated offsets
        String initialHitbox = propDef.getHitboxType();
        PropDefinition.PropState defState = propDef.getState(propDef.getDefaultState());
        if (defState != null && defState.getHitboxType() != null) {
            initialHitbox = defState.getHitboxType();
        }
        Material collisionMat = "passable".equalsIgnoreCase(initialHitbox)
                ? Material.STRUCTURE_VOID
                : Material.BARRIER;
        for (int[] off : offsets) {
            Block target = anchorBlock.getRelative(off[0], off[1], off[2]);
            target.setType(collisionMat);
        }

        // 4. Register placed prop instance
        UUID instanceId = UUID.randomUUID();
        PropInstance instance = new PropInstance(
                instanceId,
                propDef.getId(),
                anchorBlock.getWorld().getName(),
                anchorBlock.getX(),
                anchorBlock.getY(),
                anchorBlock.getZ(),
                cardinalYaw,
                System.currentTimeMillis(),
                propDef.getDefaultState()
        );

        propManager.registerPlacedProp(instance);
        propManager.broadcastSpawn(instance);

        // 5. Play placement sound and deduct item
        anchorBlock.getWorld().playSound(anchorBlock.getLocation().add(0.5, 0.5, 0.5), Sound.BLOCK_WOOD_PLACE, 1.0f, 1.0f);

        if (player.getGameMode() != GameMode.CREATIVE) {
            item.setAmount(item.getAmount() - 1);
        }

        logger.info("Placed prop " + propDef.getId() + " at " + anchorBlock.getLocation() + " with yaw " + cardinalYaw);
    }

    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true)
    public void onBlockBreak(BlockBreakEvent event) {
        Block block = event.getBlock();
        if (block.getType() == Material.LIGHT) {
            for (java.util.Map.Entry<UUID, Location> entry : propManager.getActiveLightLocations().entrySet()) {
                if (entry.getValue().equals(block.getLocation())) {
                    event.setCancelled(true);
                    return;
                }
            }
        }
        if (block.getType() != Material.BARRIER && block.getType() != Material.STRUCTURE_VOID) return;

        String worldName = block.getWorld().getName();
        PropInstance instance = propManager.getInstanceAt(worldName, block.getX(), block.getY(), block.getZ());
        if (instance == null) return;

        // Cancel default block breaking
        event.setCancelled(true);

        PropDefinition def = propManager.getDefinition(instance.getPropId());

        // 1. Broadcast destroy packet FIRST before removing entity ID mapping from memory
        propManager.broadcastDestroy(instance);

        // 2. Clean up active light block
        propManager.removePropLighting(instance.getInstanceId());

        // 3. Revert all occupied collision blocks across the rotated footprint to AIR
        World world = block.getWorld();
        List<int[]> occupiedBlocks = propManager.getOccupiedBlocks(instance);
        for (int[] coords : occupiedBlocks) {
            Block b = world.getBlockAt(coords[0], coords[1], coords[2]);
            if (b.getType() == Material.BARRIER || b.getType() == Material.STRUCTURE_VOID) {
                b.setType(Material.AIR);
            }
        }

        // 4. Remove instance from manager and disk
        propManager.removePlacedProp(instance.getInstanceId());

        // 4. Break particles and sound
        Location center = new Location(world, instance.getX() + 0.5, instance.getY() + 0.5, instance.getZ() + 0.5);
        world.playSound(center, Sound.BLOCK_WOOD_BREAK, 1.0f, 1.0f);
        try {
            world.spawnParticle(Particle.BLOCK, center, 15, 0.3, 0.3, 0.3, Material.OAK_PLANKS.createBlockData());
        } catch (Exception ignored) {
        }

        // 5. Drop item
        if (event.getPlayer().getGameMode() != GameMode.CREATIVE) {
            ItemStack dropStack = createPropItemStack(def, instance.getPropId(), itemStorage, itemAdapter);
            world.dropItemNaturally(center, dropStack);
        }

        logger.info("Destroyed prop " + instance.getPropId() + " at " + center);
    }

    public static ItemStack createPropItemStack(PropDefinition def, String propId, ItemStorage storage, ItemAdapter adapter) {
        if (def != null && def.getDropItemId() != null && !def.getDropItemId().isEmpty() && storage != null && adapter != null) {
            JsonObject dropJson = storage.getItem(def.getDropItemId());
            if (dropJson != null) {
                ItemStack stack = adapter.compile(dropJson);
                ItemMeta meta = stack.getItemMeta();
                if (meta != null) {
                    meta.getPersistentDataContainer().set(PROP_ID_KEY, PersistentDataType.STRING, propId);
                    stack.setItemMeta(meta);
                }
                return stack;
            }
        }

        String activeItemModel = null;
        if (def != null) {
            if (def.getItemModel() != null && !def.getItemModel().trim().isEmpty()) {
                activeItemModel = def.getItemModel().trim();
            } else if (def.getBlockModel() != null && !def.getBlockModel().trim().isEmpty()) {
                activeItemModel = def.getBlockModel().trim();
            }
        }

        Material mat = (activeItemModel != null && !activeItemModel.isEmpty())
                ? Material.WHITE_WOOL
                : Material.PAPER;
        ItemStack item = new ItemStack(mat);
        ItemMeta meta = item.getItemMeta();
        if (meta != null) {
            String name = (def != null && def.getDisplayName() != null) ? def.getDisplayName() : propId;
            meta.setDisplayName(name);
            meta.getPersistentDataContainer().set(PROP_ID_KEY, PersistentDataType.STRING, propId);
            if (activeItemModel != null && !activeItemModel.isEmpty()) {
                Paper121ItemAdapter.applyItemModel(meta, activeItemModel);
            }
            item.setItemMeta(meta);
        }
        return item;
    }

    public static ItemStack createPropItemStack(PropDefinition def, String propId) {
        return createPropItemStack(def, propId, null, null);
    }
}
