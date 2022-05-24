class ClusterDataEntry:

    def __init__(self,
                 research_id: str,
                 avg_stress: float,
                 max_stress: float) -> None:
        super().__init__()
        self.research_id = research_id
        self.avg_stress = avg_stress
        self.max_stress = max_stress

    def __str__(self) -> str:
        return "ClusterDataEntry[research_id: {}, avg_stress: {}, max_stress: {}]".format(
            self.research_id,
            self.avg_stress,
            self.max_stress)

