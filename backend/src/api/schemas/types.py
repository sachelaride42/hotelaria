from decimal import Decimal
from typing import Annotated

from pydantic import Field

ValorMonetario = Annotated[Decimal, Field(ge=0, decimal_places=2)]
