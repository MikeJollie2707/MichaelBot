package com.nhxv.botbackend.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nhxv.botbackend.config.CurrentUser;
import com.nhxv.botbackend.dto.Guild;
import com.nhxv.botbackend.dto.LocalUser;
import com.nhxv.botbackend.util.GeneralUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.List;

@RestController
@RequestMapping("/api")
public class UserController {

	@Autowired
	private OAuth2AuthorizedClientService clientService;

	@GetMapping("/user/me")
	@PreAuthorize("hasRole('USER')")
	public ResponseEntity<?> getCurrentUser(@CurrentUser LocalUser user) throws URISyntaxException, JsonProcessingException {
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
		return ResponseEntity.ok(GeneralUtils.buildUserInfo(user, processGuilds(guilds.getBody())));
	}

	private List<Guild> processGuilds(String guildStr) throws JsonProcessingException {
		final ObjectMapper objectMapper = new ObjectMapper();
		objectMapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
		return objectMapper.readValue(guildStr, new TypeReference<List<Guild>>(){});
	}
}
