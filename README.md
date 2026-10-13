[README.md](https://github.com/user-attachments/files/33398263/README.md)
# Distribution Centre Goods-In Simulation

A discrete event simulation (DES) of inbound supplier deliveries at a retail distribution centre (DC), built in Python with SimPy.

Supplier trucks arrive at the DC, wait in the yard for a free dock door, wait at the dock for an unloading team, are unloaded, and leave. The model is used to explore how many dock doors and unloading teams are needed to keep truck waiting times acceptable.

**Note:** all parameter values are illustrative assumptions, not real data.

## Study question

How do the number of dock doors and the number of unloading teams affect truck waiting times and resource utilisation, and which of the two resources is the bottleneck?

## Scope and Boundaries 

- **In scope:** truck arrivals, the yard queue, dock doors, unloading teams, unloading, departure
- **Out of scope:** suppliers, put-away of pallets after unloading, outbound shipments to stores

## Model components

| Component | Type | Description |
|---|---|---|
| Truck | Entity | Attribute: number of pallets |
| Yard queue | Queue | First in, first out; unlimited length |
| Dock door | Resource | Capacity: number of docks |
| Unloading team | Resource | Capacity: number of teams |

## Process flow

1. A truck arrives at the DC
2. It waits in the yard until a dock door is free
3. At the dock, it waits until an unloading team is free
4. The team unloads all pallets
5. The team is released, then the dock is released, and the truck leaves

The dock stays occupied while the truck waits for a team, as it would in practice.

## Input data (illustrative)

| Parameter | Distribution | Value |
|---|---|---|
| Time between truck arrivals | Exponential (Poisson arrivals) | Mean 11 minutes |
| Pallets per truck | Discrete uniform | 20 to 26 |
| Unloading time per pallet | Triangular | Min 1.5, mode 2, max 3 minutes |

On average a truck needs about 50 minutes of unloading.

## Assumptions and Simplifications

- The DC operates 24 hours a day, 7 days a week, with a constant arrival rate
- Unloading time depends only on the number of pallets; docking and paperwork time are ignored
- All docks and teams are identical, and any truck can use any dock
- Trucks do not leave the queue, and there is no booking system
- All loads are of the same type (no chilled or frozen distinction)

## Performance measures

- Mean wait in the yard and mean wait for a team
- Mean time in system
- Maximum total wait
- Percentage of trucks waiting more than 60 minutes
- Dock and team utilisation

## Example results

One replication of 7 days:

| Docks | Teams | Mean yard wait | Mean team wait | Mean time in system | Trucks waiting > 1 hour |
|---|---|---|---|---|---|
| 6 | 5 | 41 min | 8 min | 99 min | 26% |
| 8 | 5 | 30 min | 19 min | 99 min | 26% |
| 6 | 6 | 9 min | 0 min | 59 min | 3% |

## Findings

- **Unloading teams are the bottleneck in the base case.** Adding two dock doors without adding teams does not reduce time in system; waiting simply moves from the yard to the dock. Adding one team cuts time in system by about 40%.
- **Waiting time rises sharply near full utilisation.** In the single-resource version, removing one dock (6 to 5) increased the mean wait from about 9 to about 49 minutes, as utilisation approached 90%.

## Verification

With one team per dock, trucks never wait for a team, and the results match the earlier dock-only version of the model exactly. This confirms that adding the second resource did not change the original logic.

## Limitations

- Results are based on a single replication, so they carry no confidence intervals
- Warm-up period has not been determined: the model starts empty
- Trucks still waiting or unloading at the end of the run are not included in the measures
- Scenarios do not use common random numbers, so random variation differs slightly between configurations
