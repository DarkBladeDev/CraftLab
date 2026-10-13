package com.mcp.agent.placeholders;

import org.bukkit.OfflinePlayer;

public interface PlaceholderProvider {
    /**
     * Returns the domain key handled by this provider (e.g. "glyph", "prop", "item").
     */
    String getKey();

    /**
     * Resolves a placeholder request for the given player and domain-specific parameters.
     *
     * @param player The target player context (may be null)
     * @param params The sub-parameters following "<domainKey>_"
     * @return The resolved string, or null if the placeholder cannot be resolved
     */
    String resolve(OfflinePlayer player, String params);
}
