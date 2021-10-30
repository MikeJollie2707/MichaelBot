package com.nhxv.botbackend.model;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;

@Entity
@Table(name = "dguilds")
@NoArgsConstructor
@Getter
@Setter
public class GuildBot {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    @Column(name = "name")
    private String name;

    @Column(name = "is_whitelist")
    private boolean isWhitelist;

    @Column(name = "prefix")
    private String prefix;

    @Column(name = "enable_log")
    private boolean enableLog;

    @Column(name = "log_channel")
    private Long logChannel;

    @Column(name = "enable_welcome")
    private boolean enableWelcome;

    @Column(name = "welcome_channel")
    private Long welcomeChannel;

    @Column(name = "welcome_text")
    private String welcomeText;

    @Override
    public String toString() {
        return "DGuildBot{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", isWhitelist=" + isWhitelist +
                ", prefix='" + prefix + '\'' +
                ", enableLog=" + enableLog +
                ", logChannel=" + logChannel +
                ", enableWelcome=" + enableWelcome +
                ", welcomeChannel=" + welcomeChannel +
                ", welcomeText='" + welcomeText + '\'' +
                '}';
    }
}
