package com.nhxv.botbackend.dto;

public class Guild {
    private String id, name, icon, permissions;
    private boolean isOwner;

    public Guild() {}

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getIcon() {
        return icon;
    }

    public void setIcon(String icon) {
        this.icon = icon;
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
        if ((Long.parseLong(permissions) & 0x20) == 0x20) {
            this.permissions = "MANAGE_GUILD";
        } else if ((Long.parseLong(permissions) & 0x8) == 0x8) {
            this.permissions = "ADMINISTRATOR";
        } else {
            this.permissions = "";
        }
    }

    @Override
    public String toString() {
        return "Guild{" +
                "id='" + id + '\'' +
                ", name='" + name + '\'' +
                ", icon='" + icon + '\'' +
                ", isOwner=" + isOwner +
                ", permissions='" + permissions + '\'' +
                '}';
    }
}
