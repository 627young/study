class Settings:
    # 路径配置
    BURN_PATH = "/online/"
    OTA_PATH = "/media/sdcard/ota/"
    APP_LOG_PATH = "/media/sdcard/log/logs/"
    MCU_LOG_PATH = "/media/sdcard/data/tbox_log/"
    CONFIGS_PATH = "/oemdata/configs/tbox_config.cfg.rw"
    
    # MTD设备配置
    MTD_BOOT = "/dev/mtd/mtd28"
    MTD_DT = "/dev/mtd/mtd21"
    
    # UI配置
    WINDOW_TITLE = "RedCap-OTA升级工具 v2.0"
    WINDOW_ICON = "./icon/icon.jpg"
    WINDOW_GEOMETRY = (100, 100, 600, 600)