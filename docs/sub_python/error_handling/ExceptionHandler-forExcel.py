## Exception /Handler for Excel files
def HandleExcep(x):
    import xlrd

    try:
        file = x
        wb = xlrd.open_workbook(file)
        sheet = wb.sheet_by_index(0)
        [
            [sheet.cell_value(r, c) for c in range(sheet.ncols)]
            for r in range(sheet.nrows)
        ]

    except ImportError:
        ## If python cannot find the module
        print("No module found")

    except FileNotFoundError:
        ## Raised when a file or directory is requested but doesn’t exist.
        print("Provided file does not exists")

    except Exception:
        ## All built-in, non-system-exiting exceptions are derived from this class.
        print("Occureed an error")

    except AttributeError:
        ## Raised when an attribute reference or assignment fails. When an object does not support attribute references or attribute assignments at all, TypeError is raised.
        print("object or variable you defined have no Attributes")

    except KeyboardInterrupt:
        ## Raised when the user hits the interrupt key (normally Control-C or Delete)
        print("You cancelled the operation")


HandleExcep("riserStackup.xlsx")
