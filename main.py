from fastapi import FastAPI, Request, Response, Query, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import time
import uuid
import jwt
import os
import yaml
from dotenv import dotenv_values

os.environ["APP_WORKERS"] = "5"
os.environ["APP_LOG_LEVEL"] = "debug"

app = FastAPI()

ALLOWED_ORIGIN = "https://dash-f3xe0z.example.com"

@app.middleware("http")
async def custom_cors_and_metrics(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)
        
    process_time = max(0.0, time.perf_counter() - start_time)
    
    # Required headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    
    # CORS logic
    origin = request.headers.get("origin")
    if request.url.path in ["/effective-config", "/analytics"]:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    elif origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
    return response

@app.get("/stats")
async def get_stats(values: str = Query(...)):
    try:
        numbers = [int(x.strip()) for x in values.split(",")]
    except ValueError:
        return {"error": "Invalid input. Expected comma-separated integers."}
        
    if not numbers:
        return {"error": "No numbers provided."}

    count = len(numbers)
    total_sum = sum(numbers)
    min_val = min(numbers)
    max_val = max(numbers)
    mean_val = total_sum / count
    
    return {
        "email": "24f3004104@ds.study.iitm.ac.in",
        "count": count,
        "sum": total_sum,
        "min": min_val,
        "max": max_val,
        "mean": mean_val
    }

class TokenRequest(BaseModel):
    token: str

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

@app.post("/verify")
async def verify_token(req: TokenRequest):
    try:
        decoded = jwt.decode(
            req.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer="https://idp.exam.local",
            audience="tds-ciefqc94.apps.exam.local",
            options={"require": ["exp", "iss", "aud"]}
        )
        return {
            "valid": True,
            "email": decoded.get("email"),
            "sub": decoded.get("sub"),
            "aud": decoded.get("aud")
        }
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"valid": False})

def str_to_bool(val: str) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("true", "1", "yes", "on")

def coerce_type(key: str, value: any) -> any:
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return str_to_bool(value)
    return str(value)

@app.get("/effective-config")
async def effective_config(set: Optional[List[str]] = Query(default=[])):
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    try:
        with open("config.development.yaml", "r") as f:
            yaml_config = yaml.safe_load(f) or {}
            for k, v in yaml_config.items():
                config[k] = coerce_type(k, v)
    except FileNotFoundError:
        pass

    env_config = dotenv_values(".env")
    for k, v in env_config.items():
        if k == "NUM_WORKERS":
            config["workers"] = coerce_type("workers", v)
        elif k.startswith("APP_"):
            key = k[4:].lower()
            config[key] = coerce_type(key, v)

    for k, v in os.environ.items():
        if k == "NUM_WORKERS":
            config["workers"] = coerce_type("workers", v)
        elif k.startswith("APP_"):
            key = k[4:].lower()
            config[key] = coerce_type(key, v)

    for override in set:
        if "=" in override:
            k, v = override.split("=", 1)
            config[k] = coerce_type(k, v)

    if "api_key" in config:
        config["api_key"] = "****"

    return config

class Event(BaseModel):
    user: str
    amount: float
    ts: int

class AnalyticsRequest(BaseModel):
    events: List[Event]

@app.post("/analytics")
async def analytics(req: AnalyticsRequest, x_api_key: Optional[str] = Header(None)):
    if x_api_key != "ak_0aztrh92lumh8gwr8y4o2s19":
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    events = req.events
    total_events = len(events)
    
    unique_users = set()
    user_revenue = {}
    total_revenue = 0.0
    
    for event in events:
        unique_users.add(event.user)
        if event.amount > 0:
            total_revenue += event.amount
            user_revenue[event.user] = user_revenue.get(event.user, 0.0) + event.amount
            
    top_user = ""
    if user_revenue:
        top_user = max(user_revenue.items(), key=lambda x: x[1])[0]
        
    return {
        "email": "24f3004104@ds.study.iitm.ac.in",
        "total_events": total_events,
        "unique_users": len(unique_users),
        "revenue": total_revenue,
        "top_user": top_user
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
