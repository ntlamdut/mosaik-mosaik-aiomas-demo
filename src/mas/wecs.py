import aiomas


# To make the difference between WECS simulation model and WECS agent more
# clear, this class has the suffix "Agent".  In a real project, I would just
# name the class "WECS":
class WecsAgent(aiomas.Agent):
    """A WecsAgent is the “brain” of a simulated or real WECS.

    This class should not be instantiated directly but only via the
    :meth:`create()` factory function: ``wecs = WECS.create(...)``.  That
    function performs some async. tasks (like registering the agent with the
    Controller agent) which cannot be done in ``__init__()``.

    """
    def __init__(self, container, controller, model_conf):
        super().__init__(container)
        self.controller = controller
        self.model_conf = model_conf
        self.new_P_max = None

    @classmethod
    async def create(cls, container, controller_address, model_conf):
        """Return a new :class:`WecsAgent` instance.

        *container* is the container that the agent lives in.

        *controller_address* is the address of the Controller agent that the
        agent will register with.

        *model_conf* is a dictionary containing values for *P_rated*,
        *v_rated*, *v_min*, *v_max* (see the WECs model for details).

        """
        # We use a factory function here because __init__ cannot be a coroutine
        # and creating init *tasks* init __init__ on whose results other
        # coroutines depend is bad style, so we better to all that stuff
        # before we create the instance and then have a fully initialized
        # instance.
        #
        # Classmethods don't receive an instance "self" but the class object as
        # an argument, hence the argument name "cls".
        controller = await container.connect(controller_address)
        wecs = cls(container, controller, model_conf)
        await controller.register(wecs)
        return wecs

    @aiomas.expose
    def update_state(self, state):
        """Receive the current state of the simulated WECS from the
        MosaikAgent."""
        self.P = state['P']

    @aiomas.expose
    def get_P(self):
        """Return current power output of the simulated WECS.

        Called by the Controller agent.

        """
        return self.P

    @aiomas.expose
    def set_P_max(self, P_max):
        """Allows the Controller agent to set a new power limit *P_Max* for the
        simulated wecs."""
        if P_max is None:
            P_max = self.model_conf['P_rated']

        self.new_P_max = P_max

    @aiomas.expose
    async def get_P_max(self):
        """Return the current power limit to the MosaikAgent."""
        return self.new_P_max
