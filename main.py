import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from endpoints.secrets import secret_router
from endpoints.users import user_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix='/users')
app.include_router(secret_router, prefix='/secrets', tags=["openbao"])

if __name__ == '__main__':
    uvicorn.run(app=app, host='127.0.0.1', port=8000)

# docker run -d --name opendao -p 8200:8200 -e VAULT_DEV_ROOT_TOKEN_ID=root -e VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200 --cap-add=IPC_LOCK hashicorp/vault:1.13.0
