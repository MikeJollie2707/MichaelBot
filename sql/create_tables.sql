-- public.guilds definition

-- Drop table

-- DROP TABLE public.guilds;

CREATE TABLE public.guilds (
	id int8 NOT NULL,
	"name" text NOT NULL,
	is_whitelist bool NOT NULL DEFAULT true,
	prefix text NOT NULL DEFAULT '$'::text,
	CONSTRAINT guilds_pkey PRIMARY KEY (id)
);


-- public.users definition

-- Drop table

-- DROP TABLE public.users;

CREATE TABLE public.users (
	id int8 NOT NULL,
	"name" text NOT NULL,
	is_whitelist bool NOT NULL DEFAULT true,
	CONSTRAINT users_pkey PRIMARY KEY (id)
);


-- public.guildslogs definition

-- Drop table

-- DROP TABLE public.guildslogs;

CREATE TABLE public.guildslogs (
	guild_id int8 NOT NULL,
	log_channel int8 NULL,
	guild_channel_create bool NOT NULL DEFAULT true,
	guild_channel_delete bool NOT NULL DEFAULT true,
	guild_channel_update bool NOT NULL DEFAULT true,
	guild_ban bool NOT NULL DEFAULT true,
	guild_unban bool NOT NULL DEFAULT true,
	guild_update bool NOT NULL DEFAULT true,
	member_join bool NOT NULL DEFAULT true,
	member_leave bool NOT NULL DEFAULT true,
	member_update bool NOT NULL DEFAULT true,
	guild_bulk_message_delete bool NOT NULL DEFAULT true,
	guild_message_delete bool NOT NULL DEFAULT true,
	guild_message_update bool NOT NULL DEFAULT true,
	role_create bool NOT NULL DEFAULT true,
	role_delete bool NOT NULL DEFAULT true,
	role_update bool NOT NULL DEFAULT true,
	command_complete bool NOT NULL DEFAULT false,
	command_error bool NOT NULL DEFAULT true,
	CONSTRAINT guildslogs_guild_id_key UNIQUE (guild_id),
	CONSTRAINT fk_guildslogs_guilds FOREIGN KEY (guild_id) REFERENCES public.guilds(id)
); 
