cxx=4
f=34
kx=34
ky=34
E=30450
e1=34
tk=19.6
xx=0.2
yy=0.8
t1=0.1
c=1.74
s = float(input('enter s: '))
i = float(input('enter i: '))
t=float(input("enter t:"))
v=float(input("enter v:"))
e=float(input("enter e:"))
# The values for input are taken as below
# s=2.30,i=8.82,t=0.046,v=0.30,e=0.8
cyy=round((1+(s/float(i))**2)**2,2)
ct=round(5.34+4*(s/i)**2,2)
q=round(9.86960440108936*E/12/(1-v**2),2)
Exx_simp=round(cxx*q*(t/s)**2,2)
Eyy_simp=round(cyy*q*(t/s)**2,2)
TE_simp=round(ct*q*(t/s)**2,2)
from math import sqrt
x_simp=round(sqrt(kx/Exx_simp),2)
y_simp=round(sqrt(ky/Eyy_simp),2)
t_simp=round(sqrt(tk/TE_simp),2)
e_simp=round(sqrt(f/e*((xx/Exx_simp)**c+(yy/Eyy_simp)**c+(t1/TE_simp)**c)**(1/c)),2)
scrx_simp=round(kx/sqrt(1+x_simp**4),2)
scry_simp=round(ky/sqrt(1+y_simp**4),2)
scrz_simp=round(tk/sqrt(1+t_simp**4),2)
escr_simp=round(f/sqrt(1+e_simp**4),2)
sx_simp=round(xx/scrx_simp,2)
sy_simp=round(yy/scry_simp,2)
sz_simp=round(t1/scrz_simp,2)
se_simp=round(e/escr_simp,2)
print("Enter the vaule of cyy and ct is",cyy,ct)
print("Enter the value of q ,Exx_simp,Eyy_simp and TE_simp is",q,Exx_simp,Eyy_simp,TE_simp)
print('Enter the value of x_simp,y_simp,t_simp and e_simp is',x_simp,y_simp,t_simp,e_simp)
print("The value of scrx_simp,scry_simp,scrz_simp and escr_simp is",scrx_simp,scry_simp,scrz_simp,escr_simp)
print("The value of sx_simp,sy_simp,sz_simp and se_simp is",sx_simp,sy_simp,sz_simp,se_simp)
ucrx_simp1=round(kx/(sqrt(1+x_simp**4)),2)
ucrx_simp2=round(kx/sqrt(2)/x_simp,2)
if(x_simp<1):
    print("The value of ucrx_simp1 is ",ucrx_simp1)
else:
    print("The value of ucrx_simp2 is",ucrx_simp2)
ucry_simp1=round(ky/(sqrt(1+y_simp**4)),2)
ucry_simp2=round(ky/sqrt(2)/y_simp,2)
if(y_simp<1):
    print("The value of ucry_simp1 is ",ucry_simp1)
else:
    print("The value of ucry_simp2 is",ucry_simp2)
ucrz_simp1=round(tk/(sqrt(1+t_simp**4)),2)
ucrz_simp2=round(tk/sqrt(2)/t_simp,2)
if(t_simp<1):
    print("The value of ucrz_simp1 is ",ucrz_simp1)
else:
    print("The value of ucrz_simp2 is",ucrz_simp2)
eucr_simp1=round(e1/(sqrt(1+e_simp**4)),2)
eucr_simp2=round(e1/sqrt(2)/e_simp,2)
if(e_simp<1):
    print("The value of eucr_simp1 is",eucr_simp1)
else:
    print("The value of eucr_simp2 is",eucr_simp2)
ux_simp=round(xx/ucrx_simp1,2)
uy_simp=round(yy/ucry_simp2,2)
uz_simp=round(t1/ucrz_simp1,2)
ue_simp=round(e/eucr_simp1,2)
print("The value of ux_simp,uy_simp,uz_simp and ue_simp is",ux_simp,uy_simp,uz_simp,ue_simp)
input("press enter to quit")
