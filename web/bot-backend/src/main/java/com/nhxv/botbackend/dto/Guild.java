package com.nhxv.botbackend.dto;

import java.util.List;

public class Guild {
    private String id;
    private String name;
    private String icon;
    private List<String> features;
    private boolean isOwner;
    private String permissions;
    private String permissionsNew;

    public Guild() {}

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getId() {
        return id;
    }

    public String getIcon() {
        return icon;
    }

    public void setIcon(String icon) {
        this.icon = icon;
    }

    public List<String> getFeatures() {
        return features;
    }

    public void setFeatures(List<String> features) {
        this.features = features;
    }

    public boolean isOwner() {
        return isOwner;
    }

    public void setOwner(boolean owner) {
        isOwner = owner;
    }

    public String getPermissions() {
        return permissions;
    }

    public void setPermissions(String permissions) {
        this.permissions = permissions;
    }

    public String getPermissionsNew() {
        return permissionsNew;
    }

    public void setPermissionsNew(String permissionsNew) {
        this.permissionsNew = permissionsNew;
    }

    @Override
    public String toString() {
        return "Guild{" +
                "id='" + id + '\'' +
                ", name='" + name + '\'' +
                ", icon='" + icon + '\'' +
                ", features=" + features +
                ", isOwner=" + isOwner +
                ", permissions='" + permissions + '\'' +
                ", permissionsNew='" + permissionsNew + '\'' +
                '}';
    }
}
