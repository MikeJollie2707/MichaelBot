if __name__ == "__main__":
    import loot
    SIMULATION_TIME = 10 ** 6
    total: int = 0
    rate_tracker: dict[str, int] = {}

    for _ in range(0, SIMULATION_TIME):
        loot_rate = loot.get_activity_loot("nether_axe", "nether")

        for reward in loot_rate:
            if reward not in rate_tracker:
                rate_tracker[reward] = loot_rate[reward]
            else:
                rate_tracker[reward] += loot_rate[reward]
            
            total += loot_rate[reward]

    print(f"Sim {SIMULATION_TIME:,} times, total amount: {total:,}")
    for item, amount in rate_tracker.items():
        print(f"- {item}: {amount:,} / {total:,} ({float(amount) / total * 100 :.5f}%)")
