"""Local, durable campaign record manager."""

from .store import CampaignStore, ProtocolError, open_campaign_store

__all__ = ["CampaignStore", "ProtocolError", "open_campaign_store"]
