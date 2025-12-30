from datetime import date, datetime, timedelta
from typing import Tuple, Union

DateLike = Union[date, datetime]


def range_date(
    central_day: DateLike,
    offset: int
) -> Tuple[DateLike, DateLike]:
    """
    Retorna um intervalo de datas baseado em um dia central.

    :param central_day: date ou datetime central
    :param offset: número de dias para subtrair e somar
    :return: (start_date, stop_date)
    """
    delta = timedelta(days=offset)

    start_date = central_day - delta
    stop_date = central_day + delta

    return start_date, stop_date
