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
}
