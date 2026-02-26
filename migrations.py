from lnbits.db import Database


async def m001_initial(db: Database):
    """
    Initial settings table for the WASM host extension.
    """
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS wasm.settings (
            id TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
