"""Prospecção brasileira sem disparos: contratos e funções para integração na API."""

from .schemas import (
    BANTAnswer,
    BANTRequest,
    BANTResult,
    Business,
    DiscoveryRequest,
    DiscoveryResult,
    Draft,
    DraftRequest,
    Evidence,
    ICPRequest,
    Profile,
    ProfileRequest,
    PublishedContact,
    ScoreResult,
    Signal,
)
from .service import (
    CATEGORY_TAGS,
    ProspeccaoService,
    category_tags,
    draft_outreach,
    qualify_bant,
    score_icp,
)
from .transport import ProspeccaoError

__all__ = [
    "BANTAnswer", "BANTRequest", "BANTResult", "Business", "CATEGORY_TAGS",
    "DiscoveryRequest", "DiscoveryResult", "Draft", "DraftRequest", "Evidence",
    "ICPRequest", "Profile", "ProfileRequest", "ProspeccaoError",
    "ProspeccaoService", "PublishedContact", "ScoreResult", "Signal",
    "category_tags", "draft_outreach", "qualify_bant", "score_icp",
]
