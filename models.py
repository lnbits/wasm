from pydantic import BaseModel, Field


class WasmSettings(BaseModel):
    timeout_seconds: float = Field(default=3.0, ge=0.1)
    max_module_bytes: int = Field(default=1_000_000, ge=0)
    max_db_ops_per_min: int = Field(default=120, ge=0)
    max_kv_bytes: int = Field(default=10_000_000, ge=0)
