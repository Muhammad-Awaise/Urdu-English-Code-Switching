from fastapi import APIRouter

from app.api.routes import (
    analyze,
    annotations,
    dashboard,
    datasets,
    evaluation,
    models,
    preprocess,
    research,
    settings_routes,
    training,
)

api_router = APIRouter()
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(analyze.router, tags=["analyze"])
api_router.include_router(preprocess.router, tags=["preprocessing"])
api_router.include_router(datasets.router, tags=["datasets"])
api_router.include_router(annotations.router, tags=["annotations"])
api_router.include_router(training.router, tags=["training"])
api_router.include_router(evaluation.router, tags=["evaluation"])
api_router.include_router(models.router, tags=["models"])
api_router.include_router(research.router, tags=["research"])
api_router.include_router(settings_routes.router, tags=["settings"])
