def profrun(x,y):
   import cProfile
##   cProfile.run(x) # For printing the output in terminal
   cProfile.run(x,filename=y)

   return









##   import pstats
##   p = pstats.Stats('restats')
##   p.strip_dirs().sort_stats(-1).print_stats()
##   p.sort_stats('name')
##   p.print_stats()
