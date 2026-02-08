import json
import hashlib
from pathlib import Path

try:
    from solana.rpc.api import Client
    from solana.transaction import Transaction
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.instruction import Instruction
except Exception:  # pragma: no cover
    Client = None
    Keypair = None
    Pubkey = None
    Transaction = None
    Instruction = None


MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"


class SolanaService:
    def __init__(self, rpc_url, keypair_path):
        if Client is None:
            raise RuntimeError("solana-py is not installed")
        if not keypair_path:
            raise RuntimeError("SOLANA_KEYPAIR_PATH is not configured")

        self.client = Client(rpc_url)
        self.keypair = self._load_keypair(keypair_path)

    def _load_keypair(self, keypair_path):
        key_data = json.loads(Path(keypair_path).read_text())
        return Keypair.from_bytes(bytes(key_data))

    def send_memo(self, memo_text):
        memo_bytes = memo_text.encode("utf-8")
        memo_program = Pubkey.from_string(MEMO_PROGRAM_ID)
        instruction = Instruction(
            program_id=memo_program,
            data=memo_bytes,
            accounts=[],
        )

        tx = Transaction().add(instruction)
        response = self.client.send_transaction(tx, self.keypair)
        signature = response.get("result")
        if not signature:
            raise RuntimeError(f"Solana transaction failed: {response}")
        return signature


def hash_payload(*parts):
    joined = "|".join(str(p) for p in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
