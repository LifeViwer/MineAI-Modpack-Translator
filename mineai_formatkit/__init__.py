"""MineAI-FormatKit components vendored for MineAI integration pilots."""

from .config_locales import CollapsibleGroupsConfigLangJsonAdapter, JaopcaConfigLangJsonAdapter
from .core import TranslationPlan, TranslationUnit, ValidationError
from .ie_manual import ImmersiveEngineeringManualAdapter
from .locale_merge import LocaleMergePlan
from .locale_safe import LocaleMergePlanner, MinecraftLangJsonAdapter
from .patchouli_safe import PatchouliBookJsonAdapter

FORMATKIT_SOURCE_SHA = "7eadface1a27b667a9dcc369944c5da49e2e14f5"
FORMATKIT_PILOT_HARDENING = "books-v3.1:patchouli-template-safety"

__all__ = [
    "CollapsibleGroupsConfigLangJsonAdapter",
    "FORMATKIT_PILOT_HARDENING",
    "FORMATKIT_SOURCE_SHA",
    "ImmersiveEngineeringManualAdapter",
    "JaopcaConfigLangJsonAdapter",
    "LocaleMergePlan",
    "LocaleMergePlanner",
    "MinecraftLangJsonAdapter",
    "PatchouliBookJsonAdapter",
    "TranslationPlan",
    "TranslationUnit",
    "ValidationError",
]
