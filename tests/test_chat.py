import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("auth_mode", ["token", "cookie"])
async def test_chat_basic(clients, auth_mode):
    for mode, client in clients:
        if mode == auth_mode:
            text = await client.chat("hello")
            assert isinstance(text, str)
            assert len(text) >= 0
            await client.close()
            return
    pytest.skip(f"{auth_mode} client not available")
