"""Deprecated: monitoring tasks removed for fast-deploy minimal RAG mode.

Beat scheduler removed from docker-compose.yml and celery_app.py.
This file kept as stub to preserve imports; tasks are no-ops.
"""
import logging

logger = logging.getLogger("eka")

# Stubs - not scheduled anymore
def check_failed_documents(*args, **kwargs):
    logger.debug("check_failed_documents stub - disabled in minimal mode")

def update_metrics(*args, **kwargs):
    logger.debug("update_metrics stub - disabled in minimal mode")

def prune_blacklisted_tokens(*args, **kwargs):
    logger.debug("prune_blacklisted_tokens stub - disabled in minimal mode")
