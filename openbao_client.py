import os
import hvac  # официальный клиент для Vault/OpenBao
from dotenv import load_dotenv

load_dotenv()  # подхватываем .env

class OpenBaoClient:
    def __init__(self):
        self.addr = os.getenv("OPENBAO_ADDR")
        self.token = os.getenv("OPENBAO_TOKEN")
        self.verify = os.getenv("VERIFY_TLS", "false").lower() == "true"
        self.mount = os.getenv("MOUNT", "secret")

        self.client = hvac.Client(
            url=self.addr,
            token=self.token,
            verify=self.verify
        )

    def read_secret(self, path: str):
        return self.client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point=self.mount
        )

    def write_secret(self, path: str, secret: dict):
        return self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=secret,
            mount_point=self.mount
        )

