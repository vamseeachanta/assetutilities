from assetutilities.modules.csv_utilities.csv_utilities import CSVUtilities

csv_utilities = CSVUtilities()


class CSVUtilitiesRouter:
    def router(self, cfg):
        if cfg["csv_utilities"]["encoding"] == "latin1":
            pass

        return cfg
