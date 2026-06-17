from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import (
    auth, users, merchants, scales, standard_weights,
    appointments, verifications, labels, rectifications,
    inspections, operation_logs
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="电子秤计量检定服务 API",
    description="电子秤计量检定服务系统，支持商户管理、秤具管理、检定预约、读数记录、误差判定、合格标签签发、整改复检和监管抽查等功能。",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(merchants.router)
app.include_router(scales.router)
app.include_router(standard_weights.router)
app.include_router(appointments.router)
app.include_router(verifications.router)
app.include_router(labels.router)
app.include_router(rectifications.router)
app.include_router(inspections.router)
app.include_router(operation_logs.router)


@app.get("/", tags=["根路径"])
async def root():
    return {
        "message": "电子秤计量检定服务 API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "healthy"}
