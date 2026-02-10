"""
VideoMixer - 视频批量混剪/去重工具
"""

__version__ = "1.0.0"
__author__ = "VideoMixer Team"

from .config import VideoConfig, AppConfig
from .video_engine import VideoEngine, get_engine
from .material_pool import MaterialPool
from .batch_processor import BatchProcessor, TaskStatus, TaskResult
from .mp4_patcher import patch_mixed_video, patch_file_edit_list
from .video_classifier import (
    VideoCategory, VideoStyle, VideoFeatures,
    ClassificationResult, classify_video_file, analyze_video
)
from .smart_effects import (
    get_effect_config_for_category, get_smart_effect_config,
    describe_effect_config, CATEGORY_NAMES
)
from .smart_processor import (
    smart_process_video, batch_smart_process,
    process, process_batch, ProcessingResult
)
from .audio_effects import (
    AudioDedupConfig, build_audio_dedup_filter, build_audio_complex_filter,
    randomize_audio_config, get_audio_ffmpeg_args,
    AUDIO_DEDUP_PRESETS
)
from .param_randomizer import (
    EncodingParams, RandomizeConfig, randomize_encoding_params,
    get_encoding_ffmpeg_args, get_scale_filter, get_fps_filter,
    ENCODING_PRESETS, RANDOMIZE_PRESETS
)
from .structure_effects import (
    StructureConfig, StructureResult, IntroType, OutroType,
    build_full_structure_filter, build_structure_video_filter,
    should_mirror, get_crop_params, get_speed_factor,
    create_solid_color_video, concat_with_intro_outro,
    STRUCTURE_PRESETS
)
from .metadata_cleaner import (
    MetadataConfig, clean_metadata, clean_metadata_with_reencode,
    randomize_timestamps, generate_random_filename, generate_unique_filename,
    get_metadata_ffmpeg_args, process_output_file, verify_metadata_cleared,
    METADATA_PRESETS
)
from .smart_remix import (
    smart_remix, batch_smart_remix, DedupConfig, RemixResult,
    VideoType, CoverageConfig
)
from .advanced_dedup import (
    WeixinDedupConfig, get_weixin_preset,
    SegmentShuffleConfig, calculate_segments,
    PictureInPictureConfig, build_pip_filter,
    IntroOutroMaterialConfig,
    PixelDisturbConfig, build_pixel_disturb_filter,
    WEIXIN_DEDUP_PRESETS
)
from .weixin_remix import (
    weixin_remix, batch_weixin_remix,
    WeixinRemixConfig, WeixinRemixResult
)
from .overlay_effects import (
    # 配置类
    AdvancedOverlayConfig, FakeMusicPlayerConfig, ProgressBarConfig,
    SubtitleBarConfig, SplitScreenConfig, BlurBackgroundConfig,
    FallingParticleConfig, HolidayStickerConfig, SymmetricStickerConfig,
    WaterRippleConfig, ColorBlockConfig, ColoredSubtitleConfig,
    # 枚举
    ParticleType, HolidayTheme, SplitScreenMode,
    # 滤镜构建函数
    build_fake_player_filter, build_progress_bar_filter,
    build_subtitle_bar_filter, build_blur_background_filter,
    build_falling_particle_filter, build_holiday_sticker_filter,
    build_symmetric_sticker_filter, build_water_ripple_filter,
    build_color_block_filter, build_colored_subtitle_filter,
    build_advanced_overlay_filter,
    # 辅助函数
    get_overlay_preset, get_random_song_title,
    # 预设
    OVERLAY_PRESETS, HOLIDAY_TEXTS
)
from .video_effects import (
    EffectsConfig, MaskConfig, MaskPosition, MaskMotion, DynamicEffect,
    HandheldConfig, StickerConfig, StickerPosition, GridConfig, GridRegion,
    ScrollTextConfig, ScrollDirection, TextRegion,
    FlashConfig, FlashType,
    MagicEffectConfig, BlendMode, BlendRegion,
    WeatherEffectConfig, WeatherType,
    ParticleEffectConfig, ParticleType,
    TiltConfig, FisheyeConfig,
    BorderConfig, BorderStyle,
    SpeedConfig, SpeedMode,
    GradientIntroConfig, GradientDirection,
    # 运营团队功能配置
    CropConfig, SegmentConfig, ConcatConfig,
    AudioConfig, NoiseReductionType,
    TransitionConfig, TransitionType,
    ColorGradingConfig, ColorPreset,
    WatermarkRemovalConfig, WatermarkRemovalMethod,
    SubtitleConfig, SubtitleStyle,
    # 滤镜构建函数
    randomize_effects_config, build_effects_filter_chain,
    build_handheld_shake_filter, build_external_mask_overlay,
    get_mask_files_from_directory, choose_random_mask, delete_mask_file,
    get_sticker_files_from_directory, choose_random_sticker,
    build_sticker_overlay_filter, build_grid_filter,
    build_scroll_text_filter, get_system_fonts, choose_random_font,
    build_flash_filter, build_magic_effect_filter,
    build_weather_effect_filter, build_particle_effect_filter,
    build_tilt_filter, build_fisheye_filter, build_border_filter,
    build_speed_filter, build_gradient_intro_filter,
    # 运营团队功能滤镜
    build_crop_filter, build_audio_filter, build_bgm_mix_filter,
    build_transition_filter, build_color_grading_filter,
    build_watermark_removal_filter, build_subtitle_filter, build_segment_filter,
    # 预设
    PRESET_SUBTLE, PRESET_MODERATE, PRESET_STRONG, PRESET_HANDHELD
)

