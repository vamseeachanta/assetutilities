from cProfileFunc import profrun

##import cProfile


def printme(str):
    "This prints a passed string into this function"
    print(str)
    return


printme("fdirst line")
printme("second line")

profrun('printme("Now Profile function running..")')


##cProfile.run('printme("Profile Check")')
