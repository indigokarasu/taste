# taste

<p align="center">
  <img src="./assets/readme/hero.jpg" width="100%" alt="Taste: builds taste models from real consumption signals for food, travel, and shopping recommendations">
</p>

Taste extracts consumption signals from email and calendar data — DoorDash, Instacart, Tock, OpenTable, Amazon, hotel bookings — deduplicates across confirmation and cancellation chains, and enriches venue entities. Recommendations are grounded in real behavior, only suggest new places, and respect dietary restrictions. Signals decay over time via a configurable half-life.

**Capabilities:**
- Email and calendar signal extraction
- Venue enrichment via Google Maps
- Decaying half-life model for stale signal pruning
