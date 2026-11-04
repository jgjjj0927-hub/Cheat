# language: python, file: offsets.py — client.dll, октябрь 2026
DW_ENTITY_LIST       = 0x271C8B8
DW_LOCAL_PLAYER_PAWN = 0x25676D8
DW_VIEW_MATRIX       = 0x256CFE0
DW_VIEW_ANGLES       = 0x257DE08
DW_GLOBAL_VARS       = 0x1A3B4C0   # CGlobalVarsBase
DW_PLANTED_C4        = 0x23A1F80   # C_PlantedC4
DW_GAME_RULES        = 0x1A3B4B8   # C_CSGameRules

M_I_HEALTH           = 0x344
M_I_TEAM_NUM         = 0x3CB
M_LIFE_STATE         = 0x338
M_VEC_ORIGIN         = 0x1224
M_VEC_VIEW_OFFSET    = 0xE18
M_B_DORMANT          = 0xED8
M_AIM_PUNCH_ANGLE    = 0x173C
M_F_FLAGS            = 0x3D0
M_I_ITEM_DEFINITION  = 0x1BA4     # weapon id
M_WEAPON_SERVICES    = 0x11E0     # weapon services ptr
M_H_ACTIVE_WEAPON    = 0x60       # active weapon handle
M_I_ACCOUNT_ID       = 0x690
M_SZ_NAME            = 0x610      # player name
M_B_SPOTTED          = 0x93D      # visible by local
M_I_SHOTS_FIRED      = 0x1C40     # for spectator / aimbot detection

# bones (skeleton ESP)
M_BONE_MATRIX        = 0x1F0      # CGameSceneNode
M_MODEL_STATE        = 0x170      # CBaseEntity
M_BONE_ARRAY         = 0x80       # inside CModelState (approx, verify per build)

# C4 / bomb
M_C4_BOMB_BLOWING    = 0x1A0      # planted c4: detonation time offset (verify)
M_C4_BOMB_SITE       = 0x1A4      # site (A/B)
M_C4_BOMB_DEFUSED    = 0x1A8
M_C4_BOMB_DEFUSE_LEN = 0x1AC

# global vars
M_CURTIME            = 0x00       # global vars: curtime
M_CURTIME2           = 0x04
M_FRAMETIME          = 0x08
M_MAX_CLIENTS        = 0x10
M_INTERVAL_PER_TICK  = 0x20
