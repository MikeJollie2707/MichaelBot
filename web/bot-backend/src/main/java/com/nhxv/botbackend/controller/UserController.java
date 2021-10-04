package com.nhxv.botbackend.controller;

import com.nhxv.botbackend.config.CurrentUser;
import com.nhxv.botbackend.dto.LocalUser;
import com.nhxv.botbackend.util.GeneralUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import java.net.URI;
import java.net.URISyntaxException;
import java.security.Principal;

@RestController
@RequestMapping("/api")
public class UserController {

	@Autowired
	private OAuth2AuthorizedClientService clientService;

	@GetMapping("/user/me")
	@PreAuthorize("hasRole('USER')")
	public ResponseEntity<?> getCurrentUser(@CurrentUser LocalUser user) throws URISyntaxException {
		OAuth2AuthorizedClient client = this.clientService.loadAuthorizedClient(
				user.getUser().getProvider(),
				user.getUser().getEmail()
		);
		String accessToken = client.getAccessToken().getTokenValue();
		RestTemplate restTemplate = new RestTemplate();
		final String guildUrl = "https://discord.com/api/users/@me/guilds";
		URI uri = new URI(guildUrl);
		HttpHeaders headers = new HttpHeaders();
		headers.set(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken);
		headers.set(HttpHeaders.USER_AGENT, "Discord app");
		HttpEntity<String> request = new HttpEntity<>(headers);
		ResponseEntity<String> guilds = restTemplate.exchange(uri, HttpMethod.GET, request, String.class);
		return ResponseEntity.ok(GeneralUtils.buildUserInfo(user, guilds.getBody()));
	}
}
