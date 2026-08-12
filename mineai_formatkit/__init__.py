"""Certified MineAI-FormatKit locale stack vendored for the MineAI pilot.

Source snapshot: LifeViwer/MineAI-FormatKit@7eadface1a27b667a9dcc369944c5da49e2e14f5
Only the locale stack used by this integration pilot is exported here.
"""

from .config_locales import (
    CollapsibleGroupsConfigLangJsonAdapter,
    JaopcaConfigLangJsonAdapter,
)
from .core import TranslationPlan, TranslationUnit, ValidationError
from .locale_merge import LocaleMergePlan
from .locale_safe import LocaleMergePlanner, MinecraftLangJsonAdapter

FORMATKIT_SOURCE_SHA = "7eadface1a27b667a9dcc369944c5da49e2e14f5"

__all__ = [
    "CollapsibleGroupsConfigLangJsonAdapter",
    "FORMATKIT_SOURCE_SHA",
    "JaopcaConfigLangJsonAdapter",
    "LocaleMergePlan",
    "LocaleMergePlanner",
    "MinecraftLangJsonAdapter",
    "TranslationPlan",
    "TranslationUnit",
    "ValidationError",
]
