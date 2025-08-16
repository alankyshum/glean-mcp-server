import os
import pytest


DOC_ID = os.getenv("TEST_DOC_ID", "CONFLUENCE_HXQ6FQD_page_552207115")


@pytest.mark.asyncio
@pytest.mark.parametrize("auth_mode", ["token", "cookie"])
async def test_read_document_by_id(clients, auth_mode):
    for mode, client in clients:
        if mode == auth_mode:
            resp = await client.read_documents([{"id": DOC_ID}])
            assert isinstance(resp, dict)
            docs = resp.get("documents")
            assert isinstance(docs, dict)
            assert DOC_ID in docs
            await client.close()
            return
    pytest.skip(f"{auth_mode} client not available")
