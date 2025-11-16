# app/api/routes.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.api.inference import predict_from_bytes

app = FastAPI(title="CropGuardian AI (Local Backend)")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "CropGuardian AI backend running."}

@app.get("/healthz")
def health():
    return {"status": "healthy"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    try:
        image_bytes = await file.read()
        result = predict_from_bytes(image_bytes)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
