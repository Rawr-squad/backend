import uvicorn
from fastapi import FastAPI

from endpoints.users import user_router

app = FastAPI()
app.include_router(user_router, prefix='/auth')

if __name__ == '__main__':
    uvicorn.run(app=app, host='127.0.0.1', port=8000)