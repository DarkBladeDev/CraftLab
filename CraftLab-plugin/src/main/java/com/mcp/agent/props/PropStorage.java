package com.mcp.agent.props;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import java.io.File;
import java.lang.reflect.Type;
import java.sql.*;
import java.util.*;
import java.util.logging.Level;
import java.util.logging.Logger;

public class PropStorage {
    private final String dbUrl;
    private final Logger logger;
    private final Gson gson = new Gson();
    private static final Type INT_ARRAY_LIST_TYPE = new TypeToken<List<int[]>>() {}.getType();
    private static final Type FLOAT_LIST_TYPE = new TypeToken<List<Float>>() {}.getType();

    public PropStorage(File dataFolder, Logger logger) {
        this.logger = logger;
        if (!dataFolder.exists()) {
            dataFolder.mkdirs();
        }
        File dbFile = new File(dataFolder, "props.db");
        this.dbUrl = "jdbc:sqlite:" + dbFile.getAbsolutePath();
        initDatabase();
    }

    public PropStorage(String customDbUrl, Logger logger) {
        this.logger = logger;
        this.dbUrl = customDbUrl;
        initDatabase();
    }

    private Connection getConnection() throws SQLException {
        return DriverManager.getConnection(dbUrl);
    }

    public void initDatabase() {
        try (Connection conn = getConnection(); Statement stmt = conn.createStatement()) {
            stmt.execute("CREATE TABLE IF NOT EXISTS prop_definitions (" +
                    "id TEXT PRIMARY KEY, " +
                    "display_name TEXT NOT NULL, " +
                    "mode TEXT NOT NULL, " +
                    "item_model TEXT, " +
                    "block_model TEXT, " +
                    "scale_json TEXT NOT NULL, " +
                    "translation_json TEXT NOT NULL, " +
                    "hitbox_type TEXT NOT NULL, " +
                    "hitbox_offsets_json TEXT NOT NULL, " +
                    "interaction_type TEXT, " +
                    "seat_height REAL NOT NULL, " +
                    "hardness REAL NOT NULL, " +
                    "tool_type TEXT NOT NULL, " +
                    "drop_item_id TEXT" +
                    ")");

            // Migration checks for existing databases
            try {
                stmt.execute("ALTER TABLE prop_definitions ADD COLUMN block_model TEXT");
            } catch (SQLException ignored) {
            }
            try {
                stmt.execute("ALTER TABLE prop_definitions ADD COLUMN seat_height REAL DEFAULT 0.5");
            } catch (SQLException ignored) {
            }

            stmt.execute("CREATE TABLE IF NOT EXISTS placed_props (" +
                    "instance_id TEXT PRIMARY KEY, " +
                    "prop_id TEXT NOT NULL, " +
                    "world TEXT NOT NULL, " +
                    "x INTEGER NOT NULL, " +
                    "y INTEGER NOT NULL, " +
                    "z INTEGER NOT NULL, " +
                    "yaw REAL NOT NULL, " +
                    "placed_at INTEGER NOT NULL" +
                    ")");

            stmt.execute("CREATE INDEX IF NOT EXISTS idx_placed_props_coords ON placed_props (world, x, y, z)");
        } catch (SQLException e) {
            logger.log(Level.SEVERE, "Failed to initialize props database: " + e.getMessage(), e);
        }
    }

