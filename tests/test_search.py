import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("auth_mode", ["token", "cookie"])
async def test_search_basic(clients, auth_mode):
    # pick client for requested mode if available
    for mode, client in clients:
        if mode == auth_mode:
            res = await client.search(query="test", page_size=1)
            assert isinstance(res, dict)
            assert "results" in res
            await client.close()
            return
    pytest.skip(f"{auth_mode} client not available")
