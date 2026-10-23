# Email assistant implementation checklist

## API contract

No email HTTP API is currently exposed. Email composition and local draft storage happen in the browser; Gmail sending and Gmail draft operations remain disabled until a Gmail MCP server has been selected and its real tools have been verified.

## Must-have features

- [x] Add a send-icon action to each generated response and open an accessible review composer.
- [x] Prepopulate subject/body from the generated response without mutating that response.
- [x] Allow recipient, CC, BCC, subject, and body editing; support copy and per-response local draft save.
- [ ] Select and verify a supported Gmail MCP server, including its authorization flow, exposed tool names, and schemas; then implement server-side send and Gmail draft operations.

## Additional improvements

- [ ] Add Google Contacts search and recipient selection using only the required permissions.
- [ ] Add an optional recipient-aware email quality review with actionable, non-destructive suggestions.
