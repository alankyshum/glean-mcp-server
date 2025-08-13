def test_public_api_exports():
    import glean_mcp
    assert hasattr(glean_mcp, "glean_search")
    assert hasattr(glean_mcp, "glean_chat")
    assert hasattr(glean_mcp, "glean_read_documents")
    assert hasattr(glean_mcp, "GleanClient")
    assert hasattr(glean_mcp, "CookieExpiredError")
