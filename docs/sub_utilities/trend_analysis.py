import pandas as pd


class TrendAnalysis:
    def __init__(self):
        pass

    def find_dff_in_2_Dicts(self, cfg_ta):
        print("perform trend analysis")
        df = cfg_ta["df"]
        print(df.columns)


if __name__ == "__main__":
    trend_analysis = TrendAnalysis()
    csv_filename = "2022-04-15_incidents.csv"
    df = pd.read_csv(csv_filename)
