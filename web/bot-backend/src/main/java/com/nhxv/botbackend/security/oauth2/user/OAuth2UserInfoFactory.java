package com.nhxv.botbackend.security.oauth2.user;

import com.nhxv.botbackend.dto.SocialProvider;
import com.nhxv.botbackend.exception.OAuth2AuthenticationProcessingException;

import java.util.Map;

public class OAuth2UserInfoFactory {
	public static OAuth2UserInfo getOAuth2UserInfo(String registrationId, Map<String, Object> attributes) {
		if (registrationId.equalsIgnoreCase(SocialProvider.GOOGLE.getProviderType())) {
			return new GoogleOAuth2UserInfo(attributes);
		} else if (registrationId.equalsIgnoreCase(SocialProvider.FACEBOOK.getProviderType())) {
			return new FacebookOAuth2UserInfo(attributes);
		} else if (registrationId.equalsIgnoreCase(SocialProvider.GITHUB.getProviderType())) {
			return new GithubOAuth2UserInfo(attributes);
		} else if (registrationId.equalsIgnoreCase(SocialProvider.LINKEDIN.getProviderType())) {
			return new LinkedinOAuth2UserInfo(attributes);
		} else if (registrationId.equalsIgnoreCase(SocialProvider.DISCORD.getProviderType())) {
			return new DiscordOAuth2UserInfo(attributes);
		} else {
			throw new OAuth2AuthenticationProcessingException("Sorry! Login with " + registrationId + " is not supported yet.");
		}
	}
}