__all__ = [
    # 核心配置
    "VideoConfig",
    "AppConfig",
    "VideoEngine",
    "get_engine",
    "MaterialPool",
    "BatchProcessor",
    "TaskStatus",
    "TaskResult",
    "patch_mixed_video",
    "patch_file_edit_list",
    # 特效配置
    "EffectsConfig",
    "MaskConfig",
    "MaskPosition",
    "MaskMotion",
    "DynamicEffect",
    "HandheldConfig",
    "StickerConfig",
    "StickerPosition",
    "GridConfig",
    "GridRegion",
    "ScrollTextConfig",
    "ScrollDirection",
    "TextRegion",
    "FlashConfig",
    "FlashType",
    "MagicEffectConfig",
    "BlendMode",
    "BlendRegion",
    "WeatherEffectConfig",
    "WeatherType",
    "ParticleEffectConfig",
    "ParticleType",
    "TiltConfig",
    "FisheyeConfig",
    "BorderConfig",
    "BorderStyle",
    "SpeedConfig",
    "SpeedMode",
    "GradientIntroConfig",
    "GradientDirection",
    # 运营团队功能配置
    "CropConfig",
    "SegmentConfig",
    "ConcatConfig",
    "AudioConfig",
    "NoiseReductionType",
    "TransitionConfig",
    "TransitionType",
    "ColorGradingConfig",
    "ColorPreset",
    "WatermarkRemovalConfig",
    "WatermarkRemovalMethod",
    "SubtitleConfig",
    "SubtitleStyle",
    # 滤镜构建函数
    "randomize_effects_config",
    "build_effects_filter_chain",
    "build_handheld_shake_filter",
    "build_external_mask_overlay",
    "get_mask_files_from_directory",
    "choose_random_mask",
    "delete_mask_file",
    "get_sticker_files_from_directory",
    "choose_random_sticker",
    "build_sticker_overlay_filter",
    "build_grid_filter",
    "build_scroll_text_filter",
    "get_system_fonts",
    "choose_random_font",
    "build_flash_filter",
    "build_magic_effect_filter",
    "build_weather_effect_filter",
    "build_particle_effect_filter",
    "build_tilt_filter",
    "build_fisheye_filter",
    "build_border_filter",
    "build_speed_filter",
    "build_gradient_intro_filter",
    # 运营团队功能滤镜
    "build_crop_filter",
    "build_audio_filter",
    "build_bgm_mix_filter",
    "build_transition_filter",
    "build_color_grading_filter",
    "build_watermark_removal_filter",
    "build_subtitle_filter",
    "build_segment_filter",
    # 预设
    "PRESET_SUBTLE",
    "PRESET_MODERATE",
    "PRESET_STRONG",
    "PRESET_HANDHELD",
    # 智能视频分类
    "VideoCategory",
    "VideoStyle",
    "VideoFeatures",
    "ClassificationResult",
    "classify_video_file",
    "analyze_video",
    # 智能特效选择
    "get_effect_config_for_category",
    "get_smart_effect_config",
    "describe_effect_config",
    "CATEGORY_NAMES",
    # 智能处理器
    "smart_process_video",
    "batch_smart_process",
    "process",
    "process_batch",
    "ProcessingResult",
    # 音频去重模块
    "AudioDedupConfig",
    "build_audio_dedup_filter",
    "build_audio_complex_filter",
    "randomize_audio_config",
    "get_audio_ffmpeg_args",
    "AUDIO_DEDUP_PRESETS",
    # 参数随机化模块
    "EncodingParams",
    "RandomizeConfig",
    "randomize_encoding_params",
    "get_encoding_ffmpeg_args",
    "get_scale_filter",
    "get_fps_filter",
    "ENCODING_PRESETS",
    "RANDOMIZE_PRESETS",
    # 结构改变模块
    "StructureConfig",
    "StructureResult",
    "IntroType",
    "OutroType",
    "build_full_structure_filter",
    "build_structure_video_filter",
    "should_mirror",
    "get_crop_params",
    "get_speed_factor",
    "create_solid_color_video",
    "concat_with_intro_outro",
    "STRUCTURE_PRESETS",
    # 元数据处理模块
    "MetadataConfig",
    "clean_metadata",
    "clean_metadata_with_reencode",
    "randomize_timestamps",
    "generate_random_filename",
    "generate_unique_filename",
    "get_metadata_ffmpeg_args",
    "process_output_file",
    "verify_metadata_cleared",
    "METADATA_PRESETS",
    # 智能混剪模块
    "smart_remix",
    "batch_smart_remix",
    "DedupConfig",
    "RemixResult",
    "VideoType",
    "CoverageConfig",
    # 高级去重模块
    "WeixinDedupConfig",
    "get_weixin_preset",
    "SegmentShuffleConfig",
    "calculate_segments",
    "PictureInPictureConfig",
    "build_pip_filter",
    "IntroOutroMaterialConfig",
    "PixelDisturbConfig",
    "build_pixel_disturb_filter",
    "WEIXIN_DEDUP_PRESETS",
    # 微信视频号专用混剪
    "weixin_remix",
    "batch_weixin_remix",
    "WeixinRemixConfig",
    "WeixinRemixResult",
    # 叠加特效模块
    "AdvancedOverlayConfig",
    "FakeMusicPlayerConfig",
    "ProgressBarConfig",
    "SubtitleBarConfig",
    "SplitScreenConfig",
    "BlurBackgroundConfig",
    "FallingParticleConfig",
    "HolidayStickerConfig",
    "SymmetricStickerConfig",
    "WaterRippleConfig",
    "ColorBlockConfig",
    "ColoredSubtitleConfig",
    "ParticleType",
    "HolidayTheme",
    "SplitScreenMode",
    "build_fake_player_filter",
    "build_progress_bar_filter",
    "build_subtitle_bar_filter",
    "build_blur_background_filter",
    "build_falling_particle_filter",
    "build_holiday_sticker_filter",
    "build_symmetric_sticker_filter",
    "build_water_ripple_filter",
    "build_color_block_filter",
    "build_colored_subtitle_filter",
    "build_advanced_overlay_filter",
    "get_overlay_preset",
    "get_random_song_title",
    "OVERLAY_PRESETS",
    "HOLIDAY_TEXTS",
    # ============================================
    # 新增高级混剪能力模块 (2025-02-03)
    # ============================================
    # 高级字幕效果
    "SubtitleConfig_Advanced",
    "SubtitleStyle_Advanced",
    "build_subtitle_filter_advanced",
    "get_subtitle_preset_advanced",
    # 高级背景效果
    "BackgroundConfig",
    "BackgroundEffect",
    "build_background_filter",
    "get_background_preset",
    # 粒子特效
    "ParticleConfig",
    "ParticleType_Advanced",
    "build_particle_filter_advanced",
    "get_particle_preset_advanced",
    # UI模板
    "UITemplate",
    "MusicPlayerConfig",
    "ProgressBarConfig_Advanced",
    "RecIndicatorConfig",
    "build_ui_template",
    "get_ui_preset",
    # 布局引擎
    "LayoutConfig",
    "LayoutType",
    "build_layout",
    "get_layout_preset",
    # 标题效果
    "TitleConfig",
    "TitleStyle",
    "build_title_filter",
    "get_title_preset",
    # 高级混剪处理器
    "advanced_remix",
    "AdvancedRemixConfig",
    "remix_digital_human",
    "remix_handwriting",
    "remix_music_player",
    "remix_emotional",
    "get_strategy_for_type",
    "auto_remix",
    "auto_detect_video_type",
    "content_type_to_video_type",
    # 视频分析模块
    "VideoAnalyzer",
    "ContentType",
    "VideoAnalysisResult",
    "FaceAnalysis",
    "AudioAnalysis",
    "VisualAnalysis",
    "analyze_video_content",
    "detect_video_type",
    "get_recommended_strategy",
]

