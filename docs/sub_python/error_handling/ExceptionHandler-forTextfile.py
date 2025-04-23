## Exception Handler for Text files
def HandleException(x):
    try:
        f = open(x)
        print(f.read())

    except FileNotFoundError:
## Raised when a file or directory is requested but doesn’t exist.         
        print('File doesnot exists')

    except (IOError, ValueError):
## Raised when a built-in operation or function receives an argument that has the right type but an inappropriate value
        print("Non-numeric data found in the file")

    except Exception:
## All built-in, non-system-exiting exceptions are derived from this class.
        print("An error occurred.")

    except KeyboardInterrupt:
## Raised when the user hits the interrupt key (normally Control-C or Delete)
        print('You cancelled the operation.')


HandleException('Values.txt')


