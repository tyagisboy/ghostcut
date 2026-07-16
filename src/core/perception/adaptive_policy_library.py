class AdaptivePolicyLibrary:
    """
    Standard preset processing templates selected automatically based on scene context.
    """
    def __init__(self):
        self.library = {
            "Studio Portrait": {
                "active_regions": ["skin", "hair", "fabric"],
                "erode_size": 2,
                "preserve_transparency": True,
                "multi_scale": False
            },
            "Outdoor Portrait": {
                "active_regions": ["skin", "hair", "fabric", "shadow"],
                "erode_size": 3,
                "preserve_transparency": True,
                "multi_scale": True
            },
            "Curly Hair": {
                "active_regions": ["skin", "hair"],
                "erode_size": 1,
                "preserve_transparency": True,
                "multi_scale": True
            },
            "Straight Hair": {
                "active_regions": ["skin", "hair"],
                "erode_size": 2,
                "preserve_transparency": True,
                "multi_scale": False
            },
            "Wet Hair": {
                "active_regions": ["skin", "hair"],
                "erode_size": 3,
                "preserve_transparency": False,
                "multi_scale": True
            },
            "Pets": {
                "active_regions": ["fur"],
                "erode_size": 2,
                "preserve_transparency": True,
                "multi_scale": True
            },
            "Jewelry": {
                "active_regions": ["metal", "glass", "accessories"],
                "erode_size": 2,
                "preserve_transparency": False,
                "multi_scale": False
            },
            "Glass": {
                "active_regions": ["glass", "transparent"],
                "erode_size": 2,
                "preserve_transparency": True,
                "multi_scale": False
            },
            "Plants": {
                "active_regions": ["accessories"],
                "erode_size": 3,
                "preserve_transparency": False,
                "multi_scale": True
            },
            "Food": {
                "active_regions": ["accessories"],
                "erode_size": 2,
                "preserve_transparency": False,
                "multi_scale": False
            }
        }

    def get_policy(self, name: str) -> dict:
        return self.library.get(name, self.library["Studio Portrait"] if "Studio" in name else self.library["Food"])
