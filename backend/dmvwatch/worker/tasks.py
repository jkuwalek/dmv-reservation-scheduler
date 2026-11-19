"""Work the arq worker runs. Kept thin: the logic belongs in the services."""

from collections.abc import Sequence

from dmvwatch.domain.models import SweepResult, TransactionType
from dmvwatch.domain.protocols import SlotSource
from dmvwatch.services.sweep import SweepService


async def sweep_all_offices(
    service: SweepService,
    source: SlotSource,
    transaction_type: TransactionType,
) -> Sequence[SweepResult]:
    return [await service.sweep(office, transaction_type) for office in source.offices()]
