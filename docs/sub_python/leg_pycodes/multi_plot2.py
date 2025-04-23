import glob
import pandas as pd
import matplotlib.pyplot as plt
import pylab as pl

def plot():
    
    df = pd.read_csv(files,index_col='Time')
    df[['Differential Pressure','Fuel','Gas Flow','Heat Rate',
        'Power','Temperature']].plot()
    plt.title('Compressor Data')
    plt.legend((df),scatterpoints=1,loc='upper right',ncol=3,fontsize=8)
    pl.xticks(rotation = 13)
    plt.margins(1)
    plt.show()
    
    
   
for files in glob.glob("*.csv"):

    
    print ("showing",files)
    plot()
plt.close()    
    
 plt.savefig("{}.png".format(files))   #Saves the output graph as image
 print ("Output graph saved as image")

    