# 导入新增高级混剪能力模块
try:
    from .subtitle_effects import (
        SubtitleConfig as SubtitleConfig_Advanced,
        SubtitleStyle as SubtitleStyle_Advanced,
        build_subtitle_filter as build_subtitle_filter_advanced,
        get_subtitle_preset as get_subtitle_preset_advanced,
    )
    from .background_effects import (
        BackgroundConfig, BackgroundEffect,
        build_background_filter, get_background_preset,
    )
    from .particle_effects import (
        ParticleConfig,
        ParticleType as ParticleType_Advanced,
        build_particle_filter as build_particle_filter_advanced,
        get_particle_preset as get_particle_preset_advanced,
    )
    from .ui_templates import (
        UITemplate, MusicPlayerConfig,
        ProgressBarConfig as ProgressBarConfig_Advanced,
        RecIndicatorConfig,
        build_ui_template, get_ui_preset,
    )
    from .layout_engine import (
        LayoutConfig, LayoutType,
        build_layout, get_layout_preset,
    )
    from .title_effects import (
        TitleConfig, TitleStyle,
        build_title_filter, get_title_preset,
    )
    from .advanced_remix import (
        advanced_remix, AdvancedRemixConfig,
        remix_digital_human, remix_handwriting,
        remix_music_player, remix_emotional,
        get_strategy_for_type, auto_remix,
        auto_detect_video_type, content_type_to_video_type,
    )
    from .video_analyzer import (
        VideoAnalyzer, ContentType, VideoAnalysisResult,
        FaceAnalysis, AudioAnalysis, VisualAnalysis,
        analyze_video as analyze_video_content,
        get_video_type as detect_video_type,
        get_recommended_strategy,
    )
