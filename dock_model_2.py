"""
Inbound goods-in docks and unloading teams at a distribution centre (DC)

Supplier trucks arrive at random and wait in the yard for a free dock door.
Once at a dock, a truck waits for a free unloading team, is unloaded, then
releases the team and the dock and leaves. Time is measured in minutes.

All parameter values are illustrative assumptions, not real data.
"""

import numpy as np
import simpy

MINUTES_PER_DAY = 24 * 60


class DistributionCentre:
    """Goods-in area of a DC with limited dock doors and unloading teams."""

    def __init__(self, env, rng, n_docks, n_teams, mean_interarrival,
                 pallets_range, unload_time_per_pallet):
        self.env = env
        self.rng = rng
        self.docks = simpy.Resource(env, capacity=n_docks)
        self.teams = simpy.Resource(env, capacity=n_teams)
        self.mean_interarrival = mean_interarrival
        self.pallets_range = pallets_range                    # (min, max)
        self.unload_time_per_pallet = unload_time_per_pallet  # (min, mode, max)

        # Results: one record per truck that has finished unloading
        self.yard_waits = []       # arrival until a dock is free
        self.team_waits = []       # at the dock, until a team is free
        self.times_in_system = []  # arrival until departure
        self.dock_busy_time = 0.0  # docks are occupied while waiting for a team too
        self.team_busy_time = 0.0

        self.env.process(self.generate_trucks())

    def generate_trucks(self):
        """Trucks arrive, inter-arrival times follow an exponential distribution (Poisson arrivals)."""
        truck_id = 0
        while True:
            yield self.env.timeout(self.rng.exponential(self.mean_interarrival))
            truck_id += 1
            self.env.process(self.truck(truck_id))

    def truck(self, truck_id):
        """Life cycle of one truck: arrive, queue for a dock, wait for a team, unload, leave."""
        arrival_time = self.env.now
        n_pallets = self.rng.integers(self.pallets_range[0], self.pallets_range[1] + 1)

        with self.docks.request() as dock_request:
            yield dock_request                              # wait in the yard
            docked_time = self.env.now

            with self.teams.request() as team_request:
                yield team_request                          # wait at the dock for a team
                team_start = self.env.now

                low, mode, high = self.unload_time_per_pallet
                unload_time = self.rng.triangular(low, mode, high, size=n_pallets).sum()
                yield self.env.timeout(unload_time)         # unload
                # team is released here, when the inner "with" block ends

            # dock is released here, when the outer "with" block ends
            departure_time = self.env.now
            self.yard_waits.append(docked_time - arrival_time)
            self.team_waits.append(team_start - docked_time)
            self.times_in_system.append(departure_time - arrival_time)
            self.dock_busy_time += departure_time - docked_time
            self.team_busy_time += unload_time


def run(n_docks=6, n_teams=5, days=7, seed=1, mean_interarrival=11,
        pallets_range=(20, 26), unload_time_per_pallet=(1.5, 2, 3)):
    """Run one replication and return a dictionary of performance measures."""
    env = simpy.Environment()
    rng = np.random.default_rng(seed)
    dc = DistributionCentre(env, rng, n_docks, n_teams, mean_interarrival,
                            pallets_range, unload_time_per_pallet)
    run_length = days * MINUTES_PER_DAY
    env.run(until=run_length)

    yard = np.array(dc.yard_waits)
    team = np.array(dc.team_waits)
    total_wait = yard + team
    return {
        "trucks_unloaded": len(yard),
        "mean_yard_wait_min": yard.mean(),
        "mean_team_wait_min": team.mean(),
        "mean_time_in_system_min": np.mean(dc.times_in_system),
        "max_total_wait_min": total_wait.max(),
        "pct_wait_over_60": (total_wait > 60).mean() * 100,
        "dock_utilisation_pct": dc.dock_busy_time / (n_docks * run_length) * 100,
        "team_utilisation_pct": dc.team_busy_time / (n_teams * run_length) * 100,
    }


if __name__ == "__main__":
    results = run(n_docks=6, n_teams=5)
    print(f"Trucks served:            {results['trucks_unloaded']}")
    print(f"Mean wait in yard:        {results['mean_yard_wait_min']:.1f} min")
    print(f"Mean wait for a team:     {results['mean_team_wait_min']:.1f} min")
    print(f"Mean time in system:      {results['mean_time_in_system_min']:.1f} min")
    print(f"Max total wait:           {results['max_total_wait_min']:.1f} min")
    print(f"Trucks waiting > 1 h:     {results['pct_wait_over_60']:.1f}%")
    print(f"Dock utilisation:         {results['dock_utilisation_pct']:.1f}%")
    print(f"Team utilisation:         {results['team_utilisation_pct']:.1f}%")
