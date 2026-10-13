"""
Inbound goods-in docks at a distribution centre (DC)

Supplier trucks arrive at random, wait in the yard for a free dock door,
unload their pallets, then leave. Time is measured in minutes.

All parameter values are illustrative assumptions, not real data.
"""

import numpy as np
import simpy

MINUTES_PER_DAY = 24 * 60


class DistributionCentre:
    """Goods-in area of a DC with a limited number of dock doors."""

    def __init__(self, env, rng, n_docks, mean_interarrival,
                 pallets_range, unload_time_per_pallet):
        self.env = env
        self.rng = rng
        self.docks = simpy.Resource(env, capacity=n_docks)
        self.mean_interarrival = mean_interarrival
        self.pallets_range = pallets_range                    # (min, max)
        self.unload_time_per_pallet = unload_time_per_pallet  # (min, mode, max)

        # Results: one record per truck that has finished unloading
        self.waiting_times = []
        self.dock_busy_time = 0.0

        self.env.process(self.generate_trucks())

    def generate_trucks(self):
        """Trucks arrive, inter-arrival times follow an exponential distribution (Poisson arrivals)."""
        truck_id = 0
        while True:
            yield self.env.timeout(self.rng.exponential(self.mean_interarrival))
            truck_id += 1
            self.env.process(self.truck(truck_id))

    def truck(self, truck_id):
        """Life cycle of one truck: arrive, queue for a dock, unload, leave."""
        arrival_time = self.env.now
        n_pallets = self.rng.integers(self.pallets_range[0], self.pallets_range[1] + 1)

        with self.docks.request() as request:
            yield request                                   # wait in the yard
            self.waiting_times.append(self.env.now - arrival_time)

            low, mode, high = self.unload_time_per_pallet
            unload_time = self.rng.triangular(low, mode, high, size=n_pallets).sum()
            yield self.env.timeout(unload_time)             # unload at the dock
            self.dock_busy_time += unload_time


def run(n_docks=6, days=7, seed=1, mean_interarrival=11,
        pallets_range=(20, 26), unload_time_per_pallet=(1.5, 2, 3)):
    """Run one replication and return a dictionary of performance measures."""
    env = simpy.Environment()
    rng = np.random.default_rng(seed)
    dc = DistributionCentre(env, rng, n_docks, mean_interarrival,
                            pallets_range, unload_time_per_pallet)
    run_length = days * MINUTES_PER_DAY
    env.run(until=run_length)

    waits = np.array(dc.waiting_times)
    return {
        "trucks_unloaded": len(waits),
        "mean_wait_min": waits.mean(),
        "max_wait_min": waits.max(),
        "pct_wait_over_60": (waits > 60).mean() * 100,
        "dock_utilisation_pct": dc.dock_busy_time / (n_docks * run_length) * 100,
    }


if __name__ == "__main__":
    results = run(n_docks=5)
    print(f"Trucks served:         {results['trucks_unloaded']}")
    print(f"Mean wait:             {results['mean_wait_min']:.1f} min")
    print(f"Max wait:              {results['max_wait_min']:.1f} min")
    print(f"Trucks waiting > 1 h:  {results['pct_wait_over_60']:.1f}%")
    print(f"Dock utilisation:      {results['dock_utilisation_pct']:.1f}%")
