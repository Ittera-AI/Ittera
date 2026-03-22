from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BasePipeline(ABC, Generic[InputT, OutputT]):
    """Base class for all Iterra AI pipelines.

    Subclass this to create typed, composable AI pipelines
    that can be chained and evaluated consistently.
    """

    @abstractmethod
    def run(self, input: InputT) -> OutputT:
        """Execute the pipeline with the given input.

        Args:
            input: Typed pipeline input.

        Returns:
            Typed pipeline output.
        """
        ...

    def validate_input(self, input: InputT) -> None:
        """Optional input validation hook. Override to add pre-run checks."""

    def validate_output(self, output: OutputT) -> None:
        """Optional output validation hook. Override to add post-run checks."""
