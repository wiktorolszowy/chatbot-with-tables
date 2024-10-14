from contextlib import contextmanager
from functools import lru_cache
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

    @lru_cache(maxsize=1)
    def get_cached_agent(self, data_id: int):
        """
        Returns a cached instance of the pandas dataframe agent.

        This method uses the lru_cache decorator with maxsize=1 to cache a single instance of the agent, separately for each df.
        The create_pandas_dataframe_agent function is called only once per df, and the result is cached for future use.

        Args:
            data_id: The unique identifier for the DataFrame.

        Returns:
            The cached agent instance.
        """

        return create_pandas_dataframe_agent(
            llm=self.llm,
            df=self.data,
            verbose=self.verbose,
            allow_dangerous_code=self.allow_dangerous_code,
            agent_type=self.agent_type,
            **self.kwargs,
        )

    def invoke(self, message: str) -> str:
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

        # Get the cached agent instance with the DataFrame's memory address as part of the cache key
        agent = self.get_cached_agent(id(self.data))

        # Process the message with the agent
        result = agent.invoke(message, self.data, **self.kwargs)

        return result["output"]
