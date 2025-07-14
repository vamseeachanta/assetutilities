from calculations.dynaCardCalculation import *


def start_with_arguments():
    from argumentParseFunction import argumentParseFunction

    args_dict = argumentParseFunction()
    read_file_input_and_calculate_algorithm(args_dict.file_name, args_dict.data_source)


def read_file_input_and_calculate_algorithm(file_name, data_source=None):
    from config.ConfigurationManager import ConfigurationManager

    config_manager = ConfigurationManager(main_data_source=data_source)
    configured_dependencies = config_manager.get_congured_dependencies()

    data_manager = configured_dependencies.data_manager

    input_data = data_manager.get_data(file_name)

    calculation_output = dynaCardCalculation(input_data, configured_dependencies)

    plot_manager = configured_dependencies.plot_manager
    plot_manager.plot_output(calculation_output)


if __name__ == "__main__":
    # file_name = "C://Users//kuriags//Documents//projects//code//dynacard//testData//testCases//NoError_withSurveyData.json"
    file_name = "C://Users//kuriags//Documents//projects//code//dynacard//test_scripts//input_data//GRANTHM_PO.xlsx"

    read_file_input_and_calculate_algorithm(file_name)

    # start_with_arguments()