    public synchronized void saveDefinition(PropDefinition def) {
        String sql = "INSERT OR REPLACE INTO prop_definitions (id, display_name, mode, item_model, block_model, " +
                "scale_json, translation_json, hitbox_type, hitbox_offsets_json, interaction_type, " +
                "seat_height, hardness, tool_type, drop_item_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
        try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, def.getId());
            ps.setString(2, def.getDisplayName());
            ps.setString(3, def.getMode());
            ps.setString(4, def.getItemModel());
            ps.setString(5, def.getBlockModel());
            ps.setString(6, gson.toJson(def.getScale()));
            ps.setString(7, gson.toJson(def.getTranslation()));
            ps.setString(8, def.getHitboxType());
            ps.setString(9, gson.toJson(def.getHitboxOffsets()));
            ps.setString(10, def.getInteractionType());
            ps.setFloat(11, def.getSeatHeight());
            ps.setFloat(12, def.getHardness());
            ps.setString(13, def.getToolType());
            ps.setString(14, def.getDropItemId());
            ps.executeUpdate();
        } catch (SQLException e) {
            logger.log(Level.SEVERE, "Failed to save prop definition: " + def.getId(), e);
        }
    }

    public PropDefinition getDefinition(String id) {
        String sql = "SELECT * FROM prop_definitions WHERE id = ?";
        try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    return mapDefinition(rs);
                }
            }
        } catch (SQLException e) {
            logger.log(Level.SEVERE, "Failed to get prop definition: " + id, e);
        }
        return null;
    }

    public Map<String, PropDefinition> getAllDefinitions() {
        Map<String, PropDefinition> map = new HashMap<>();
        String sql = "SELECT * FROM prop_definitions";
        try (Connection conn = getConnection(); Statement stmt = conn.createStatement(); ResultSet rs = stmt.executeQuery(sql)) {
            while (rs.next()) {
                PropDefinition def = mapDefinition(rs);
                map.put(def.getId(), def);
            }
        } catch (SQLException e) {
            logger.log(Level.SEVERE, "Failed to get all prop definitions", e);
        }
        return map;
    }

    private PropDefinition mapDefinition(ResultSet rs) throws SQLException {
        PropDefinition def = new PropDefinition();
        def.setId(rs.getString("id"));
        def.setDisplayName(rs.getString("display_name"));
        def.setMode(rs.getString("mode"));
        def.setItemModel(rs.getString("item_model"));
        try {
            def.setBlockModel(rs.getString("block_model"));
        } catch (SQLException ignored) {
        }
        def.setScale(gson.fromJson(rs.getString("scale_json"), FLOAT_LIST_TYPE));
        def.setTranslation(gson.fromJson(rs.getString("translation_json"), FLOAT_LIST_TYPE));
        def.setHitboxType(rs.getString("hitbox_type"));
        def.setHitboxOffsets(gson.fromJson(rs.getString("hitbox_offsets_json"), INT_ARRAY_LIST_TYPE));
        def.setInteractionType(rs.getString("interaction_type"));
        def.setSeatHeight(rs.getFloat("seat_height"));
        def.setHardness(rs.getFloat("hardness"));
        def.setToolType(rs.getString("tool_type"));
        def.setDropItemId(rs.getString("drop_item_id"));
        return def;
    }

    public synchronized void saveInstance(PropInstance instance) {
        String sql = "INSERT OR REPLACE INTO placed_props (instance_id, prop_id, world, x, y, z, yaw, placed_at) " +
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)";
        try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, instance.getInstanceId().toString());
            ps.setString(2, instance.getPropId());
            ps.setString(3, instance.getWorld());
            ps.setInt(4, instance.getX());
            ps.setInt(5, instance.getY());
            ps.setInt(6, instance.getZ());
            ps.setFloat(7, instance.getYaw());
            ps.setLong(8, instance.getPlacedAt());
            ps.executeUpdate();
        } catch (SQLException e) {
            logger.log(Level.SEVERE, "Failed to save prop instance: " + instance.getInstanceId(), e);
        }
    }

    public synchronized void removeInstance(UUID instanceId) {
        String sql = "DELETE FROM placed_props WHERE instance_id = ?";
        try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, instanceId.toString());
            ps.executeUpdate();
        } catch (SQLException e) {
            logger.log(Level.SEVERE, "Failed to remove prop instance: " + instanceId, e);
        }
    }

    public List<PropInstance> getAllInstances() {
        List<PropInstance> list = new ArrayList<>();
        String sql = "SELECT * FROM placed_props";
        try (Connection conn = getConnection(); Statement stmt = conn.createStatement(); ResultSet rs = stmt.executeQuery(sql)) {
            while (rs.next()) {
                list.add(mapInstance(rs));
            }
        } catch (SQLException e) {
            logger.log(Level.SEVERE, "Failed to get all placed props", e);
        }
        return list;
    }

    public PropInstance getInstanceAt(String world, int x, int y, int z) {
        String sql = "SELECT * FROM placed_props WHERE world = ? AND x = ? AND y = ? AND z = ?";
        try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, world);
            ps.setInt(2, x);
            ps.setInt(3, y);
            ps.setInt(4, z);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    return mapInstance(rs);
                }
            }
        } catch (SQLException e) {
            logger.log(Level.SEVERE, "Failed to get prop instance at coordinates", e);
        }
        return null;
    }

    private PropInstance mapInstance(ResultSet rs) throws SQLException {
        return new PropInstance(
                UUID.fromString(rs.getString("instance_id")),
                rs.getString("prop_id"),
                rs.getString("world"),
                rs.getInt("x"),
                rs.getInt("y"),
                rs.getInt("z"),
                rs.getFloat("yaw"),
                rs.getLong("placed_at")
        );
    }
}
