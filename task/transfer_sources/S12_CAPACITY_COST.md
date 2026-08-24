# Capacity, spool, and migration cost model

## Capacity conclusion

us-east and eu-central can sustain the planned dual-write path through 75% under forecast load. us-west crosses the 80% CPU safety ceiling above 60% unless two StreamCore shards are added first.
Current encrypted spool capacity is six hours in us-west and eight hours elsewhere. The E-31 continuity target is twelve hours at projected peak in every region; storage and replay throughput must be expanded before promotion beyond 25%.
The two-shard us-west expansion and twelve-hour spools fit the approved quarterly budget. Permanent full dual-write does not; dual-write is a bounded migration control, not the steady-state design.

## Forecast

| region | candidate traffic | projected CPU | spool hours | disposition |
|---|---|---|---|---|
| us-east | 0% | 54.0% | 4.5h | within-plan |
| us-west | 0% | 63.0% | 4.5h | within-plan |
| eu-central | 0% | 58.0% | 4.5h | within-plan |
| us-east | 5% | 55.2% | 4.8h | within-plan |
| us-west | 5% | 64.6% | 4.9h | within-plan |
| eu-central | 5% | 59.2% | 4.8h | within-plan |
| us-east | 10% | 56.4% | 5.0h | within-plan |
| us-west | 10% | 66.1% | 5.2h | within-plan |
| eu-central | 10% | 60.4% | 5.0h | within-plan |
| us-east | 15% | 57.6% | 5.3h | within-plan |
| us-west | 15% | 67.7% | 5.6h | within-plan |
| eu-central | 15% | 61.6% | 5.3h | within-plan |
| us-east | 20% | 58.8% | 5.6h | within-plan |
| us-west | 20% | 69.2% | 6.0h | within-plan |
| eu-central | 20% | 62.8% | 5.6h | within-plan |
| us-east | 25% | 60.0% | 5.9h | within-plan |
| us-west | 25% | 70.8% | 6.4h | within-plan |
| eu-central | 25% | 64.0% | 5.9h | within-plan |
| us-east | 30% | 61.2% | 6.2h | within-plan |
| us-west | 30% | 72.3% | 6.8h | within-plan |
| eu-central | 30% | 65.2% | 6.2h | within-plan |
| us-east | 35% | 62.4% | 6.4h | within-plan |
| us-west | 35% | 73.8% | 7.1h | within-plan |
| eu-central | 35% | 66.4% | 6.4h | within-plan |
| us-east | 40% | 63.6% | 6.7h | within-plan |
| us-west | 40% | 75.4% | 7.5h | within-plan |
| eu-central | 40% | 67.6% | 6.7h | within-plan |
| us-east | 45% | 64.8% | 7.0h | within-plan |
| us-west | 45% | 76.9% | 7.9h | within-plan |
| eu-central | 45% | 68.8% | 7.0h | within-plan |
| us-east | 50% | 66.0% | 7.2h | within-plan |
| us-west | 50% | 78.5% | 8.2h | within-plan |
| eu-central | 50% | 70.0% | 7.2h | within-plan |
| us-east | 55% | 67.2% | 7.5h | within-plan |
| us-west | 55% | 80.1% | 8.6h | within-plan |
| eu-central | 55% | 71.2% | 7.5h | within-plan |
| us-east | 60% | 68.4% | 7.8h | within-plan |
| us-west | 60% | 81.6% | 9.0h | within-plan |
| eu-central | 60% | 72.4% | 7.8h | within-plan |
| us-east | 65% | 69.6% | 8.1h | within-plan |
| us-west | 65% | 83.1% | 9.4h | expand-before-advance |
| eu-central | 65% | 73.6% | 8.1h | within-plan |
| us-east | 70% | 70.8% | 8.3h | within-plan |
| us-west | 70% | 84.7% | 9.8h | expand-before-advance |
| eu-central | 70% | 74.8% | 8.3h | within-plan |
| us-east | 75% | 72.0% | 8.6h | within-plan |
| us-west | 75% | 86.2% | 10.1h | expand-before-advance |
| eu-central | 75% | 76.0% | 8.6h | within-plan |
| us-east | 80% | 73.2% | 8.9h | within-plan |
| us-west | 80% | 87.8% | 10.5h | expand-before-advance |
| eu-central | 80% | 77.2% | 8.9h | within-plan |
| us-east | 85% | 74.4% | 9.2h | within-plan |
| us-west | 85% | 89.4% | 10.9h | expand-before-advance |
| eu-central | 85% | 78.4% | 9.2h | within-plan |
| us-east | 90% | 75.6% | 9.4h | within-plan |
| us-west | 90% | 90.9% | 11.2h | expand-before-advance |
| eu-central | 90% | 79.6% | 9.4h | within-plan |
| us-east | 95% | 76.8% | 9.7h | within-plan |
| us-west | 95% | 92.4% | 11.6h | expand-before-advance |
| eu-central | 95% | 80.8% | 9.7h | within-plan |
| us-east | 100% | 78.0% | 10.0h | within-plan |
| us-west | 100% | 94.0% | 12.0h | expand-before-advance |
| eu-central | 100% | 82.0% | 10.0h | within-plan |

## Economic gate

Cost is subordinate to integrity and residency hard gates, but the plan must name when migration-only capacity can be retired and what evidence authorizes that effect.
