import aiohttp
from loguru import logger
from config import config
from typing import Optional, dict


class SMMApiService:
    """
    Connects to any SMM panel that uses the standard SMM API v2 format.
    Compatible with: JustAnotherPanel, Peakerr, SMMHeaven, etc.
    """

    def __init__(self):
        self.url = config.SMM_API_URL
        self.key = config.SMM_API_KEY

    async def _request(self, data: dict) -> Optional[dict]:
        data["key"] = self.key
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, data=data, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    result = await resp.json()
                    return result
        except Exception as e:
            logger.error(f"SMM API Error: {e}")
            return None

    async def get_services(self) -> Optional[list]:
        result = await self._request({"action": "services"})
        return result

    async def place_order(self, service_id: str, link: str, quantity: int) -> Optional[str]:
        result = await self._request({
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity,
        })
        if result and "order" in result:
            return str(result["order"])
        logger.warning(f"Order placement failed: {result}")
        return None

    async def get_order_status(self, order_id: str) -> Optional[dict]:
        result = await self._request({
            "action": "status",
            "order": order_id,
        })
        return result

    async def get_multiple_statuses(self, order_ids: list) -> Optional[dict]:
        result = await self._request({
            "action": "status",
            "orders": ",".join(str(o) for o in order_ids),
        })
        return result

    async def get_balance(self) -> Optional[float]:
        result = await self._request({"action": "balance"})
        if result and "balance" in result:
            try:
                return float(result["balance"])
            except (ValueError, TypeError):
                pass
        return None

    async def refill_order(self, order_id: str) -> Optional[str]:
        result = await self._request({
            "action": "refill",
            "order": order_id,
        })
        if result and "refill" in result:
            return str(result["refill"])
        return None

    async def cancel_order(self, order_id: str) -> bool:
        result = await self._request({
            "action": "cancel",
            "orders": order_id,
        })
        return result is not None


smm_api = SMMApiService()
