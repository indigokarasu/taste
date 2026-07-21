# taste

<p align="center">
<img src="./assets/readme/hero.jpg" width="100%" alt="Taste: personalized recommendation engine — builds taste models from real consumption signals for food, travel, and shopping.">
</p>

taste — Taste: personalized recommendation engine — builds taste models from real consumption signals for food, travel, and shopping.


> Tell it what you need. It does the work.

## What it does

Taste extracts consumption signals from email and calendar data (DoorDash, Instacart, Tock, OpenTable, Amazon, hotel bookings, and more), deduplicates across confirmation/reminder/cancellation chains, and enriches venue entities with taste-relevant attributes via Google Maps. Every recommendation is grounded in real behavior, only suggests new places, and respects dietary restrictions. Signals decay over time using a configurable half-life.

## Dependencies

- [Sift](https://github.com/indigokarasu/sift) — additional item enrichment via web research
- [Elephas](https://github.com/indigokarasu/elephas) — Chronicle entity context (read-only)
- User's email account, Google Calendar, Google Maps

---

*taste is part of the [OCAS Agent Suite](https://github.com/indigokarasu).*