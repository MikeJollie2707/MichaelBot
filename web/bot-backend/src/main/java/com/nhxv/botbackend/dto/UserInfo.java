package com.nhxv.botbackend.dto;

import java.util.List;

public class UserInfo {
	private String id, displayName, email, guilds;
	private List<String> roles;

	public UserInfo(String id, String displayName, String email, List<String> roles, String guilds) {
		this.id = id;
		this.displayName = displayName;
		this.email = email;
		this.roles = roles;
		this.guilds = guilds;
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

	public String getEmail() {
		return email;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public List<String> getRoles() {
		return roles;
	}

	public void setRoles(List<String> roles) {
		this.roles = roles;
	}

	public String getGuilds() {
		return guilds;
	}

	public void setGuilds(String guilds) {
		this.guilds = guilds;
	}

	@Override
	public String toString() {
		return "UserInfo{" +
				"id='" + id + '\'' +
				", displayName='" + displayName + '\'' +
				", email='" + email + '\'' +
				", guilds='" + guilds + '\'' +
				", roles=" + roles +
				'}';
	}
}
