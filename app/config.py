from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(
    PROJECT_ROOT / ".env"
)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    supabase_url: str
    supabase_key: str

    admin_ids: frozenset[int]

    restaurant_phone: str
    restaurant_address: str

    inpay_merchant_id: str
    inpay_merchant_token: str
    inpay_callback_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv(
            "BOT_TOKEN",
            "",
        ).strip()

        url = os.getenv(
            "SUPABASE_URL",
            "",
        ).strip()

        key = os.getenv(
            "SUPABASE_KEY",
            "",
        ).strip()

        missing = [
            name
            for name, value in (
                ("BOT_TOKEN", token),
                ("SUPABASE_URL", url),
                ("SUPABASE_KEY", key),
            )
            if not value
        ]

        if missing:
            raise RuntimeError(
                "Required environment variables are missing: "
                + ", ".join(missing)
            )

        raw_admin_ids = os.getenv(
            "ADMIN_IDS",
            "",
        )

        admin_ids: set[int] = set()

        for value in raw_admin_ids.split(","):
            value = value.strip()

            if not value:
                continue

            try:
                admin_ids.add(
                    int(value)
                )
            except ValueError as exc:
                raise RuntimeError(
                    "ADMIN_IDS contains a non-numeric value: "
                    f"{value}"
                ) from exc

        if not admin_ids:
            raise RuntimeError(
                "ADMIN_IDS must contain at least one Telegram ID"
            )

        return cls(
            bot_token=token,
            supabase_url=url,
            supabase_key=key,
            admin_ids=frozenset(
                admin_ids
            ),
            restaurant_phone=os.getenv(
                "RESTAURANT_PHONE",
                "+998 90 000 00 00",
            ).strip(),
            restaurant_address=os.getenv(
                "RESTAURANT_ADDRESS",
                "Oazis Fast Food",
            ).strip(),
            inpay_merchant_id=os.getenv(
                "INPAY_MERCHANT_ID",
                "",
            ).strip(),
            inpay_merchant_token=os.getenv(
                "INPAY_MERCHANT_TOKEN",
                "",
            ).strip(),
            inpay_callback_url=os.getenv(
                "INPAY_CALLBACK_URL",
                "",
            ).strip(),
        )