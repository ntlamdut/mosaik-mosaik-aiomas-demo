import asyncio

import aiomas


class Controller(aiomas.Agent):
    """The Controller agent knows all WecsAgents of its wind farm.

    It regularly (every *check_interval* seconds) collects the current power
    output of all WECS from the WecsAgents and checks if the total power output
    exceeds *max_windpark_feedin*.  If so, it sets power limits to the WECS.
    It also requires the *start_date* of the simulation to calculate the
    initial check time.

    """
    def __init__(self, container, *,
                 start_date, check_interval, max_windpark_feedin):
        super().__init__(container)
        self.start_date = start_date
        self.check_interval = check_interval
        self.max_windpark_feedin = max_windpark_feedin

        self.wecs = []  # List of WecsAgent proxies registered with us.

        # Schedule the cyclic wind park feed-in check:
        self.cycle_done = asyncio.Future()
        self.t_check_feedin = aiomas.create_task(self.check_windpark_feedin())

    async def stop(self):
        """Stop the agent and cancel all background tasks."""
        if not self.t_check_feedin.done():
            self.t_check_feedin.cancel()
            try:
                # We just cancelled this task so it will raise a CancelledError
                # which we need to catch.
                await self.t_check_feedin
            except asyncio.CancelledError:
                pass  # Because we just cancelled the task on purpose :)

        # If we had multiple tasks that we wanted to cancel and wait for and we
        # didn't wanna repeat the try...except block, we could also do this::
        #
        #     tasks = []
        #     if not self.task_a.done():
        #         self.task_a.cancel()
        #         tasks.append(self.task_a)
        #
        #     if self.task_b is not None and not self.task_b.done():
        #         self.task_b.cancel()
        #         tasks.append(self.task_b)
        #
        #     # Wait for tasks ignoring their CancelledErrors:
        #     await asyncio.gather(*tasks, return_exceptions=True)

    @aiomas.expose
    def register(self, wecs_proxy):
        """Called by WecsAgents to register themselves with this controller."""
        # We don't want duplicate registrations:
        assert wecs_proxy not in self.wecs
        self.wecs.append(wecs_proxy)

    @aiomas.expose
    async def step_done(self):
        """Used by the MosaikAgent to wait until one cycle of the feed-in check
        is done."""
        await self.cycle_done

    async def check_windpark_feedin(self):
        """Background task that repeatedly checks if the cumulated feed-in of
        all WECS exceeds a given limit for the wind park."""
        # Repeat until cancelled:
        sleep_until = self.start_date  # Initial time; updated every cycle.
        check_interval = self.check_interval
        max_feedin = self.max_windpark_feedin

        while True:
            await self.container.clock.sleep_until(sleep_until)
            futs = [wecs.get_P() for wecs in self.wecs]
            wecs_feedin = await asyncio.gather(*futs)
            current_feedin = sum(wecs_feedin)

            if current_feedin > max_feedin:
                # Set new power limits *P_max* for all WECS
                factor = max_feedin / current_feedin
                P_max = [P * factor for P in wecs_feedin]

                # Check invariant: "sum(P_max) == max_feedin", but use
                # subtraction to check float-equality
                assert abs(sum(P_max) - max_feedin) < 0.01

                # Prepare the calls to the WecsAgents
                futs = [w.set_P_max(p) for (w, p) in zip(self.wecs, P_max)]
            else:
                # Reset *P_max* for all WECS
                # Prepare the calls to the WecsAgents
                futs = [w.set_P_max(None) for w in self.wecs]

            # Actually make the calls and wait until they’re done:
            await asyncio.gather(*futs)

            # Set result for "cycle_done" so that the MosaikAgent knows we
            # are ready.  Create a new future for the next cycle.
            self.cycle_done.set_result(None)
            self.cycle_done = asyncio.Future()

            # Get the new time until which to sleep:
            sleep_until = sleep_until.replace(seconds=check_interval)
