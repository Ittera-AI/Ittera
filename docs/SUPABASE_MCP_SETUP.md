# Supabase MCP Server Setup Guide

## Overview
The Supabase MCP (Model Context Protocol) server allows direct database operations, schema management, and monitoring through AI assistants.

## Configuration Status

✅ **Config file created:** `.mcp.json` at project root

## Next Steps: Authentication

The Supabase MCP server uses OAuth 2.1 authentication. To complete setup:

### Step 1: Verify MCP Server is Reachable
```bash
curl -so /dev/null -w "%{http_code}" https://mcp.supabase.com/mcp
# Expected: 401 (no token) - means server is up
```

### Step 2: Authenticate
1. Open your Cursor IDE
2. The MCP server should prompt you to authenticate when you try to use a Supabase tool
3. Complete the OAuth flow in your browser
4. Return to Cursor - the session should be authenticated

### Step 3: Verify Connection
Once authenticated, you can test with these MCP tools:

| Tool | Purpose |
|------|---------|
| `execute_sql` | Run SQL directly on your Supabase database |
| `get_advisors` | Run database advisors for best practices |
| `search_docs` | Search Supabase documentation |

## Available MCP Tools

### 1. execute_sql
Run SQL queries directly on your Supabase database:

```json
{
  "query": "SELECT * FROM users LIMIT 10"
}
```

### 2. get_advisors
Get database optimization recommendations:

```json
{
  "advisor": "performance"  // or "security", "indexing"
}
```

### 3. search_docs
Search Supabase documentation:

```json
{
  "query": "RLS policies best practices"
}
```

## Project Database Details

Your Iterra project uses:
- **Local Development:** PostgreSQL via Docker Compose (port 5432)
- **Production:** Supabase PostgreSQL (configured via `SUPABASE_URL`)

### Connection Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Cursor    │────▶│  MCP Server │────▶│ Supabase Postgres│
│  (Claude)   │     │  (Proxy)    │     │   (Cloud/Local)  │
└─────────────┘     └─────────────┘     └─────────────────┘
```

## Common Use Cases

### 1. Ad-hoc Queries
```sql
-- Check user count
SELECT COUNT(*) FROM users;

-- Find content plans by niche
SELECT niche, COUNT(*) FROM content_plans GROUP BY niche;
```

### 2. Schema Validation
```sql
-- Check table structure
\d users

-- List all indexes
SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public';
```

### 3. RLS Policy Management
```sql
-- Enable RLS on a table
ALTER TABLE content_plans ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY "Users can only see their own plans"
ON content_plans FOR SELECT
USING (user_id = auth.uid());
```

## Troubleshooting

### Issue: MCP tools not appearing
**Solution:** Reload Cursor window after authentication completes

### Issue: "Server unreachable" error
**Check:**
```bash
# Test connectivity
curl https://mcp.supabase.com/mcp
# Should return 401 (unauthorized) if server is up
```

### Issue: Authentication fails
**Check:**
1. Verify `.mcp.json` is in project root
2. Ensure you're logged into Supabase in your browser
3. Check if your Supabase project is active

## Security Notes

⚠️ **Important:** The MCP server has direct database access. Be careful with:
- `DELETE` or `DROP` operations
- Modifying production data
- Exposing sensitive user data in queries

## References

- [Supabase MCP Documentation](https://supabase.com/docs/guides/getting-started/mcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

---

**Last Updated:** 2026-05-28
**Status:** Configuration complete - awaiting authentication
