"""Authenticated API for the canonical Himma reward catalog."""

from fastapi import APIRouter, Depends

from dependencies import get_any_authenticated
from reward_catalog import catalog_payload


router = APIRouter(tags=["Rewards"])


@router.get("/reward-catalog")
def reward_catalog(_auth=Depends(get_any_authenticated)):
    return catalog_payload()
