# Security Policy

## Reporting Security Issues

**Please do not report security vulnerabilities through public GitHub issues.**

Email security issues to: `contact@xxanqw.pp.ua`

## Security Considerations

JustDD requires elevated privileges to write to disk devices. This creates inherent security risks:

- **Data Loss**: Can permanently erase drives
- **Privilege Escalation**: Uses `pkexec` for root access
- **Input Validation**: Processes user-selected ISO files and devices

## Best Practices

- Always verify target drive before flashing
- Only use ISOs from trusted sources
- Keep system and dependencies updated
- Run as regular user (never as root)

## Supported Versions

Only the latest release receives security updates.
