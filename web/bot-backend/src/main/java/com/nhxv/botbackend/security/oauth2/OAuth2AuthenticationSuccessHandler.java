package com.nhxv.botbackend.security.oauth2;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.nhxv.botbackend.config.AppProperties;
import com.nhxv.botbackend.dto.Guild;
import com.nhxv.botbackend.exception.BadRequestException;
import com.nhxv.botbackend.security.jwt.TokenProvider;
import com.nhxv.botbackend.service.UserService;
import com.nhxv.botbackend.util.CookieUtils;
import com.nhxv.botbackend.config.AppProperties;
import com.nhxv.botbackend.exception.BadRequestException;
import com.nhxv.botbackend.security.jwt.TokenProvider;
import com.nhxv.botbackend.util.CookieUtils;
import com.sun.jndi.toolkit.url.Uri;
import lombok.SneakyThrows;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import javax.servlet.ServletException;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.Optional;

import static com.nhxv.botbackend.security.oauth2.HttpCookieOAuth2AuthorizationRequestRepository.REDIRECT_URI_PARAM_COOKIE_NAME;

@Component
public class OAuth2AuthenticationSuccessHandler extends SimpleUrlAuthenticationSuccessHandler {
	private TokenProvider tokenProvider;
	private AppProperties appProperties;
	private HttpCookieOAuth2AuthorizationRequestRepository httpCookieOAuth2AuthorizationRequestRepository;
	private OAuth2AuthorizedClientService clientService;

	@Autowired
	OAuth2AuthenticationSuccessHandler(TokenProvider tokenProvider, AppProperties appProperties,
									   OAuth2AuthorizedClientService clientService,
			HttpCookieOAuth2AuthorizationRequestRepository httpCookieOAuth2AuthorizationRequestRepository) {
		this.tokenProvider = tokenProvider;
		this.appProperties = appProperties;
		this.clientService = clientService;
		this.httpCookieOAuth2AuthorizationRequestRepository = httpCookieOAuth2AuthorizationRequestRepository;
	}

	@SneakyThrows
	@Override
	public void onAuthenticationSuccess(HttpServletRequest request, HttpServletResponse response, Authentication authentication) throws IOException, ServletException {
		String targetUrl = determineTargetUrl(request, response, authentication);

		if (response.isCommitted()) {
			logger.debug("Response has already been committed. Unable to redirect to " + targetUrl);
			return;
		}

		System.out.println("target URL: " + targetUrl);

		clearAuthenticationAttributes(request, response);
		getRedirectStrategy().sendRedirect(request, response, targetUrl);
	}

	@Override
	protected String determineTargetUrl(HttpServletRequest request, HttpServletResponse response, Authentication authentication) {
		Optional<String> redirectUri = CookieUtils.getCookie(request, REDIRECT_URI_PARAM_COOKIE_NAME).map(Cookie::getValue);

		if (redirectUri.isPresent() && !isAuthorizedRedirectUri(redirectUri.get())) {
			throw new BadRequestException("Sorry! We've got an Unauthorized Redirect URI and can't proceed with the authentication");
		}

		String targetUrl = redirectUri.orElse(getDefaultTargetUrl());

		String token = tokenProvider.createToken(authentication);

		logger.info(targetUrl);

		return UriComponentsBuilder.fromUriString(targetUrl).queryParam("token", token).build().toUriString();
	}

	protected void clearAuthenticationAttributes(HttpServletRequest request, HttpServletResponse response) {
		super.clearAuthenticationAttributes(request);
		httpCookieOAuth2AuthorizationRequestRepository.removeAuthorizationRequestCookies(request, response);
	}

	private boolean isAuthorizedRedirectUri(String uri) {
		URI clientRedirectUri = URI.create(uri);

		return appProperties.getOauth2().getAuthorizedRedirectUris().stream().anyMatch(authorizedRedirectUri -> {
			// Only validate host and port. Let the clients use different paths if they want to
			URI authorizedURI = URI.create(authorizedRedirectUri);
			if (authorizedURI.getHost().equalsIgnoreCase(clientRedirectUri.getHost()) && authorizedURI.getPort() == clientRedirectUri.getPort()) {
				return true;
			}
			return false;
		});
	}

//	private String getGuilds(Authentication authentication) throws URISyntaxException {
//		System.out.println("Auth when get guilds: " + authentication);
//		OAuth2AuthenticationToken oauthToken = (OAuth2AuthenticationToken) authentication;
//		OAuth2AuthorizedClient client = this.clientService.loadAuthorizedClient(
//				oauthToken.getAuthorizedClientRegistrationId(),
//				oauthToken.getName()
//		);
//		String accessToken = client.getAccessToken().getTokenValue();
//		RestTemplate restTemplate = new RestTemplate();
//		final String guildUrl = "https://discord.com/api/users/@me/guilds";
//		URI uri = new URI(guildUrl);
//		HttpHeaders headers = new HttpHeaders();
//		headers.set(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken);
//		headers.set(HttpHeaders.USER_AGENT, "Discord app");
//		HttpEntity<String> request = new HttpEntity<>(headers);
//		ResponseEntity<String> response = restTemplate.exchange(uri, HttpMethod.GET, request, String.class);
//		return response.getBody();
//	}
}