except ImportError as e:
    # 新模块可能尚未完全就绪，静默处理
    pass

# ============================================
# 新增功能模块 (2025-02-04)
# ============================================
try:
    # 转场效果模块
    from .transitions import (
        TransitionType, add_transition, add_flash_effect,
        concat_with_transitions, get_random_transition,
    )
    # 分屏效果模块
    from .split_screen import (
        SplitType, create_horizontal_split, create_vertical_split,
        create_grid_2x2, create_grid_3x3, create_pip,
        create_three_split_horizontal, create_three_split_vertical,
    )
    # 背景虚化模块
    from .background_blur import (
        AspectMode, create_blur_background, create_gradient_blur_background,
        create_color_blur_background, create_mirror_blur_background,
    )
    # 文字动画模块
    from .text_effects import (
        TextAnimation, TextStyle, add_static_text, add_typewriter_text,
        add_scroll_text, add_bounce_text, add_fade_text,
        add_subtitle_sequence, add_karaoke_text,
    )
    # 综合效果处理器
    from .all_effects import (
        EffectCategory, EffectConfig, ProcessingResult as AllEffectsResult,
        AllEffectsProcessor, create_preset_config, quick_process,
    )
    # 视频去重模块
    from .video_dedup import (
        DedupLevel, DedupConfig as VideoDedupConfig,
        apply_dedup, get_dedup_preset,
    )
    # 超级混剪模块
    from .super_remix import (
        super_remix, batch_super_remix,
    )

    # 添加到 __all__
    __all__.extend([
        # 转场效果
        "TransitionType", "add_transition", "add_flash_effect",
        "concat_with_transitions", "get_random_transition",
        # 分屏效果
        "SplitType", "create_horizontal_split", "create_vertical_split",
        "create_grid_2x2", "create_grid_3x3", "create_pip",
        "create_three_split_horizontal", "create_three_split_vertical",
        # 背景虚化
        "AspectMode", "create_blur_background", "create_gradient_blur_background",
        "create_color_blur_background", "create_mirror_blur_background",
        # 文字动画
        "TextAnimation", "TextStyle", "add_static_text", "add_typewriter_text",
        "add_scroll_text", "add_bounce_text", "add_fade_text",
        "add_subtitle_sequence", "add_karaoke_text",
        # 综合效果
        "EffectCategory", "EffectConfig", "AllEffectsResult",
        "AllEffectsProcessor", "create_preset_config", "quick_process",
        # 视频去重
        "DedupLevel", "VideoDedupConfig",
        "apply_dedup", "get_dedup_preset",
        # 超级混剪
        "super_remix", "batch_super_remix",
    ])
except ImportError as e:
    pass

# 混剪策略选择模块
try:
    from .editing_strategy import (
        VideoType as StrategyVideoType,
        Pace, EffectIntensity,
        ColorConfig, EditingStrategy,
        get_strategy, get_strategy_by_name,
        adjust_strategy_intensity, get_pace_params,
        describe_strategy, list_all_strategies,
        STRATEGIES,
    )

    __all__.extend([
        "StrategyVideoType", "Pace", "EffectIntensity",
        "ColorConfig", "EditingStrategy",
        "get_strategy", "get_strategy_by_name",
        "adjust_strategy_intensity", "get_pace_params",
        "describe_strategy", "list_all_strategies",
        "STRATEGIES",
    ])
except ImportError:
    pass
