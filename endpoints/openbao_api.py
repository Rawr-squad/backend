from fastapi import APIRouter, HTTPException
from openbao_client import OpenBaoClient

router = APIRouter()
client = OpenBaoClient()

@router.get("/secret/{path}")
def get_secret(path: str):
    try:
        secret = client.read_secret(path)
        return {"data": secret["data"]["data"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/secret/{path}")
def create_secret(path: str, payload: dict):
    try:
        client.write_secret(path, payload)
        return {"status": "ok", "path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
