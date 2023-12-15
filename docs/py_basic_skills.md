# Introduction

Document/Questionnaire for Basic python skils. Fill in to the best of your knowledge and share the responses.

## Tools EcoSystem

| Tools        | Category |  Installed? | Years Used? | Comments |
|--------------|:-----:|-----------:|-----------:|-----------:|
| VS Code |  General     |        yes |        2 months|        nice |
| Git |  Version control |        no |        0|        no |
| Jira  |  Programming |        no|        0 |        new thing to hear |
| Python  |  Programming |        yes |        1 year |        good one |
| Github Copilot  |  Programming |        no |        0 |        no|

## Questions

**Software Principles**

- Do you know object oriented programming?
 yes i know the basic concepts of OOP 
  - Share code where you have a function?
  #python program to remove element and return length of array
def sam(arr, val):
    i = 0
    while i < len(arr):
        if arr[i] == val:
            arr.pop(i)
        else:
            i += 1

    return len(arr)

arr = [3,2,1,3,4,3,5]
val = 3
w = sam(arr, val)
print(w)

  - Share code where you have a class?
   not familiar with
- Are you femiliar with test driven development (TDD)?
  No.
  - Can you share a program with a test in your github repository?
   no 

**Python**

- What python IDE (Integrated Development Enviornment) did you work?
  Jupyter 
- Did you work in VS Code IDE (Integrated Development Enviornment)?
  yes

**Git and Github**

- What is the difference between Git and Github?
  Github is a code platform for collaboration , i basically use it to store my project code , coding programs ,
  I am not familiar with git
- Did you work with Git?
  - Did you create a branch?
  - Did you push a branch?

- Did you work in GitHub?
  - Can you share a few programs you wrote in Github?
   i didnot wrote any program in github but i write in idle(or) jupyter and uploade them in github.
  - Did you work with a team (>2 programmers) in github?
    No
  - Did you use Github Actions?
   No
  - Did you clone a Github repository in your personal computer?
  yeah , i did many times.
  - Can you share your own github repository?
  yeah , https://github.com/samdansk2/Python3.git

**Others**

- Share any program you have written (in any programming language) that you are very proud of
 yes i have written many programs , recently i solved one problem 
 #Program to return the sum in between given inclusive range :
 def sam (arr,l,r):
    n=len(arr)
    arr1=[]
    for i in range(n):
        for j in range(i+1,n):
            ab=arr[i]+arr[j]
            arr1.append(ab)
    count=0
    for i in range(len(arr1)):
        if arr1[i]>=l and arr1[i]<=r:
            count+=1
        else:
            continue
    return count

arr=list(map(int,input().split()))
l=int(input())
r=int(input())
k=sam(arr,l,r)
print(k)

- Share a communication or email that you are proud of
 yes , s180716@rguktsklm.ac.in this is my mail id you can communicate with me in anytime.
