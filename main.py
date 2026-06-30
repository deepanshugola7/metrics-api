from fastapi import FastAPI, Request, Response, Query
import time
import uuid

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
    if origin == ALLOWED_ORIGIN:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
