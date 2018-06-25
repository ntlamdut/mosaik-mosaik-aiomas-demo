"""Some utility functions for the MAS."""
import aiomas
import arrow
import click


def get_container_kwargs(start_date):
    """Return a dictionary with keyword arguments *(kwargs)* used by both, the
    root container, and the containers in the sub processes.

    *start_date* is an Arrow date-time object used to initialize the container
    clock.

    """
    return {
        'clock': aiomas.ExternalClock(start_date, init_time=-1),
        'codec': aiomas.MsgPackBlosc,
    }


def validate_addr(ctx, param, value):
    """*Click* validator that makes sure that *value* is a valid address
    *host:port*."""
    try:
        host, port = value.rsplit(':', 1)
        return (host, int(port))
    except ValueError as e:
        raise click.BadParameter(e)


def validate_start_date(ctx, param, value):
    """*Click* validator that makes sure that *value* is a date string that
    *arrow* can parse."""
    try:
        arrow.get(value)  # Check if the date can be parsed
    except arrow.parser.ParserError as e:
        raise click.BadParameter(e)
    return value
