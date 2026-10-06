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

import java.util.List;
import java.util.UUID;
import java.util.logging.Logger;

public class PropPlaceBreakListener implements Listener {
    public static final NamespacedKey PROP_ID_KEY = new NamespacedKey("mcp", "prop_id");

    private final Plugin plugin;
    private final PropManager propManager;
    private final Logger logger;

    public PropPlaceBreakListener(Plugin plugin, PropManager propManager, Logger logger) {
        this.plugin = plugin;
        this.propManager = propManager;
        this.logger = logger;
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
        Block targetBlock = clickedBlock.getRelative(face);

        if (!targetBlock.getType().isAir() && targetBlock.getType() != Material.STRUCTURE_VOID) {
            return;
        }

        event.setCancelled(true);

        // 1. Calculate cardinal facing (0, 90, 180, 270)
        float cardinalYaw = PropManager.normalizeToCardinalYaw(player.getLocation().getYaw());

        // 2. Place barrier collision block
        targetBlock.setType(Material.BARRIER);

        // 3. Register placed prop instance
        UUID instanceId = UUID.randomUUID();
        PropInstance instance = new PropInstance(
                instanceId,
                propDef.getId(),
                targetBlock.getWorld().getName(),
                targetBlock.getX(),
                targetBlock.getY(),
                targetBlock.getZ(),
                cardinalYaw,
                System.currentTimeMillis()
        );

        propManager.registerPlacedProp(instance);
        propManager.broadcastSpawn(instance);

        // 4. Play placement sound and deduct item
        targetBlock.getWorld().playSound(targetBlock.getLocation().add(0.5, 0.5, 0.5), Sound.BLOCK_WOOD_PLACE, 1.0f, 1.0f);

        if (player.getGameMode() != GameMode.CREATIVE) {
            item.setAmount(item.getAmount() - 1);
        }

        logger.info("Placed prop " + propDef.getId() + " at " + targetBlock.getLocation() + " with yaw " + cardinalYaw);
    }

    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true)
    public void onBlockBreak(BlockBreakEvent event) {
        Block block = event.getBlock();
        if (block.getType() != Material.BARRIER) return;

        String worldName = block.getWorld().getName();
        PropInstance instance = propManager.getInstanceAt(worldName, block.getX(), block.getY(), block.getZ());
        if (instance == null) return;

        // Cancel default barrier breaking
        event.setCancelled(true);
        block.setType(Material.AIR);

        PropDefinition def = propManager.getDefinition(instance.getPropId());

        // Remove from manager and disk
        propManager.removePlacedProp(instance.getInstanceId());
        propManager.broadcastDestroy(instance);

        // Break particles and sound
        Location center = block.getLocation().add(0.5, 0.5, 0.5);
        block.getWorld().playSound(center, Sound.BLOCK_WOOD_BREAK, 1.0f, 1.0f);
        try {
            block.getWorld().spawnParticle(Particle.BLOCK, center, 15, 0.3, 0.3, 0.3, Material.OAK_PLANKS.createBlockData());
        } catch (Exception ignored) {
        }

        // Drop item
        if (event.getPlayer().getGameMode() != GameMode.CREATIVE) {
            ItemStack dropStack = createPropItemStack(def, instance.getPropId());
            block.getWorld().dropItemNaturally(center, dropStack);
        }

        logger.info("Destroyed prop " + instance.getPropId() + " at " + center);
    }

    public static ItemStack createPropItemStack(PropDefinition def, String propId) {
        ItemStack item = new ItemStack(Material.PAPER);
        ItemMeta meta = item.getItemMeta();
        if (meta != null) {
            String name = (def != null && def.getDisplayName() != null) ? def.getDisplayName() : propId;
            meta.setDisplayName(name);
            meta.getPersistentDataContainer().set(PROP_ID_KEY, PersistentDataType.STRING, propId);
            item.setItemMeta(meta);
        }
        return item;
    }
}
