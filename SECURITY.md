# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | ✅ Active          |
| < 1.0   | ❌                 |

## Reporting a vulnerability

We take security seriously. If you discover a security issue, **do not** open
a public issue. Instead, report it privately.

- **Email:** `sabynextdoor@gmail.com`
- **Subject:** `[AeroQR Security] <short-description>`

Please include:

1. The affected version(s).
2. A description of the vulnerability and how to reproduce it.
3. The impact you believe the issue has.

You should normally receive a reply within **72 hours**. If the issue is
confirmed, we will work towards a fix and coordinate a coordinated disclosure
with you.

## Security considerations for drone use

AeroQR's drone control uses an **unauthenticated UDP command channel**. Only
deploy this on trusted, isolated networks:

- Never expose the command port (`8888`) to the public internet.
- Place the drone and ground station on a dedicated Wi-Fi or ad-hoc network.
- Prefer flight controllers that support authenticated command protocols for
  production deployments.
- Always keep a manual kill-switch/recovery procedure available during any
  autonomous run.