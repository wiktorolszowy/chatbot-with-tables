# Contact: Wiktor Olszowy, olszowyw@gmail.com

from contextlib import contextmanager
from typing import Any, Generator, Optional

import pandas as pd
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent


class CustomPdDataFrameAgentWithContext:
    """
    A custom agent for handling pandas DataFrame operations within a context manager.

    Attributes:
        llm: The language model to be used by the agent.
        verbose: If True, enables verbose logging.
        allow_dangerous_code: If True, allows execution of potentially dangerous code.
        agent_type: The type of agent to be created.
        kwargs: Additional keyword arguments to be passed to the agent.
    """

    def __init__(
        self,
        llm: Any,
        verbose: bool = False,
        allow_dangerous_code: bool = False,
        agent_type: str = "default",
        **kwargs: Any,
    ) -> None:
        """
        Initializes the CustomPdDataFrameAgentWithContext.

        Args:
            llm: The language model to be used by the agent.
            verbose: If True, enables verbose logging.
            allow_dangerous_code: If True, allows execution of potentially dangerous code.
            agent_type: The type of agent to be created.
            kwargs: Additional keyword arguments to be passed to the agent.
        """
        self.llm = llm
        self.verbose = verbose
        self.allow_dangerous_code = allow_dangerous_code
        self.agent_type = agent_type
        self.kwargs = kwargs
        self.data: Optional[pd.DataFrame] = None

    @contextmanager
    def inject_dataframe(self, data: pd.DataFrame) -> Generator[None, None, None]:
        """
        Context manager to inject a pandas DataFrame into the agent.

        Args:
            data: The pandas DataFrame to be injected.

        Yields:
            None
        """
        self.data = data
        yield
        self.data = None

    def invoke(self, message: str) -> Any:
        """
        Invokes the agent with the provided message.

        Args:
            message: The message to be processed by the agent.

        Returns:
            The result of the agent's invocation.

        Raises:
            ValueError: If the DataFrame is not provided using the context manager.
        """
        if self.data is None:
            raise ValueError("DataFrame must be provided using the context manager.")

        agent = create_pandas_dataframe_agent(
            self.llm,
            self.data,
            verbose=self.verbose,
            allow_dangerous_code=self.allow_dangerous_code,
            agent_type=self.agent_type,
            **self.kwargs,
        )
        return agent.invoke(message)