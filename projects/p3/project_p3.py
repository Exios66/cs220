"""
Loads data from madison_budget.csv.
Provides public functions for interacting with this data without
needing to know how to open csv data or how to index into a dict/list.
"""

import csv

_years: list[int] = []
_budget_by_id_and_year: dict[tuple[int, int], float] = {}
_id_by_agency: dict[str, int] = {}


def init(path: str) -> None:
    """Loads data; must be called before other module member functions"""

    with open(path, encoding="utf-8") as f:
        data = list(csv.reader(f))

    for agency_idx in range(1, len(data)):
        agency = data[agency_idx][1]
        agency_id = int(data[agency_idx][0])
        _id_by_agency[agency] = agency_id
        for year_idx in range(2, len(data[0])):
            year = int(data[0][year_idx])
            if year not in _years:
                _years.append(year)
            agency_budget = float(data[agency_idx][year_idx])
            _budget_by_id_and_year[(agency_id, year)] = agency_budget


def dump() -> None:
    """prints all of the currently loaded csv data"""

    _check_did_initialize()

    for agency in sorted(_id_by_agency.keys()):
        agency_id = _id_by_agency[agency]
        print(f"{agency} [ID: {agency_id}]")
        for year in _years:
            print(f"-{year}: ${_budget_by_id_and_year[(agency_id, year)]} MIL")
        print()


def get_id(agency: str) -> int:
    """The ID of the specified agency with the provided name"""

    _check_did_initialize()

    if not agency in _id_by_agency:
        raise ValueError(
            (
                f"Agency {agency} does not exist in the currently loaded data. Please check"
                f"your argument against these available options: {','.join(_id_by_agency.keys())}"
            )
        )
    return _id_by_agency[agency]


def get_budget(agency_id: int, year: int = 2023) -> float:
    """The budget (in millions of dollars) allotted to the specified agency that year"""

    _check_did_initialize()

    if (agency_id, year) not in _budget_by_id_and_year:
        raise KeyError(
            (
                f"Could not find data for {agency_id=}, in {year=}. Please check the .csv file "
                "that is currently loaded to see valid ID and year pairs. Also check your data "
                "types. Both agency_id and year should be integers."
            )
        )
    return _budget_by_id_and_year[(agency_id, year)]


class _DidNotInitializeError(Exception):
    """Custom exception to raise when student did not call project.init"""

    _DID_NOT_INITIALIZE_MSG = (
        "You must call project.init before calling this function. "
        "Please scroll to the top of the current lab or projection "
        "and run the cell containing project.init(...)."
    )

    def __init__(self, message=_DID_NOT_INITIALIZE_MSG):
        super().__init__(message)


def _check_did_initialize() -> None:
    """Common logic for functions that need init to be called before them"""

    if len(_id_by_agency) == 0:
        raise _DidNotInitializeError()
