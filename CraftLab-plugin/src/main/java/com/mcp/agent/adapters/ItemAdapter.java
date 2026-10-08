package com.mcp.agent.adapters;

import com.google.gson.JsonObject;
import org.bukkit.inventory.ItemStack;

public interface ItemAdapter {
    /**
     * Translates canonical JSON item definition into a Bukkit/Paper ItemStack.
     */
    ItemStack compile(JsonObject itemJson);

    /**
     * Indicates whether this adapter supports the running server version.
     */
    boolean supports(String minecraftVersion);
}
