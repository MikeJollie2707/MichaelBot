package com.nhxv.botbackend.controller;

import com.nhxv.botbackend.model.GuildBot;
import com.nhxv.botbackend.repo.GuildBotRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/guildBot")
public class GuildBotController {
    @Autowired
    private GuildBotRepository dGuildRepository;

    @GetMapping("/{guildBotId}")
    private ResponseEntity<GuildBot> getDGuild(@PathVariable Long guildBotId) throws Exception {
        GuildBot guildBot = this.dGuildRepository.findById(guildBotId).orElseThrow(() -> new Exception("Guild bot not found for id: " + guildBotId));
        return ResponseEntity.ok().body(guildBot);
    }
}
