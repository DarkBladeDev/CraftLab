package com.mcp.agent.props;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class PropDefinition {
    private String id;
    private String displayName;
    private String mode = "display_prop";
    private String itemModel;
    private List<Float> scale = Arrays.asList(1.0f, 1.0f, 1.0f);
    private List<Float> translation = Arrays.asList(0.0f, 0.0f, 0.0f);
    private String hitboxType = "solid";
    private List<int[]> hitboxOffsets = new ArrayList<>();
    private String interactionType = "none";
    private float seatHeight = 0.5f;
    private float hardness = 1.0f;
    private String toolType = "AXE";
    private String dropItemId;

    public PropDefinition() {
        hitboxOffsets.add(new int[]{0, 0, 0});
    }

    public PropDefinition(String id, String displayName, String itemModel) {
        this();
        this.id = id;
        this.displayName = displayName;
        this.itemModel = itemModel;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) {
        this.displayName = displayName;
    }

    public String getMode() {
        return mode;
    }

    public void setMode(String mode) {
        this.mode = mode;
    }

    public String getItemModel() {
        return itemModel;
    }

    public void setItemModel(String itemModel) {
        this.itemModel = itemModel;
    }

    public List<Float> getScale() {
        return scale;
    }

    public void setScale(List<Float> scale) {
        this.scale = scale;
    }

    public List<Float> getTranslation() {
        return translation;
    }

    public void setTranslation(List<Float> translation) {
        this.translation = translation;
    }

    public String getHitboxType() {
        return hitboxType;
    }

    public void setHitboxType(String hitboxType) {
        this.hitboxType = hitboxType;
    }

    public List<int[]> getHitboxOffsets() {
        return hitboxOffsets;
    }

    public void setHitboxOffsets(List<int[]> hitboxOffsets) {
        this.hitboxOffsets = hitboxOffsets;
    }

    public String getInteractionType() {
        return interactionType;
    }

    public void setInteractionType(String interactionType) {
        this.interactionType = interactionType;
    }

    public float getSeatHeight() {
        return seatHeight;
    }

    public void setSeatHeight(float seatHeight) {
        this.seatHeight = seatHeight;
    }

    public float getHardness() {
        return hardness;
    }

    public void setHardness(float hardness) {
        this.hardness = hardness;
    }

    public String getToolType() {
        return toolType;
    }

    public void setToolType(String toolType) {
        this.toolType = toolType;
    }

    public String getDropItemId() {
        return dropItemId;
    }

    public void setDropItemId(String dropItemId) {
        this.dropItemId = dropItemId;
    }

    public static PropDefinition fromJson(com.google.gson.JsonObject obj) {
        PropDefinition def = new PropDefinition();
        if (obj.has("id")) def.setId(obj.get("id").getAsString());
        if (obj.has("display_name")) def.setDisplayName(obj.get("display_name").getAsString());
        else if (obj.has("displayName")) def.setDisplayName(obj.get("displayName").getAsString());

        if (obj.has("mode")) def.setMode(obj.get("mode").getAsString());
        if (obj.has("item_model") && !obj.get("item_model").isJsonNull()) def.setItemModel(obj.get("item_model").getAsString());
        else if (obj.has("itemModel") && !obj.get("itemModel").isJsonNull()) def.setItemModel(obj.get("itemModel").getAsString());

        Gson gson = new Gson();
        if (obj.has("scale") && obj.get("scale").isJsonArray()) {
            List<Float> scale = gson.fromJson(obj.get("scale"), new TypeToken<List<Float>>(){}.getType());
            def.setScale(scale);
        }
        if (obj.has("translation") && obj.get("translation").isJsonArray()) {
            List<Float> translation = gson.fromJson(obj.get("translation"), new TypeToken<List<Float>>(){}.getType());
            def.setTranslation(translation);
        }
        if (obj.has("hitbox_type")) def.setHitboxType(obj.get("hitbox_type").getAsString());
        else if (obj.has("hitboxType")) def.setHitboxType(obj.get("hitboxType").getAsString());

        if (obj.has("hitbox_offsets") && obj.get("hitbox_offsets").isJsonArray()) {
            List<int[]> offsets = gson.fromJson(obj.get("hitbox_offsets"), new TypeToken<List<int[]>>(){}.getType());
            def.setHitboxOffsets(offsets);
        } else if (obj.has("hitboxOffsets") && obj.get("hitboxOffsets").isJsonArray()) {
            List<int[]> offsets = gson.fromJson(obj.get("hitboxOffsets"), new TypeToken<List<int[]>>(){}.getType());
            def.setHitboxOffsets(offsets);
        }

        if (obj.has("interaction_type") && !obj.get("interaction_type").isJsonNull()) def.setInteractionType(obj.get("interaction_type").getAsString());
        else if (obj.has("interactionType") && !obj.get("interactionType").isJsonNull()) def.setInteractionType(obj.get("interactionType").getAsString());

        if (obj.has("seat_height")) def.setSeatHeight(obj.get("seat_height").getAsFloat());
        else if (obj.has("seatHeight")) def.setSeatHeight(obj.get("seatHeight").getAsFloat());

        if (obj.has("hardness")) def.setHardness(obj.get("hardness").getAsFloat());

        if (obj.has("tool_type")) def.setToolType(obj.get("tool_type").getAsString());
        else if (obj.has("toolType")) def.setToolType(obj.get("toolType").getAsString());

        if (obj.has("drop_item_id") && !obj.get("drop_item_id").isJsonNull()) def.setDropItemId(obj.get("drop_item_id").getAsString());
        else if (obj.has("dropItemId") && !obj.get("dropItemId").isJsonNull()) def.setDropItemId(obj.get("dropItemId").getAsString());

        return def;
    }
}
