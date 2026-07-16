class BaseLearningRuntime:
    """
    Abstract Base Class defining the Adaptive Learning SDK Contract.
    Continually calibrates parameters, maps recipe memory, logs failures,
    and checks for performance regressions.
    """
    def initialize(self, config: dict) -> None:
        """
        Optional initialization logic.
        """
        pass

    def get_metadata(self) -> dict:
        """
        Returns metadata:
        - id: Unique learning runtime ID
        - version: Version string
        - inputs: Expected input profile metrics
        - outputs: Recommendation properties
        """
        raise NotImplementedError("Learning runtimes must implement get_metadata method.")

    def learn(self, input_data: dict, outcome_data: dict) -> dict:
        """
        Processes new image evaluation telemetry to update offline intelligence files.
        """
        raise NotImplementedError("Learning runtimes must implement learn method.")

    def apply_policy(self, profile, context: dict = None) -> dict:
        """
        Recommends parameter adjustments based on historical evidence.
        """
        return {}
