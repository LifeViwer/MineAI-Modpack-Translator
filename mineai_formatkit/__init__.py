"""MineAI-FormatKit components vendored for the MineAI integration pilots.

Certified base snapshot: LifeViwer/MineAI-FormatKit@7eadface1a27b667a9dcc369944c5da49e2e14f5
Pilot v3 adds only corpus-proven Patchouli/IE runtime hardening pending upstream SDK acceptance.
"""

from .config_locales import CollapsibleGroupsConfigLangJsonAdapter, JaopcaConfigLangJsonAdapter
from .core import TranslationPlan, TranslationUnit, ValidationError
from .ie_manual import ImmersiveEngineeringManualAdapter
from .locale_merge import LocaleMergePlan
from .locale_safe import LocaleMergePlanner, MinecraftLangJsonAdapter
from .patchouli_safe import PatchouliBookJsonAdapter
from .patchouli_template import PatchouliTemplateJsonAdapter

FORMATKIT_SOURCE_SHA = "7eadface1a27b667a9dcc369944c5da49e2e14f5"
FORMATKIT_PILOT_HARDENING = "books-v3.2:per-unit-precache-validation+stable-patchouli-fingerprint+backslash-safety+v3.1"

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
    "PatchouliTemplateJsonAdapter",
    "TranslationPlan",
    "TranslationUnit",
    "ValidationError",
]
