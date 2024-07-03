import asyncio
import logging

from bots import registry


async def main():
    await registry.run_strategies()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
    )

    asyncio.run(main())
