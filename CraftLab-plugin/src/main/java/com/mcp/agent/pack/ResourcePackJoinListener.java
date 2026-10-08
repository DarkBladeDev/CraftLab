package com.mcp.agent.pack;

import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;

public class ResourcePackJoinListener implements Listener {
    private final ResourcePackManager packManager;

    public ResourcePackJoinListener(ResourcePackManager packManager) {
        this.packManager = packManager;
    }

    @EventHandler(priority = EventPriority.NORMAL)
    public void onPlayerJoin(PlayerJoinEvent event) {
        if (packManager != null && packManager.hasActivePack()) {
            packManager.applyToPlayer(event.getPlayer());
        }
    }
}
