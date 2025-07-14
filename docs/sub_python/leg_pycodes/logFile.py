import datetime
import os


def createLogFile():
    programStartTime = datetime.datetime.now()
    logFileName = programStartTime.strftime("%Y%m%d_%Hh%Mm") + ".log"
    # Create log directory if not existing
    logDirectory = os.getcwd() + r"\logs"
    if not os.path.exists(logDirectory):
        os.makedirs(logDirectory)

    fLog = open(logDirectory + "/" + logFileName, "w")
    return (programStartTime, fLog)


def writeRunTime(programStartTime, fLog):
    fLog.write(
        "RunTime in HH:MM:SS is " + str(datetime.datetime.now() - programStartTime)
    )
    fLog.close()
