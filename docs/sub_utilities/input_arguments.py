import logging
import sys


def get_etl_parameters(kwargs):
    """
    :param kwargs:
    :return:
    Example parameters: db_name=db_name db_user_name=db_user_name sp_query="EXEC Analysis.SPGetReservoirPressure"
    """
    db_name = kwargs.get("db_name", None)
    db_user_name = kwargs.get("db_user_name", None)
    sp_query = kwargs.get("sp_query", None)
    db_config_parameters = f"Parameters for stored procedure are: {sp_query} using {db_name} & username {db_user_name}"
    if db_name is None or db_user_name is None or sp_query is None:
        logging.error(
            f"Insufficient Information to execute Stored Procedure. {db_config_parameters} ... FAIL"
        )
        raise Exception(
            f"Insufficient Information to execute Stored Procedure. {db_config_parameters} ... FAIL"
        )

    return db_name, db_user_name, sp_query


try:
    argv = sys.argv[1:]
    kwargs = {kw[0]: kw[1] for kw in [ar.split("=") for ar in argv if ar.find("=") > 0]}
    args = [arg for arg in argv if arg.find("=") < 0]
    logging.info(f"kwargs: {kwargs}")
    logging.info(f"args: {args}")

    db_name, db_user_name, sp_query = get_etl_parameters(kwargs)

except Exception as ex:
    logging.error(ex)
