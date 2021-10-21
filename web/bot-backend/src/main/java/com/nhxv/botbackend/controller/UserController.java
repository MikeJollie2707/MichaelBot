package com.nhxv.botbackend.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nhxv.botbackend.config.CurrentUser;
import com.nhxv.botbackend.dto.Guild;
import com.nhxv.botbackend.dto.LocalUser;
import com.nhxv.botbackend.dto.UserInfo;
import com.nhxv.botbackend.util.GeneralUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
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
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestTemplate;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public class UserController {

	@Autowired
	private OAuth2AuthorizedClientService clientService;

	@Value("${spring.security.oauth2.client.registration.discord.clientId}")
	private String clientId;

	@Value("${bot.token}")
	private String botToken;

	@GetMapping("/user/me")
	@PreAuthorize("hasRole('USER')")
	public ResponseEntity<UserInfo> getCurrentUser(@CurrentUser LocalUser user) throws URISyntaxException, JsonProcessingException {
		OAuth2AuthorizedClient client = this.clientService.loadAuthorizedClient(
				user.getUser().getProvider(),
				user.getUser().getEmail()
		);
		String accessToken = client.getAccessToken().getTokenValue();
		RestTemplate restTemplate = new RestTemplate();
		final String url = "https://discord.com/api";
		final String myGuildUrl =  url + "/users/@me/guilds";
		URI myGuildUri = new URI(myGuildUrl);
		HttpHeaders headers = new HttpHeaders();
		headers.set(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken);
		headers.set(HttpHeaders.USER_AGENT, "Discord app");
		HttpEntity<String> request = new HttpEntity<>(headers);
		ResponseEntity<String> guildsRes = restTemplate.exchange(myGuildUri, HttpMethod.GET, request, String.class);
		System.out.println(guildsRes.getBody());
		List<Guild> managedGuilds = filterBot(filterPermission(processGuilds(guildsRes.getBody())));
		return ResponseEntity.ok(GeneralUtils.buildUserInfo(user, managedGuilds));
	}

	private List<Guild> processGuilds(String guildStr) throws JsonProcessingException {
		final ObjectMapper objectMapper = new ObjectMapper();
		objectMapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
		return objectMapper.readValue(guildStr, new TypeReference<List<Guild>>(){});
	}

	private List<Guild> filterPermission(List<Guild> guilds) {
		return guilds.stream().filter(
				guild -> guild.isOwner() ||
						guild.getPermissions().equals("ADMINISTRATOR") ||
						guild.getPermissions().equals("MANAGE_GUILD")).collect(Collectors.toList());
	}

	private List<Guild> filterBot(List<Guild> managedGuilds) throws URISyntaxException {
		RestTemplate restTemplate = new RestTemplate();
		final String url = "https://discord.com/api";
		HttpHeaders headers = new HttpHeaders();
		headers.set(HttpHeaders.AUTHORIZATION, "Bot " + botToken);
		headers.set(HttpHeaders.USER_AGENT, "Discord app");
		HttpEntity<String> request = new HttpEntity<>(headers);

		List<Guild> filteredGuilds = new ArrayList<>();

		for (Guild g : managedGuilds) {
			final String checkBotUrl = url + "/guilds/" + g.getId() + "/members/" + clientId;
			URI checkBotUri = new URI(checkBotUrl);
			try {
				ResponseEntity<String> checkBotRes = restTemplate.exchange(checkBotUri, HttpMethod.GET, request, String.class);
				filteredGuilds.add(g);
			} catch(HttpStatusCodeException e) {
				System.out.println("Error type: " + e.getStatusCode());
			}
		}
		return filteredGuilds;
	}
}
