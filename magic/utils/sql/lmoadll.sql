-- 用户表
create table lmoadll_users
(
    uid        integer not null
        constraint key
            primary key,
    name       varchar(32)  default null,
    password   varchar(255)  default null,
    mail       varchar(150) default null,
    url        varchar(150) default null,
    createdAt  int(10)      default 0,
    lastLogin  int(10)      default 0,
    isActive   int(10)      default 0,
    isLoggedIn int(10)      default 0,
    "group"    varchar(16)  default 'visitor'
);


-- 用户元数据表
create table lmoadll_usermeta
(
    umeta_id   integer      not null
        constraint lmoadll_usermeta_pk
            primary key autoincrement,
    user_id    integer      not null,
    meta_key   varchar(255) not null,
    meta_value text,
    created_at integer      default 0,
    updated_at integer      default 0,
    foreign key (user_id) references lmoadll_users (uid) on delete cascade
);

-- usermeta表索引
create index lmoadll_usermeta_user_id on lmoadll_usermeta (user_id);
create index lmoadll_usermeta_meta_key on lmoadll_usermeta (meta_key);
create index lmoadll_usermeta_user_meta on lmoadll_usermeta (user_id, meta_key);


-- 存储用户与扣子平台服务的关联信息
create table lmoadll_coze_ai
(   
    id              integer      not null
        constraint lmoadll_coze_ai_pk
            primary key autoincrement,
    user_id         integer      not null,
    cozehh_id       integer      not null,
    name            varchar(64)  default null,
    last_section_id int(20)      default null,
    created_at      int(10)      default 0,
    updated_at      int(10)      default 0,
    
    foreign key (user_id) references lmoadll_users (uid) on delete cascade,
    
    constraint lmoadll_coze_ai_unique 
        unique (user_id, cozehh_id)
);

-- lmoadll_coze_ai表索引
create index lmoadll_coze_ai_user_id on lmoadll_coze_ai (user_id);
create index lmoadll_coze_ai_cozehh_id on lmoadll_coze_ai (cozehh_id);
create index lmoadll_coze_ai_user_cozehh on lmoadll_coze_ai (user_id, cozehh_id);


-- 选项表
create table lmoadll_options
(
    name  varchar(32)         not null,
    user  int(10) default '0' not null,
    value text
);

create unique index lmoadll_options__name_user
    on lmoadll_options (name, user);
